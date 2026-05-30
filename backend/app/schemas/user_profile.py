from pydantic import BaseModel, Field


class SocialLinks(BaseModel):
    linkedin: str | None = Field(default=None, max_length=500)
    facebook: str | None = Field(default=None, max_length=500)
    instagram: str | None = Field(default=None, max_length=500)
    x: str | None = Field(default=None, max_length=500)
    youtube: str | None = Field(default=None, max_length=500)


class UserProfileIn(BaseModel):
    full_name: str = Field(min_length=1, max_length=200)
    country: str | None = Field(default=None, max_length=120)
    age: int | None = Field(default=None, ge=1, le=150)
    birthdate: str | None = Field(default=None, max_length=40)
    social_links: SocialLinks = Field(default_factory=SocialLinks)


class UserProfileOut(BaseModel):
    full_name: str
    country: str | None = None
    age: int | None = None
    birthdate: str | None = None
    social_links: SocialLinks = Field(default_factory=SocialLinks)
