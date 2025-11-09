"""Image validation utilities for medical imaging applications.

Provides comprehensive validation for medical images including dimension checks,
file format validation, pixel value ranges, and clinical constraints.

Regulatory Mapping:
- IEC 62304: Software lifecycle validation
- ISO 14971: Risk analysis and mitigation
- FDA 21 CFR 11: Data integrity and authenticity
"""

import logging
from typing import Optional, Tuple, Set
from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)


class ImageValidationError(Exception):
    """Custom exception for image validation failures.

    Attributes:
        message: Human-readable error message (safe for client response)
        error_code: Machine-readable error code for programmatic handling
        details: Additional context information (internal use only)
    """

    def __init__(
        self,
        message: str,
        error_code: str,
        details: Optional[dict] = None,
    ) -> None:
        """Initialize validation error.

        Args:
            message: Error message for client
            error_code: Unique error code
            details: Optional context for logging
        """
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        logger.warning(
            f"Image validation error: {error_code} - {message}",
            extra={
                "error_code": error_code,
                "validation_details": self.details,
            },
        )
        super().__init__(self.message)

    def __repr__(self) -> str:
        """Return string representation."""
        return f"ImageValidationError(code={self.error_code}, msg={self.message})"


class ImageDimensions(BaseModel):
    """Validated image dimension constraints.

    Enforces minimum and maximum dimensions for medical images to ensure
    clinical usability and system performance.

    Attributes:
        min_width: Minimum image width in pixels
        max_width: Maximum image width in pixels
        min_height: Minimum image height in pixels
        max_height: Maximum image height in pixels
        required_channels: Number of required color channels (1-4)
    """

    min_width: int = Field(
        default=64,
        ge=1,
        le=4096,
        description="Minimum image width in pixels",
    )
    max_width: int = Field(
        default=2048,
        ge=1,
        le=8192,
        description="Maximum image width in pixels",
    )
    min_height: int = Field(
        default=64,
        ge=1,
        le=4096,
        description="Minimum image height in pixels",
    )
    max_height: int = Field(
        default=2048,
        ge=1,
        le=8192,
        description="Maximum image height in pixels",
    )
    required_channels: int = Field(
        default=3,
        ge=1,
        le=4,
        description="Number of required color channels",
    )

    @field_validator("max_width")
    @classmethod
    def max_width_greater_than_min(cls, v: int, info) -> int:
        """Validate max_width > min_width."""
        if "min_width" in info.data and v < info.data["min_width"]:
            raise ValueError("max_width must be greater than min_width")
        return v

    @field_validator("max_height")
    @classmethod
    def max_height_greater_than_min(cls, v: int, info) -> int:
        """Validate max_height > min_height."""
        if "min_height" in info.data and v < info.data["min_height"]:
            raise ValueError("max_height must be greater than min_height")
        return v

    class Config:
        """Pydantic configuration."""
        frozen = True  # Make immutable for thread safety


class ImageValidator:
    """Validate medical images against clinical and technical constraints.

    Performs comprehensive validation of medical image files including:
    - File size validation
    - Format/extension checking
    - Dimension validation
    - Pixel value range validation
    - Data type compatibility

    Regulatory Compliance:
        - IEC 62304: Validation of input data
        - ISO 14971: Risk mitigation through validation
        - FDA 21 CFR 11: Data integrity controls

    Examples:
        >>> validator = ImageValidator(max_file_size_mb=50)
        >>> validator.validate_file_size(1024 * 100)  # 100 KB
        >>> validator.validate_format("scan.png")
        >>> validator.validate_dimensions(512, 512)
    """

    # Supported image formats
    SUPPORTED_FORMATS: Set[str] = {"PNG", "JPEG", "JPG", "DICOM", "DCM"}

    # Valid data types for medical images
    VALID_DTYPES: Set[str] = {"uint8", "uint16", "float32", "float64"}

    # Expected pixel value ranges per data type
    DTYPE_RANGES = {
        "uint8": (0, 255),
        "uint16": (0, 65535),
        "float32": (0.0, 1.0),
        "float64": (0.0, 1.0),
    }

    def __init__(
        self,
        max_file_size_mb: int = 50,
        supported_formats: Optional[Set[str]] = None,
    ) -> None:
        """Initialize image validator.

        Args:
            max_file_size_mb: Maximum allowed file size in MB
            supported_formats: Override default supported formats

        Raises:
            ValueError: If max_file_size_mb <= 0
        """
        if max_file_size_mb <= 0:
            raise ValueError("max_file_size_mb must be positive")

        self.max_file_size_bytes = max_file_size_mb * 1024 * 1024
        self.max_file_size_mb = max_file_size_mb
        self.supported_formats = (
            supported_formats or self.SUPPORTED_FORMATS
        )

        logger.info(
            "ImageValidator initialized",
            extra={
                "max_size_mb": max_file_size_mb,
                "formats": len(self.supported_formats),
            },
        )

    def validate_file_size(self, size_bytes: int) -> None:
        """Validate file size is within acceptable range.

        Args:
            size_bytes: File size in bytes

        Raises:
            ImageValidationError: If file size invalid
        """
        if size_bytes <= 0:
            raise ImageValidationError(
                message="File size must be greater than zero",
                error_code="EMPTY_FILE",
                details={"size_bytes": size_bytes},
            )

        if size_bytes > self.max_file_size_bytes:
            raise ImageValidationError(
                message=(
                    f"File size {size_bytes} bytes exceeds maximum "
                    f"{self.max_file_size_bytes} bytes "
                    f"({self.max_file_size_mb} MB)"
                ),
                error_code="FILE_TOO_LARGE",
                details={
                    "size_bytes": size_bytes,
                    "max_bytes": self.max_file_size_bytes,
                },
            )

        logger.debug(f"File size validation passed: {size_bytes} bytes")

    def validate_format(self, filename: str) -> str:
        """Validate image format from filename extension.

        Args:
            filename: Image filename with extension

        Returns:
            File extension in uppercase

        Raises:
            ImageValidationError: If format not supported
        """
        if not filename or "." not in filename:
            raise ImageValidationError(
                message="Filename must include extension",
                error_code="INVALID_FILENAME",
                details={"filename": filename},
            )

        ext = filename.rsplit(".", 1)[-1].upper()

        if ext not in self.supported_formats:
            raise ImageValidationError(
                message=(
                    f"Invalid format '.{ext}'. "
                    f"Supported formats: {', '.join(sorted(self.supported_formats))}"
                ),
                error_code="UNSUPPORTED_FORMAT",
                details={"format": ext, "supported": list(self.supported_formats)},
            )

        logger.debug(f"Format validation passed: {ext}")
        return ext

    def validate_dimensions(
        self,
        width: int,
        height: int,
        constraints: Optional[ImageDimensions] = None,
    ) -> None:
        """Validate image dimensions are within constraints.

        Args:
            width: Image width in pixels
            height: Image height in pixels
            constraints: Dimension constraints (uses defaults if None)

        Raises:
            ImageValidationError: If dimensions invalid
        """
        if constraints is None:
            constraints = ImageDimensions()

        # Validate width
        if width < constraints.min_width:
            raise ImageValidationError(
                message=(
                    f"Image width {width} pixels is below minimum "
                    f"{constraints.min_width} pixels"
                ),
                error_code="WIDTH_TOO_SMALL",
                details={
                    "width": width,
                    "min_width": constraints.min_width,
                },
            )

        if width > constraints.max_width:
            raise ImageValidationError(
                message=(
                    f"Image width {width} pixels exceeds maximum "
                    f"{constraints.max_width} pixels"
                ),
                error_code="WIDTH_TOO_LARGE",
                details={
                    "width": width,
                    "max_width": constraints.max_width,
                },
            )

        # Validate height
        if height < constraints.min_height:
            raise ImageValidationError(
                message=(
                    f"Image height {height} pixels is below minimum "
                    f"{constraints.min_height} pixels"
                ),
                error_code="HEIGHT_TOO_SMALL",
                details={
                    "height": height,
                    "min_height": constraints.min_height,
                },
            )

        if height > constraints.max_height:
            raise ImageValidationError(
                message=(
                    f"Image height {height} pixels exceeds maximum "
                    f"{constraints.max_height} pixels"
                ),
                error_code="HEIGHT_TOO_LARGE",
                details={
                    "height": height,
                    "max_height": constraints.max_height,
                },
            )

        logger.debug(
            f"Dimension validation passed: {width}x{height}"
        )

    def validate_pixel_values(
        self,
        min_val: float,
        max_val: float,
        dtype: str = "uint8",
    ) -> None:
        """Validate pixel value ranges for data type.

        Args:
            min_val: Minimum pixel value in image
            max_val: Maximum pixel value in image
            dtype: Data type identifier (uint8, uint16, float32, float64)

        Raises:
            ImageValidationError: If values invalid for dtype
        """
        if dtype not in self.VALID_DTYPES:
            raise ImageValidationError(
                message=(
                    f"Unknown data type '{dtype}'. "
                    f"Supported types: {', '.join(sorted(self.VALID_DTYPES))}"
                ),
                error_code="INVALID_DTYPE",
                details={"dtype": dtype, "supported": list(self.VALID_DTYPES)},
            )

        expected_min, expected_max = self.DTYPE_RANGES[dtype]

        if min_val < expected_min:
            raise ImageValidationError(
                message=(
                    f"Minimum pixel value {min_val} is below expected "
                    f"range {expected_min}-{expected_max} for {dtype}"
                ),
                error_code="PIXEL_VALUE_OUT_OF_RANGE",
                details={
                    "min_val": min_val,
                    "expected_min": expected_min,
                    "dtype": dtype,
                },
            )

        if max_val > expected_max:
            raise ImageValidationError(
                message=(
                    f"Maximum pixel value {max_val} exceeds expected "
                    f"range {expected_min}-{expected_max} for {dtype}"
                ),
                error_code="PIXEL_VALUE_OUT_OF_RANGE",
                details={
                    "max_val": max_val,
                    "expected_max": expected_max,
                    "dtype": dtype,
                },
            )

        logger.debug(
            f"Pixel value validation passed: [{min_val}, {max_val}] for {dtype}"
        )

    def validate_aspect_ratio(
        self,
        width: int,
        height: int,
        min_ratio: float = 0.5,
        max_ratio: float = 2.0,
    ) -> None:
        """Validate image aspect ratio.

        Args:
            width: Image width in pixels
            height: Image height in pixels
            min_ratio: Minimum allowed ratio (width/height)
            max_ratio: Maximum allowed ratio (width/height)

        Raises:
            ImageValidationError: If aspect ratio invalid
        """
        if height == 0:
            raise ImageValidationError(
                message="Image height cannot be zero",
                error_code="INVALID_DIMENSIONS",
                details={"height": height},
            )

        ratio = width / height

        if ratio < min_ratio or ratio > max_ratio:
            raise ImageValidationError(
                message=(
                    f"Aspect ratio {ratio:.2f} outside acceptable range "
                    f"[{min_ratio}, {max_ratio}]"
                ),
                error_code="INVALID_ASPECT_RATIO",
                details={
                    "ratio": ratio,
                    "min_ratio": min_ratio,
                    "max_ratio": max_ratio,
                },
            )

        logger.debug(f"Aspect ratio validation passed: {ratio:.2f}")
