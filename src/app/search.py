"""search.py

The module enabling the search functionality on the website.

"""

from sqlalchemy import select, func, text
from sqlalchemy.orm import selectinload
from app.cgdb import Document
from app.utils import strip_to_alphanum


async def search_documents(Session, search_term, limit=100):
    """Search database documents (title and author last names)

    Limits results up to 'limit' rows.
    Session must be created by async_sessionmaker()."""
    stripped = strip_to_alphanum(search_term)
    stmt = (
        select(Document)
        .options(selectinload(Document.authors))
        .filter(Document.tsv_title.match(stripped))
        .limit(limit)
    )
    async with Session() as session:
        results = await session.execute(stmt)
    return [
        (doc.title, ", ".join([a.author for a in doc.authors]))
        for doc in results.scalars().all()
    ]
