"""search.py

The module enabling the search functionality on the website.

"""

from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload
from app.cgdb import Document
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


def doc_to_result(doc):
    """Convert a document to a search result."""
    return (
        doc.title,
        doc_stringify_id(doc),
        ", ".join([a.author for a in doc.authors]),
        ", ".join([u.email for u in doc.cgusers]),
    )


async def search_documents(Session, search_term, limit=100):
    """Search database documents (title and author last names)

    Limits results up to 'limit' rows.
    Session must be created by async_sessionmaker()."""
    stripped = strip_to_alphanum(search_term)
    stmt = (
        select(Document)
        .options(
            selectinload(Document.authors),
            selectinload(Document.cgusers),
            selectinload(Document.isbn10),
            selectinload(Document.isbn13),
            selectinload(Document.doi),
            selectinload(Document.arxiv),
        )
        .filter(Document.tsv_title.match(stripped))
        .limit(limit)
    )
    async with Session() as session:
        results = await session.execute(stmt)
    return [doc_to_result(doc) for doc in results.scalars().all()]


async def search_recent(Session, limit=10):
    """Search database for the most recent documents.

    Skips the books with no subscribers."""
    stmt = (
        select(Document)
        .options(
            selectinload(Document.authors),
            selectinload(Document.cgusers),
            selectinload(Document.isbn10),
            selectinload(Document.isbn13),
            selectinload(Document.doi),
            selectinload(Document.arxiv),
        )
        .filter(Document.cgusers.any())
        .order_by(desc(Document.id))
        .limit(limit)
    )
    async with Session() as session:
        results = await session.execute(stmt)
    return [doc_to_result(doc) for doc in results.scalars().all()]
