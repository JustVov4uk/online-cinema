from fastapi.testclient import TestClient


def test_openapi_schema_contains_documented_api_sections(client: TestClient) -> None:
    response = client.get("/openapi.json")

    assert response.status_code == 200

    schema = response.json()
    tag_names = {tag["name"] for tag in schema["tags"]}

    assert {
        "auth",
        "movies",
        "cart",
        "orders",
        "payments",
        "profile",
    }.issubset(tag_names)
    assert "/api/v1/profile/avatar" in schema["paths"]


def test_avatar_endpoint_is_documented_as_file_upload(client: TestClient) -> None:
    response = client.get("/openapi.json")

    assert response.status_code == 200

    schema = response.json()
    avatar_endpoint = schema["paths"]["/api/v1/profile/avatar"]["post"]

    assert "multipart/form-data" in avatar_endpoint["requestBody"]["content"]
