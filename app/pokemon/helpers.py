from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.pokemon.models import (
    Pokemon,
    PokemonEvolution,
)

FULL_LOAD = [
    selectinload(Pokemon.base_stats),
    selectinload(Pokemon.typing),
    selectinload(Pokemon.physical_attributes),
    selectinload(Pokemon.evolution).selectinload(PokemonEvolution.evolves_from),
]


async def get_pokemon_or_404(pokemon_id: int, db: AsyncSession) -> Pokemon:
    query = select(Pokemon).where(Pokemon.id == pokemon_id).options(*FULL_LOAD)
    result = await db.scalars(query)
    pokemon = result.first()
    if not pokemon:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pokemon #{pokemon_id} not found",
        )
    return pokemon
