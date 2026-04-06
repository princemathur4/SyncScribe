from sqlalchemy import (
    Column, Integer, String, Text, ForeignKey,
    DateTime, Index
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import TSVECTOR
from .database.postgres import Base


class User(Base):
    __tablename__ = "users"

    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # pages this user last edited
    created_pages = relationship("Page", back_populates="creator", foreign_keys="Page.created_by")
    edited_pages = relationship("Page", back_populates="last_editor", foreign_keys="Page.last_edited_by")


class Page(Base):
    __tablename__ = "pages"

    title = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, nullable=False, index=True)
    body = Column(Text, nullable=False, default="")
    # Self-referential: null parent_id means this is a root-level page
    parent_id = Column(Integer, ForeignKey("pages.id", ondelete="SET NULL"), nullable=True)

    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    last_edited_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    # full-text search vector column, updated by a Postgres trigger
    search_vector = Column(TSVECTOR)

    # children: pages that have this page as their parent
    # parent:   the page this page belongs to
    children = relationship(
        "Page",
        back_populates="parent",
        foreign_keys=[parent_id],
        cascade="all",
    )
    parent = relationship("Page", back_populates="children", remote_side="Page.id")
    creator = relationship("User", back_populates="created_pages", foreign_keys=[created_by])
    last_editor = relationship("User", back_populates="edited_pages", foreign_keys=[last_edited_by])

    __table_args__ = (
        Index("ix_pages_search_vector", "search_vector", postgresql_using="gin"),
    )
