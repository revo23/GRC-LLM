"""
Dependency injection helpers for FastAPI.
Currently, services are instantiated directly in routes.
This module is reserved for future DI patterns (e.g., shared DB connections).
"""
from app.config import settings


def get_settings():
    return settings
