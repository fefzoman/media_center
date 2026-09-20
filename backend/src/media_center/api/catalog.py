"""Catalog and catalog-backed playback routes."""

from typing import Annotated, Literal
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from media_center.dependencies import (
    get_database_session,
    get_torrent_backend,
)
from media_center.persistence import MediaSource, Movie
from media_center.torrents import (
    NoPlayableMediaError,
    TorrentBackend,
    TorrentBackendError,
    TorrentBackendUnavailable,
    TorrentMetadataTimeout,
    select_media_file,
)

router = APIRouter(tags=["catalog"])


class MovieSummary(BaseModel):
    id: str
    title: str
    year: int | None
    poster_url: str | None
    progress: float = 0.0


class MovieDetail(MovieSummary):
    original_title: str | None
    description: str
    backdrop_url: str | None
    runtime_seconds: int | None


class ClientCapabilities(BaseModel):
    h264: bool = True
    hevc: bool = False
    aac: bool = True
    hls: bool = True


class PlayRequest(BaseModel):
    client_id: str = Field(min_length=1, max_length=128)
    capabilities: ClientCapabilities = Field(default_factory=ClientCapabilities)


class PlayResponse(BaseModel):
    session_id: str
    mode: Literal["direct"] = "direct"
    url: str
    resume_position_seconds: int = 0


def movie_summary(movie: Movie) -> MovieSummary:
    return MovieSummary(
        id=movie.id,
        title=movie.title,
        year=movie.year,
        poster_url=movie.poster_url,
    )


def movie_detail(movie: Movie) -> MovieDetail:
    return MovieDetail(
        **movie_summary(movie).model_dump(),
        original_title=movie.original_title,
        description=movie.description,
        backdrop_url=movie.backdrop_url,
        runtime_seconds=movie.runtime_seconds,
    )


def require_movie(session: Session, movie_id: str) -> Movie:
    movie = session.get(Movie, movie_id)
    if movie is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Movie not found."
        )
    return movie


@router.get("/movies", response_model=list[MovieSummary])
def list_movies(
    session: Annotated[Session, Depends(get_database_session)],
) -> list[MovieSummary]:
    movies = session.scalars(select(Movie).order_by(Movie.title, Movie.id)).all()
    return [movie_summary(movie) for movie in movies]


@router.get("/movies/{movie_id}", response_model=MovieDetail)
def get_movie(
    movie_id: str,
    session: Annotated[Session, Depends(get_database_session)],
) -> MovieDetail:
    return movie_detail(require_movie(session, movie_id))


@router.post("/movies/{movie_id}/play", response_model=PlayResponse)
async def play_movie(
    movie_id: str,
    request: PlayRequest,
    session: Annotated[Session, Depends(get_database_session)],
    backend: Annotated[TorrentBackend, Depends(get_torrent_backend)],
) -> PlayResponse:
    require_movie(session, movie_id)
    source = session.scalar(
        select(MediaSource).where(MediaSource.movie_id == movie_id).limit(1)
    )
    if source is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No media source is configured for this movie.",
        )
    if source.source_type != "torrent":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="The configured media source is unsupported.",
        )

    try:
        handle = await backend.ensure_source(source.torrent_uri)
        torrent_file = select_media_file(
            await backend.list_files(handle), source.preferred_file_index
        )
        stream_url = await backend.get_stream_url(handle, torrent_file.index)
    except TorrentBackendUnavailable as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Torrent service is unavailable.",
        ) from exc
    except TorrentMetadataTimeout as exc:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Movie metadata did not become available before the timeout.",
        ) from exc
    except NoPlayableMediaError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
        ) from exc
    except TorrentBackendError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Torrent service returned an invalid response.",
        ) from exc

    return PlayResponse(
        session_id=f"session_{uuid4().hex}",
        url=stream_url,
    )
