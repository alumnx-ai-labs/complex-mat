from datetime import datetime, timedelta, timezone

from jose import jwt

from app.core.config import get_settings
from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)

# ---------- hash_password / verify_password ----------


def test_hash_password_does_not_return_the_plaintext():
    hashed = hash_password("Password123!")
    assert hashed != "Password123!"


def test_hash_password_is_salted_and_nondeterministic():
    first = hash_password("Password123!")
    second = hash_password("Password123!")
    assert first != second


def test_verify_password_accepts_the_correct_password():
    hashed = hash_password("Password123!")
    assert verify_password("Password123!", hashed) is True


def test_verify_password_rejects_an_incorrect_password():
    hashed = hash_password("Password123!")
    assert verify_password("wrong-password", hashed) is False


def test_verify_password_is_case_sensitive():
    hashed = hash_password("Password123!")
    assert verify_password("password123!", hashed) is False


# ---------- create_access_token / decode_access_token ----------


def test_create_access_token_encodes_the_subject_as_a_string_claim():
    token = create_access_token(subject=42)
    payload = decode_access_token(token)
    assert payload is not None
    assert payload["sub"] == "42"


def test_create_access_token_sets_an_expiry_in_the_future():
    settings = get_settings()
    before = datetime.now(timezone.utc)
    token = create_access_token(subject=7)
    payload = decode_access_token(token)
    assert payload is not None
    expires_at = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
    assert expires_at > before
    assert expires_at <= before + timedelta(minutes=settings.jwt_expire_minutes + 1)


def test_decode_access_token_round_trips_a_valid_token():
    token = create_access_token(subject=1)
    payload = decode_access_token(token)
    assert payload is not None
    assert payload["sub"] == "1"


def test_decode_access_token_returns_none_for_a_malformed_token():
    assert decode_access_token("not-a-real-token") is None


def test_decode_access_token_returns_none_for_an_empty_token():
    assert decode_access_token("") is None


def test_decode_access_token_returns_none_for_a_token_signed_with_a_different_secret():
    settings = get_settings()
    bad_token = jwt.encode(
        {"sub": "1", "exp": datetime.now(timezone.utc) + timedelta(minutes=5)},
        "a-completely-different-secret",
        algorithm=settings.jwt_algorithm,
    )
    assert decode_access_token(bad_token) is None


def test_decode_access_token_returns_none_for_an_expired_token():
    settings = get_settings()
    expired_token = jwt.encode(
        {"sub": "1", "exp": datetime.now(timezone.utc) - timedelta(minutes=1)},
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )
    assert decode_access_token(expired_token) is None
