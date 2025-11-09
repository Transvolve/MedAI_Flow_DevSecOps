"""Unit tests for validation module (2.1 deliverable).

Tests cover:
- Image validation (format, size, dimensions, pixel values, aspect ratio)
- Clinical constraints (brightness, contrast, motion, noise, quality)
- Error handling and edge cases
- Pydantic model validation

Target Coverage: 100% of validation module
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from backend.app.validation import (
    ImageValidator,
    ImageValidationError,
    ImageDimensions,
    ClinicalConstraints,
    ValidationResult,
)


class TestImageDimensions:
    """Test Pydantic ImageDimensions model."""

    def test_valid_dimensions(self):
        """Test creating valid ImageDimensions."""
        dims = ImageDimensions(min_width=64, max_width=512, min_height=64, max_height=512)
        assert dims.min_width == 64
        assert dims.max_width == 512
        assert dims.max_height == 512

    def test_minimum_dimensions(self):
        """Test minimum dimension constraints."""
        dims = ImageDimensions(min_width=64, max_width=128, min_height=64, max_height=128)
        assert dims.min_width == 64

    def test_maximum_dimensions(self):
        """Test maximum dimension constraints."""
        dims = ImageDimensions(min_width=1024, max_width=2048, min_height=1024, max_height=2048)
        assert dims.max_width == 2048

    def test_default_dimensions(self):
        """Test default dimension constraints."""
        dims = ImageDimensions()
        assert dims.min_width == 64
        assert dims.max_width == 2048
        assert dims.min_height == 64
        assert dims.max_height == 2048

    def test_invalid_min_width_too_small(self):
        """Test min_width below absolute minimum."""
        with pytest.raises(ValueError):
            ImageDimensions(min_width=0, max_width=512)

    def test_invalid_max_width_too_large(self):
        """Test max_width above absolute maximum."""
        with pytest.raises(ValueError):
            ImageDimensions(max_width=9000)

    def test_required_channels(self):
        """Test required_channels validation."""
        dims = ImageDimensions(required_channels=1)
        assert dims.required_channels == 1
        
        dims = ImageDimensions(required_channels=4)
        assert dims.required_channels == 4


class TestImageValidationError:
    """Test ImageValidationError exception."""

    def test_error_creation(self):
        """Test creating validation error."""
        error = ImageValidationError(
            message="File is empty",
            error_code="EMPTY_FILE",
            details={"size": 0},
        )
        assert error.error_code == "EMPTY_FILE"
        assert error.message == "File is empty"
        assert error.details == {"size": 0}

    def test_error_string_representation(self):
        """Test error string representation."""
        error = ImageValidationError(
            message="File exceeds maximum size",
            error_code="FILE_TOO_LARGE",
        )
        error_str = repr(error)
        assert "FILE_TOO_LARGE" in error_str
        assert "File exceeds maximum size" in error_str

    def test_error_inheritance(self):
        """Test that ImageValidationError is Exception."""
        error = ImageValidationError("test message", "TEST")
        assert isinstance(error, Exception)


class TestImageValidator:
    """Test ImageValidator class."""

    def setup_method(self):
        """Setup test fixtures."""
        self.validator = ImageValidator(max_file_size_mb=50)

    def test_validator_creation(self):
        """Test creating validator."""
        validator = ImageValidator(max_file_size_mb=100)
        assert validator.max_file_size_mb == 100

    def test_validator_creation_invalid(self):
        """Test creating validator with invalid size."""
        with pytest.raises(ValueError):
            ImageValidator(max_file_size_mb=0)

    def test_validate_file_size_empty(self):
        """Test validation of empty file."""
        with pytest.raises(ImageValidationError) as exc_info:
            self.validator.validate_file_size(0)
        assert exc_info.value.error_code == "EMPTY_FILE"

    def test_validate_file_size_too_large(self):
        """Test validation of file exceeding max size."""
        max_bytes = 50 * 1024 * 1024
        over_size = max_bytes + 1024
        with pytest.raises(ImageValidationError) as exc_info:
            self.validator.validate_file_size(over_size)
        assert exc_info.value.error_code == "FILE_TOO_LARGE"

    def test_validate_file_size_valid(self):
        """Test validation of valid file size."""
        result = self.validator.validate_file_size(1024 * 1024)  # 1MB
        assert result is None

    def test_validate_format_supported(self):
        """Test validation of supported format."""
        result = self.validator.validate_format("test.png")
        assert result == "PNG"

    def test_validate_format_unsupported(self):
        """Test validation of unsupported format."""
        with pytest.raises(ImageValidationError) as exc_info:
            self.validator.validate_format("test.bmp")
        assert exc_info.value.error_code == "UNSUPPORTED_FORMAT"

    def test_validate_format_case_insensitive(self):
        """Test format validation is case insensitive."""
        result = self.validator.validate_format("test.PNG")
        assert result == "PNG"
        result = self.validator.validate_format("test.jpeg")
        assert result == "JPEG"

    def test_validate_format_no_extension(self):
        """Test validation of file without extension."""
        with pytest.raises(ImageValidationError) as exc_info:
            self.validator.validate_format("testimage")
        assert exc_info.value.error_code == "INVALID_FILENAME"

    def test_supported_formats(self):
        """Test all supported formats."""
        supported = ["test.png", "test.jpeg", "test.jpg", "test.dicom", "test.dcm"]
        for filename in supported:
            result = self.validator.validate_format(filename)
            assert result is not None


class TestClinicalConstraints:
    """Test ClinicalConstraints validator."""

    def setup_method(self):
        """Setup test fixtures."""
        self.constraints = ClinicalConstraints(
            min_pixel_brightness=10.0,
            max_pixel_brightness=245.0,
            min_contrast=10.0,
            max_motion_artifacts=0.15,
            max_noise_ratio=0.10,
            required_quality_score=0.7,
        )

    def test_constraints_frozen(self):
        """Test that constraints dataclass is frozen."""
        with pytest.raises((AttributeError, TypeError)):
            self.constraints.min_pixel_brightness = 20.0

    def test_validate_brightness_valid(self):
        """Test brightness validation with valid value."""
        passed, issues = self.constraints.validate_brightness(128.0)
        assert passed is True
        assert issues is None

    def test_validate_brightness_too_low(self):
        """Test brightness validation below minimum."""
        passed, issues = self.constraints.validate_brightness(5.0)
        assert passed is False
        assert issues is not None
        assert "brightness" in issues.lower()

    def test_validate_brightness_too_high(self):
        """Test brightness validation above maximum."""
        passed, issues = self.constraints.validate_brightness(250.0)
        assert passed is False
        assert issues is not None

    def test_validate_brightness_boundaries(self):
        """Test brightness at minimum and maximum."""
        # At minimum
        passed, _ = self.constraints.validate_brightness(10.0)
        assert passed is True

        # At maximum
        passed, _ = self.constraints.validate_brightness(245.0)
        assert passed is True

    def test_validate_contrast_valid(self):
        """Test contrast validation with valid value."""
        passed, issues = self.constraints.validate_contrast(15.0)
        assert passed is True
        assert issues is None

    def test_validate_contrast_too_low(self):
        """Test contrast validation below minimum."""
        passed, issues = self.constraints.validate_contrast(5.0)
        assert passed is False
        assert issues is not None

    def test_validate_motion_artifacts_valid(self):
        """Test motion artifacts validation with valid ratio."""
        passed, issues = self.constraints.validate_motion_artifacts(0.10)  # 10%
        assert passed is True
        assert issues is None

    def test_validate_motion_artifacts_too_high(self):
        """Test motion artifacts validation exceeding limit."""
        passed, issues = self.constraints.validate_motion_artifacts(0.20)  # 20%
        assert passed is False
        assert issues is not None

    def test_validate_noise_valid(self):
        """Test noise ratio validation with valid value."""
        passed, issues = self.constraints.validate_noise(0.08)  # 8%
        assert passed is True
        assert issues is None

    def test_validate_noise_too_high(self):
        """Test noise ratio validation exceeding limit."""
        passed, issues = self.constraints.validate_noise(0.15)  # 15%
        assert passed is False
        assert issues is not None

    def test_validate_quality_valid(self):
        """Test quality score validation with valid value."""
        passed, issues = self.constraints.validate_quality(0.85)  # 85%
        assert passed is True
        assert issues is None

    def test_validate_quality_too_low(self):
        """Test quality score validation below minimum."""
        passed, issues = self.constraints.validate_quality(0.60)  # 60%
        assert passed is False
        assert issues is not None

    def test_validate_all_all_pass(self):
        """Test composite validation when all constraints pass."""
        brightness = 128.0
        contrast = 15.0
        motion = 0.10
        noise = 0.08
        quality = 0.85

        result = self.constraints.validate_all(
            brightness, contrast, motion, noise, quality
        )

        assert result.passed is True
        assert len(result.issues) == 0
        assert result.confidence_score >= 0.85

    def test_validate_all_some_fail(self):
        """Test composite validation when some constraints fail."""
        brightness = 5.0  # Too low
        contrast = 15.0  # OK
        motion = 0.20  # Too high
        noise = 0.08  # OK
        quality = 0.85  # OK

        result = self.constraints.validate_all(
            brightness, contrast, motion, noise, quality
        )

        assert result.passed is False
        assert len(result.issues) > 0
        assert any("brightness" in issue.lower() for issue in result.issues)
        assert any("motion" in issue.lower() for issue in result.issues)

    def test_validate_all_all_fail(self):
        """Test composite validation when all constraints fail."""
        brightness = 5.0  # Too low
        contrast = 5.0  # Too low
        motion = 0.20  # Too high
        noise = 0.15  # Too high
        quality = 0.60  # Too low

        result = self.constraints.validate_all(
            brightness, contrast, motion, noise, quality
        )

        assert result.passed is False
        assert len(result.issues) == 5


class TestValidationIntegration:
    """Integration tests for validation module."""

    def test_validator_pipeline(self):
        """Test complete validation pipeline."""
        validator = ImageValidator()
        constraints = ClinicalConstraints()

        # Simulate valid image
        validator.validate_file_size(1024 * 1024)
        fmt = validator.validate_format("test.png")
        assert fmt == "PNG"

        result = constraints.validate_all(128, 15, 0.10, 0.08, 0.85)
        assert result.passed is True

    def test_validation_error_accumulation(self):
        """Test that validation errors are properly raised."""
        validator = ImageValidator()

        errors = []
        try:
            validator.validate_file_size(0)
        except ImageValidationError as e:
            errors.append(e)

        try:
            validator.validate_format("test.bmp")
        except ImageValidationError as e:
            errors.append(e)

        assert len(errors) == 2
        assert errors[0].error_code == "EMPTY_FILE"
        assert errors[1].error_code == "UNSUPPORTED_FORMAT"

    def test_default_constraints(self):
        """Test that default constraints are sensible."""
        validator = ImageValidator()
        constraints = ClinicalConstraints()

        # Ensure defaults are set
        assert validator.max_file_size_mb > 0
        assert validator.max_file_size_bytes > 0
        assert constraints.min_pixel_brightness >= 0
        assert constraints.max_pixel_brightness <= 255
        assert constraints.required_quality_score > 0
        assert constraints.required_quality_score <= 1


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_validator_with_small_max_size(self):
        """Test validator with very small max file size."""
        validator = ImageValidator(max_file_size_mb=1)
        with pytest.raises(ImageValidationError):
            validator.validate_file_size(2 * 1024 * 1024)  # 2MB

    def test_validator_with_large_max_size(self):
        """Test validator with very large max file size."""
        validator = ImageValidator(max_file_size_mb=1000)  # 1GB
        validator.validate_file_size(500 * 1024 * 1024)  # Should pass

    def test_format_validation_various_extensions(self):
        """Test format validation with various extensions."""
        validator = ImageValidator()
        
        valid_formats = ["test.png", "test.jpeg", "test.jpg", "test.dicom", "test.dcm"]
        for filename in valid_formats:
            result = validator.validate_format(filename)
            assert result is not None

    def test_dimensions_boundary_validation(self):
        """Test dimension boundary validation."""
        dims = ImageDimensions(min_width=100, max_width=100)
        assert dims.min_width == 100
        assert dims.max_width == 100


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
