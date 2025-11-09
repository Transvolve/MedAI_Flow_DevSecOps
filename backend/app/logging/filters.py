"""PHI/PII filtering and detection for healthcare compliance.

Detects and masks Protected Health Information (PHI) and Personally Identifiable
Information (PII) in logs to prevent accidental exposure of sensitive data.

Regulatory Compliance:
- HIPAA: Protection of PHI
- GDPR: Protection of personal data
- FDA 21 CFR 11: Data protection and confidentiality
"""

import re
from typing import Dict, Pattern


class PHIFilter:
    """Detect and mask PHI/PII in logs and messages.
    
    Uses regular expressions to identify common PHI/PII patterns and replaces
    them with safe placeholders to prevent sensitive data exposure in logs.
    
    Patterns Detected:
    - Email addresses
    - Phone numbers (10+ digits with formatting)
    - Medical Record Numbers (MRN)
    - Social Security Numbers (XXX-XX-XXXX)
    - Dates of birth
    - Credit card numbers
    - IP addresses
    """

    # Regex patterns for PHI/PII detection
    PATTERNS: Dict[str, Pattern] = {
        "email": re.compile(
            r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
            re.IGNORECASE,
        ),
        "phone": re.compile(
            r"(?:\+1[-.\s]?)?"
            r"(?:\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}|"
            r"(?<!\d)[0-9]{3}[-.\s][0-9]{4}(?!\d))",
        ),
        "mrn": re.compile(r"(?:MRN|mrn|patient_id|PatientID)[\s:]*(\d{5,})", re.IGNORECASE),
        "ssn": re.compile(r"\d{3}-\d{2}-\d{4}"),
        "date_of_birth": re.compile(
            r"(?:DOB|dob|date_of_birth)[\s:]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
            re.IGNORECASE,
        ),
        "credit_card": re.compile(r"\b(?:\d{4}[-\s]?){3}\d{4}\b"),
        "ipv4": re.compile(r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b"),
    }

    # Redaction placeholder template
    REDACTION_TEMPLATE = "[REDACTED_{phi_type}]"

    @staticmethod
    def mask_phi(text: str) -> str:
        """Mask all PHI/PII in text.
        
        Args:
            text: Text that may contain PHI/PII
            
        Returns:
            Text with PHI/PII replaced by safe placeholders
            
        Examples:
            >>> PHIFilter.mask_phi("Email: john@example.com")
            "Email: [REDACTED_EMAIL]"
        """
        if not text or not isinstance(text, str):
            return text

        result = text
        for phi_type, pattern in PHIFilter.PATTERNS.items():
            placeholder = PHIFilter.REDACTION_TEMPLATE.format(phi_type=phi_type.upper())
            result = pattern.sub(placeholder, result)

        return result

    @staticmethod
    def contains_phi(text: str) -> bool:
        """Check if text contains PHI/PII.
        
        Args:
            text: Text to check
            
        Returns:
            True if PHI/PII detected
            
        Examples:
            >>> PHIFilter.contains_phi("SSN: 123-45-6789")
            True
        """
        if not text or not isinstance(text, str):
            return False

        for pattern in PHIFilter.PATTERNS.values():
            if pattern.search(text):
                return True

        return False

    @staticmethod
    def get_phi_types(text: str) -> list[str]:
        """Identify types of PHI/PII in text.
        
        Args:
            text: Text to analyze
            
        Returns:
            List of PHI/PII types found
            
        Examples:
            >>> PHIFilter.get_phi_types("Email: john@example.com, Phone: 555-1234")
            ["email", "phone"]
        """
        if not text or not isinstance(text, str):
            return []

        found_types = []
        for phi_type, pattern in PHIFilter.PATTERNS.items():
            if pattern.search(text):
                found_types.append(phi_type)

        return found_types


class AuditLogFilter(PHIFilter):
    """Filter for audit logs with PHI/PII detection and masking.
    
    Extends PHIFilter with audit-specific functionality for compliance logging.
    """

    @staticmethod
    def filter_audit_entry(entry: dict) -> tuple[dict, bool]:
        """Filter audit log entry for PHI/PII.
        
        Args:
            entry: Audit log entry dictionary
            
        Returns:
            Tuple of (filtered_entry, has_phi)
        """
        has_phi = False
        filtered = entry.copy()

        for key, value in filtered.items():
            if isinstance(value, str):
                if PHIFilter.contains_phi(value):
                    has_phi = True
                    filtered[key] = PHIFilter.mask_phi(value)

        return filtered, has_phi
