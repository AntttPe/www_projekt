"""Schematy Pydantic dla endpointów hodowli (Lab 6 — walidacja wejścia)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, EmailStr, Field, HttpUrl

ALLOWED_SPECIES = {"dog", "horse", "cat"}


class FarmCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    description: str = Field(default="", max_length=4000)
    species: Literal["dog", "horse", "cat"]
    city: str = Field(default="", max_length=120)
    voivodeship: str = Field(default="", max_length=60)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    contact_email: EmailStr | None = None
    contact_phone: str = Field(default="", max_length=40)
    website: HttpUrl | None = None


class FarmUpdate(FarmCreate):
    pass


class FarmRead(BaseModel):
    id: int
    name: str
    description: str
    species: str
    city: str
    voivodeship: str
    latitude: float | None
    longitude: float | None
    is_verified: bool
    contact_email: str
    contact_phone: str
    website: str

    model_config = {"from_attributes": True}
