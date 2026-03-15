from app.core.settings import settings
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.auth.endpoints import router as auth_router
from app.pokemon.endpoints import read_router as pokemon_read_router
from app.pokemon.endpoints import management_router as pokemon_management_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    yield
    # shutdown


def create_app() -> FastAPI:
    app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan)

    # Add CORS middleware for development
    if settings.ENVIRONMENT == "local":
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    return app


app = create_app()
app.include_router(auth_router)
app.include_router(pokemon_read_router)
app.include_router(pokemon_management_router)
