"""Input validation module for clinical data processing.

This module provides comprehensive validation utilities for medical imaging data,
including dimension validation, pixel value ranges, format checking, and clinical
constraint enforcement.

Regulatory Compliance:
- IEC 62304: Input validation requirements
- ISO 14971: Risk mitigation for invalid inputs
- FDA 21 CFR Part 11: Data integrity validation

Examples:
    Basic image validation:
    >>> validator = ImageValidator(max_file_size_mb=50)
    >>> validator.validate_file_size(1024 * 100)
    >>> validator.validate_format("image.png")

    With clinical constraints:
    >>> constraints = ClinicalConstraints()
    >>> validator.validate_pixel_values(0, 255, dtype="uint8")
"""

from .image_validator import ImageValidator, ImageValidationError, ImageDimensions
from .clinical_constraints import ClinicalConstraints, ValidationResult

__version__ = "1.0.0"
__all__ = [
    "ImageValidator",
    "ImageValidationError",
    "ImageDimensions",
    "ClinicalConstraints",
    "ValidationResult",
]
