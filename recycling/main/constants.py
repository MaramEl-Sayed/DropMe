"""
Constants for the recycling system.
Centralizes configuration values and business rules.
"""

# Duplicate scan prevention window (in seconds)
DUPLICATE_SCAN_WINDOW_SECONDS = 5

# Phone number validation
PHONE_LENGTH = 11

# Material types (should match MATERIAL_CHOICES in models)
VALID_MATERIAL_TYPES = ["plastic", "can"]
