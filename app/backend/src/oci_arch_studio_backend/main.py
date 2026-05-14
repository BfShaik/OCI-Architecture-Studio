from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from oci_arch_studio_backend.api.routes import router
from oci_arch_studio_backend.core.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="OCI Architecture Studio API",
        version="0.1.0",
        description="Backend API for grounded OCI architecture guidance.",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(router)
    return app


app = create_app()
