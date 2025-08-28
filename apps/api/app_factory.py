"""
App factory for FastAPI application.

This module creates the FastAPI app instance and registers routes,
avoiding circular imports and syntax errors from main.py.
"""

from fastapi import FastAPI
from packages.wp_core.utils.flags import events_disabled
from packages.wp_places.api import register_places_routes

# Event-related imports are conditional to avoid issues when events are disabled
# from apps.events.api import register_event_routes  # Uncomment when events API is ready


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.
    
    Returns:
        FastAPI: Configured application instance
    """
    app = FastAPI(
        title="Week Planner API",
        description="API for week planning and places discovery",
        version="1.0.0"
    )
    
    # Always register places routes (core functionality)
    register_places_routes(app)
    
    # Conditionally register event routes based on feature flag
    if not events_disabled():
        # TODO: Uncomment when events API is implemented
        # register_event_routes(app)
        pass
    else:
        # Add stub endpoints when events are disabled
        from fastapi import HTTPException
        
        @app.get("/api/events")
        def events_disabled_stub():
            raise HTTPException(status_code=503, detail="Events temporarily disabled")
        
        @app.post("/api/plan")
        def plan_disabled_stub():
            raise HTTPException(status_code=503, detail="Planner (events) disabled")
        
        @app.get("/api/live-events")
        def live_events_disabled_stub():
            raise HTTPException(status_code=503, detail="Live events temporarily disabled")
        
        @app.get("/api/plan-cards")
        def plan_cards_disabled_stub():
            raise HTTPException(status_code=503, detail="Plan cards (events) disabled")
        
        @app.get("/api/day-cards")
        def day_cards_disabled_stub():
            raise HTTPException(status_code=503, detail="Day cards (events) disabled")
        
        @app.get("/api/categories")
        def categories_disabled_stub():
            raise HTTPException(status_code=503, detail="Event categories temporarily disabled")
        
        @app.get("/api/sources")
        def sources_disabled_stub():
            raise HTTPException(status_code=503, detail="Event sources temporarily disabled")
        
        @app.post("/api/debug/source-ping")
        def source_ping_disabled_stub():
            raise HTTPException(status_code=503, detail="Source ping (events) disabled")
    
    return app
