"""cgdb.py

Provides the ORM class definitions.

"""

from __future__ import annotations
from typing import List

from nameparser import HumanName
from sqlalchemy import (
    func,
    event,
    Index,
    Table,
    Column,
    Integer,
    String,
    ForeignKey,
)
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase, relationship
from sqlalchemy.dialects.postgresql import TSVECTOR


class Base(DeclarativeBase):
    pass


# This table is not subclassing Base because it will not be
# managed/inspected directly.
cguser_document_association = Table(
    "cguser_document",
    Base.metadata,
    Column(
        "doc_id",
        Integer,
        ForeignKey("document.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "email",
        String,
        ForeignKey("cguser.email", ondelete="CASCADE"),
        primary_key=True,
    ),
)


# This table is not subclassing Base because it will not be
# managed/inspected directly.
author_document_association = Table(
    "author_document",
    Base.metadata,
    Column(
        "doc_id",
        Integer,
        ForeignKey("document.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "author",
        String,
        ForeignKey("author.author", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class CGUser(Base):
    __tablename__ = "cguser"
    email: Mapped[str] = mapped_column(primary_key=True)
    documents: Mapped[List["Document"]] = relationship(
        secondary=cguser_document_association,
        back_populates="cgusers",
        passive_deletes=True,
    )


class Author(Base):
    __tablename__ = "author"
    author: Mapped[str] = mapped_column(primary_key=True)
    documents: Mapped[List["Document"]] = relationship(
        secondary=author_document_association,
        back_populates="authors",
        passive_deletes=True,
    )


class Document(Base):
    __tablename__ = "document"
    __table_args__ = (
        Index(
            "idx_tsv_title",
            "tsv_title",
            postgresql_using="gin",
        ),
    )
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column()
    tsv_title = mapped_column(TSVECTOR)
    isbn10: Mapped["Isbn10"] = relationship(back_populates="document")
    isbn13: Mapped["Isbn13"] = relationship(back_populates="document")
    arxiv: Mapped["Arxiv"] = relationship(back_populates="document")
    doi: Mapped["Doi"] = relationship(back_populates="document")
    cgusers: Mapped[List["CGUser"]] = relationship(
        secondary=cguser_document_association,
        back_populates="documents",
        passive_deletes=True,
    )
    authors: Mapped[List["Author"]] = relationship(
        secondary=author_document_association,
        back_populates="documents",
        passive_deletes=True,
    )


@event.listens_for(Document, "before_insert")
@event.listens_for(Document, "before_update")
def populate_tsvector(mapper, connection, target):
    del mapper, connection
    author_last_names = " ".join(
        map(lambda a: HumanName(a.author).last, target.authors)
    )
    title_and_authors = f"{target.title} {author_last_names}"
    target.tsv_title = func.to_tsvector("english", title_and_authors)


class Isbn10(Base):
    __tablename__ = "isbn10"
    isbn10: Mapped[str] = mapped_column(primary_key=True)
    id: Mapped[int] = mapped_column(ForeignKey("document.id"))
    document: Mapped["Document"] = relationship(back_populates="isbn10")


class Isbn13(Base):
    __tablename__ = "isbn13"
    isbn13: Mapped[str] = mapped_column(primary_key=True)
    id: Mapped[int] = mapped_column(ForeignKey("document.id"))
    document: Mapped["Document"] = relationship(back_populates="isbn13")


class Arxiv(Base):
    __tablename__ = "arxiv"
    arxiv: Mapped[str] = mapped_column(primary_key=True)
    id: Mapped[int] = mapped_column(ForeignKey("document.id"))
    document: Mapped["Document"] = relationship(back_populates="arxiv")


class Doi(Base):
    __tablename__ = "doi"
    doi: Mapped[str] = mapped_column(primary_key=True)
    id: Mapped[int] = mapped_column(ForeignKey("document.id"))
    document: Mapped["Document"] = relationship(back_populates="doi")
