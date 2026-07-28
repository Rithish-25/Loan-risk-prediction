import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# Import database module and model loader
import database
import model_loader

# Import method route modules
from routes import post_routes, get_routes, delete_routes

app = FastAPI(title="CreditGuard AI Risk Prediction API")

# Configure CORS to allow access from local development servers
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_event():
    # Initialize SQLite Database
    database.init_db()

    # Load Model Pipeline
    model_loader.load_model()

# Include method routers
app.include_router(post_routes.router)
app.include_router(get_routes.router)
app.include_router(delete_routes.router)

# Mount Frontend static files to root "/"
# Note: Mount at "/" must be defined last so it doesn't hijack api routes
frontend_dist = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.exists(frontend_dist):
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")
elif os.path.exists(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
else:
    print(f"Warning: static frontend directory not found at {frontend_dir}")
