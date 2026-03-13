import os

import requests
from dotenv import load_dotenv
from fastapi import HTTPException

from app.services.cache_service import (
    get_cached_movie_profile,
    get_cached_movie_recommendations,
    set_cached_movie_profile,
    set_cached_movie_recommendations,
)

# Loading the .env file here to keep module self contained and avoids depending on import order in other files.
load_dotenv()

TMDB_API_KEY = os.getenv("TMDB_API_KEY")
TMDB_SEARCH_MOVIE_URL = "https://api.themoviedb.org/3/search/movie"
DEFAULT_SEARCH_TERM = "batman"
MAX_RESULTS_PER_PAGE = 5
REQUEST_TIMEOUT_SECONDS = 30
MAX_CAST_MEMBERS = 10
MAX_RECOMMENDATION_CANDIDATES_PER_SEED = 10
TMDB_IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w500"
TMDB_BACKDROP_BASE_URL = "https://image.tmdb.org/t/p/original"

def build_poster_url(poster_path: str | None) -> str | None:
    if not poster_path:
        return None

    return f"{TMDB_IMAGE_BASE_URL}{poster_path}"


def build_backdrop_url(backdrop_path: str | None) -> str | None:
    if not backdrop_path:
        return None

    return f"{TMDB_BACKDROP_BASE_URL}{backdrop_path}"


def is_tmdb_configured() -> bool:
    return bool(TMDB_API_KEY)


def build_tmdb_search_params(search_term: str) -> dict:
    return {
        "api_key": TMDB_API_KEY,
        "query": search_term,
    }


def fetch_movies_from_tmdb(search_term: str) -> list[dict]:
    if not is_tmdb_configured():
        raise HTTPException(status_code=500, detail="TMDB API key not found in environment")

    response = requests.get(
        TMDB_SEARCH_MOVIE_URL,
        params=build_tmdb_search_params(search_term),
        timeout=REQUEST_TIMEOUT_SECONDS,
    )

    try:
        response.raise_for_status()
    except requests.HTTPError as exc:
        raise HTTPException(status_code=502, detail="TMDB request failed") from exc

    tmdb_payload = response.json()
    movie_results = tmdb_payload.get("results", [])
    return movie_results[:MAX_RESULTS_PER_PAGE]


def format_movie_summary(movie: dict) -> dict:
    poster_path = movie.get("poster_path")
    backdrop_path = movie.get("backdrop_path")

    # image URLs so the future frontend can render movie cards
    # without needing to understand TMDb's image path format on its own.
    return {
        "id": movie.get("id"),
        "title": movie.get("title"),
        "release_date": movie.get("release_date"),
        "overview": movie.get("overview"),
        "poster_path": poster_path,
        "poster_url": build_poster_url(poster_path),
        "backdrop_path": backdrop_path,
        "backdrop_url": build_backdrop_url(backdrop_path),
    }

def build_movie_details_url(movie_id: int) -> str:
    return f"https://api.themoviedb.org/3/movie/{movie_id}"


def fetch_movie_details_from_tmdb(movie_id: int) -> dict:
    if not is_tmdb_configured():
        # stop here so missing configuration shows up as our own clear error, andnot as some vague failure from the request layer.
        raise HTTPException(status_code=500, detail="TMDB API key not found in environment")

    response = requests.get(
        build_movie_details_url(movie_id),
        params={"api_key": TMDB_API_KEY},
        timeout=REQUEST_TIMEOUT_SECONDS,
    )

    if response.status_code == 404:
        # A missing movie is a normal app case, so we return a 404.
        raise HTTPException(status_code=404, detail="Movie not found")

    try:
        response.raise_for_status()
    except requests.HTTPError as exc:
        # Keep the response generic so our API stays consistent even if
        # TMDb changes the wording of their upstream errors.
        raise HTTPException(status_code=502, detail="TMDB movie details request failed") from exc

    return response.json()


def format_movie_details(movie: dict) -> dict:
    genre_names = [genre.get("name") for genre in movie.get("genres", []) if genre.get("name")]
    poster_path = movie.get("poster_path")
    backdrop_path = movie.get("backdrop_path")

    # shape the response here so the route stays small and the frontend gets
    # a stable payload even if TMDb returns many extra fields we do not need yet.
    return {
        "id": movie.get("id"),
        "title": movie.get("title"),
        "release_date": movie.get("release_date"),
        "runtime_minutes": movie.get("runtime"),
        "genres": genre_names,
        "tmdb_vote_average": movie.get("vote_average"),
        "overview": movie.get("overview"),
        "poster_path": poster_path,
        "poster_url": build_poster_url(poster_path),
        "backdrop_path": backdrop_path,
        "backdrop_url": build_backdrop_url(backdrop_path),
    }

def build_movie_credits_url(movie_id: int) -> str:
    return f"https://api.themoviedb.org/3/movie/{movie_id}/credits"


def fetch_movie_credits_from_tmdb(movie_id: int) -> dict:
    if not is_tmdb_configured():
        # handling missing configuration right here so every TMDb facing function fails in the same clear way.
        raise HTTPException(status_code=500, detail="TMDB API key not found in environment")

    response = requests.get(
        build_movie_credits_url(movie_id),
        params={"api_key": TMDB_API_KEY},
        timeout=REQUEST_TIMEOUT_SECONDS,
    )

    if response.status_code == 404:
        # A missing movie should look like a normal not-found response to the client,not like an infrastructure problem.
        raise HTTPException(status_code=404, detail="Movie credits not found")

    try:
        response.raise_for_status()
    except requests.HTTPError as exc:
        # keep the upstream error hidden so our API contract stays stable.
        raise HTTPException(status_code=502, detail="TMDB movie credits request failed") from exc

    return response.json()


def format_cast_member(cast_member: dict) -> dict:
    return {
        "id": cast_member.get("id"),
        "name": cast_member.get("name"),
        "character": cast_member.get("character"),
        "popularity": cast_member.get("popularity"),
    }


def format_movie_credits(credits_payload: dict) -> dict:
    raw_cast_members = credits_payload.get("cast", [])
    limited_cast_members = raw_cast_members[:MAX_CAST_MEMBERS]
    formatted_cast_members = [
        format_cast_member(cast_member)
        for cast_member in limited_cast_members
    ]

    # (intentional)) keeping the cast list short for now because recommendation
    # matching usually cares more about top billed actors than the full credits page.
    return {
        "cast_count": len(formatted_cast_members),
        "cast": formatted_cast_members,
    }

def build_movie_profile(movie_id: int) -> dict:
    cached_movie_profile = get_cached_movie_profile(movie_id)

    if cached_movie_profile is not None:
        return cached_movie_profile

    movie_details = fetch_movie_details_from_tmdb(movie_id)
    movie_credits = fetch_movie_credits_from_tmdb(movie_id)

    formatted_movie_details = format_movie_details(movie_details)
    formatted_movie_credits = format_movie_credits(movie_credits)

    movie_profile = {
        "movie": formatted_movie_details,
        "credits": formatted_movie_credits,
    }

    # A combined movie profile is requested often by the recommendation logic,
    # so caching it avoids repeating both details and credits lookups.
    set_cached_movie_profile(movie_id, movie_profile)

    return movie_profile

def fetch_first_movie_match_from_tmdb(search_term: str) -> dict | None:
    search_results = fetch_movies_from_tmdb(search_term)

    if not search_results:
        return None

    return search_results[0]


def format_resolved_movie_match(search_term: str, movie: dict | None) -> dict:
    if not movie:
        return {
            "search_term": search_term,
            "was_matched": False,
            "movie_id": None,
            "title": None,
            "release_date": None,
            "overview": None,
        }

    # Keep the matched payload small for now.. only because the goal is to identify
    # the movie cleanly before we start pulling in heavier profile data.
    return {
        "search_term": search_term,
        "was_matched": True,
        "movie_id": movie.get("id"),
        "title": movie.get("title"),
        "release_date": movie.get("release_date"),
        "overview": movie.get("overview"),
    }


def resolve_movie_title_to_match(search_term: str) -> dict:
    matched_movie = fetch_first_movie_match_from_tmdb(search_term)
    return format_resolved_movie_match(search_term, matched_movie)

def build_movie_recommendations_url(movie_id: int) -> str:
    return f"https://api.themoviedb.org/3/movie/{movie_id}/recommendations"


def fetch_movie_recommendations_from_tmdb(movie_id: int) -> list[dict]:
    cached_recommendations = get_cached_movie_recommendations(movie_id)

    if cached_recommendations is not None:
        return cached_recommendations

    if not is_tmdb_configured():
        # fail early so recommendation routes behave consistently with the rest of the TMDb client when configuration is missing.
        raise HTTPException(status_code=500, detail="TMDB API key not found in environment")

    response = requests.get(
        build_movie_recommendations_url(movie_id),
        params={"api_key": TMDB_API_KEY},
        timeout=REQUEST_TIMEOUT_SECONDS,
    )

    if response.status_code == 404:
        raise HTTPException(status_code=404, detail="Movie recommendations not found")

    try:
        response.raise_for_status()
    except requests.HTTPError as exc:
        raise HTTPException(status_code=502, detail="TMDB movie recommendations request failed") from exc

    tmdb_payload = response.json()
    recommendation_results = tmdb_payload.get("results", [])
    limited_recommendation_results = recommendation_results[:MAX_RECOMMENDATION_CANDIDATES_PER_SEED]

    # Recommendation candidates for a given movie do not need to be re fetched
    # on every request during local development, so a short cache gives speed
    # without making the code so much more complex than it already is...
    set_cached_movie_recommendations(movie_id, limited_recommendation_results)

    return limited_recommendation_results


def format_recommendation_candidate(movie: dict) -> dict:
    poster_path = movie.get("poster_path")
    backdrop_path = movie.get("backdrop_path")

    return {
        "id": movie.get("id"),
        "title": movie.get("title"),
        "release_date": movie.get("release_date"),
        "overview": movie.get("overview"),
        "poster_path": poster_path,
        "poster_url": build_poster_url(poster_path),
        "backdrop_path": backdrop_path,
        "backdrop_url": build_backdrop_url(backdrop_path),
    }