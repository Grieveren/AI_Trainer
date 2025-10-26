"""FastAPI application entry point."""
from contextlib import asynccontextmanager

# Load environment variables before other imports
from dotenv import load_dotenv

load_dotenv()

# Standard library and third-party imports
from fastapi import FastAPI  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402

# Local application imports
from src.api.routes import auth, garmin, recovery  # noqa: E402
from src.database.connection import engine  # noqa: E402


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup: Tables are created via Alembic migrations
    # No need to create them here

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
    allow_origins=[
        "http://localhost:5173",  # Vite default port
        "http://localhost:5176",  # Vite alternative port
    ],
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
