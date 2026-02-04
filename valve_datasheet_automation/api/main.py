"""
FastAPI Application for Valve Datasheet Automation API.

Run with:
    uvicorn valve_datasheet_automation.api.main:app --reload --port 8000

Or:
    python -m valve_datasheet_automation.api.main
"""

import sys
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Add parent to path for package imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from .routes import router, init_engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup/shutdown."""
    # Startup: Initialize the datasheet engine
    print("Initializing Valve Datasheet Automation Engine...")

    # Find data directory
    possible_data_paths = [
        Path(__file__).parent.parent.parent / "unstructured",
        Path.cwd() / "unstructured",
        Path.cwd().parent / "unstructured",
    ]

    data_dir = None
    for p in possible_data_paths:
        if p.exists():
            data_dir = p
            print(f"  Data directory: {data_dir}")
            break

    if not data_dir:
        print("  Warning: Data directory not found, using defaults")

    # Config directory
    config_dir = Path(__file__).parent.parent / "config"
    print(f"  Config directory: {config_dir}")

    # Initialize engine
    init_engine(config_dir=config_dir, data_dir=data_dir)
    print("Engine initialized successfully!")

    yield

    # Shutdown
    print("Shutting down Valve Datasheet Automation API...")


# Create FastAPI app
app = FastAPI(
    title="Valve Datasheet Automation API",
    description="""
## VDS-Driven Valve Datasheet Automation System

This API provides endpoints for:

- **VDS Operations**: Decode and validate VDS numbers
- **Datasheet Generation**: Generate complete valve datasheets from VDS numbers
- **Metadata**: Get available valve types, piping classes, and configuration options

### VDS Number Format

VDS numbers follow the pattern: `{Prefix}{BoreType}[MetalSeated]{PipingClass}[Modifiers]{EndConnection}`

Example: `BSFA1R`
- `BS` = Ball Valve
- `F` = Full Bore
- `A1` = Piping Class A1
- `R` = RF (Raised Face flange)

### Data Sources

The system resolves datasheet fields from multiple sources:
- **VDS**: Derived from VDS number decoding
- **PMS**: Piping Material Specification data
- **VDS_INDEX**: Pre-computed valve specifications
- **VALVE_STANDARD**: Fixed standards (API 6D, ASME B16.34, etc.)
- **CALCULATED**: Computed values (e.g., hydrotest pressures)
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",      # React dev server
        "http://localhost:5173",      # Vite dev server
        "http://localhost:8080",      # Alternative port
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8080",
        "*",  # Allow all for development (remove in production)
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router, prefix="/api")


# Root endpoint
@app.get("/", tags=["System"])
async def root():
    """API root endpoint with welcome message."""
    return {
        "message": "Valve Datasheet Automation API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/health",
    }


# Run with uvicorn if executed directly
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "valve_datasheet_automation.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
