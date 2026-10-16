from __future__ import annotations

from time import perf_counter

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

from app.api import analysis_router, approvals_router, auth_router, knowledge_router, retrieval_router, tickets_router, users_router
from app.core.config import get_settings


settings = get_settings()

HTTP_REQUESTS = Counter(
    "helpdesk_http_requests_total",
    "HTTP requests served by the helpdesk API",
    ("method", "route", "status"),
)
HTTP_REQUEST_DURATION = Histogram(
    "helpdesk_http_request_duration_seconds",
    "HTTP request duration in seconds",
    ("method", "route"),
)

app = FastAPI(title=settings.app_name)


@app.middleware("http")
async def collect_http_metrics(request: Request, call_next):
    if request.url.path == "/metrics":
        return await call_next(request)
    started = perf_counter()
    status_code = 500
    try:
        response = await call_next(request)
        status_code = response.status_code
        return response
    finally:
        route = request.scope.get("route")
        route_name = route.path if route is not None else "unmatched"
        HTTP_REQUESTS.labels(request.method, route_name, str(status_code)).inc()
        HTTP_REQUEST_DURATION.labels(request.method, route_name).observe(perf_counter() - started)


@app.get("/metrics", include_in_schema=False)
def metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8080",
        "http://127.0.0.1:8080",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "OPTIONS"],
    allow_headers=["Content-Type"],
)
app.include_router(auth_router, prefix="/api")
app.include_router(users_router, prefix="/api")
app.include_router(analysis_router, prefix="/api")
app.include_router(approvals_router, prefix="/api")
app.include_router(knowledge_router, prefix="/api")
app.include_router(retrieval_router, prefix="/api")
app.include_router(tickets_router, prefix="/api")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "app": settings.app_name, "env": settings.env}
