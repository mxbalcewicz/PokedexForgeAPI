from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.pokemon.models import (
    Pokemon,
    PokemonEvolution,
)


class PokemonQuery:
    FULL_LOAD = [
        selectinload(Pokemon.base_stats),
        selectinload(Pokemon.typing),
        selectinload(Pokemon.physical_attributes),
        selectinload(Pokemon.evolution).selectinload(PokemonEvolution.evolves_from),
    ]

    @staticmethod
    async def get_pokemon_or_404(pokedex_id: int, db: AsyncSession) -> Pokemon:
        query = (
            select(Pokemon)
            .where(Pokemon.pokedex_id == pokedex_id)
            .options(*PokemonQuery.FULL_LOAD)
        )
        result = await db.scalars(query)
        pokemon = result.first()
        if not pokemon:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Pokemon #{pokedex_id} not found",
            )
        return pokemon
