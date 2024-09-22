import daemon
import pathlib
import watchdog
import watchdog.events
import watchdog.observers
import psycopg
import sqlalchemy
from .cgdb import Author, CGUser, Document, Isbn10, Isbn13, Doi, Arxiv
from .parsemail import parse_mail_from_file, parse_address_from_file
from .idparser import IDType, idparse
from .docid import lookup_doc
from .utils import remove_first

FQDN = "communalgrowth.org"
DB_URL = "postgresql+psycopg://tiger@localhost:5432/communalgrowth-database"


def make_doc(doctype, docdata):
    """Return a newly-minted instance of a table entry for (doctype, docdata)

    docdata is expected to be the return value of docid.lookup_doc()"""
    doc = None
    match doctype:
        case x if x in [IDType.ISBN10, IDType.ISBN13]:
            isbn10 = Isbn10(isbn10=docdata["isbn10"])
            isbn13 = Isbn10(isbn10=docdata["isbn13"])
            authors = [Author(author=author) for author in docdata["authors"]]
            doc = Document(
                title=docdata["title"],
                isbn10=isbn10,
                isbn13=isbn13,
                authors=authors,
            )
        case IDType.DOI:
            doi = Doi(doi=docdata["doi"])
            authors = [Author(author=author) for author in docdata["authors"]]
            doc = Document(
                title=docdata["title"],
                doi=doi,
                authors=authors,
            )
        case IDType.ARXIV:
            arxiv = Arxiv(arxiv=docdata["arxiv"])
            authors = [Author(author=author) for author in docdata["authors"]]
            doc = Document(
                title=docdata["title"],
                arxiv=arxiv,
                authors=authors,
            )
    return doc


def db_select_doc(session, doctype, docid):
    """Query the database for the particular (doctype, docid) combination

    Returns None if not found, otherwise returns a Document instance.
    """
    result = None
    match doctype:
        case IDType.ISBN10:
            result = session.query(Isbn10).where(Isbn10.isbn10 == docid).one_or_none()
        case IDType.ISBN13:
            result = session.query(Isbn13).where(Isbn13.isbn13 == docid).one_or_none()
        case IDType.DOI:
            result = session.query(Doi).where(Doi.Doi == docid).one_or_none()
        case IDType.ARXIV:
            result = session.query(Arxiv).where(Arxiv.arxiv == docid).one_or_none()
    return result


def db_select_user(session, addr):
    """Query the database for the user with e-mail address addr

    Returns None if not found, otherwise returns a CGUser instance.
    """
    result = session.query(CGUser).where(CGUser.email == addr).one_or_none()
    return result


def db_subscribe(Session, mail_path):
    """Subscribe user to document IDs

    The mail_path denotes an e-mail sent by the user to the subscribe
    address. It contains a list of document IDs, such as ISBN, doi,
    arXiv IDs. These IDs will be looked up online if they are not
    found in the database, and the user will be subscribed to these
    IDs.
    """
    # Parse the sender address and textual body of the e-mail.
    sender_addr, body = parse_mail_from_file(mail_path)
    # Apart from splitting on newlines, we also want to split on
    # commas.
    ids = [idparse(token) for line in body for token in line.split(",")]
    ids = [(doctype, docid) for (doctype, docid) in ids if doctype != IDType.TITLE]
    # For each requested ID, check if it already exists in the
    # database; if not, look it up on the internet first. Then proceed
    # to subscribing the user to the document.
    with Session() as session:
        user = db_select_user(session, sender_addr)
        if not user:
            user = CGUser(email=sender_addr)
            session.add(user)
        for doctype, docid in ids:
            doc = db_select_doc(session, doctype, docid)
            if not doc:
                # We need to lookup the document online because it
                # does not have an entry in the database.
                docdata = lookup_doc(doctype, docid)
                if not docdata:
                    # Internet lookup failure; just ignore this.
                    # TODO: here I should be inserting the failure in
                    # a table in the database along with a timestamp
                    # to avoid performing the same mistake too often.
                    continue
                doc = make_doc(doctype, docdata)
                session.add(doc)
            if not any(sender_addr == user.email for user in doc.cgusers):
                doc.cgusers.append(user)
        session.commit()


def db_unsubscribe(Session, mail_path):
    """Unsubscribe user from document IDs

    The mail_path denotes an e-mail sent by the user to the subscribe
    address. It contains a list of document IDs, such as ISBN, doi,
    arXiv IDs. The user will be unsubscribed from these IDs. If the
    user ends up with no subscriptions, the user is removed from the
    database.
    """
    sender_addr, body = parse_mail_from_file(mail_path)
    ids = [idparse(token) for line in body for token in line.split(",")]
    ids = [(doctype, docid) for (doctype, docid) in ids if doctype != IDType.TITLE]
    with Session() as session:
        user = db_select_user(session, sender_addr)
        if not user:
            return
        for doctype, docid in ids:
            match doctype:
                case IDType.ISBN10:
                    remove_first(
                        lambda doc: doc.isbn10 == docid,
                        user.documents,
                    )
                case IDType.ISBN13:
                    remove_first(
                        lambda doc: doc.isbn13 == docid,
                        user.documents,
                    )
                case IDType.DOI:
                    remove_first(
                        lambda doc: doc.doi == docid,
                        user.documents,
                    )
                case IDType.ARXIV:
                    remove_first(
                        lambda doc: doc.isbn13 == docid,
                        user.documents,
                    )
        if not user.documents:
            session.delete(user)
        session.commit()


def db_forget(Session, mail_path):
    """Delete all mentions of user from database

    The email in mail_path is parsed for the sender address and all
    mentions of that address are removed from the database.
    """
    sender_addr = parse_address_from_file(mail_path)
    with Session() as session:
        result = session.query(CGUser).where(CGUser.email == sender_addr)
        if result:
            session.delete(result)
            session.commit()


class ProcessMaildir(watchdog.events.FileSystemEventHandler):
    def __init__(self, Session):
        super().__init__()
        self.Session = Session

    def on_closed(self, event):
        """Callback when email arrives in Maildir"""
        path = pathlib.Path(event.src_path)
        account = path.parents[-2].stem
        match account:
            case "subscribe":
                try:
                    db_subscribe(self.Session, path)
                except:
                    pass
                path.unlink()
            case "unsubscribe":
                try:
                    db_unsubscribe(self.Session, path)
                except:
                    pass
                path.unlink()
            case "forget":
                try:
                    db_forget(self.Session, path)
                except:
                    pass
                path.unlink()


def main():
    wd = pathlib.Path("/var/mail/vhosts") / FQDN
    with daemon.DaemonContext(
        working_directory=str(wd),
        detach_process=True,
    ):
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
        Session = sessionmaker(bind=engine)
        # Set up the Maildir event handler.
        event_handler = ProcessMaildir(Session)
        observer = watchdog.observers.Observer()
        observer.schedule(event_handler, ".", recursive=True)
        observer.start()
        try:
            while observer.is_alive():
                observer.join(1)
        finally:
            observer.stop()
            observer.join()


# ----- CUT here ------------

# Create the SQLAlchemy engine; the password is specified in the .pgpass file.
engine = create_engine(
    "postgresql+psycopg://tiger@localhost:5432/communalgrowth-database"
)

# Create all tables defined by Base subclasses
Base.metadata.create_all(engine)

# Create a session
Session = sessionmaker(bind=engine)

doc = Document(
    title="Advanced Classical Electromagnetism",
    type=DocType.BOOK,
)
author = Author(author="R. Wald")
doc.authors += [author]
user_1 = CGUser(email="george@example.com")
user_2 = CGUser(email="christina@example.com")

# SELECT statements.
stmt = select(Document).where(Document.title == doc.title)
stmt_u_1 = select(CGUser).where(CGUser.email == user_1.email)

with Session() as session:
    # Insert the data
    result = session.execute(stmt).one_or_none()
    if not result:
        session.add(doc)
        session.commit()
        doc.isbn10 = Isbn10(isbn10="0691220395")
        doc.isbn13 = Isbn13(isbn13="9780691220390")
        doc.cgusers += [user_1, user_2]
        session.commit()

    # Notice how we asked for a Document but we got the corresponding
    # Isbn10 entry "for free" in x.isbn10! If it didn't exist, it'd be
    # None.
    x = session.query(Document).one()
    print((x.id, x.title, x.authors, x.type, x.isbn10))
    [print(f"{x.id} <-> {u.email}") for u in x.cgusers]

    # We can just delete an association if we want.

    # Let's delete the user entirely.
    u_1 = session.execute(stmt_u_1).one()
    session.delete(u_1[0])
    # Let's only delete the association, keeping the user.  DELETE
    # statement for the doc <-> user_2 association.
    # The `sqlalchemy.exc.NoResultFound` exception will be thrown if
    # the entry does not exist.
    session.execute(
        delete(cguser_document_association).where(
            (cguser_document_association.c.email == user_2.email)
            & (cguser_document_association.c.doc_id == doc.id)
        )
    )
    session.commit()
