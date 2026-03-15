from __future__ import annotations
from sqlalchemy import Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.pokemon.enums import PokemonType


class PokemonBaseStats(Base):
    __tablename__ = "pokemon_base_stats"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    hp: Mapped[int]
    attack: Mapped[int]
    defense: Mapped[int]
    special_attack: Mapped[int]
    special_defense: Mapped[int]
    speed: Mapped[int]

    pokemon_id: Mapped[int] = mapped_column(
        ForeignKey("pokemon.id", ondelete="CASCADE"), unique=True, index=True
    )
    pokemon: Mapped["Pokemon"] = relationship("Pokemon", back_populates="base_stats")

    @property
    def total(self) -> int:
        return (
            self.hp
            + self.attack
            + self.defense
            + self.special_attack
            + self.special_defense
            + self.speed
        )


class PokemonTyping(Base):
    __tablename__ = "pokemon_typing"

    id: Mapped[int] = mapped_column(primary_key=True)
    primary_type: Mapped[PokemonType] = mapped_column(Enum(PokemonType))
    secondary_type: Mapped[PokemonType | None] = mapped_column(
        Enum(PokemonType), nullable=True
    )

    pokemon_id: Mapped[int] = mapped_column(
        ForeignKey("pokemon.id", ondelete="CASCADE"), unique=True, index=True
    )
    pokemon: Mapped["Pokemon"] = relationship("Pokemon", back_populates="typing")


class PhysicalAttributes(Base):
    __tablename__ = "pokemon_physical_attributes"

    id: Mapped[int] = mapped_column(primary_key=True)
    height: Mapped[float]
    weight: Mapped[float]

    pokemon_id: Mapped[int] = mapped_column(
        ForeignKey("pokemon.id", ondelete="CASCADE"), unique=True, index=True
    )
    pokemon: Mapped["Pokemon"] = relationship(
        "Pokemon", back_populates="physical_attributes"
    )


class PokemonEvolution(Base):
    __tablename__ = "pokemon_evolutions"

    id: Mapped[int] = mapped_column(primary_key=True)

    evolves_from_id: Mapped[int | None] = mapped_column(
        ForeignKey("pokemon.id", ondelete="SET NULL"), nullable=True, index=True
    )

    pokemon_id: Mapped[int] = mapped_column(
        ForeignKey("pokemon.id", ondelete="CASCADE"), unique=True, index=True
    )

    evolves_from: Mapped[Pokemon | None] = relationship(
        "Pokemon", foreign_keys=[evolves_from_id], viewonly=True
    )
    pokemon: Mapped["Pokemon"] = relationship(
        "Pokemon", foreign_keys=[pokemon_id], back_populates="evolution"
    )


class Pokemon(Base):
    __tablename__ = "pokemon"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    pokedex_id: Mapped[int] = mapped_column(unique=True, index=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    generation: Mapped[int]

    base_stats: Mapped[PokemonBaseStats] = relationship(
        "PokemonBaseStats",
        back_populates="pokemon",
        uselist=False,
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    typing: Mapped[PokemonTyping] = relationship(
        "PokemonTyping",
        back_populates="pokemon",
        uselist=False,
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    physical_attributes: Mapped[PhysicalAttributes | None] = relationship(
        "PhysicalAttributes",
        back_populates="pokemon",
        uselist=False,
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    evolution: Mapped[PokemonEvolution | None] = relationship(
        "PokemonEvolution",
        foreign_keys="PokemonEvolution.pokemon_id",
        back_populates="pokemon",
        uselist=False,
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    @property
    def primary_type(self) -> PokemonType | None:
        """Helper property used by summary schema."""
        return self.typing.primary_type if self.typing else None

    @property
    def formatted_pokedex_id(self) -> str:
        return f"{self.pokedex_id:04d}"
