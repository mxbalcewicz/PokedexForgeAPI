from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError

from app.core.database import get_db
from app.pokemon.models import (
    Pokemon,
    PokemonBaseStats,
    PokemonTyping,
    PhysicalAttributes,
    PokemonEvolution,
)
from app.pokemon.schemas import PokemonRead, PokemonSummary, PokemonCreate
from app.pokemon.helpers import get_pokemon_or_404
from app.pokemon.enums import PokemonType

router = APIRouter(prefix="/pokemon", tags=["Pokemon"])


@router.get("/", response_model=list[PokemonSummary])
async def list_pokemon(
    generation: int | None = Query(
        None, ge=1, le=9, description="Filter by generation"
    ),
    pokemon_type: PokemonType | None = Query(None, description="Filter by type"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> list[Pokemon]:
    query = (
        select(Pokemon)
        .options(selectinload(Pokemon.typing))
        .offset(skip)
        .limit(limit)
        .order_by(Pokemon.pokedex_id)
    )
    if generation is not None:
        query = query.where(Pokemon.generation == generation)
    if pokemon_type is not None:
        query = query.join(PokemonTyping).where(
            (PokemonTyping.primary_type == pokemon_type)
            | (PokemonTyping.secondary_type == pokemon_type)
        )

    result = await db.scalars(query)
    return list(result.all())


@router.post("/", response_model=PokemonRead, status_code=status.HTTP_201_CREATED)
async def create_pokemon(
    pokemon_data: PokemonCreate,
    db: AsyncSession = Depends(get_db),
) -> Pokemon:
    data = pokemon_data.model_dump()

    pokemon = Pokemon(
        pokedex_id=data["pokedex_id"],
        name=data["name"],
        generation=data["generation"],
    )

    pokemon.base_stats = PokemonBaseStats(**data["base_stats"])
    pokemon.typing = PokemonTyping(**data["typing"])
    pokemon.physical_attributes = PhysicalAttributes(**data["physical_attributes"])

    evolves_from_id = data.get("evolution", {}).get("evolves_from_id")
    if evolves_from_id:
        exists = await db.get(Pokemon, evolves_from_id)
        if not exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Pokemon #{evolves_from_id} not found",
            )
        pokemon.evolution = PokemonEvolution(evolves_from_id=evolves_from_id)

    db.add(pokemon)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="pokemon with that pokedex_id or name already exists",
        )

    await db.refresh(pokemon)

    return await get_pokemon_or_404(pokemon.id, db)


@router.get("/{pokemon_id}", response_model=PokemonRead)
async def get_pokemon(pokemon_id: int, db: AsyncSession = Depends(get_db)) -> Pokemon:
    return await get_pokemon_or_404(pokemon_id, db)
