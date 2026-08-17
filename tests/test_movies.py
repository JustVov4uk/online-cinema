from fastapi.testclient import TestClient


def test_list_movies_returns_200(client: TestClient) -> None:
    response = client.get("/api/v1/movies")

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_retrieve_unknown_movie_returns_404(client: TestClient) -> None:
    response = client.get("/api/v1/movies/999999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Movie not found."}
