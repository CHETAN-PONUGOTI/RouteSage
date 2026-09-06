import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routers import health, optimization, routes, shipments

logger = logging.getLogger(__name__)

def create_app() -> FastAPI:
    app = FastAPI(
        title="Safiri Route Intelligence API",
        version="1.0.0",
        description="Shipment-route optimization API"
    )

    # CORS Configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # For development purposes
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Global Exception Handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unexpected error: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": "An unexpected internal server error occurred."}
        )

    # Include Routers
    app.include_router(health.router)
    app.include_router(shipments.router)
    app.include_router(routes.router)
    app.include_router(optimization.router)

    return app

app = create_app()
