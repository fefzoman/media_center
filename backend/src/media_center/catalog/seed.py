"""Idempotent catalog seed data."""

from sqlalchemy.orm import Session

from media_center.persistence.models import MediaSource, Movie

SINTEL_MOVIE_ID = "sintel"
SINTEL_INFO_HASH = "08ada5a7a6183aae1e09d831df6748d566095a10"


def seed_catalog(session: Session, torrent_uri: str) -> None:
    if session.get(Movie, SINTEL_MOVIE_ID) is not None:
        return

    movie = Movie(
        id=SINTEL_MOVIE_ID,
        title="Sintel",
        original_title="Sintel",
        year=2010,
        description=(
            "A young woman searches for the dragon she befriended, following a "
            "trail that leads her through a frozen mountain landscape."
        ),
        poster_url="/tv/assets/posters/sintel.svg",
        backdrop_url=None,
        runtime_seconds=888,
    )
    movie.media_sources.append(
        MediaSource(
            id="source_sintel",
            source_type="torrent",
            torrent_uri=torrent_uri,
            info_hash=SINTEL_INFO_HASH,
            preferred_file_index=None,
        )
    )
    session.add(movie)
    session.commit()
