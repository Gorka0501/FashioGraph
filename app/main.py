"""
Main FastAPI Application for Fashion Wardrobe Management.
Entry point for the backend server.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
import sys
from pathlib import Path

# Setup logging first
from app.backend.logging_config import logger

# Ensure app module is importable
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.backend.database import init_db, engine, Base

from app.backend.routes import auth, wardrobe, items, outfits, changes, health, ml, storage
from app.utils import ml_models

# Store models cache in ml_models when preloaded
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events."""
    # Startup
    logger.info("🚀 Starting up Fashion Wardrobe API...")
    init_db()
    from app.backend.database import DB_PATH
    logger.info(f"✅ Database initialized at: {DB_PATH}")
    
    # Preload ML models
    logger.info("🤖 Preloading ML models...")
    try:
        from app.models.load_models import load_all_models
        models = load_all_models()
        
        # Store in ml_models module cache
        ml_models._models_cache = models
        
        logger.info("✅ All ML models preloaded and ready")
    except Exception as e:
        logger.warning(f"⚠️  Could not preload models: {e}. Models will be loaded on-demand.")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down Fashion Wardrobe API...")

# Create FastAPI app with lifespan
app = FastAPI(
    title="Fashion Wardrobe API",
    description="API for managing fashion wardrobes with ML-powered outfit generation",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers with API v1 prefix
app.include_router(auth.router, prefix="/api/v1")
app.include_router(wardrobe.router, prefix="/api/v1")
app.include_router(items.router, prefix="/api/v1")
app.include_router(outfits.router, prefix="/api/v1")
app.include_router(changes.router, prefix="/api/v1")
app.include_router(ml.router, prefix="/api/v1")
app.include_router(storage.router, prefix="/api/v1")
app.include_router(health.router, prefix="/api/v1")

@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "fashion-wardrobe-api"}

@app.get("/")
def root():
    """Root endpoint."""
    return {
        "name": "Fashion Wardrobe API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
