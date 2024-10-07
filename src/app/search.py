from sqlalchemy import select, func, text
from app.cgdb import Document
from app.utils import strip_to_alphanum


async def search_documents(Session, search_term, limit=100):
    """Search database documents (title and author last names)

    Limits results up to 'limit' rows.
    Session must be created by async_sessionmaker()."""
    stripped = strip_to_alphanum(search_term)
    async with Session() as session:
        results = await (
            session.query(Document)
            .filter(Document.tsv_title.match(stripped))
            .limit(limit)
            .all()
        )
    return [(doc.title, ", ".join([a.author for a in doc.authors])) for doc in results]
