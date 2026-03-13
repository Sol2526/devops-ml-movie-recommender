from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


VALID_FEEDBACK_BUCKETS = {"seen", "watch_again", "bad_pick"}


def get_current_utc_time() -> datetime:
    # Stored timezone UTC timestamps so feedback stays consistent across envs and future deployments.
    return datetime.now(UTC)


class MovieFeedback(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    movie_id: int = Field(index=True)
    movie_title: str
    feedback_bucket: str = Field(index=True)
    reason_tags: str = ""
    free_text_reason: str = ""
    created_at: datetime = Field(default_factory=get_current_utc_time)