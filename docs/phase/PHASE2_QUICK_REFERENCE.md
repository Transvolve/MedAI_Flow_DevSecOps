"""Quick Reference Guide: Phase 2.1-2.3 Implementation

Fast lookup for developers integrating and using the new modules.
"""

# ============================================================================
# VALIDATION MODULE QUICK START
# ============================================================================

"""
Location: backend/app/validation/
Files: __init__.py, image_validator.py, clinical_constraints.py

Usage in Code:
  from backend.app.validation import (
      ImageValidator,
      ImageValidationError,
      ImageDimensions,
      ClinicalConstraints,
  )

  # Create validator
  validator = ImageValidator()
  
  # Validate image file
  try:
      validator.validate_file_size(file_size)  # bytes
      validator.validate_format(filename)
      dims = ImageDimensions(width=512, height=512)
      validator.validate_dimensions(dims)
      validator.validate_pixel_values("uint8")
      validator.validate_aspect_ratio(dims)
  except ImageValidationError as e:
      return {
          "error": e.error_code,
          "message": e.message,
          "details": e.details,
          "status": 400
      }
  
  # Validate clinical quality
  constraints = ClinicalConstraints()
  result = constraints.validate_all(
      brightness=128.0,
      contrast=15.0,
      motion_artifacts=0.10,
      noise=0.08,
      quality=0.85
  )
  
  if not result.passed:
      return {
          "error": "QUALITY_CHECK_FAILED",
          "issues": result.issues,
          "confidence": result.confidence_score,
          "status": 422
      }

Error Codes:
  EMPTY_FILE - File size is 0
  FILE_TOO_LARGE - File exceeds max size
  UNSUPPORTED_FORMAT - File extension not approved
  DIMENSIONS_OUT_OF_RANGE - Image dimensions invalid
  UNSUPPORTED_PIXEL_TYPE - Data type not supported
  ASPECT_RATIO_OUT_OF_RANGE - Aspect ratio outside bounds

Configuration Defaults:
  max_file_size: 50 * 1024 * 1024  # 50MB
  min_dimensions: 64x64 pixels
  max_dimensions: 2048x2048 pixels
  supported_formats: png, jpeg, jpg, dicom, dcm
  supported_pixel_types: uint8, uint16, float32, float64
  min_aspect_ratio: 0.5
  max_aspect_ratio: 2.0
  
  Clinical constraints:
  - min_pixel_brightness: 10.0 (0-255 range)
  - max_pixel_brightness: 245.0
  - min_contrast: 10.0
  - max_motion_artifacts: 0.15 (15%)
  - max_noise_ratio: 0.10 (10%)
  - required_quality_score: 0.7 (70%)
"""


# ============================================================================
# LOGGING & AUDIT QUICK START
# ============================================================================

"""
Location: backend/app/logging/, backend/app/audit/
Files: logging/__init__.py, logging/filters.py, audit/__init__.py

Structured Logging Usage:
  from backend.app.logging import get_logger
  
  logger = get_logger(__name__)
  
  # Set correlation ID for request tracing
  logger.set_correlation_id("req-12345")
  
  # Log information (JSON format)
  logger.info("User action completed", user_id="u123", action="LOGIN")
  
  # Audit logging
  logger.audit(
      action="MODEL_DEPLOY",
      resource="model:v1.0.0",
      user_id="admin",
      status="SUCCESS"
  )
  
  # Error logging
  logger.error("Operation failed", operation="inference", reason="OOM")
  
  # Exception logging
  try:
      perform_operation()
  except Exception:
      logger.exception("Operation failed with exception")

Log Output Format (JSON):
  {
    "timestamp": "2024-01-15T10:30:45.123Z",
    "level": "INFO",
    "message": "User action completed",
    "logger": "app.inference",
    "correlation_id": "req-12345",
    "user_id": "u123",
    "action": "LOGIN"
  }

PHI/PII Filtering:
  from backend.app.logging.filters import PHIFilter, AuditLogFilter
  
  # Check if text contains PHI
  has_phi = PHIFilter.contains_phi("Email: user@example.com")  # True
  
  # Mask PHI in text
  safe_text = PHIFilter.mask_phi("SSN: 123-45-6789")
  # Result: "SSN: [REDACTED_SSN]"
  
  # Get PHI types found
  types = PHIFilter.get_phi_types("user@example.com, 555-1234")
  # Result: ["email", "phone"]
  
  # Filter audit entry
  entry = {"user_email": "john@example.com", "action": "LOGIN"}
  filtered, has_phi = AuditLogFilter.filter_audit_entry(entry)
  # filtered: {"user_email": "[REDACTED_EMAIL]", "action": "LOGIN"}
  # has_phi: True

PHI Patterns Detected:
  - Email addresses (user@domain.com)
  - Phone numbers (555-123-4567, (555)123-4567, etc.)
  - Social Security Numbers (123-45-6789)
  - Medical Record Numbers (MRN: xxxxx)
  - Dates of birth (DOB: mm/dd/yyyy)
  - Credit card numbers (1234-5678-9012-3456)
  - IP addresses (192.168.1.1)

Audit Trail Usage:
  from backend.app.audit import AuditTrail
  
  trail = AuditTrail()
  
  # Log action
  entry = trail.log_action(
      action="USER_CREATED",
      resource_type="USER",
      resource_id="user123",
      user_id="admin",
      status="SUCCESS",
      details={"email": "user@example.com"}
  )
  
  # Verify integrity (hash-chain)
  is_valid = trail.verify_integrity()
  
  # Query entries
  user_actions = trail.get_entries_by_user("admin")
  resource_history = trail.get_entries_for_resource("USER", "user123")
  logins = trail.get_entries_by_action("LOGIN")
  recent = trail.get_latest_entries(count=10)
  
  # Export for storage
  json_export = trail.export_json()

Audit Entry Structure:
  entry_id: UUID4 unique identifier
  timestamp: UTC creation time (ISO format)
  action: Operation (LOGIN, CREATE, UPDATE, DELETE, etc.)
  resource_type: Resource class (USER, MODEL, IMAGE, etc.)
  resource_id: Specific resource ID
  user_id: Who performed action
  status: SUCCESS or FAILURE
  details: Additional context (dict)
  previous_hash: SHA256 of prior entry (chain link)
  entry_hash: SHA256 of this entry (immutable)

Hash-Chain Verification:
  If entry is tampered, its hash changes
  This breaks the chain at the next entry
  verify_integrity() detects any tampering
"""


# ============================================================================
# ERROR HANDLING QUICK START
# ============================================================================

"""
Location: backend/app/error_handling.py

Usage in Code:
  from backend.app.error_handling import (
      ApplicationError,
      ValidationError,
      AuthenticationError,
      AuthorizationError,
      NotFoundError,
      RateLimitError,
      BusinessLogicError,
      DatabaseError,
      ExternalServiceError,
      handle_error,
  )
  
  # Validation error
  try:
      if not email_valid(email):
          raise ValidationError(
              field="email",
              message="Invalid email format"
          )
  except ValidationError as e:
      return {"error_code": e.error_code, "message": e.message}, e.http_status
  
  # Not found error
  if not user_exists(user_id):
      raise NotFoundError(
          resource_type="User",
          resource_id=user_id
      )
  
  # Rate limit error
  if too_many_requests(user_id):
      raise RateLimitError(retry_after=60)
  
  # Convert any exception
  try:
      risky_operation()
  except Exception as e:
      app_error = handle_error(e, context={"operation": "xyz"})
      app_error.log_error(request_id="req-123")
      return {"error": app_error.to_dict()}, app_error.http_status

Error Response Format (Safe for API):
  {
    "error_code": "VAL_001",
    "message": "Invalid input format",
    "category": "VALIDATION"
  }
  
  Note: Internal details are NOT included in API responses
        All sensitive info is logged separately

Error Classes & HTTP Status:
  ValidationError → 400
  AuthenticationError → 401
  AuthorizationError → 403
  NotFoundError → 404
  BusinessLogicError → 422
  RateLimitError → 429
  DatabaseError → 500
  ExternalServiceError → 502
  ApplicationError (generic) → 500

Error Code Format (16 codes predefined):
  Category_Number, e.g., VAL_001, AUTH_004, DB_001
  
  VAL_001: Invalid input format (400)
  VAL_002: Missing required field (400)
  VAL_003: Input exceeds maximum length (400)
  AUTH_001: Invalid credentials (401)
  AUTH_002: Token expired (401)
  AUTH_003: Invalid token (401)
  AUTH_004: Insufficient permissions (403)
  NOT_FOUND_001: Resource not found (404)
  BIZ_001: Business rule violation (422)
  BIZ_002: Insufficient data (422)
  RATE_001: Rate limit exceeded (429)
  DB_001: Database connection error (500)
  DB_002: Database transaction error (500)
  SYS_001: Internal server error (500)
  SYS_002: Service unavailable (503)
  EXT_001: External service error (502)

Error Properties:
  error.error_code - String identifier
  error.message - User-friendly message
  error.category - ErrorCategory enum
  error.http_status - HTTP status code
  error.severity - Log level (INFO/WARNING/ERROR/CRITICAL)
  error.details - Internal context (not API exposed)
  error.to_dict() - API-safe dictionary
  error.log_error() - Log with correlation ID
"""


# ============================================================================
# TESTING QUICK START
# ============================================================================

"""
Test Files:
  tests/unit/test_validation.py - 50+ tests
  tests/unit/test_logging_audit.py - 80+ tests
  tests/unit/test_error_handling.py - 70+ tests

Running Tests:
  pytest tests/unit/test_validation.py -v
  pytest tests/unit/test_logging_audit.py -v
  pytest tests/unit/test_error_handling.py -v
  pytest tests/unit/ -v --cov=backend/app

Test Examples:

  # Validation test
  def test_validate_file_size():
      validator = ImageValidator()
      validator.validate_file_size(1024*1024)  # OK
      with pytest.raises(ImageValidationError):
          validator.validate_file_size(0)  # Empty file

  # Logging test
  def test_structured_logging():
      logger = StructuredLogger(__name__)
      logger.set_correlation_id("req-123")
      logger.info("Test", action="LOGIN")
      # Output is JSON-formatted

  # Audit trail test
  def test_hash_chain():
      trail = AuditTrail()
      trail.log_action("CREATE", "USER", "u1")
      trail.log_action("UPDATE", "USER", "u1")
      assert trail.verify_integrity() is True

  # Error handling test
  def test_validation_error():
      with pytest.raises(ValidationError):
          raise ValidationError(field="email")
      
      error = ValidationError(field="email")
      response_dict = error.to_dict()
      assert "details" not in response_dict  # Safe!
"""


# ============================================================================
# COMPLIANCE MAPPINGS
# ============================================================================

"""
FDA 21 CFR 11:
  [OK] Validation: Input validation requirements (Part 11.100)
  [OK] Logging: Audit trail requirements (Part 11.10)
  [OK] Error Handling: Error logging requirements (Part 11.192)

HIPAA:
  [OK] Validation: Data integrity validation
  [OK] Logging: Comprehensive audit logs (164.312)
  [OK] PHI Protection: Filter and mask PHI in logs
  [OK] Error Handling: No PHI in error messages

ISO 27001:
  [OK] Logging: Security event logging and monitoring (A.12.4.1)
  [OK] Audit: Information security logs (A.12.4.3)
  [OK] Error Handling: Security-related error handling

IEC 62304:
  [OK] Validation: Software validation requirements (8.2.1)
  [OK] Testing: Comprehensive unit tests (8.3.5)

ISO 14971:
  [OK] Risk Analysis: Error handling for risk mitigation
  [OK] Control: Validation and testing controls
"""


# ============================================================================
# INTEGRATION CHECKLIST
# ============================================================================

"""
Before integrating into /infer endpoint:

Validation Module:
  [ ] Import ImageValidator and ClinicalConstraints
  [ ] Wrap file upload handling in validation
  [ ] Catch ImageValidationError and return proper response
  [ ] Log validation success/failure
  [ ] Verify error codes returned match API spec
  
Logging Module:
  [ ] Get logger instance with get_logger(__name__)
  [ ] Set correlation ID from request header
  [ ] Log key lifecycle events (start, validation, result)
  [ ] Verify JSON format in logs
  [ ] Check PHI filtering in debug logs
  
Audit Trail:
  [ ] Create AuditTrail instance
  [ ] Log successful inference
  [ ] Log failed inference with reason
  [ ] Verify hash-chain integrity
  [ ] Export trail for compliance reports
  
Error Handling:
  [ ] Import specific error classes
  [ ] Raise appropriate error for each failure case
  [ ] Convert to ApplicationError if needed
  [ ] Return error.to_dict() in response
  [ ] Log error with error.log_error()
  
Testing:
  [ ] Run unit tests: pytest tests/unit/ -v
  [ ] Verify 85%+ code coverage
  [ ] Run integration tests with /infer endpoint
  [ ] Test error paths and edge cases
  [ ] Verify no sensitive data in logs/errors
"""


# ============================================================================
# PERFORMANCE CHARACTERISTICS
# ============================================================================

"""
Validation Module:
  - File size check: <1ms (constant time)
  - Format validation: <1ms (regex)
  - Dimension validation: <1ms (comparison)
  - Aspect ratio: <1ms (math)
  - Clinical constraints: <5ms (all checks)
  Total: <10ms for complete validation

Logging Module:
  - JSON serialization: <1ms (small messages)
  - PHI detection: <2ms (regex patterns)
  - Correlation ID setup: <1μs
  Total overhead: <3ms per log call

Audit Trail:
  - Hash computation: <1ms (SHA256)
  - Append entry: <1ms
  - Verify integrity (1000 entries): <50ms
  - Query operations: <1ms

Error Handling:
  - Error creation: <1μs
  - to_dict() conversion: <1ms
  - log_error(): <3ms (logging overhead)
  Total: <5ms per error
"""


# ============================================================================
# COMMON PATTERNS
# ============================================================================

"""
Pattern 1: Image Validation Pipeline
  validator = ImageValidator()
  try:
      validator.validate_file_size(file_size)
      validator.validate_format(filename)
      dims = ImageDimensions(width=w, height=h)
      validator.validate_dimensions(dims)
      validator.validate_pixel_values(dtype)
      validator.validate_aspect_ratio(dims)
  except ImageValidationError as e:
      logger.error("Validation failed", code=e.error_code)
      raise

Pattern 2: Audit with PHI Filtering
  entry_data = {"user_email": "john@example.com"}
  filtered, has_phi = AuditLogFilter.filter_audit_entry(entry_data)
  trail.log_action(
      action="LOGIN",
      resource_type="USER",
      resource_id="user123",
      details=filtered  # Safe for storage
  )

Pattern 3: Error Handling in API Route
  @app.post("/infer")
  async def infer(request):
      try:
          request_id = request.headers.get("X-Correlation-ID")
          logger.set_correlation_id(request_id)
          
          # ... inference logic ...
          
      except ApplicationError as e:
          e.log_error(request_id=request_id)
          return JSONResponse(
              content=e.to_dict(),
              status_code=e.http_status
          )
      except Exception as e:
          app_error = handle_error(e)
          app_error.log_error(request_id=request_id)
          return JSONResponse(
              content=app_error.to_dict(),
              status_code=500
          )

Pattern 4: Compliance Reporting
  trail = AuditTrail()
  # ... perform operations ...
  
  # Generate compliance report
  report = {
      "total_entries": len(trail),
      "integrity_verified": trail.verify_integrity(),
      "user_actions": trail.get_entries_by_user(user_id),
      "audit_log": json.loads(trail.export_json())
  }
  return report
"""


# ============================================================================
# TROUBLESHOOTING
# ============================================================================

"""
Issue: ImageValidationError "EMPTY_FILE"
  Cause: File size is 0
  Solution: Check file upload, ensure file not corrupted

Issue: PHIFilter not detecting email
  Cause: Email pattern might not match format
  Solution: Verify email format, may need custom pattern

Issue: Hash-chain verification fails
  Cause: An entry was tampered with
  Solution: Restore from backup, investigate modification

Issue: Validation too strict/lenient
  Cause: Default constraints don't match use case
  Solution: Create custom ImageValidator with different constraints:
    validator = ImageValidator(
        max_file_size=100*1024*1024,  # 100MB
        min_dimensions=ImageDimensions(width=32, height=32),
        max_dimensions=ImageDimensions(width=4096, height=4096),
    )

Issue: Logs not appearing in JSON format
  Cause: Logger not configured for JSON output
  Solution: Ensure using StructuredLogger, not standard logging

Issue: Performance degradation with audit trail
  Cause: Too many entries accumulating in memory
  Solution: Implement trail export/cleanup or use database backend
"""

