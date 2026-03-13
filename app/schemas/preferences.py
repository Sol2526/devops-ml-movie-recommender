# Script used to make FastAPI able to validate incoming request automatically. Makes a cleaner route.
from pydantic import BaseModel, Field


class SurveyPreferencesRequest(BaseModel):
    favorite_genres: list[str] = Field(default_factory=list)
    disliked_genres: list[str] = Field(default_factory=list)
    favorite_actors: list[str] = Field(default_factory=list)
    disliked_actors: list[str] = Field(default_factory=list)
    favorite_movies: list[str] = Field(default_factory=list)
    disliked_movies: list[str] = Field(default_factory=list)


class SurveyPreferencesResponse(BaseModel):
    favorite_genres: list[str]
    disliked_genres: list[str]
    favorite_actors: list[str]
    disliked_actors: list[str]
    favorite_movies: list[str]
    disliked_movies: list[str]
    total_preferences_received: int


class ResolvedMovieMatch(BaseModel):
    search_term: str
    was_matched: bool
    movie_id: int | None = None
    title: str | None = None
    release_date: str | None = None
    overview: str | None = None


class ResolvedSurveyPreferencesResponse(BaseModel):
    favorite_genres: list[str]
    disliked_genres: list[str]
    favorite_actors: list[str]
    disliked_actors: list[str]
    favorite_movies: list[str]
    disliked_movies: list[str]
    total_preferences_received: int
    resolved_favorite_movies: list[ResolvedMovieMatch]
    resolved_disliked_movies: list[ResolvedMovieMatch]