def test_cache_stats_route_returns_expected_keys(client):
    response = client.get("/cache/stats")

    assert response.status_code == 200

    payload = response.json()
    assert "movie_profile_cache_entries" in payload
    assert "movie_recommendations_cache_entries" in payload


def test_cache_clear_route_returns_success_message(client):
    response = client.post("/cache/clear")

    assert response.status_code == 200

    payload = response.json()
    assert payload["message"] == "All caches cleared"