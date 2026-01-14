"""
Points calculation rules for recycling materials.
Centralizes business logic for point awards.
"""

POINT_RULES = {
    "plastic": 5,   # 5 points per item
    "can": 10,      # 10 points per item
}


def calculate_points(material_type: str, quantity: int) -> int:
    """
    Calculate awarded points based on material type and quantity.
    
    Args:
        material_type: Type of material being recycled (e.g., "plastic", "can")
        quantity: Number of items being recycled
        
    Returns:
        Total points to award
        
    Raises:
        ValueError: If material_type is not in POINT_RULES
    """
    if material_type not in POINT_RULES:
        raise ValueError(f"Invalid material type: {material_type}. Allowed: {list(POINT_RULES.keys())}")

    return POINT_RULES[material_type] * quantity
