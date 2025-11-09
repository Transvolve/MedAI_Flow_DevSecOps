"""Clinical constraint validation for medical imaging.

Enforces clinical and domain-specific constraints on medical images to ensure
data quality, clinical appropriateness, and diagnostic validity.

Regulatory Mapping:
- ISO 14971: Risk assessment and mitigation
- IEC 62304: Software verification and validation
- FDA 21 CFR 11: Data integrity and quality
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, Optional

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ValidationResult:
    """Result of clinical constraint validation.
    
    Attributes:
        passed: Whether all constraints passed
        issues: List of constraint violations
        confidence_score: Overall quality score (0-1)
    """

    passed: bool = True
    issues: list = field(default_factory=list)
    confidence_score: float = 1.0

    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"ValidationResult(passed={self.passed}, "
            f"issues={len(self.issues)}, score={self.confidence_score:.2f})"
        )


@dataclass(frozen=True)
class ClinicalConstraints:
    """Clinical constraints for medical imaging validation.
    
    Enforces quality, brightness, contrast, and clinical appropriateness
    constraints for medical images.
    
    Regulatory Context:
        These constraints are based on clinical practice guidelines and
        FDA recommendations for medical image quality assessment.
    
    Attributes:
        min_pixel_brightness: Minimum acceptable average brightness (0-255)
        max_pixel_brightness: Maximum acceptable average brightness (0-255)
        min_contrast: Minimum acceptable image contrast ratio
        max_motion_artifacts: Maximum acceptable motion artifact ratio
        max_noise_ratio: Maximum acceptable noise-to-signal ratio
        required_quality_score: Minimum required quality score (0-1)
    """

    # Brightness constraints (relevant for grayscale and RGB images)
    min_pixel_brightness: float = 10.0
    max_pixel_brightness: float = 245.0

    # Contrast constraints
    min_contrast: float = 10.0

    # Image quality constraints
    max_motion_artifacts: float = 0.15  # 15% max motion artifacts
    max_noise_ratio: float = 0.10  # 10% max noise ratio
    required_quality_score: float = 0.7  # 70% minimum quality

    def validate_brightness(self, brightness: float) -> tuple[bool, Optional[str]]:
        """Validate image brightness is within clinical range.
        
        Args:
            brightness: Average brightness value (0-255)
            
        Returns:
            Tuple of (passed, error_message)
        """
        if not isinstance(brightness, (int, float)):
            return False, "Brightness must be numeric"

        if brightness < self.min_pixel_brightness:
            return (
                False,
                f"Brightness {brightness:.1f} below minimum {self.min_pixel_brightness}",
            )

        if brightness > self.max_pixel_brightness:
            return (
                False,
                f"Brightness {brightness:.1f} exceeds maximum {self.max_pixel_brightness}",
            )

        logger.debug(f"Brightness validation passed: {brightness:.1f}")
        return True, None

    def validate_contrast(self, contrast: float) -> tuple[bool, Optional[str]]:
        """Validate image contrast meets clinical standards.
        
        Args:
            contrast: Contrast ratio (higher is better)
            
        Returns:
            Tuple of (passed, error_message)
        """
        if not isinstance(contrast, (int, float)):
            return False, "Contrast must be numeric"

        if contrast < self.min_contrast:
            return (
                False,
                f"Contrast {contrast:.1f} below minimum {self.min_contrast}",
            )

        logger.debug(f"Contrast validation passed: {contrast:.1f}")
        return True, None

    def validate_motion_artifacts(
        self, motion_ratio: float
    ) -> tuple[bool, Optional[str]]:
        """Validate motion artifacts within acceptable limits.
        
        Args:
            motion_ratio: Estimated motion artifact ratio (0-1)
            
        Returns:
            Tuple of (passed, error_message)
        """
        if not isinstance(motion_ratio, (int, float)):
            return False, "Motion ratio must be numeric"

        if motion_ratio < 0 or motion_ratio > 1:
            return (
                False,
                f"Motion ratio must be between 0 and 1, got {motion_ratio}",
            )

        if motion_ratio > self.max_motion_artifacts:
            return (
                False,
                f"Motion artifacts {motion_ratio:.1%} exceed maximum {self.max_motion_artifacts:.1%}",
            )

        logger.debug(f"Motion artifact validation passed: {motion_ratio:.1%}")
        return True, None

    def validate_noise(self, noise_ratio: float) -> tuple[bool, Optional[str]]:
        """Validate noise levels within acceptable limits.
        
        Args:
            noise_ratio: Estimated noise-to-signal ratio (0-1)
            
        Returns:
            Tuple of (passed, error_message)
        """
        if not isinstance(noise_ratio, (int, float)):
            return False, "Noise ratio must be numeric"

        if noise_ratio < 0 or noise_ratio > 1:
            return (
                False,
                f"Noise ratio must be between 0 and 1, got {noise_ratio}",
            )

        if noise_ratio > self.max_noise_ratio:
            return (
                False,
                f"Noise level {noise_ratio:.1%} exceeds maximum {self.max_noise_ratio:.1%}",
            )

        logger.debug(f"Noise validation passed: {noise_ratio:.1%}")
        return True, None

    def validate_quality(self, quality_score: float) -> tuple[bool, Optional[str]]:
        """Validate overall image quality score meets clinical standards.
        
        Args:
            quality_score: Overall quality score (0-1)
            
        Returns:
            Tuple of (passed, error_message)
        """
        if not isinstance(quality_score, (int, float)):
            return False, "Quality score must be numeric"

        if quality_score < 0 or quality_score > 1:
            return (
                False,
                f"Quality score must be between 0 and 1, got {quality_score}",
            )

        if quality_score < self.required_quality_score:
            return (
                False,
                f"Quality {quality_score:.1%} below minimum {self.required_quality_score:.1%}",
            )

        logger.debug(f"Quality validation passed: {quality_score:.1%}")
        return True, None

    def validate_all(
        self,
        brightness: Optional[float] = None,
        contrast: Optional[float] = None,
        motion_ratio: Optional[float] = None,
        noise_ratio: Optional[float] = None,
        quality_score: Optional[float] = None,
    ) -> ValidationResult:
        """Validate all clinical constraints.
        
        Args:
            brightness: Average brightness value
            contrast: Image contrast
            motion_ratio: Motion artifact ratio
            noise_ratio: Noise-to-signal ratio
            quality_score: Overall quality score
            
        Returns:
            ValidationResult with all issues
        """
        issues = []

        if brightness is not None:
            passed, error = self.validate_brightness(brightness)
            if not passed:
                issues.append(error)

        if contrast is not None:
            passed, error = self.validate_contrast(contrast)
            if not passed:
                issues.append(error)

        if motion_ratio is not None:
            passed, error = self.validate_motion_artifacts(motion_ratio)
            if not passed:
                issues.append(error)

        if noise_ratio is not None:
            passed, error = self.validate_noise(noise_ratio)
            if not passed:
                issues.append(error)

        # Quality is composite score, affects overall confidence
        final_quality = quality_score or 1.0
        if quality_score is not None:
            passed, error = self.validate_quality(quality_score)
            if not passed:
                issues.append(error)

        result = ValidationResult(
            passed=len(issues) == 0,
            issues=issues,
            confidence_score=final_quality,
        )

        logger.info(
            f"Clinical validation completed",
            extra={
                "passed": result.passed,
                "issues": len(result.issues),
                "confidence": result.confidence_score,
            },
        )

        return result
