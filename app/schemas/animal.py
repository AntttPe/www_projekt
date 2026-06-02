"""Schematy Pydantic dla endpointów zwierząt."""

from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


class AnimalCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    species: Literal["dog", "horse", "cat"]
    breed: str = Field(min_length=2, max_length=120)
    sex: Literal["male", "female"]
    birth_date: date | None = None
    color: str = Field(default="", max_length=80)
    registration_number: str = Field(default="", max_length=60)
    description: str = Field(default="", max_length=4000)
    available_for_breeding: bool = False
    title: str = Field(default="", max_length=120)
    sire_id: int | None = None
    dam_id: int | None = None


class AnimalUpdate(AnimalCreate):
    pass


class AnimalRead(BaseModel):
    id: int
    farm_id: int
    name: str
    species: str
    breed: str
    sex: str
    birth_date: date | None
    color: str
    registration_number: str
    description: str
    available_for_breeding: bool
    title: str
    sire_id: int | None
    dam_id: int | None

    model_config = {"from_attributes": True}
