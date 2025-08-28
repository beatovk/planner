#!/usr/bin/env python3
"""
Unit tests for register_places_routes function.
"""

import pytest
from unittest.mock import patch, MagicMock
import sys
import os

# Add project root to path
sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from fastapi import FastAPI
from src.api.places_api import register_places_routes


class TestRegisterPlacesRoutes:
    """Test that register_places_routes correctly attaches routes to FastAPI app."""

    def test_register_places_routes_attaches_routes(self):
        """Test that register_places_routes attaches all expected routes."""
        # Create a test FastAPI app
        app = FastAPI()

        # Mock the PlacesAPI to avoid actual initialization
        with patch("src.api.places_api.PlacesAPI") as mock_places_api_class:
            mock_places_api = MagicMock()
            mock_places_api_class.return_value = mock_places_api

            # Call the function
            result = register_places_routes(app)

            # Verify PlacesAPI was created
            mock_places_api_class.assert_called_once()

            # Verify _register_routes was called with the app
            mock_places_api._register_routes.assert_called_once_with(app)

            # Verify the result is the PlacesAPI instance
            assert result == mock_places_api

    def test_register_places_routes_returns_places_api_instance(self):
        """Test that register_places_routes returns the PlacesAPI instance."""
        app = FastAPI()

        with patch("src.api.places_api.PlacesAPI") as mock_places_api_class:
            mock_places_api = MagicMock()
            mock_places_api_class.return_value = mock_places_api

            result = register_places_routes(app)

            assert result == mock_places_api
            assert hasattr(result, "_register_routes")

    def test_register_places_routes_calls_register_routes_method(self):
        """Test that the _register_routes method is called correctly."""
        app = FastAPI()

        with patch("src.api.places_api.PlacesAPI") as mock_places_api_class:
            mock_places_api = MagicMock()
            mock_places_api_class.return_value = mock_places_api

            register_places_routes(app)

            # Verify the method was called with the app
            mock_places_api._register_routes.assert_called_once_with(app)

    def test_register_places_routes_creates_new_places_api_instance(self):
        """Test that a new PlacesAPI instance is created each time."""
        app1 = FastAPI()
        app2 = FastAPI()

        with patch("src.api.places_api.PlacesAPI") as mock_places_api_class:
            mock_places_api1 = MagicMock()
            mock_places_api2 = MagicMock()
            mock_places_api_class.side_effect = [mock_places_api1, mock_places_api2]

            # Register routes on two different apps
            result1 = register_places_routes(app1)
            result2 = register_places_routes(app2)

            # Verify two instances were created
            assert mock_places_api_class.call_count == 2
            assert result1 == mock_places_api1
            assert result2 == mock_places_api2
            assert result1 != result2

    def test_register_places_routes_handles_import_errors_gracefully(self):
        """Test that register_places_routes handles import errors gracefully."""
        app = FastAPI()

        # Test with missing dependencies
        with patch(
            "src.api.places_api.PlacesAPI",
            side_effect=ImportError("Missing dependency"),
        ):
            with pytest.raises(ImportError):
                register_places_routes(app)

    def test_register_places_routes_preserves_app_state(self):
        """Test that register_places_routes doesn't modify the app's existing state."""
        app = FastAPI()

        # Add some existing routes
        @app.get("/existing")
        def existing_route():
            return {"message": "existing"}

        # Store initial state
        initial_routes = list(app.routes)

        with patch("src.api.places_api.PlacesAPI") as mock_places_api_class:
            mock_places_api = MagicMock()
            mock_places_api_class.return_value = mock_places_api

            # Register places routes
            register_places_routes(app)

            # Verify existing routes are preserved
            assert len(app.routes) >= len(initial_routes)
            assert any(route.path == "/existing" for route in app.routes)


if __name__ == "__main__":
    pytest.main([__file__])
