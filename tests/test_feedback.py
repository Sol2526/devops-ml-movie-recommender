def test_create_feedback_and_list_feedback(client):
    create_response = client.post(
        "/feedback",
        json={
            "movie_id": 603,
            "movie_title": "The Matrix",
            "feedback_bucket": "watch_again",
            "reason_tags": ["nostalgic", "great action"],
            "free_text_reason": "Always rewatchable.",
        },
    )

    assert create_response.status_code == 200

    created_feedback = create_response.json()
    assert created_feedback["movie_id"] == 603
    assert created_feedback["movie_title"] == "The Matrix"
    assert created_feedback["feedback_bucket"] == "watch_again"
    assert created_feedback["reason_tags"] == ["nostalgic", "great action"]
    assert created_feedback["free_text_reason"] == "Always rewatchable."

    list_response = client.get("/feedback")

    assert list_response.status_code == 200

    feedback_items = list_response.json()
    assert len(feedback_items) == 1
    assert feedback_items[0]["movie_id"] == 603
    assert feedback_items[0]["feedback_bucket"] == "watch_again"