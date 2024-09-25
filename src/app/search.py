from sqlalchemy import select, func, text
from app.cgdb import Document
from app.utils import strip_to_alphanum


def search_documents(Session, search_term, limit=100):
    """Search database documents (title and author last names)

    Limits results up to 'limit' rows."""
    stripped = strip_to_alphanum(search_term)
    with Session() as session:
        result = (
            session.query(Document)
            .filter(Document.tsv_title.match(stripped))
            .limit(limit)
            .all()
        )
    return result
