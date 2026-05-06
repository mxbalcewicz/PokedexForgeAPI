from __future__ import annotations
from pydantic import BaseModel, Field, model_validator
from typing import Optional
from app.pokemon.enums import PokemonType


class PokemonBaseStatsBase(BaseModel):
    hp: int = Field(..., ge=1, le=255)
    attack: int = Field(..., ge=1, le=255)
    defense: int = Field(..., ge=1, le=255)
    special_attack: int = Field(..., ge=1, le=255)
    special_defense: int = Field(..., ge=1, le=255)
    speed: int = Field(..., ge=1, le=255)


class PokemonBaseStatsCreate(PokemonBaseStatsBase):
    pass


class PokemonBaseStatsUpdate(PokemonBaseStatsBase):
    pass


class BaseStatsRead(PokemonBaseStatsBase):
    id: int
    total: int

    model_config = {"from_attributes": True}


class TypingBase(BaseModel):
    primary_type: PokemonType
    secondary_type: Optional[PokemonType] = None

    @model_validator(mode="after")
    def types_must_differ(self) -> TypingBase:
        if self.secondary_type and self.secondary_type == self.primary_type:
            raise ValueError("primary_type and secondary_type must be different")
        return self


class TypingCreate(TypingBase):
    pass


class TypingRead(TypingBase):
    model_config = {"from_attributes": True}


class PhysicalAttributesBase(BaseModel):
    height: Optional[float] = Field(..., gt=0, description="Height in meters")
    weight: Optional[float] = Field(..., gt=0, description="Weight in kilograms")


class PhysicalAttributesCreate(PhysicalAttributesBase):
    pass


class PhysicalAttributesRead(PhysicalAttributesBase):
    model_config = {"from_attributes": True}


class EvolutionBase(BaseModel):
    evolves_from_id: Optional[int] = None


class EvolutionCreate(EvolutionBase):
    pass


class EvolutionRead(EvolutionBase):
    evolves_from_name: Optional[str] = None

    model_config = {"from_attributes": True}


class PokemonBase(BaseModel):
    pokedex_id: int = Field(..., ge=1)
    name: str = Field(..., min_length=1, max_length=100)
    generation: int = Field(..., ge=1, le=9)


class PokemonCreate(PokemonBase):
    base_stats: Optional[PokemonBaseStatsCreate] = None
    typing: TypingCreate
    physical_attributes: Optional[PhysicalAttributesCreate] = None
    evolution: Optional[EvolutionCreate] = None

    @model_validator(mode="after")
    def validate_evolution(self) -> PokemonCreate:
        if self.evolution and self.evolution.evolves_from_id == self.pokedex_id:
            raise ValueError("A Pokemon cannot evolve from itself.")
        return self


class PokemonUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    generation: Optional[int] = Field(None, ge=1, le=9)
    base_stats: Optional[PokemonBaseStatsCreate] = None
    typing: Optional[TypingCreate] = None
    physical_attributes: Optional[PhysicalAttributesCreate] = None
    evolution: Optional[EvolutionCreate] = None


class PokemonRead(PokemonBase):
    id: int
    base_stats: Optional[BaseStatsRead] = None
    typing: TypingRead
    physical_attributes: Optional[PhysicalAttributesRead] = None
    evolution: Optional[EvolutionRead] = None

    model_config = {"from_attributes": True}


class PokemonSummary(BaseModel):
    id: int
    pokedex_id: int
    name: str
    generation: int
    primary_type: Optional[PokemonType] = None

    model_config = {"from_attributes": True}
