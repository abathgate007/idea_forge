"""FastAPI application entrypoint."""

from fastapi import FastAPI


def create_app() -> FastAPI:
    """Create the Idea Forge FastAPI application."""
    app = FastAPI(title="Idea Forge")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
