def test_health_route_returns_running_status(client):
    response = client.get("/health")

    assert response.status_code == 200

    payload = response.json()
    assert payload["status"] == "running"
    assert "tmdb_api_key_loaded" in payload