"""
Category mapping utilities to load and map all CSV indices to readable names.
"""

import csv
from pathlib import Path
from typing import Dict, List, Optional

# Get the models directory path
MODELS_DIR = Path(__file__).parent.parent / "models"

# Cache for loaded mappings
_mapping_cache = {}


def load_mapping(filename: str) -> Dict[int, str]:
    """Load a CSV mapping file (index -> name)."""
    global _mapping_cache
    
    if filename in _mapping_cache:
        return _mapping_cache[filename]
    
    mapping = {}
    csv_path = MODELS_DIR / filename
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                idx = int(row['index'])
                name = row['name']
                mapping[idx] = name
    except Exception as e:
        print(f"Warning: Could not load {filename}: {e}")
    
    _mapping_cache[filename] = mapping
    return mapping


def get_main_categories() -> Dict[int, str]:
    """Get main categories mapping (11 categories)."""
    return load_mapping('idx2main.csv')


def get_sub_categories() -> Dict[int, str]:
    """Get sub categories mapping (143 categories)."""
    return load_mapping('idx2sub.csv')


def get_categories() -> Dict[int, str]:
    """Get full categories mapping (212 categories)."""
    return load_mapping('idx2category.csv')


def get_related_items() -> Dict[int, str]:
    """Get related items mapping (314 items)."""
    return load_mapping('idx2related.csv')


def get_main_category_name(idx: int) -> str:
    """Get readable name for main category index."""
    mapping = get_main_categories()
    return mapping.get(idx, f"Unknown Main ({idx})")


def get_sub_category_name(idx: int) -> str:
    """Get readable name for sub category index."""
    mapping = get_sub_categories()
    return mapping.get(idx, f"Unknown Sub ({idx})")


def get_category_name(idx: int) -> str:
    """Get readable name for category index."""
    mapping = get_categories()
    return mapping.get(idx, f"Unknown Category ({idx})")


def get_related_name(idx: int) -> str:
    """Get readable name for related item index."""
    mapping = get_related_items()
    return mapping.get(idx, f"Unknown Related ({idx})")


def format_main_categories(indices: List[int]) -> str:
    """Format main category indices to readable string."""
    if not indices:
        return "📭 No main categories"
    
    names = [get_main_category_name(idx) for idx in indices]
    return ", ".join(names)


def format_sub_categories(indices: List[int]) -> str:
    """Format sub category indices to readable string."""
    if not indices:
        return "📭 No sub categories"
    
    names = [get_sub_category_name(idx) for idx in indices]
    return ", ".join(names)


def format_categories(indices: List[int]) -> str:
    """Format category indices to readable string."""
    if not indices:
        return "📭 No categories"
    
    names = [get_category_name(idx) for idx in indices]
    return ", ".join(names)


def format_related_items(indices: List[int]) -> str:
    """Format related item indices to readable string."""
    if not indices:
        return "📭 No related items"
    
    names = [get_related_name(idx) for idx in indices]
    return ", ".join(names)


def format_all_attributes(
    main_indices: List[int],
    sub_indices: List[int],
    category_indices: List[int],
    related_indices: List[int]
) -> Dict[str, str]:
    """
    Format all attributes to readable strings.
    
    Returns a dictionary with formatted versions of all attributes.
    """
    return {
        'main_categories': format_main_categories(main_indices),
        'sub_categories': format_sub_categories(sub_indices),
        'categories': format_categories(category_indices),
        'related_items': format_related_items(related_indices)
    }
