"""
Clothing compatibility logic based on main categories.
Determines which items can be worn together in an outfit.
"""

from typing import List, Set

# Define clothing compatibility rules
# Some items can't be worn together based on main category

INCOMPATIBLE_PAIRS = {
    # All-body items (full outfits) can't be paired with tops or bottoms
    (0, 1): True,  # all-body + bottoms
    (0, 2): True,  # all-body + tops
    (1, 0): True,  # bottoms + all-body
    (2, 0): True,  # tops + all-body
}

# Categories that can be worn together (truthy values)
COMPATIBLE_CATEGORIES = {
    # Tops
    2: {1, 3, 4, 5, 6, 7, 8, 9, 10},  # tops go with: bottoms, outerwear, bags, shoes, accessories, scarves, hats, sunglasses, jewellery
    
    # Bottoms
    1: {2, 3, 4, 5, 6, 7, 8, 9, 10},  # bottoms go with: tops, outerwear, bags, shoes, accessories, scarves, hats, sunglasses, jewellery
    
    # Outerwear
    3: {1, 2, 4, 5, 6, 7, 8, 9, 10},  # outerwear goes with: bottoms, tops, bags, shoes, accessories, scarves, hats, sunglasses, jewellery
    
    # All-body items (full outfit, can't mix with tops/bottoms)
    0: {3, 4, 5, 6, 7, 8, 9, 10},  # all-body goes with: outerwear, bags, shoes, accessories, scarves, hats, sunglasses, jewellery
    
    # Bags, Shoes, Accessories, Scarves, Hats, Sunglasses, Jewellery are compatible with everything else
    4: {0, 1, 2, 3, 5, 6, 7, 8, 9, 10},  # bags
    5: {0, 1, 2, 3, 4, 6, 7, 8, 9, 10},  # shoes
    6: {0, 1, 2, 3, 4, 5, 7, 8, 9, 10},  # accessories
    7: {0, 1, 2, 3, 4, 5, 6, 8, 9, 10},  # scarves
    8: {0, 1, 2, 3, 4, 5, 6, 7, 9, 10},  # hats
    9: {0, 1, 2, 3, 4, 5, 6, 7, 8, 10},  # sunglasses
    10: {0, 1, 2, 3, 4, 5, 6, 7, 8, 9},  # jewellery
}

# Clothing category names
CATEGORY_NAMES = {
    0: "All-Body",
    1: "Bottoms",
    2: "Tops",
    3: "Outerwear",
    4: "Bags",
    5: "Shoes",
    6: "Accessories",
    7: "Scarves",
    8: "Hats",
    9: "Sunglasses",
    10: "Jewellery"
}

def is_compatible(main_cat_1: int, main_cat_2: int) -> bool:
    """
    Check if two items with given main categories can be worn together.
    
    Args:
        main_cat_1: Main category index of first item
        main_cat_2: Main category index of second item
    
    Returns:
        True if compatible, False otherwise
    """
    # Same category is always compatible
    if main_cat_1 == main_cat_2:
        return True
    
    # Check incompatible pairs
    if (main_cat_1, main_cat_2) in INCOMPATIBLE_PAIRS:
        return False
    
    # Check if in compatibility map
    if main_cat_1 in COMPATIBLE_CATEGORIES:
        return main_cat_2 in COMPATIBLE_CATEGORIES[main_cat_1]
    
    # Default to compatible if not explicitly defined
    return True


def can_add_to_outfit(new_item_main_cat: int, outfit_items_main_cats: List[int]) -> bool:
    """
    Check if a new item can be added to an existing outfit based on main categories.
    
    Args:
        new_item_main_cat: Main category index of new item to add
        outfit_items_main_cats: List of main category indices of existing items in outfit
    
    Returns:
        True if item can be added, False otherwise
    """
    # Check compatibility with all existing items
    for existing_cat in outfit_items_main_cats:
        if not is_compatible(new_item_main_cat, existing_cat):
            return False
    
    return True
