from app.schemas.preferences import (
    ResolvedSurveyPreferencesResponse,
    SurveyPreferencesRequest,
    SurveyPreferencesResponse,
)
from app.services.tmdb_client import resolve_movie_title_to_match


def normalize_text_list(values: list[str]) -> list[str]:
    cleaned_values = []

    for value in values:
        normalized_value = value.strip()

        if normalized_value:
            cleaned_values.append(normalized_value)

    return cleaned_values


def count_total_preferences(preferences: SurveyPreferencesRequest) -> int:
    return (
        len(preferences.favorite_genres)
        + len(preferences.disliked_genres)
        + len(preferences.favorite_actors)
        + len(preferences.disliked_actors)
        + len(preferences.favorite_movies)
        + len(preferences.disliked_movies)
    )


def normalize_preferences(preferences: SurveyPreferencesRequest) -> SurveyPreferencesRequest:
    return SurveyPreferencesRequest(
        favorite_genres=normalize_text_list(preferences.favorite_genres),
        disliked_genres=normalize_text_list(preferences.disliked_genres),
        favorite_actors=normalize_text_list(preferences.favorite_actors),
        disliked_actors=normalize_text_list(preferences.disliked_actors),
        favorite_movies=normalize_text_list(preferences.favorite_movies),
        disliked_movies=normalize_text_list(preferences.disliked_movies),
    )


def build_preferences_profile(
    preferences: SurveyPreferencesRequest,
) -> SurveyPreferencesResponse:
    normalized_preferences = normalize_preferences(preferences)

    # Reminder to self: Here normalizing first gives a stable base profile that later steps can reuse without having to re clean raw user input over and over and oveer.
    return SurveyPreferencesResponse(
        favorite_genres=normalized_preferences.favorite_genres,
        disliked_genres=normalized_preferences.disliked_genres,
        favorite_actors=normalized_preferences.favorite_actors,
        disliked_actors=normalized_preferences.disliked_actors,
        favorite_movies=normalized_preferences.favorite_movies,
        disliked_movies=normalized_preferences.disliked_movies,
        total_preferences_received=count_total_preferences(normalized_preferences),
    )


def resolve_movie_list(movie_titles: list[str]) -> list[dict]:
    resolved_movies = []

    for movie_title in movie_titles:
        resolved_movies.append(resolve_movie_title_to_match(movie_title))

    return resolved_movies


def build_resolved_preferences_profile(
    preferences: SurveyPreferencesRequest,
) -> ResolvedSurveyPreferencesResponse:
    normalized_preferences = normalize_preferences(preferences)

    resolved_favorite_movies = resolve_movie_list(normalized_preferences.favorite_movies)
    resolved_disliked_movies = resolve_movie_list(normalized_preferences.disliked_movies)

    # resolved movie titles after normalization so we do not waste external API calls on empty strings or messy input with extra spaces.
    return ResolvedSurveyPreferencesResponse(
        favorite_genres=normalized_preferences.favorite_genres,
        disliked_genres=normalized_preferences.disliked_genres,
        favorite_actors=normalized_preferences.favorite_actors,
        disliked_actors=normalized_preferences.disliked_actors,
        favorite_movies=normalized_preferences.favorite_movies,
        disliked_movies=normalized_preferences.disliked_movies,
        total_preferences_received=count_total_preferences(normalized_preferences),
        resolved_favorite_movies=resolved_favorite_movies,
        resolved_disliked_movies=resolved_disliked_movies,
    )