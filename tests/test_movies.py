from uuid import uuid4

from fastapi.testclient import TestClient
from psycopg import connect

from tests.test_auth_login import (
    activate_user_in_database,
    get_sync_database_url,
    unique_email,
)


def test_list_movies_returns_200(client: TestClient) -> None:
    response = client.get("/api/v1/movies")

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_retrieve_unknown_movie_returns_404(client: TestClient) -> None:
    response = client.get("/api/v1/movies/999999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Movie not found."}


def valid_movie_payload(
    name: str | None = None,
    director_id: int = 1,
    certification_id: int = 1,
    genre_ids: list[int] | None = None,
    star_ids: list[int] | None = None,
) -> dict:
    return {
        "name": name or f"Test Movie {uuid4().hex}",
        "year": 2010,
        "time": 148,
        "imdb": 8.8,
        "votes": 2500000,
        "metascore": 74,
        "gross": "839030630.00",
        "description": "Test movie description.",
        "price": "9.99",
        "director_id": director_id,
        "certification_id": certification_id,
        "genre_ids": genre_ids or [1, 2],
        "star_ids": star_ids or [1, 2],
    }


def seed_movie_reference_data() -> dict[str, int | list[int]]:
    with connect(get_sync_database_url()) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO directors (name)
                VALUES ('Christopher Nolan')
                ON CONFLICT (name) DO NOTHING;

                INSERT INTO certifications (name)
                VALUES ('PG-13')
                ON CONFLICT (name) DO NOTHING;

                INSERT INTO genres (name)
                VALUES ('Sci-Fi'), ('Thriller')
                ON CONFLICT (name) DO NOTHING;

                INSERT INTO stars (name)
                VALUES ('Leonardo DiCaprio'), ('Joseph Gordon-Levitt')
                ON CONFLICT (name) DO NOTHING;
                """
            )
            cursor.execute("SELECT id FROM directors WHERE name = 'Christopher Nolan'")
            director_id = cursor.fetchone()[0]
            cursor.execute("SELECT id FROM certifications WHERE name = 'PG-13'")
            certification_id = cursor.fetchone()[0]
            cursor.execute(
                """
                SELECT id
                FROM genres
                WHERE name IN ('Sci-Fi', 'Thriller')
                ORDER BY id
                """
            )
            genre_ids = [row[0] for row in cursor.fetchall()]
            cursor.execute(
                """
                SELECT id
                FROM stars
                WHERE name IN ('Leonardo DiCaprio', 'Joseph Gordon-Levitt')
                ORDER BY id
                """
            )
            star_ids = [row[0] for row in cursor.fetchall()]

    return {
        "director_id": director_id,
        "certification_id": certification_id,
        "genre_ids": genre_ids,
        "star_ids": star_ids,
    }


def make_admin_access_token(client: TestClient) -> str:
    email = unique_email()
    password = "StrongPassword123"

    register_response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password},
    )
    assert register_response.status_code == 201

    activate_user_in_database(email)

    with connect(get_sync_database_url()) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE users
                SET group_id = (
                    SELECT id
                    FROM user_groups
                    WHERE name = 'ADMIN'
                )
                WHERE email = %s
                """,
                (email,),
            )

    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert login_response.status_code == 200

    return str(login_response.json()["access_token"])


def test_create_movie_without_token_returns_401(client: TestClient) -> None:
    response = client.post(
        "/api/v1/movies/",
        json=valid_movie_payload(),
    )

    assert response.status_code == 401


def test_create_movie_with_regular_user_returns_403(client: TestClient) -> None:
    email = unique_email()
    password = "StrongPassword123"

    register_response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password},
    )
    assert register_response.status_code == 201

    activate_user_in_database(email)

    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert login_response.status_code == 200

    access_token = login_response.json()["access_token"]

    response = client.post(
        "/api/v1/movies/",
        json=valid_movie_payload(),
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 403
    assert response.json() == {"detail": "Moderator or admin permissions required."}


def test_create_movie_with_admin_returns_201(client: TestClient) -> None:
    reference_data = seed_movie_reference_data()
    access_token = make_admin_access_token(client)
    payload = valid_movie_payload(
        director_id=reference_data["director_id"],
        certification_id=reference_data["certification_id"],
        genre_ids=reference_data["genre_ids"],
        star_ids=reference_data["star_ids"],
    )

    response = client.post(
        "/api/v1/movies/",
        json=payload,
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 201
    response_data = response.json()
    assert response_data["name"] == payload["name"]
    assert response_data["director"]["id"] == payload["director_id"]
    assert response_data["certification"]["id"] == payload["certification_id"]
    assert len(response_data["genres"]) == len(payload["genre_ids"])
    assert len(response_data["stars"]) == len(payload["star_ids"])


def test_update_movie_with_admin_returns_updated_movie(client: TestClient) -> None:
    reference_data = seed_movie_reference_data()
    access_token = make_admin_access_token(client)
    create_payload = valid_movie_payload(
        director_id=reference_data["director_id"],
        certification_id=reference_data["certification_id"],
        genre_ids=reference_data["genre_ids"],
        star_ids=reference_data["star_ids"],
    )
    create_response = client.post(
        "/api/v1/movies/",
        json=create_payload,
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert create_response.status_code == 201
    movie_id = create_response.json()["id"]

    update_response = client.patch(
        f"/api/v1/movies/{movie_id}",
        json={"price": "12.99", "imdb": 9.0},
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert update_response.status_code == 200
    response_data = update_response.json()
    assert response_data["id"] == movie_id
    assert response_data["price"] == "12.99"
    assert response_data["imdb"] == 9.0


def test_delete_movie_with_admin_returns_204(client: TestClient) -> None:
    reference_data = seed_movie_reference_data()
    access_token = make_admin_access_token(client)
    create_payload = valid_movie_payload(
        director_id=reference_data["director_id"],
        certification_id=reference_data["certification_id"],
        genre_ids=reference_data["genre_ids"],
        star_ids=reference_data["star_ids"],
    )
    create_response = client.post(
        "/api/v1/movies/",
        json=create_payload,
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert create_response.status_code == 201
    movie_id = create_response.json()["id"]

    delete_response = client.delete(
        f"/api/v1/movies/{movie_id}",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert delete_response.status_code == 204

    get_response = client.get(f"/api/v1/movies/{movie_id}")

    assert get_response.status_code == 404
