"""Authentication routes."""
from fastapi import APIRouter

router = APIRouter()


@router.post("/register")
async def register():
    """User registration endpoint (placeholder)."""
    return {"message": "Registration endpoint - to be implemented"}


@router.post("/login")
async def login():
    """User login endpoint (placeholder)."""
    return {"message": "Login endpoint - to be implemented"}
