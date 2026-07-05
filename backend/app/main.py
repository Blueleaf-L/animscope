import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import engine, Base
from app.routers import companies, works, analysis, charts

# Determine frontend directory
FRONTEND_DIR = Path(__file__).parent.parent.parent / "frontend"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan: create tables on startup."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(
    title="中国动画公司作品分析平台",
    description="基于72家中国动画公司、586部作品的Web分析平台 API",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(companies.router)
app.include_router(works.router)
app.include_router(analysis.router)
app.include_router(charts.router)


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "version": "2.0.0"}


# Serve frontend static files (development convenience)
if FRONTEND_DIR.exists():
    # Mount static assets (CSS, JS)
    css_dir = FRONTEND_DIR / "css"
    js_dir = FRONTEND_DIR / "js"
    if css_dir.exists():
        app.mount("/css", StaticFiles(directory=str(css_dir)), name="css")
    if js_dir.exists():
        app.mount("/js", StaticFiles(directory=str(js_dir)), name="js")

    @app.get("/", response_class=HTMLResponse)
    async def index():
        """Serve the main SPA page."""
        index_path = FRONTEND_DIR / "index.html"
        if index_path.exists():
            return index_path.read_text(encoding="utf-8")
        return HTMLResponse("<h1>Frontend not found</h1>", status_code=404)

    @app.get("/{full_path:path}")
    async def spa_fallback(full_path: str, request: Request):
        """SPA fallback — serve index.html for all non-API paths."""
        # Skip API paths
        if full_path.startswith("api/") or full_path.startswith("docs") or full_path.startswith("redoc") or full_path.startswith("openapi"):
            return JSONResponse({"detail": "Not found"}, status_code=404)

        # Try to serve static file
        file_path = FRONTEND_DIR / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(str(file_path))

        # SPA fallback
        index_path = FRONTEND_DIR / "index.html"
        if index_path.exists():
            return HTMLResponse(index_path.read_text(encoding="utf-8"))
        return JSONResponse({"detail": "Not found"}, status_code=404)
