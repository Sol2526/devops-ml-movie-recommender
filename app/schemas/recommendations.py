from pydantic import BaseModel, Field

from app.schemas.preferences import SurveyPreferencesRequest


class RecommendationPreviewRequest(BaseModel):
    preferences: SurveyPreferencesRequest
    offset: int = Field(default=0, ge=0)
    limit: int = Field(default=10, ge=1, le=20)


class RecommendationScoreBreakdown(BaseModel):
    favorite_genre_matches: int
    disliked_genre_matches: int
    favorite_actor_matches: int
    disliked_actor_matches: int
    watch_again_genre_matches: int
    watch_again_actor_matches: int
    bad_pick_genre_matches: int
    bad_pick_actor_matches: int
    final_score: float


class RecommendedMovie(BaseModel):
    movie_id: int
    title: str
    release_date: str | None = None
    overview: str | None = None
    genres: list[str]
    matched_actors: list[str]
    poster_url: str | None = None
    backdrop_url: str | None = None
    score_breakdown: RecommendationScoreBreakdown


class RecommendationPreviewResponse(BaseModel):
    offset: int
    limit: int
    total_ranked_candidates: int
    recommendations_returned: int
    has_more: bool
    recommendations: list[RecommendedMovie]