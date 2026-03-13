from time import time


MOVIE_PROFILE_CACHE_TTL_SECONDS = 60 * 30
MOVIE_RECOMMENDATIONS_CACHE_TTL_SECONDS = 60 * 15

movie_profile_cache: dict[int, dict] = {}
movie_recommendations_cache: dict[int, dict] = {}


def build_cache_entry(value, ttl_seconds: int) -> dict:
    expires_at = time() + ttl_seconds

    return {
        "value": value,
        "expires_at": expires_at,
    }


def get_cached_value(cache_store: dict, cache_key):
    cache_entry = cache_store.get(cache_key)

    if not cache_entry:
        return None

    if time() >= cache_entry["expires_at"]:
        # removed expired entries quick so later reads don't keep paying the cost of checking stale cache records.
        del cache_store[cache_key]
        return None

    return cache_entry["value"]


def set_cached_value(cache_store: dict, cache_key, value, ttl_seconds: int) -> None:
    cache_store[cache_key] = build_cache_entry(value, ttl_seconds)


def get_cached_movie_profile(movie_id: int):
    return get_cached_value(movie_profile_cache, movie_id)


def set_cached_movie_profile(movie_id: int, movie_profile: dict) -> None:
    set_cached_value(
        cache_store=movie_profile_cache,
        cache_key=movie_id,
        value=movie_profile,
        ttl_seconds=MOVIE_PROFILE_CACHE_TTL_SECONDS,
    )


def get_cached_movie_recommendations(movie_id: int):
    return get_cached_value(movie_recommendations_cache, movie_id)


def set_cached_movie_recommendations(movie_id: int, recommendations: list[dict]) -> None:
    set_cached_value(
        cache_store=movie_recommendations_cache,
        cache_key=movie_id,
        value=recommendations,
        ttl_seconds=MOVIE_RECOMMENDATIONS_CACHE_TTL_SECONDS,
    )


def get_cache_stats() -> dict:
    return {
        "movie_profile_cache_entries": len(movie_profile_cache),
        "movie_recommendations_cache_entries": len(movie_recommendations_cache),
    }


def clear_all_caches() -> dict:
    cleared_movie_profile_entries = len(movie_profile_cache)
    cleared_movie_recommendation_entries = len(movie_recommendations_cache)

    movie_profile_cache.clear()
    movie_recommendations_cache.clear()

    return {
        "message": "All caches cleared",
        "cleared_movie_profile_entries": cleared_movie_profile_entries,
        "cleared_movie_recommendation_entries": cleared_movie_recommendation_entries,
    }