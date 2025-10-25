"""FastAPI application entry point."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from src.api.routes import auth, garmin, recovery
from src.database.connection import engine, Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup: Create database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    # Shutdown: Close connections
    await engine.dispose()


app = FastAPI(
    title="AI Trainer API",
    description="Intelligent Training Optimization System",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routes
app.include_router(auth.router, prefix="/api/v1/auth", tags=["authentication"])
app.include_router(garmin.router, prefix="/api/v1/garmin", tags=["garmin"])
app.include_router(recovery.router, prefix="/api/v1/recovery", tags=["recovery"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "AI Trainer API", "version": "0.1.0", "docs": "/docs"}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
