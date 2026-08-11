import pytest
from pydantic import ValidationError

from app.schemas.auth import LoginRequest
from app.security import hash_password, verify_password


def test_login_preserves_existing_username_case() -> None:
    sample_password = "credential"
    payload = LoginRequest(username="  Administrator  ", password=sample_password)
    assert payload.username == "Administrator"


def test_passwords_beyond_bcrypt_limit_are_rejected() -> None:
    password = "é" * 37
    with pytest.raises(ValidationError, match="byte length"):
        LoginRequest(username="analyst", password=password)
    with pytest.raises(ValueError, match="bcrypt"):
        hash_password(password)


def test_password_verification_rejects_oversized_inputs() -> None:
    password_hash = hash_password("valid-password")
    assert not verify_password("é" * 37, password_hash)
