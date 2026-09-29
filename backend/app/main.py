from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.database.db import init_db
from app.api import health, policies, treatments, estimate

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize SQLite database schema & seed treatment cost benchmarks on startup
    init_db()
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Backend API for Spasth: Insurance Policy Intelligence & Treatment Cost Estimator",
    lifespan=lifespan
)

# Configure CORS for frontend access
origins = [
    settings.FRONTEND_URL,
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(health.router, prefix=settings.API_V1_STR)
app.include_router(policies.router, prefix=settings.API_V1_STR)
app.include_router(treatments.router, prefix=settings.API_V1_STR)
app.include_router(estimate.router, prefix=settings.API_V1_STR)

@app.get("/")
def root():
    return {
        "message": "Welcome to Spasth API",
        "docs": "/docs",
        "health": f"{settings.API_V1_STR}/health"
    }
