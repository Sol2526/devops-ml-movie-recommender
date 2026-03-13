from datetime import datetime
from pydantic import BaseModel, Field


class MovieFeedbackCreateRequest(BaseModel):
    movie_id: int
    movie_title: str
    feedback_bucket: str = Field(pattern="^(seen|watch_again|bad_pick)$")
    reason_tags: list[str] = Field(default_factory=list)
    free_text_reason: str = ""


class MovieFeedbackResponse(BaseModel):
    id: int
    movie_id: int
    movie_title: str
    feedback_bucket: str
    reason_tags: list[str]
    free_text_reason: str
    created_at: datetime