from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from sqlmodel import Session

from app.db.session import create_db_and_tables, get_session
from app.schemas.feedback import MovieFeedbackCreateRequest, MovieFeedbackResponse
from app.schemas.preferences import SurveyPreferencesRequest
from app.schemas.recommendations import RecommendationPreviewRequest
from app.services.cache_service import clear_all_caches, get_cache_stats
from app.services.feedback_service import create_movie_feedback, list_movie_feedback
from app.services.preferences_service import (
    build_preferences_profile,
    build_resolved_preferences_profile,
)
from app.services.recommendation_service import build_recommendation_preview
from app.services.tmdb_client import (
    DEFAULT_SEARCH_TERM,
    build_movie_profile,
    fetch_movie_credits_from_tmdb,
    fetch_movie_details_from_tmdb,
    fetch_movies_from_tmdb,
    format_movie_credits,
    format_movie_details,
    format_movie_summary,
    is_tmdb_configured,
)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    # created tables on startup so local development and tests do not depend on a separate setup step.
    create_db_and_tables()
    yield


app = FastAPI(lifespan=lifespan)


@app.get("/")
def home():
    return {"message": "DevOps ML Movie Recommender is running"}


@app.get("/health")
def health():
    return {
        "status": "running",
        "tmdb_api_key_loaded": is_tmdb_configured(),
    }


@app.get("/movie-search")
def movie_search(query: str = DEFAULT_SEARCH_TERM):
    raw_movie_results = fetch_movies_from_tmdb(query)
    formatted_movie_results = [format_movie_summary(movie) for movie in raw_movie_results]

    return {
        "query": query,
        "results_count": len(formatted_movie_results),
        "results": formatted_movie_results,
    }


@app.get("/movies/{movie_id}")
def get_movie_details(movie_id: int):
    raw_movie_details = fetch_movie_details_from_tmdb(movie_id)
    formatted_movie_details = format_movie_details(raw_movie_details)

    return formatted_movie_details


@app.get("/movies/{movie_id}/credits")
def get_movie_credits(movie_id: int):
    raw_movie_credits = fetch_movie_credits_from_tmdb(movie_id)
    formatted_movie_credits = format_movie_credits(raw_movie_credits)

    return formatted_movie_credits


@app.get("/movies/{movie_id}/profile")
def get_movie_profile(movie_id: int):
    return build_movie_profile(movie_id)


@app.post("/survey/preferences")
def create_survey_preferences(preferences: SurveyPreferencesRequest):
    return build_preferences_profile(preferences)


@app.post("/survey/preferences/resolve")
def resolve_survey_preferences(preferences: SurveyPreferencesRequest):
    return build_resolved_preferences_profile(preferences)


@app.post("/recommendations/preview")
def preview_recommendations(
    request: RecommendationPreviewRequest,
    session: Session = Depends(get_session),
):
    return build_recommendation_preview(
        session=session,
        preferences=request.preferences,
        offset=request.offset,
        limit=request.limit,
    )


@app.get("/cache/stats")
def read_cache_stats():
    return get_cache_stats()


@app.post("/cache/clear")
def clear_cache():
    return clear_all_caches()


@app.post("/feedback", response_model=MovieFeedbackResponse)
def submit_movie_feedback(
    feedback_request: MovieFeedbackCreateRequest,
    session: Session = Depends(get_session),
):
    return create_movie_feedback(session, feedback_request)


@app.get("/feedback", response_model=list[MovieFeedbackResponse])
def read_movie_feedback(
    session: Session = Depends(get_session),
):
    return list_movie_feedback(session)