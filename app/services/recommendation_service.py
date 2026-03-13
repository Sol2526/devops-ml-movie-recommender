from sqlmodel import Session

from app.schemas.preferences import SurveyPreferencesRequest
from app.schemas.recommendations import (
    RecommendationPreviewResponse,
    RecommendationScoreBreakdown,
    RecommendedMovie,
)
from app.services.feedback_service import (
    get_all_feedback_movie_ids,
    get_bad_pick_movie_ids,
    get_watch_again_movie_ids,
)
from app.services.preferences_service import (
    build_resolved_preferences_profile,
    normalize_preferences,
)
from app.services.tmdb_client import (
    build_movie_profile,
    fetch_movie_recommendations_from_tmdb,
)


def extract_seed_movie_ids(resolved_preferences) -> list[int]:
    seed_movie_ids = []

    for resolved_movie in resolved_preferences.resolved_favorite_movies:
        if resolved_movie.was_matched and resolved_movie.movie_id is not None:
            seed_movie_ids.append(resolved_movie.movie_id)

    return seed_movie_ids


def extract_disliked_movie_ids(resolved_preferences) -> set[int]:
    disliked_movie_ids = set()

    for resolved_movie in resolved_preferences.resolved_disliked_movies:
        if resolved_movie.was_matched and resolved_movie.movie_id is not None:
            disliked_movie_ids.add(resolved_movie.movie_id)

    return disliked_movie_ids


def collect_candidate_movies(seed_movie_ids: list[int]) -> dict[int, dict]:
    candidate_movies_by_id: dict[int, dict] = {}

    for seed_movie_id in seed_movie_ids:
        recommendation_candidates = fetch_movie_recommendations_from_tmdb(seed_movie_id)

        for candidate_movie in recommendation_candidates:
            candidate_movie_id = candidate_movie.get("id")

            if candidate_movie_id is None:
                continue

            # de-duplicate by movie ID so the same candidate can be suggested by multiple seed movies without appearing multiple times in the final list.
            candidate_movies_by_id[candidate_movie_id] = candidate_movie

    return candidate_movies_by_id


def extract_lowercase_set(values: list[str]) -> set[str]:
    return {value.strip().lower() for value in values if value.strip()}


def build_feedback_profile(
    session: Session,
    feedback_bucket: str,
) -> tuple[set[str], set[str]]:
    if feedback_bucket == "bad_pick":
        feedback_movie_ids = get_bad_pick_movie_ids(session)
    elif feedback_bucket == "watch_again":
        feedback_movie_ids = get_watch_again_movie_ids(session)
    else:
        feedback_movie_ids = set()

    profile_genres: set[str] = set()
    profile_actors: set[str] = set()

    for movie_id in feedback_movie_ids:
        movie_profile = build_movie_profile(movie_id)

        movie_details = movie_profile["movie"]
        movie_credits = movie_profile["credits"]

        movie_genres = {
            genre.lower()
            for genre in movie_details.get("genres", [])
            if genre.strip()
        }

        movie_actor_names = {
            cast_member["name"].strip().lower()
            for cast_member in movie_credits.get("cast", [])
            if cast_member.get("name") and cast_member["name"].strip()
        }

        profile_genres.update(movie_genres)
        profile_actors.update(movie_actor_names)

    # these profiles are from stored feedback so the recommender can react
    # to actual viewing behavior before we add a more advanced training pipeline.
    return profile_genres, profile_actors


def score_candidate_movie(
    movie_profile: dict,
    favorite_genres: set[str],
    disliked_genres: set[str],
    favorite_actors: set[str],
    disliked_actors: set[str],
    watch_again_genres_from_feedback: set[str],
    watch_again_actors_from_feedback: set[str],
    bad_pick_genres_from_feedback: set[str],
    bad_pick_actors_from_feedback: set[str],
) -> tuple[float, int, int, int, int, int, int, int, int, list[str]]:
    movie_details = movie_profile["movie"]
    movie_credits = movie_profile["credits"]

    movie_genres = [genre.lower() for genre in movie_details.get("genres", [])]
    cast_names = [cast_member["name"] for cast_member in movie_credits.get("cast", [])]
    cast_names_lower = [cast_name.lower() for cast_name in cast_names]

    favorite_genre_matches = sum(1 for genre in movie_genres if genre in favorite_genres)
    disliked_genre_matches = sum(1 for genre in movie_genres if genre in disliked_genres)
    favorite_actor_matches = sum(1 for actor in cast_names_lower if actor in favorite_actors)
    disliked_actor_matches = sum(1 for actor in cast_names_lower if actor in disliked_actors)

    watch_again_genre_matches = sum(
        1 for genre in movie_genres if genre in watch_again_genres_from_feedback
    )
    watch_again_actor_matches = sum(
        1 for actor in cast_names_lower if actor in watch_again_actors_from_feedback
    )

    bad_pick_genre_matches = sum(
        1 for genre in movie_genres if genre in bad_pick_genres_from_feedback
    )
    bad_pick_actor_matches = sum(
        1 for actor in cast_names_lower if actor in bad_pick_actors_from_feedback
    )

    matched_favorite_actors = [
        cast_names[index]
        for index, actor_name in enumerate(cast_names_lower)
        if actor_name in favorite_actors
    ]

    score = 0.0
    score += favorite_genre_matches * 3
    score -= disliked_genre_matches * 4
    score += favorite_actor_matches * 5
    score -= disliked_actor_matches * 6

    # Watch again feedback is a strong positive signal because it tells us the
    # movies the user actively wants to revisit, not just movies they tolerated.
    score += watch_again_genre_matches * 2
    score += watch_again_actor_matches * 3

    # Feedback derived penalties are a little softer than explicit dislikes
    # because they are inferred from past bad picks rather than directly stated.
    score -= bad_pick_genre_matches * 2
    score -= bad_pick_actor_matches * 3

    return (
        score,
        favorite_genre_matches,
        disliked_genre_matches,
        favorite_actor_matches,
        disliked_actor_matches,
        watch_again_genre_matches,
        watch_again_actor_matches,
        bad_pick_genre_matches,
        bad_pick_actor_matches,
        matched_favorite_actors,
    )


def build_recommendation_preview(
    session: Session,
    preferences: SurveyPreferencesRequest,
    offset: int,
    limit: int,
) -> RecommendationPreviewResponse:
    normalized_preferences = normalize_preferences(preferences)
    resolved_preferences = build_resolved_preferences_profile(normalized_preferences)

    seed_movie_ids = extract_seed_movie_ids(resolved_preferences)
    disliked_movie_ids = extract_disliked_movie_ids(resolved_preferences)
    feedback_movie_ids = get_all_feedback_movie_ids(session)

    if not seed_movie_ids:
        # for this first version, it depends on favorite movie seeds because that gives us
        # better candidate quality than guessing from free text genres alone.
        return RecommendationPreviewResponse(
            offset=offset,
            limit=limit,
            total_ranked_candidates=0,
            recommendations_returned=0,
            has_more=False,
            recommendations=[],
        )

    candidate_movies_by_id = collect_candidate_movies(seed_movie_ids)

    favorite_genres = extract_lowercase_set(normalized_preferences.favorite_genres)
    disliked_genres = extract_lowercase_set(normalized_preferences.disliked_genres)
    favorite_actors = extract_lowercase_set(normalized_preferences.favorite_actors)
    disliked_actors = extract_lowercase_set(normalized_preferences.disliked_actors)

    watch_again_genres_from_feedback, watch_again_actors_from_feedback = build_feedback_profile(
        session=session,
        feedback_bucket="watch_again",
    )
    bad_pick_genres_from_feedback, bad_pick_actors_from_feedback = build_feedback_profile(
        session=session,
        feedback_bucket="bad_pick",
    )

    ranked_recommendations: list[RecommendedMovie] = []

    for candidate_movie_id in candidate_movies_by_id:
        if candidate_movie_id in seed_movie_ids:
            continue

        if candidate_movie_id in disliked_movie_ids:
            continue

        if candidate_movie_id in feedback_movie_ids:
            # Once the user has already categorized a movie, we stop recommending it so each new batch feels fresher and more useful!
            continue

        movie_profile = build_movie_profile(candidate_movie_id)

        (
            final_score,
            favorite_genre_matches,
            disliked_genre_matches,
            favorite_actor_matches,
            disliked_actor_matches,
            watch_again_genre_matches,
            watch_again_actor_matches,
            bad_pick_genre_matches,
            bad_pick_actor_matches,
            matched_favorite_actors,
        ) = score_candidate_movie(
            movie_profile=movie_profile,
            favorite_genres=favorite_genres,
            disliked_genres=disliked_genres,
            favorite_actors=favorite_actors,
            disliked_actors=disliked_actors,
            watch_again_genres_from_feedback=watch_again_genres_from_feedback,
            watch_again_actors_from_feedback=watch_again_actors_from_feedback,
            bad_pick_genres_from_feedback=bad_pick_genres_from_feedback,
            bad_pick_actors_from_feedback=bad_pick_actors_from_feedback,
        )

        movie_details = movie_profile["movie"]

        ranked_recommendations.append(
    RecommendedMovie(
        movie_id=movie_details["id"],
        title=movie_details["title"],
        release_date=movie_details.get("release_date"),
        overview=movie_details.get("overview"),
        genres=movie_details.get("genres", []),
        matched_actors=matched_favorite_actors,
        poster_url=movie_details.get("poster_url"),
        backdrop_url=movie_details.get("backdrop_url"),
        score_breakdown=RecommendationScoreBreakdown(
            favorite_genre_matches=favorite_genre_matches,
            disliked_genre_matches=disliked_genre_matches,
            favorite_actor_matches=favorite_actor_matches,
            disliked_actor_matches=disliked_actor_matches,
            watch_again_genre_matches=watch_again_genre_matches,
            watch_again_actor_matches=watch_again_actor_matches,
            bad_pick_genre_matches=bad_pick_genre_matches,
            bad_pick_actor_matches=bad_pick_actor_matches,
            final_score=final_score,
        ),
    )
)

    ranked_recommendations.sort(
        key=lambda recommendation: recommendation.score_breakdown.final_score,
        reverse=True,
    )

    paged_recommendations = ranked_recommendations[offset:offset + limit]
    total_ranked_candidates = len(ranked_recommendations)
    has_more = offset + limit < total_ranked_candidates

    return RecommendationPreviewResponse(
        offset=offset,
        limit=limit,
        total_ranked_candidates=total_ranked_candidates,
        recommendations_returned=len(paged_recommendations),
        has_more=has_more,
        recommendations=paged_recommendations,
    )