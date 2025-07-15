"""search.py

The module enabling the search functionality on the website.

"""

from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload
from app.cgdb import Document
from app.utils import strip_to_alphanum


def doc_to_result(doc):
    """Convert a document to a search result."""
    return (
        doc.title,
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
        .options(selectinload(Document.authors))
        .options(selectinload(Document.cgusers))
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
        .options(selectinload(Document.authors))
        .options(selectinload(Document.cgusers))
        .filter(Document.cgusers.any())
        .order_by(desc(Document.id))
        .limit(limit)
    )
    async with Session() as session:
        results = await session.execute(stmt)
    return [doc_to_result(doc) for doc in results.scalars().all()]
