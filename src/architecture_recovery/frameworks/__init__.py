from .base import (
    FrameworkAdapter,
    FrameworkAdapterRegistry,
    FrameworkAnalysis,
    FrameworkAnalysisContext,
    FrameworkDetection,
)
from .fastapi import FastAPIAdapter


def default_registry() -> FrameworkAdapterRegistry:
    return FrameworkAdapterRegistry(adapters=(FastAPIAdapter(),))


__all__ = [
    "FastAPIAdapter",
    "FrameworkAdapter",
    "FrameworkAdapterRegistry",
    "FrameworkAnalysis",
    "FrameworkAnalysisContext",
    "FrameworkDetection",
    "default_registry",
]
