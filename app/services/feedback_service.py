from sqlmodel import Session, select

from app.db.models import MovieFeedback
from app.schemas.feedback import MovieFeedbackCreateRequest, MovieFeedbackResponse


def serialize_reason_tags(reason_tags: list[str]) -> str:
    cleaned_tags = []

    for tag in reason_tags:
        normalized_tag = tag.strip()

        if normalized_tag:
            cleaned_tags.append(normalized_tag)

    return ",".join(cleaned_tags)


def deserialize_reason_tags(reason_tags: str) -> list[str]:
    if not reason_tags.strip():
        return []

    return [tag.strip() for tag in reason_tags.split(",") if tag.strip()]


def create_movie_feedback(
    session: Session,
    feedback_request: MovieFeedbackCreateRequest,
) -> MovieFeedbackResponse:
    feedback_record = MovieFeedback(
        movie_id=feedback_request.movie_id,
        movie_title=feedback_request.movie_title.strip(),
        feedback_bucket=feedback_request.feedback_bucket,
        reason_tags=serialize_reason_tags(feedback_request.reason_tags),
        free_text_reason=feedback_request.free_text_reason.strip(),
    )

    # stored the first version of feedback immediately so later recommendation logic can treat the database as the source of truth instead of temporary memory.
    session.add(feedback_record)
    session.commit()
    session.refresh(feedback_record)

    return MovieFeedbackResponse(
        id=feedback_record.id,
        movie_id=feedback_record.movie_id,
        movie_title=feedback_record.movie_title,
        feedback_bucket=feedback_record.feedback_bucket,
        reason_tags=deserialize_reason_tags(feedback_record.reason_tags),
        free_text_reason=feedback_record.free_text_reason,
        created_at=feedback_record.created_at,
    )


def list_movie_feedback(session: Session) -> list[MovieFeedbackResponse]:
    statement = select(MovieFeedback).order_by(MovieFeedback.created_at.desc())
    feedback_records = session.exec(statement).all()

    return [
        MovieFeedbackResponse(
            id=record.id,
            movie_id=record.movie_id,
            movie_title=record.movie_title,
            feedback_bucket=record.feedback_bucket,
            reason_tags=deserialize_reason_tags(record.reason_tags),
            free_text_reason=record.free_text_reason,
            created_at=record.created_at,
        )
        for record in feedback_records
    ]
    
def get_feedback_movie_ids_by_bucket(session: Session, feedback_bucket: str) -> set[int]:
    statement = select(MovieFeedback).where(MovieFeedback.feedback_bucket == feedback_bucket)
    feedback_records = session.exec(statement).all()

    return {record.movie_id for record in feedback_records}


def get_all_feedback_movie_ids(session: Session) -> set[int]:
    statement = select(MovieFeedback)
    feedback_records = session.exec(statement).all()

    return {record.movie_id for record in feedback_records}

def get_bad_pick_movie_ids(session: Session) -> set[int]:
    return get_feedback_movie_ids_by_bucket(session, "bad_pick")

def get_watch_again_movie_ids(session: Session) -> set[int]:
    return get_feedback_movie_ids_by_bucket(session, "watch_again")