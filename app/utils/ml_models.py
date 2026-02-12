"""ML Models management and caching."""
from pathlib import Path

# Global cache
_models_cache = None


def get_models():
    """Get cached ML models."""
    global _models_cache
    if _models_cache is None:
        try:
            from app.models.load_models import load_all_models
            _models_cache = load_all_models()
        except Exception as e:
            print(f"⚠️  Models not available: {e}")
            _models_cache = None
    return _models_cache


def clear_models_cache():
    """Clear the models cache."""
    global _models_cache
    _models_cache = None
