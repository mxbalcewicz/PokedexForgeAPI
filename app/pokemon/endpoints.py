from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.pokemon.models import (
    Pokemon,
    PokemonBaseStats,
    PokemonTyping,
    PhysicalAttributes,
    PokemonEvolution,
)
from app.pokemon.schemas import (
    PokemonRead,
    PokemonSummary,
    PokemonCreate,
    PokemonBaseStatsUpdate,
)
from app.pokemon.helpers.query_helpers import PokemonQuery
from app.pokemon.enums import PokemonType

read_router = APIRouter(prefix="/pokemon", tags=["Pokemon Read Endpoints"])
management_router = APIRouter(prefix="/pokemon", tags=["Pokemon Management Endpoints"])


@read_router.get("/summary", response_model=list[PokemonSummary])
async def pokemon_summary(
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


@read_router.get("/{pokedex_id}", response_model=PokemonRead)
async def get_pokemon(pokedex_id: int, db: AsyncSession = Depends(get_db)) -> Pokemon:
    return await PokemonQuery.get_pokemon_or_404(pokedex_id=pokedex_id, db=db)


@management_router.post(
    "/",
    response_model=PokemonRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new Pokemon",
)
async def create_pokemon(
    payload: PokemonCreate,
    db: AsyncSession = Depends(get_db),
) -> Pokemon:
    if payload.evolution and payload.evolution.evolves_from_id is not None:
        parent = await db.get(Pokemon, payload.evolution.evolves_from_id)
        if not parent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No Pokemon found with id={payload.evolution.evolves_from_id}.",
            )

    pokemon = Pokemon(
        pokedex_id=payload.pokedex_id,
        name=payload.name,
        generation=payload.generation,
        base_stats=PokemonBaseStats(**payload.base_stats.model_dump())
        if payload.base_stats
        else None,
        typing=PokemonTyping(**payload.typing.model_dump()),
        physical_attributes=PhysicalAttributes(
            **payload.physical_attributes.model_dump()
        )
        if payload.physical_attributes
        else None,
        evolution=PokemonEvolution(**payload.evolution.model_dump())
        if payload.evolution
        else None,
    )

    db.add(pokemon)
    try:
        await db.commit()
    except SQLAlchemyError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="...")

    await db.refresh(pokemon)
    return pokemon


@management_router.delete("/{pokedex_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_pokemon(pokedex_id: int, db: AsyncSession = Depends(get_db)):
    query = select(Pokemon).where(Pokemon.pokedex_id == pokedex_id)
    result = await db.scalars(query)
    pokemon = result.first()
    if not pokemon:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pokemon #{pokedex_id} not found",
        )
    await db.delete(pokemon)
    try:
        await db.commit()
    except SQLAlchemyError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete Pokemon.",
        )


@management_router.patch("/stats/{pokedex_id}", response_model=PokemonRead)
async def update_pokemon_stats(
    pokedex_id: int, payload: PokemonBaseStatsUpdate, db: AsyncSession = Depends(get_db)
):
    pokemon = await PokemonQuery.get_pokemon_or_404(pokedex_id=pokedex_id, db=db)

    if pokemon.base_stats:
        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(pokemon.base_stats, key, value)
    else:
        pokemon.base_stats = PokemonBaseStats(**payload.model_dump())

    db.add(pokemon)
    try:
        await db.commit()
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    await db.refresh(pokemon)
    return pokemon
