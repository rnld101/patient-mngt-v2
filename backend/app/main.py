from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.database import init_db
from app.core.config import settings
from app.utils.aws import load_secrets_from_manager
from app.models import Base
from app.api import auth, patients


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events."""
    # Startup
    try:
        # Load secrets from AWS Secrets Manager
        load_secrets_from_manager("patient-management-secrets")
        
        # Initialize database
        init_db()
        
        print("✓ Database initialized")
        print("✓ Secrets loaded from AWS Secrets Manager")
    except Exception as e:
        print(f"✗ Startup failed: {str(e)}")
        raise
    
    yield
    
    # Shutdown
    print("✓ Application shutdown")


app = FastAPI(
    title=settings.app_name,
    description="Simple Patient Management Application API",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix=settings.api_prefix)
app.include_router(patients.router, prefix=settings.api_prefix)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Patient Management API",
        "version": "1.0.0",
        "docs": "/docs"
    }
