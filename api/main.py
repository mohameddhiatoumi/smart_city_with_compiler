"""
FastAPI main application for Neo-Sousse 2030 Smart City Platform
Version 2.0 with FSM and AI modules integrated
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from dotenv import load_dotenv  # ← ADD THIS

import os
import sys
load_dotenv() 

# Get project root directory
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

# Import config
from api.config import (
    API_TITLE, API_VERSION, API_DESCRIPTION, CORS_ORIGINS
)

# Import existing routes
from api.routes import sensors, zones, dashboard, query, ai

# Import FSM and AI routes (with error handling)
FSM_AVAILABLE = False
AI_AVAILABLE = False

try:
    from fsm_routes import router as fsm_router, init_fsm_manager
    FSM_AVAILABLE = True
except (ImportError, ModuleNotFoundError) as e:
    print(f"⚠️  FSM module not found: {e}")
    print("   Place fsm_routes.py in the project root directory")
    fsm_router = None

try:
    from ai_routes import router as ai_router, init_ai_generator
    AI_AVAILABLE = True
except (ImportError, ModuleNotFoundError) as e:
    print(f"⚠️  AI module not found: {e}")
    print("   Place ai_routes.py in the project root directory")
    ai_router = None

# Database path
DB_PATH = os.path.join(PROJECT_ROOT, "neo_sousse.db")

# Create FastAPI app with updated metadata
app = FastAPI(
    title="Neo-Sousse 2030 API",
    description="Smart City Management System",
    version="1.0.0"
)

# Configure CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize modules on startup
@app.on_event("startup")
async def startup_event():
    """Initialize modules on startup"""
    print("\n" + "="*60)
    print("  Neo-Sousse 2030 API v2.0 - Starting...")
    print("="*60)
    
    # Check database
    if os.path.exists(DB_PATH):
        print(f"✓ Database found: {DB_PATH}")
    else:
        print(f"⚠️  Database not found at: {DB_PATH}")
        print("   Run: python database/db_init.py")
    
    # Initialize FSM Manager
    if FSM_AVAILABLE:
        try:
            init_fsm_manager(DB_PATH)
            print("✓ FSM Manager initialized successfully")
        except Exception as e:
            print(f"⚠️  FSM initialization failed: {e}")
    
    # Initialize AI Generator
    if AI_AVAILABLE:
        try:
            init_ai_generator(DB_PATH, use_openai=True)
            print("✓ AI Generator initialized successfully")
        except Exception as e:
            print(f"⚠️  AI initialization failed: {e}")
    
    print("="*60)
    print("  Server ready!")
    print(f"  Swagger UI: http://localhost:8000/docs")
    print("="*60 + "\n")


# Include existing routers
app.include_router(sensors.router)
app.include_router(zones.router)
app.include_router(dashboard.router)
app.include_router(query.router)
app.include_router(ai.router)

# Include FSM and AI routers if available
if FSM_AVAILABLE and fsm_router is not None:
    app.include_router(fsm_router)
    print("✓ FSM routes registered")

if AI_AVAILABLE and ai_router is not None:
    app.include_router(ai_router)
    print("✓ AI routes registered")


@app.get("/", include_in_schema=False)
async def root():
    """Redirect root to API docs"""
    return RedirectResponse(url="/docs")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Neo-Sousse 2030 API",
        "version": API_VERSION,
        "database": os.path.exists(DB_PATH),
        "fsm_module": FSM_AVAILABLE,
        "ai_module": AI_AVAILABLE
    }


@app.get("/api/info")
async def api_info():
    """Get API information"""
    modules = [
        "Natural Language Query Compiler",
        "Sensor & Zone Management",
        "Dashboard & Analytics"
    ]
    
    if FSM_AVAILABLE:
        modules.append("Finite State Machines (Sensor/Intervention/Vehicle)")
    if AI_AVAILABLE:
        modules.append("AI Generative Module (Reports & Recommendations)")
    
    return {
        "name": API_TITLE,
        "version": API_VERSION,
        "description": API_DESCRIPTION,
        "modules": modules,
        "status": {
            "fsm": "available" if FSM_AVAILABLE else "not_installed",
            "ai": "available" if AI_AVAILABLE else "not_installed"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)