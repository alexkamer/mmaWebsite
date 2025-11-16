"""FastAPI main application."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .fighters import router as fighters_router
from .events import router as events_router
from .rankings import router as rankings_router
from .betting import router as betting_router
from .espn import router as espn_router
from .wordle import router as wordle_router
from .query import router as query_router

# Create FastAPI app
app = FastAPI(
    title="MMA Website API",
    description="REST API for MMA fighter, event, and ranking data",
    version="2.0.0"
)

# Configure CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Next.js dev server
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(fighters_router, prefix="/api/fighters", tags=["fighters"])
app.include_router(events_router, prefix="/api/events", tags=["events"])
app.include_router(rankings_router, prefix="/api/rankings", tags=["rankings"])
app.include_router(betting_router, prefix="/api/betting", tags=["betting"])
app.include_router(espn_router, prefix="/api/espn", tags=["espn"])
app.include_router(wordle_router, prefix="/api/wordle", tags=["wordle"])
app.include_router(query_router, prefix="/api/query", tags=["query"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "MMA Website API",
        "version": "2.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
