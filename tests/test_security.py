from src.core.security import hash_password, verify_password


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
