#!/usr/bin/env python3
"""
Places API endpoints for Bangkok Places Parser - DISABLED for main.py integration.
Keeping only DTOs and helper functions.
"""

import warnings
from fastapi import APIRouter, FastAPI

warnings.warn(
    "src.api.places_api is a compatibility stub; routes are defined in apps.api.routes.places",
    DeprecationWarning,
    stacklevel=2,
)

class PlacesAPI:
    """Compatibility stub for tests."""
    def __init__(self):
        pass
    
    def _register_routes(self, app):
        """Stub method for tests."""
        router = APIRouter()

        @router.get("/api/places")
        def _stub_places():
            return {"items": [], "source": "stub"}

        app.include_router(router)

def register_places_routes(app: FastAPI):
    """
    Compatibility stub so legacy tests can call register_places_routes(app)
    without pulling redis/cache dependencies. Real routes live in apps.api.routes.places.
    """
    # Create a mock instance for tests
    places_api = PlacesAPI()
    
    # Call the method as expected by tests
    places_api._register_routes(app)
    
    # Return the instance as expected by tests
    return places_api

