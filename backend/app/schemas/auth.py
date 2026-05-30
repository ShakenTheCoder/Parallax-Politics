from pydantic import BaseModel, Field


class AccessCodeRequest(BaseModel):
    code: str = Field(min_length=1, max_length=120)


class AccessCodeResponse(BaseModel):
    valid: bool


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=120)
    password: str = Field(min_length=1, max_length=200)


class RegisterRequest(BaseModel):
    username: str = Field(min_length=1, max_length=120)
    password: str = Field(min_length=6, max_length=200)
    access_code: str = Field(min_length=1, max_length=120)


class UserOut(BaseModel):
    id: str
    username: str
    display_name: str | None = None
    role: str
    access_code: str | None = None
    has_profile: bool = False


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut
