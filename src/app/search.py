# communalgrowth-website, the communalgrowth.org website.
# Copyright (C) 2024  Communal Growth, LLC
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""search.py

The module enabling the search functionality on the website.

"""

from collections import defaultdict

from sqlalchemy import select, desc, func
from sqlalchemy.orm import selectinload
from app.cgdb import Document, CGUser, cguser_document_association
from app.utils import strip_to_alphanum


def doc_stringify_id(doc):
    """Return a string containing the document ID.

    ISBN-13 takes precedence over ISBN-10."""
    if doc.isbn13:
        return f"ISBN-13:{doc.isbn13.isbn13}"
    elif doc.isbn10:
        return f"ISBN-10:{doc.isbn10.isbn10}"
    elif doc.doi:
        return f"doi:{doc.doi.doi}"
    elif doc.arxiv:
        return f"arXiv:{doc.arxiv.arxiv}"
    else:
        return ""


def doc_to_result(doc, cgusers):
    """Convert a document to a search result."""
    return (
        doc.title,
        doc_stringify_id(doc),
        ", ".join(a.author for a in doc.authors),
        ", ".join(u.email for u in cgusers),
    )


async def search_documents(Session, search_term, limit=100, email_limit=10):
    """Search database documents (title and author last names)

    Limits results up to 'limit' rows.
    Session must be created by async_sessionmaker()."""
    stripped = strip_to_alphanum(search_term)
    # fmt: off
    top_docs_subq = (
        select(Document.id)
        .order_by(desc(Document.id))
        .limit(limit)
        .subquery()
    )
    row_number = (
        func.row_number().over(
            partition_by=cguser_document_association.c.doc_id,
            order_by=func.random()
        ).label("rn")
    )
    subq = (
        select(
            cguser_document_association.c.doc_id,
            cguser_document_association.c.email,
            row_number,
        )
        .where(cguser_document_association.c.doc_id.in_(select(top_docs_subq.c.id)))
        .subquery()
    )
    stmt = (
        select(Document, CGUser)
        .options(
            selectinload(Document.authors),
            selectinload(Document.isbn10),
            selectinload(Document.isbn13),
            selectinload(Document.doi),
            selectinload(Document.arxiv),
        )
        .filter(Document.tsv_title.match(stripped))
        .select_from(
            subq
            .join(Document, Document.id == subq.c.doc_id)
            .join(CGUser, CGUser.email == subq.c.email)
        )
        .where(subq.c.rn <= email_limit)
        .order_by(desc(subq.c.doc_id))
    )
    # fmt: on
    async with Session() as session:
        result = await session.execute(stmt)
    d = defaultdict(list)
    for doc, cguser in result.all():
        d[doc].append(cguser)
    return [doc_to_result(doc, d[doc]) for doc in d.keys()]


async def search_recent(Session, limit=10, email_limit=10):
    """Search database for the most recent documents.

    Skips the books with no subscribers. Displays `limit` documents
    with `email_limit` emails.

    """
    # fmt: off
    top_docs_subq = (
        select(Document.id)
        .order_by(desc(Document.id))
        .limit(limit)
        .subquery()
    )
    row_number = (
        func.row_number().over(
            partition_by=cguser_document_association.c.doc_id,
            order_by=func.random()
        ).label("rn")
    )
    subq = (
        select(
            cguser_document_association.c.doc_id,
            cguser_document_association.c.email,
            row_number,
        )
        .where(cguser_document_association.c.doc_id.in_(select(top_docs_subq.c.id)))
        .subquery()
    )
    stmt = (
        select(Document, CGUser)
        .options(
            selectinload(Document.authors),
            selectinload(Document.isbn10),
            selectinload(Document.isbn13),
            selectinload(Document.doi),
            selectinload(Document.arxiv),
        )
        .select_from(
            subq
            .join(Document, Document.id == subq.c.doc_id)
            .join(CGUser, CGUser.email == subq.c.email)
        )
        .where(subq.c.rn <= email_limit)
        .order_by(desc(subq.c.doc_id))
    )
    # fmt: on
    async with Session() as session:
        result = await session.execute(stmt)
    d = defaultdict(list)
    for doc, cguser in result.all():
        d[doc].append(cguser)
    return [doc_to_result(doc, d[doc]) for doc in d.keys()]
