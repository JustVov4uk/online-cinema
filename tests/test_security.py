from src.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)


def test_hash_password_returns_different_value() -> None:
    password = "strong_password"
    hashed_password = hash_password(password)
    assert hashed_password != password

def test_verify_password_returns_true_for_valid_password() -> None:
    password = "strong_password"
    hashed_password = hash_password(password)
    assert verify_password(password, hashed_password) is True

def test_verify_password_returns_false_for_invalid_password() -> None:
    hashed_password = hash_password("strong_password")
    assert verify_password("wrong_password", hashed_password) is False

def test_create_access_token_returns_access_payload() -> None:
    token = create_access_token(subject="1")
    payload = decode_token(token)

    assert payload["sub"] == "1"
    assert payload["type"] == "access"
    assert "exp" in payload

def test_create_refresh_token_returns_refresh_payload() -> None:
    token = create_refresh_token(subject="1")
    payload = decode_token(token)

    assert payload["sub"] == "1"
    assert payload["type"] == "refresh"
    assert "exp" in payload
