#!/usr/bin/env python3

import click
import email
import email.policy
from email.parser import BytesParser
import imaplib
import logging
import pathlib
import psycopg
import sqlalchemy
import sqlalchemy.orm
import ssl
import time
from app.cgdb import (
    Author,
    Base,
    CGUser,
    Document,
    Isbn10,
    Isbn13,
    Doi,
    Arxiv,
    cguser_document_association,
)
from app.conf import DB_URL, FQDN, CG_IMAP_PWD_FILE, CG_TLS_DIR
from app.parsemail import mail_to_docid, parse_address
from app.idparser import IDType
from app.docid import lookup_doc

logging.basicConfig(format="maildirdaemon: %(message)s")
logger = logging.getLogger(__name__)


def create_tls_context(ca: str, cert: str, key: str) -> ssl.SSLContext:
    """Create a TLS context using the root CA and client cert/key.

    The CA is used to verify the IMAP server.

    """
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.check_hostname = False  # We use localhost instead of communalgrowth.org
    ctx.set_ciphers("DEFAULT@SECLEVEL=2")
    ctx.load_verify_locations(ca)
    ctx.load_cert_chain(certfile=cert, keyfile=key)
    return ctx


def make_doc(session, doctype, docdata):
    """Return a newly-minted instance of a table entry for (doctype, docdata)

    docdata is expected to be the return value of docid.lookup_doc().
    """
    match doctype:
        case x if x in [IDType.ISBN10, IDType.ISBN13]:
            doc = Document(title=docdata["title"], authors=[])
            if docdata["isbn10"]:
                doc.isbn10 = Isbn10(isbn10=docdata["isbn10"])
            if docdata["isbn13"]:
                doc.isbn13 = Isbn13(isbn13=docdata["isbn13"])
        case IDType.DOI:
            doi = Doi(doi=docdata["doi"])
            doc = Document(title=docdata["title"], doi=doi, authors=[])
        case IDType.ARXIV:
            arxiv = Arxiv(arxiv=docdata["arxiv"])
            doc = Document(title=docdata["title"], arxiv=arxiv, authors=[])
        case _:
            return None
    for a in docdata["authors"]:
        result = session.query(Author).where(Author.author == a).one_or_none()
        # The author does not exist in the database, create an entry.
        if not result:
            result = Author(author=a)
        doc.authors.append(result)
    return doc


def db_select_doc(session, doctype, docid):
    """Query the database for the particular (doctype, docid) combination

    Returns None if not found, otherwise returns a Document instance.
    """
    result = None
    match doctype:
        case IDType.ISBN10:
            result = (
                session.query(Document)
                .where(Document.isbn10.has(Isbn10.isbn10 == docid))
                .one_or_none()
            )
        case IDType.ISBN13:
            result = (
                session.query(Document)
                .where(Document.isbn13.has(Isbn13.isbn13 == docid))
                .one_or_none()
            )
        case IDType.DOI:
            result = (
                session.query(Document)
                .where(Document.doi.has(Doi.doi == docid))
                .one_or_none()
            )
        case IDType.ARXIV:
            result = (
                session.query(Document)
                .where(Document.arxiv.has(Arxiv.arxiv == docid))
                .one_or_none()
            )
    return result


def db_select_user(session, addr):
    """Query the database for the user with e-mail address addr

    Returns None if not found, otherwise returns a CGUser instance.
    """
    result = session.query(CGUser).where(CGUser.email == addr).one_or_none()
    return result


def db_subscribe(Session, mail):
    """Subscribe user to document IDs.

    mail denotes an EmailMessage sent by the user to the subscribe
    address. It contains in its body a list of document IDs, such as
    ISBN, doi, arXiv IDs. These IDs will be looked up online if they
    are not found in the database, and the user will be subscribed to
    these IDs.

    """
    # Parse the sender address and textual body of the e-mail.
    sender_addr, docids = mail_to_docid(mail)
    # For each requested ID, check if it already exists in the
    # database; if not, look it up on the internet first. Then proceed
    # to subscribing the user to the document.
    with Session() as session:
        user = db_select_user(session, sender_addr)
        if not user:
            user = CGUser(email=sender_addr)
            session.add(user)
        for doctype, docid in docids:
            doc = db_select_doc(session, doctype, docid)
            if not doc:
                # We need to lookup the document online because docid
                # does not have an entry in the database.
                docdata = lookup_doc(doctype, docid)
                if not docdata:
                    # Internet lookup failure; just ignore this.
                    # TODO: here I should be inserting the failure in
                    # a table in the database along with a timestamp
                    # to avoid performing the same mistake too often.
                    continue
                if doctype == IDType.ISBN10:
                    # The subscriber requested an ISBN10 document;
                    # first check that there is no corresponding
                    # ISBN13 already in the database.
                    doc = db_select_doc(session, IDType.ISBN13, docdata["isbn13"])
                    if doc:
                        doc.isbn10 = Isbn10(isbn10=docdata["isbn10"])
                elif doctype == IDType.ISBN13:
                    # The subscriber requested an ISBN13 document;
                    # first check that there is no corresponding
                    # ISBN10 already in the database.
                    doc = db_select_doc(session, IDType.ISBN10, docdata["isbn10"])
                    if doc:
                        doc.isbn13 = Isbn13(isbn13=docdata["isbn13"])
                # If the document simply did not exist, then create a
                # document and add it.
                if not doc:
                    doc = make_doc(session, doctype, docdata)
                    if not doc:
                        continue
                    session.add(doc)
            if not any(sender_addr == user.email for user in doc.cgusers):
                doc.cgusers.append(user)
        session.commit()


def db_unsubscribe(Session, mail):
    """Unsubscribe user from document IDs

    mail is an EmailMessage sent by the user to the subscribe
    address. It contains in its body a list of document IDs, such as
    ISBN, doi, arXiv IDs. The user will be unsubscribed from these
    IDs. If the user ends up with no subscriptions, the user is
    removed from the database.
    """
    sender_addr, docids = mail_to_docid(mail)
    with Session() as session:
        user = db_select_user(session, sender_addr)
        if not user:
            return
        # TODO instead of this loop the deletion can be issued
        # directly to the database...  delete ... where user == myuser
        # and docid == mydocid ...
        docids = [
            doc.id for doc in map(lambda d: db_select_doc(session, *d), docids) if doc
        ]
        session.query(cguser_document_association).filter(
            cguser_document_association.c.email == sender_addr,
            cguser_document_association.c.doc_id.in_(docids),
        ).delete(synchronize_session="fetch")
        # Delete the user if their subscriptions are empty.
        if not user.documents:
            session.delete(user)
        session.commit()


def db_forget(Session, mail):
    """Delete all mentions of user from database

    mail is an EmailMessage and the sender address and all mentions of
    that address are removed from the database.
    """
    sender_addr = parse_address(mail)
    with Session() as session:
        user = db_select_user(session, sender_addr)
        if not user:
            return
        session.delete(user)
        session.commit()


class ProcessMaildir:
    def __init__(self, Session):
        super().__init__()
        self.Session = Session

    def process_mail(self, path):
        """Process received email

        This is the main functionality of the Maildir daemon.

        """
        account = self.parse_account_from_mail(path)
        path = pathlib.Path(path)
        match account:
            case "subscribe":
                try:
                    self.call_with_mail(db_subscribe, path)
                except:
                    pass
                path.unlink()
            case "unsubscribe":
                try:
                    self.call_with_mail(db_unsubscribe, path)
                except:
                    pass
                path.unlink()
            case "forget":
                try:
                    self.call_with_mail(db_forget, path)
                except:
                    pass
                path.unlink()

    def parse_account_from_mail(self, path):
        """Skip e-mail not in correct Maildir with correct account

        Return None or the account string, i.e. one of:
        - "subscribe"
        - "unsubscribe"
        - "forget"
        """
        if not path:
            return None
        path = pathlib.Path(path)
        account = path.parents[-2].stem
        delivered = path.parents[-3].stem
        if delivered != "new":
            return None
        if account not in ["subscribe", "unsubscribe", "forget"]:
            return None
        return account

    def call_with_mail(self, procedure, path):
        """Call procedure with self.Session and an EmailMessage from path

        Returns the return value of procedure.
        """
        with open(path, "rb") as f:
            mail = email.message_from_binary_file(f, policy=email.policy.EmailPolicy())
        return procedure(self.Session, mail)


def maildirdaemon(imap_pwd: bytes):
    """The entry point to the Maildir processing daemon."""
    # Create the SQLAlchemy engine; the password is specified in
    # the .pgpass file.
    engine = sqlalchemy.create_engine(
        DB_URL,
        pool_size=1,
        max_overflow=1,
        pool_pre_ping=True,
        connect_args={"sslmode": "require"},
    )
    # Create all tables defined by Base subclasses, i.e. all
    # tables.
    Base.metadata.create_all(engine)
    # Create a session factory.
    Session = sqlalchemy.orm.sessionmaker(bind=engine)
    # Create a TLS context.
    ctx = create_tls_context(
        ca=f"{CG_TLS_DIR}/ca-cert.pem",
        cert=f"{CG_TLS_DIR}/cg-message-daemon-tls-cert.pem",
        key=f"{CG_TLS_DIR}/cg-message-daemon-tls-key.pem",
    )
    while True:
        process_emails(ctx, Session, imap_pwd)
        time.sleep(10)


def process_emails(ctx, Session, imap_pwd: bytes, batch_size=10):
    actions = [
        ("subscribe", db_subscribe),
        ("unsubscribe", db_unsubscribe),
        ("forget", db_forget),
    ]
    for user, action in actions:
        with imaplib.IMAP4_SSL(host="localhost", port=37419, ssl_context=ctx) as imap:
            imap.login(
                f"{user}@communalgrowth.org*vmail", str(imap_pwd, encoding="utf-8")
            )
            imap.select()
            status, data = imap.uid("SEARCH", "ALL")
            email_ids = sorted(data[0].split(), key=int)[:batch_size]
            for num in email_ids:
                try:
                    status, data = imap.uid("FETCH", num, "(RFC822)")
                    mail = BytesParser(policy=email.policy.EmailPolicy()).parsebytes(
                        data[0][1]
                    )
                    action(Session, mail)
                except:
                    pass
                # Delete the processed file.
                imap.uid("STORE", num, "+FLAGS", "\\Deleted")
                imap.expunge()
            imap.close()


@click.command(context_settings=dict(help_option_names=["-h", "--help"]))
@click.version_option(None, "-v", "--version", package_name="webserver")
def main():
    try:
        with open(CG_IMAP_PWD_FILE, "rb") as f:
            imap_pwd = f.read()
    except FileNotFoundError:
        logger.error("File not found in CG_IMAP_PWD_FILE.")
        exit(1)
    except Exception as e:
        logger.error(f"{e}")
        exit(1)
    maildirdaemon(imap_pwd)


if __name__ == "__main__":
    main()
