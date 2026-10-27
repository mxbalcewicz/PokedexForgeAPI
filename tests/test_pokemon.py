import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.pokemon.enums import PokemonType


def create_pokemon_payload(
    pokedex_id: int,
    name: str,
    generation: int,
    primary_type: PokemonType,
    secondary_type: PokemonType | None = None,
    height: float = 0.7,
    weight: float = 9.0,
    hp: int = 45,
    attack: int = 49,
    defense: int = 49,
    special_attack: int = 65,
    special_defense: int = 65,
    speed: int = 45,
    evolves_from_id: int | None = None,
) -> dict:
    payload = {
        "pokedex_id": pokedex_id,
        "name": name,
        "generation": generation,
        "typing": {
            "primary_type": primary_type.value,
            "secondary_type": secondary_type.value if secondary_type else None,
        },
    }

    payload["physical_attributes"] = {"height": height, "weight": weight}
    payload["base_stats"] = {
        "hp": hp,
        "attack": attack,
        "defense": defense,
        "special_attack": special_attack,
        "special_defense": special_defense,
        "speed": speed,
    }

    if evolves_from_id is not None:
        payload["evolution"] = {"evolves_from_id": evolves_from_id}

    return payload


class TestPokemonEndpoints:
    @pytest.mark.asyncio
    async def test_create_and_get_pokemon(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        payload = create_pokemon_payload(
            pokedex_id=1,
            name="Bulbasaur",
            generation=1,
            primary_type=PokemonType.grass,
            secondary_type=PokemonType.poison,
        )

        create_response = await client.post("/pokemon/", json=payload)
        assert create_response.status_code == 201
        created = create_response.json()

        assert created["pokedex_id"] == payload["pokedex_id"]
        assert created["name"] == payload["name"]
        assert created["generation"] == payload["generation"]
        assert created["typing"]["primary_type"] == payload["typing"]["primary_type"]
        assert (
            created["typing"]["secondary_type"] == payload["typing"]["secondary_type"]
        )
        assert created["base_stats"]["hp"] == payload["base_stats"]["hp"]
        assert (
            created["physical_attributes"]["height"]
            == payload["physical_attributes"]["height"]
        )

        get_response = await client.get(f"/pokemon/{payload['pokedex_id']}")
        assert get_response.status_code == 200
        fetched = get_response.json()
        assert fetched["name"] == payload["name"]
        assert fetched["typing"]["primary_type"] == payload["typing"]["primary_type"]

    @pytest.mark.asyncio
    async def test_pokemon_summary_filters(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        fire_payload = create_pokemon_payload(
            pokedex_id=4,
            name="Charmander",
            generation=1,
            primary_type=PokemonType.fire,
        )
        water_payload = create_pokemon_payload(
            pokedex_id=7,
            name="Squirtle",
            generation=1,
            primary_type=PokemonType.water,
        )

        await client.post("/pokemon/", json=fire_payload)
        await client.post("/pokemon/", json=water_payload)

        response = await client.get(
            "/pokemon/summary",
            params={"pokemon_type": PokemonType.fire.value, "generation": 1},
        )
        assert response.status_code == 200
        results = response.json()

        assert len(results) == 1
        assert results[0]["pokedex_id"] == fire_payload["pokedex_id"]
        assert results[0]["primary_type"] == PokemonType.fire.value

    @pytest.mark.asyncio
    async def test_update_pokemon_stats(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        payload = create_pokemon_payload(
            pokedex_id=25,
            name="Pikachu",
            generation=1,
            primary_type=PokemonType.electric,
            hp=35,
            attack=55,
            defense=40,
            special_attack=50,
            special_defense=50,
            speed=90,
        )

        await client.post("/pokemon/", json=payload)

        updated_stats = {
            "hp": 45,
            "attack": 65,
            "defense": 50,
            "special_attack": 60,
            "special_defense": 60,
            "speed": 100,
        }
        response = await client.patch(
            f"/pokemon/stats/{payload['pokedex_id']}", json=updated_stats
        )

        assert response.status_code == 200
        updated = response.json()
        assert updated["base_stats"]["hp"] == updated_stats["hp"]
        assert updated["base_stats"]["attack"] == updated_stats["attack"]
        assert updated["base_stats"]["speed"] == updated_stats["speed"]
        assert updated["base_stats"]["total"] == sum(updated_stats.values())

    @pytest.mark.asyncio
    async def test_delete_pokemon(self, client: AsyncClient, db_session: AsyncSession):
        payload = create_pokemon_payload(
            pokedex_id=39,
            name="Jigglypuff",
            generation=1,
            primary_type=PokemonType.normal,
            secondary_type=PokemonType.fairy,
            height=0.5,
            weight=5.5,
        )

        await client.post("/pokemon/", json=payload)

        response = await client.delete(f"/pokemon/{payload['pokedex_id']}")
        assert response.status_code == 204

        missing_response = await client.get(f"/pokemon/{payload['pokedex_id']}")
        assert missing_response.status_code == 404
