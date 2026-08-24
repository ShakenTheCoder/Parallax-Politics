from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class AccessCodeRequest(BaseModel):
    code: str = Field(min_length=1, max_length=120)


class AccessCodeResponse(BaseModel):
    valid: bool


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    username: str = Field(min_length=1, max_length=120)
    password: str = Field(min_length=1, max_length=200)

    @field_validator("username")
    @classmethod
    def normalize_username(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized or any(ord(char) < 32 for char in normalized):
            raise ValueError("invalid username")
        return normalized

    @field_validator("password")
    @classmethod
    def validate_password_bytes(cls, value: str) -> str:
        if len(value.encode("utf-8")) > 72:
            raise ValueError("password exceeds the supported byte length")
        return value


class RegisterRequest(BaseModel):
    username: str = Field(min_length=1, max_length=120)
    password: str = Field(min_length=6, max_length=200)
    access_code: str = Field(min_length=1, max_length=120)

    @field_validator("password")
    @classmethod
    def validate_password_bytes(cls, value: str) -> str:
        if len(value.encode("utf-8")) > 72:
            raise ValueError("password exceeds the supported byte length")
        return value


class UserOut(BaseModel):
    id: str
    username: str
    display_name: str | None = None
    role: str
    has_profile: bool = False


UserRole = Literal["principal", "superadmin"]


class AdminUserCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    username: str = Field(min_length=1, max_length=120)
    password: str = Field(min_length=6, max_length=200)
    display_name: str | None = Field(default=None, max_length=200)
    role: UserRole = "principal"

    @field_validator("username")
    @classmethod
    def normalize_username(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized or any(ord(char) < 32 for char in normalized):
            raise ValueError("invalid username")
        return normalized

    @field_validator("password")
    @classmethod
    def validate_password_bytes(cls, value: str) -> str:
        if len(value.encode("utf-8")) > 72:
            raise ValueError("password exceeds the supported byte length")
        return value


class AdminUserOut(BaseModel):
    id: str
    username: str
    display_name: str | None = None
    role: UserRole
    created_at: datetime
    has_profile: bool = False


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut
