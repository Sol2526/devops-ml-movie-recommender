def test_survey_preferences_normalizes_and_counts_values(client):
    request_body = {
        "favorite_genres": [" Sci-Fi ", "Action", ""],
        "disliked_genres": [" Romance "],
        "favorite_actors": [" Keanu Reeves "],
        "disliked_actors": [""],
        "favorite_movies": [" The Matrix "],
        "disliked_movies": [" Movie 43 "],
    }

    response = client.post("/survey/preferences", json=request_body)

    assert response.status_code == 200

    payload = response.json()
    assert payload["favorite_genres"] == ["Sci-Fi", "Action"]
    assert payload["disliked_genres"] == ["Romance"]
    assert payload["favorite_actors"] == ["Keanu Reeves"]
    assert payload["favorite_movies"] == ["The Matrix"]
    assert payload["disliked_movies"] == ["Movie 43"]
    assert payload["total_preferences_received"] == 6