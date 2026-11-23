from fastapi import FastAPI, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from src.infrastructure.api.exceptions_handler import register_exception_handlers
from src.infrastructure.api.routes.authentication_router import router as auth_router
from src.infrastructure.api.routes.query_router import router as query_router
from src.infrastructure.api.routes.storage_router import router as storage_router
from src.infrastructure.middleware.middlewares import observability_middleware

app = FastAPI(title="RAG provider via API")

app.middleware("http")(observability_middleware)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/metrics")
def metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


register_exception_handlers(app=app)

app.include_router(query_router, prefix="/api/v1", tags=["Query Endpoints"])
app.include_router(auth_router, prefix="/api/v1", tags=["Authentication Endpoints"])
app.include_router(storage_router, prefix="/api/v1", tags=["Storage Endpoints"])
