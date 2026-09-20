"""SQLAlchemy persistence models for catalog metadata."""

from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def utc_now() -> datetime:
    return datetime.now(UTC)


class Base(DeclarativeBase):
    pass


class Movie(Base):
    __tablename__ = "movies"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    original_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    year: Mapped[int | None] = mapped_column(nullable=True)
    description: Mapped[str] = mapped_column(Text, default="")
    poster_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    backdrop_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    runtime_seconds: Mapped[int | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )
    media_sources: Mapped[list["MediaSource"]] = relationship(
        back_populates="movie", cascade="all, delete-orphan"
    )


class MediaSource(Base):
    __tablename__ = "media_sources"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    movie_id: Mapped[str] = mapped_column(
        ForeignKey("movies.id", ondelete="CASCADE"), unique=True, index=True
    )
    source_type: Mapped[str] = mapped_column(String(32), default="torrent")
    torrent_uri: Mapped[str] = mapped_column(Text)
    info_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    preferred_file_index: Mapped[int | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now
    )
    movie: Mapped[Movie] = relationship(back_populates="media_sources")
