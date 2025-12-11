# PHASE 2: ENHANCED FEATURES & COMPLIANCE - Implementation Guide

**Phase:** Phase 2 (Enhanced Features & Compliance)  
**Timeline:** Weeks 4-6 (3 weeks)  
**Release Target:** v2.1.0  
**Estimated Effort:** 45 story points total  
**Regulatory Impact:** ⭐⭐⭐⭐  
**Starting Point:** v2.0.0 (Phase 1 Complete)

---

##  Phase 2 Overview

### Objectives
1. [OK] Implement advanced input validation with clinical constraints
2. [OK] Add structured logging with audit trails
3. [OK] Build robust error handling with no PHI leakage
4. [OK] Expand test coverage to 85%+
5. [OK] Enhance observability with production metrics
6. [OK] Integrate PostgreSQL for persistent storage
7. [OK] Enhance API with batch processing and results management

### Success Criteria
- [ ] Test coverage: 85%+ (from current ~60%)
- [ ] 500+ tests passing
- [ ] Zero critical security issues
- [ ] Full compliance documentation updated
- [ ] All deliverables code-reviewed and merged
- [ ] v2.1.0 release tagged and deployed

---

##  Deliverable 2.1: Advanced Input Validation

**Story Points:** 5  
**Priority:** HIGH  
**Timeline:** Week 4 (Days 1-2)

### Objective
Implement clinical-grade input validation with comprehensive error handling

### Files to Create

#### 1. `backend/app/validation/__init__.py`
```python
"""Input validation module for clinical data."""
from .image_validator import ImageValidator, ImageValidationError
from .clinical_constraints import ClinicalConstraints

__all__ = [
    "ImageValidator",
    "ImageValidationError",
    "ClinicalConstraints",
]
```

#### 2. `backend/app/validation/image_validator.py`
```python
"""Image validation utilities for medical imaging."""
from typing import Tuple, Optional
import logging
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ImageValidationError(Exception):
    """Raised when image validation fails."""
    
    def __init__(self, message: str, error_code: str):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class ImageDimensions(BaseModel):
    """Valid image dimension constraints."""
    min_width: int = Field(default=64, ge=1)
    max_width: int = Field(default=2048, ge=1)
    min_height: int = Field(default=64, ge=1)
    max_height: int = Field(default=2048, ge=1)
    required_channels: int = Field(default=3, ge=1, le=4)


class ImageValidator:
    """Validate medical images against clinical constraints."""
    
    def __init__(self, max_file_size_mb: int = 50):
        self.max_file_size = max_file_size_mb * 1024 * 1024
        self.valid_formats = {"PNG", "JPEG", "JPG", "DICOM", "DCM"}
    
    def validate_file_size(self, size_bytes: int) -> None:
        """Validate file size."""
        if size_bytes > self.max_file_size:
            raise ImageValidationError(
                f"File size {size_bytes} bytes exceeds maximum {self.max_file_size}",
                "INVALID_FILE_SIZE"
            )
        if size_bytes == 0:
            raise ImageValidationError(
                "File size cannot be zero",
                "EMPTY_FILE"
            )
    
    def validate_format(self, filename: str) -> str:
        """Validate image format from filename."""
        ext = filename.split(".")[-1].upper()
        if ext not in self.valid_formats:
            raise ImageValidationError(
                f"Invalid format '{ext}'. Supported: {', '.join(self.valid_formats)}",
                "INVALID_FORMAT"
            )
        return ext
    
    def validate_dimensions(
        self, 
        width: int, 
        height: int,
        constraints: Optional[ImageDimensions] = None
    ) -> None:
        """Validate image dimensions."""
        if constraints is None:
            constraints = ImageDimensions()
        
        if width < constraints.min_width or width > constraints.max_width:
            raise ImageValidationError(
                f"Width {width} outside valid range [{constraints.min_width}, {constraints.max_width}]",
                "INVALID_WIDTH"
            )
        
        if height < constraints.min_height or height > constraints.max_height:
            raise ImageValidationError(
                f"Height {height} outside valid range [{constraints.min_height}, {constraints.max_height}]",
                "INVALID_HEIGHT"
            )
    
    def validate_pixel_values(
        self,
        min_val: float,
        max_val: float,
        dtype: str = "uint8"
    ) -> None:
        """Validate pixel value ranges."""
        valid_ranges = {
            "uint8": (0, 255),
            "uint16": (0, 65535),
            "float32": (0.0, 1.0),
            "float64": (0.0, 1.0),
        }
        
        if dtype not in valid_ranges:
            raise ImageValidationError(
                f"Unknown data type '{dtype}'",
                "INVALID_DTYPE"
            )
        
        expected_min, expected_max = valid_ranges[dtype]
        
        if min_val < expected_min or max_val > expected_max:
            raise ImageValidationError(
                f"Pixel values [{min_val}, {max_val}] outside valid range for {dtype}",
                "INVALID_PIXEL_VALUES"
            )
```

#### 3. `backend/app/validation/clinical_constraints.py`
```python
"""Clinical constraint validation."""
from dataclasses import dataclass
from typing import Optional


@dataclass
class ClinicalConstraints:
    """Clinical constraints for medical imaging."""
    
    # Imaging constraints
    min_pixel_brightness: float = 10.0  # Minimum average brightness
    max_pixel_brightness: float = 245.0  # Maximum average brightness
    min_contrast: float = 10.0  # Minimum contrast ratio
    
    # Clinical constraints
    max_motion_artifacts: float = 0.15  # Max motion artifact ratio
    max_noise_ratio: float = 0.10  # Max noise ratio
    required_quality_score: float = 0.7  # Min quality score (0-1)
    
    def validate_brightness(self, brightness: float) -> bool:
        """Check if brightness within acceptable range."""
        return self.min_pixel_brightness <= brightness <= self.max_pixel_brightness
    
    def validate_contrast(self, contrast: float) -> bool:
        """Check if contrast within acceptable range."""
        return contrast >= self.min_contrast
    
    def validate_quality(self, quality_score: float) -> bool:
        """Check if quality meets minimum requirements."""
        return quality_score >= self.required_quality_score
```

### Implementation Steps

1. **Create validation module directory:**
   ```bash
   mkdir -p backend/app/validation
   ```

2. **Create validation files with code above**

3. **Update `backend/app/routes.py` to use validation:**
   ```python
   from app.validation import ImageValidator, ImageValidationError
   
   @router.post("/infer")
   async def infer(request: InferenceRequest):
       validator = ImageValidator(max_file_size_mb=50)
       try:
           validator.validate_file_size(len(request.image_data))
           validator.validate_format(request.filename or "image.png")
           # Additional validations...
       except ImageValidationError as e:
           raise HTTPException(
               status_code=400,
               detail={
                   "error": e.message,
                   "code": e.error_code
               }
           )
   ```

4. **Add unit tests** in `tests/unit/test_validation.py`

### Acceptance Criteria
- [ ] All validation utilities implemented
- [ ] Image dimension validation working
- [ ] Pixel value validation working
- [ ] Clinical constraints enforced
- [ ] Error codes defined for all validation failures
- [ ] 100% test coverage for validation module
- [ ] No PHI/PII in error messages

---

##  Deliverable 2.2: Structured Logging & Audit Trails

**Story Points:** 8  
**Priority:** HIGH  
**Timeline:** Week 4 (Days 3-5)

### Objective
Enterprise-grade logging with compliance audit support

### Files to Create

#### 1. `backend/app/logging/__init__.py`
```python
"""Structured logging module."""
from .structured import StructuredLogger, get_logger
from .filters import PHIFilter

__all__ = ["StructuredLogger", "get_logger", "PHIFilter"]
```

#### 2. `backend/app/logging/structured.py`
```python
"""Structured JSON logging for compliance."""
import json
import logging
import sys
from typing import Any, Dict, Optional
from datetime import datetime
import uuid


class StructuredLogger:
    """JSON structured logger for compliance and monitoring."""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.correlation_id: Optional[str] = None
    
    def _build_log_entry(
        self,
        level: str,
        message: str,
        **kwargs
    ) -> str:
        """Build structured log entry."""
        entry: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": level,
            "message": message,
            "logger": self.logger.name,
            "correlation_id": self.correlation_id or str(uuid.uuid4()),
        }
        entry.update(kwargs)
        return json.dumps(entry)
    
    def set_correlation_id(self, correlation_id: str) -> None:
        """Set correlation ID for request tracing."""
        self.correlation_id = correlation_id
    
    def debug(self, message: str, **kwargs) -> None:
        """Log debug level."""
        self.logger.debug(self._build_log_entry("DEBUG", message, **kwargs))
    
    def info(self, message: str, **kwargs) -> None:
        """Log info level."""
        self.logger.info(self._build_log_entry("INFO", message, **kwargs))
    
    def warning(self, message: str, **kwargs) -> None:
        """Log warning level."""
        self.logger.warning(self._build_log_entry("WARNING", message, **kwargs))
    
    def error(self, message: str, **kwargs) -> None:
        """Log error level."""
        self.logger.error(self._build_log_entry("ERROR", message, **kwargs))
    
    def critical(self, message: str, **kwargs) -> None:
        """Log critical level."""
        self.logger.critical(self._build_log_entry("CRITICAL", message, **kwargs))
    
    def audit(
        self,
        action: str,
        resource: str,
        user_id: Optional[str] = None,
        status: str = "SUCCESS",
        **kwargs
    ) -> None:
        """Log audit event."""
        self.info(
            f"AUDIT: {action}",
            action=action,
            resource=resource,
            user_id=user_id,
            status=status,
            **kwargs
        )


def get_logger(name: str) -> StructuredLogger:
    """Get structured logger instance."""
    return StructuredLogger(name)
```

#### 3. `backend/app/logging/filters.py`
```python
"""PHI/PII filtering for logs."""
import re


class PHIFilter:
    """Filter to detect and mask PHI/PII in logs."""
    
    # Patterns for common PHI/PII
    PATTERNS = {
        "email": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
        "phone": r"[\d\-\(\)\s]{10,}",
        "mrn": r"(?:MRN|mrn|patient_id)[\s:]*(\d{5,})",
        "ssn": r"\d{3}-\d{2}-\d{4}",
        "date_of_birth": r"(?:DOB|dob)[\s:]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
    }
    
    @staticmethod
    def mask_phi(text: str) -> str:
        """Mask PHI/PII in text."""
        result = text
        for phi_type, pattern in PHIFilter.PATTERNS.items():
            result = re.sub(pattern, f"[REDACTED_{phi_type.upper()}]", result)
        return result
    
    @staticmethod
    def contains_phi(text: str) -> bool:
        """Check if text contains PHI/PII."""
        for pattern in PHIFilter.PATTERNS.values():
            if re.search(pattern, text):
                return True
        return False
```

#### 4. `backend/app/audit/audit_log.py`
```python
"""Audit logging for compliance."""
from datetime import datetime
from typing import Optional, Dict, Any
import hashlib
import json


class AuditLog:
    """Tamper-evident audit logging."""
    
    def __init__(self):
        self.entries: list = []
        self.last_hash: str = "0" * 64
    
    def _calculate_hash(self, entry: str) -> str:
        """Calculate SHA256 hash of entry with previous hash."""
        combined = f"{self.last_hash}{entry}"
        return hashlib.sha256(combined.encode()).hexdigest()
    
    def log_event(
        self,
        event_type: str,
        user_id: str,
        resource: str,
        action: str,
        details: Optional[Dict[str, Any]] = None
    ) -> str:
        """Log audit event with integrity check."""
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "user_id": user_id,
            "resource": resource,
            "action": action,
            "details": details or {},
        }
        
        entry_str = json.dumps(entry)
        entry_hash = self._calculate_hash(entry_str)
        
        audit_record = {
            **entry,
            "hash": entry_hash,
            "previous_hash": self.last_hash,
        }
        
        self.entries.append(audit_record)
        self.last_hash = entry_hash
        
        return entry_hash
    
    def verify_integrity(self) -> bool:
        """Verify audit log integrity (hash chain)."""
        if not self.entries:
            return True
        
        current_hash = "0" * 64
        for entry in self.entries:
            expected_previous = current_hash
            actual_previous = entry["previous_hash"]
            
            if expected_previous != actual_previous:
                return False
            
            current_hash = entry["hash"]
        
        return True
```

### Implementation Steps

1. **Create logging module:**
   ```bash
   mkdir -p backend/app/logging
   mkdir -p backend/app/audit
   ```

2. **Create logging files with code above**

3. **Update `backend/app/middleware.py` to add correlation IDs:**
   ```python
   from app.logging import get_logger
   import uuid
   
   logger = get_logger(__name__)
   
   @app.middleware("http")
   async def add_correlation_id(request, call_next):
       correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
       request.state.correlation_id = correlation_id
       logger.set_correlation_id(correlation_id)
       
       response = await call_next(request)
       response.headers["X-Correlation-ID"] = correlation_id
       return response
   ```

4. **Add unit tests** in `tests/unit/test_logging.py`

### Acceptance Criteria
- [ ] JSON structured logging implemented
- [ ] Correlation IDs tracked end-to-end
- [ ] PHI/PII detection and masking working
- [ ] Audit logging with hash chain working
- [ ] Log integrity verification working
- [ ] 100% test coverage for logging module
- [ ] All logs are JSON-formatted

---

##  Deliverable 2.3: Enhanced Error Handling

**Story Points:** 5  
**Priority:** HIGH  
**Timeline:** Week 5 (Days 1-2)

### Objective
Clinical-safe error handling with no PHI leakage

### Files to Create

#### 1. `backend/app/exceptions.py`
```python
"""Custom exception hierarchy for the application."""
from typing import Optional, Dict, Any


class MedAIFlowException(Exception):
    """Base exception for all MedAI Flow errors."""
    
    def __init__(
        self,
        message: str,
        error_code: str,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(MedAIFlowException):
    """Raised when input validation fails."""
    
    def __init__(self, message: str, field: Optional[str] = None):
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            status_code=400,
            details={"field": field} if field else {}
        )


class AuthenticationError(MedAIFlowException):
    """Raised when authentication fails."""
    
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(
            message=message,
            error_code="AUTHENTICATION_ERROR",
            status_code=401
        )


class AuthorizationError(MedAIFlowException):
    """Raised when user lacks required permissions."""
    
    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(
            message=message,
            error_code="AUTHORIZATION_ERROR",
            status_code=403
        )


class InferenceError(MedAIFlowException):
    """Raised when inference fails."""
    
    def __init__(self, message: str, inference_id: Optional[str] = None):
        super().__init__(
            message=message,
            error_code="INFERENCE_ERROR",
            status_code=500,
            details={"inference_id": inference_id} if inference_id else {}
        )


class ResourceNotFoundError(MedAIFlowException):
    """Raised when resource not found."""
    
    def __init__(self, resource_type: str, resource_id: str):
        super().__init__(
            message=f"{resource_type} '{resource_id}' not found",
            error_code="NOT_FOUND",
            status_code=404,
            details={"resource_type": resource_type, "resource_id": resource_id}
        )


class RateLimitError(MedAIFlowException):
    """Raised when rate limit exceeded."""
    
    def __init__(self, retry_after: int = 60):
        super().__init__(
            message="Rate limit exceeded. Please retry after some time.",
            error_code="RATE_LIMIT_EXCEEDED",
            status_code=429,
            details={"retry_after": retry_after}
        )
```

#### 2. `backend/app/error_handlers.py`
```python
"""FastAPI error handlers."""
from fastapi import Request
from fastapi.responses import JSONResponse
from app.exceptions import MedAIFlowException
from app.logging import get_logger

logger = get_logger(__name__)


async def medaiflow_exception_handler(
    request: Request,
    exc: MedAIFlowException
):
    """Handle MedAI Flow exceptions."""
    
    # Log internally with full details
    logger.error(
        f"Exception: {exc.message}",
        error_code=exc.error_code,
        status_code=exc.status_code,
        details=exc.details
    )
    
    # Return sanitized response (no internal details)
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.message,
            "error_code": exc.error_code,
            "details": exc.details,  # Contains only non-sensitive info
        }
    )


async def generic_exception_handler(
    request: Request,
    exc: Exception
):
    """Handle unexpected exceptions."""
    
    # Log full details internally
    logger.error(
        f"Unexpected error: {str(exc)}",
        error_type=type(exc).__name__
    )
    
    # Return generic error to client (no internal details)
    return JSONResponse(
        status_code=500,
        content={
            "error": "An unexpected error occurred",
            "error_code": "INTERNAL_ERROR"
        }
    )
```

### Integration Steps

1. **Update `backend/app/main.py`:**
   ```python
   from app.exceptions import MedAIFlowException
   from app.error_handlers import medaiflow_exception_handler, generic_exception_handler
   
   app.add_exception_handler(MedAIFlowException, medaiflow_exception_handler)
   app.add_exception_handler(Exception, generic_exception_handler)
   ```

2. **Update routes to use custom exceptions:**
   ```python
   from app.exceptions import ValidationError, AuthenticationError
   
   @router.post("/infer")
   async def infer(request: InferenceRequest):
       if not request.image_data:
           raise ValidationError("Image data required", field="image_data")
   ```

3. **Add unit tests** in `tests/unit/test_exceptions.py`

### Acceptance Criteria
- [ ] Custom exception hierarchy implemented
- [ ] All exceptions have error codes
- [ ] Error handlers registered in FastAPI
- [ ] Internal logging has full details
- [ ] Client responses sanitized (no PHI/PII)
- [ ] HTTP status codes correct
- [ ] 100% test coverage

---

##  Deliverable 2.4: Test Coverage Expansion to 85%+

**Story Points:** 13  
**Priority:** HIGH  
**Timeline:** Week 5 (Days 3-5) + Week 6

### Objective
Comprehensive test suite covering all code paths

### Test Structure
```
tests/
├── unit/
│   ├── test_config.py
│   ├── test_validation.py
│   ├── test_utils.py
│   ├── test_logging.py
│   ├── test_exceptions.py
│   └── test_audit.py
├── integration/
│   ├── test_api_auth_flows.py
│   ├── test_api_inference_flows.py
│   ├── test_error_scenarios.py
│   └── test_rate_limiting.py
├── security/
│   ├── test_auth_bypass.py
│   ├── test_input_injection.py
│   └── test_header_security.py
└── conftest.py
```

### Key Tests to Add

#### Unit Tests
- Config loading and validation
- Validation utility edge cases
- Logging format and filtering
- Exception creation and serialization
- Audit log integrity

#### Integration Tests
- Complete authentication flows
- Inference request → response cycles
- Error handling workflows
- Rate limit enforcement

#### Security Tests
- JWT token manipulation attempts
- SQL injection attempts
- XSS payload attempts
- CORS bypass attempts

### Implementation Steps

1. **Create test directories:**
   ```bash
   mkdir -p tests/unit tests/integration tests/security
   ```

2. **Create `tests/conftest.py` with fixtures:**
   ```python
   import pytest
   from fastapi.testclient import TestClient
   from app.main import app
   
   @pytest.fixture
   def client():
       return TestClient(app)
   
   @pytest.fixture
   def valid_token():
       # Create valid JWT token for testing
       from app.security.jwt_manager import JWTManager
       manager = JWTManager()
       return manager.create_token("test_user")
   ```

3. **Implement test files with comprehensive coverage**

4. **Add coverage reporting to CI/CD:**
   ```yaml
   - name: Generate coverage report
     run: |
       pytest --cov=backend --cov-report=xml --cov-report=term
       coverage report --fail-under=85
   ```

### Acceptance Criteria
- [ ] 500+ tests total
- [ ] 85%+ code coverage
- [ ] All edge cases covered
- [ ] Security tests passing
- [ ] Coverage report generated in CI/CD
- [ ] Coverage enforcement at 85% minimum
- [ ] All tests green

---

##  Deliverable 2.5: Observability Enhancement

**Story Points:** 8  
**Priority:** MEDIUM  
**Timeline:** Week 6 (Days 1-3)

### Objective
Production-grade monitoring and observability

### Metrics to Add

```python
# Application metrics
request_latency = Histogram(
    "http_request_latency_ms",
    "Request latency in milliseconds",
    buckets=[10, 50, 100, 250, 500, 1000]
)

inference_latency = Histogram(
    "inference_latency_ms",
    "Inference latency in milliseconds",
    buckets=[50, 100, 250, 500, 1000, 2000]
)

error_counter = Counter(
    "errors_total",
    "Total errors by type",
    labelnames=["error_type", "endpoint"]
)

auth_attempts = Counter(
    "auth_attempts_total",
    "Authentication attempts by result",
    labelnames=["result"]  # success, failure
)

rate_limit_hits = Counter(
    "rate_limit_hits_total",
    "Rate limit hits by user",
    labelnames=["user_id"]
)
```

### Files to Create

#### `backend/app/metrics.py`
```python
"""Prometheus metrics collection."""
from prometheus_client import Counter, Histogram, Gauge
import time


class MetricsCollector:
    """Collect application metrics."""
    
    def __init__(self):
        self.request_latency = Histogram(
            "http_request_latency_ms",
            "Request latency",
            buckets=[10, 50, 100, 250, 500, 1000]
        )
        
        self.inference_latency = Histogram(
            "inference_latency_ms",
            "Inference latency",
            buckets=[50, 100, 250, 500, 1000, 2000]
        )
        
        self.errors_total = Counter(
            "errors_total",
            "Total errors",
            labelnames=["error_type", "endpoint"]
        )
        
        self.auth_attempts = Counter(
            "auth_attempts_total",
            "Auth attempts",
            labelnames=["result"]
        )
    
    def record_request_latency(self, latency_ms: float):
        """Record HTTP request latency."""
        self.request_latency.observe(latency_ms)
    
    def record_inference_latency(self, latency_ms: float):
        """Record inference latency."""
        self.inference_latency.observe(latency_ms)
    
    def record_error(self, error_type: str, endpoint: str):
        """Record error occurrence."""
        self.errors_total.labels(
            error_type=error_type,
            endpoint=endpoint
        ).inc()
```

### Grafana Dashboards

Create dashboard JSON for visualization:
```json
{
  "dashboard": {
    "title": "MedAI Flow Metrics",
    "panels": [
      {
        "title": "Request Latency (p95)",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, http_request_latency_ms)"
          }
        ]
      },
      {
        "title": "Inference Latency (p95)",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, inference_latency_ms)"
          }
        ]
      },
      {
        "title": "Error Rate",
        "targets": [
          {
            "expr": "rate(errors_total[5m])"
          }
        ]
      }
    ]
  }
}
```

### Acceptance Criteria
- [ ] 150+ application metrics defined
- [ ] Prometheus endpoint working
- [ ] Grafana dashboards created
- [ ] Alert rules defined
- [ ] Metrics documented
- [ ] Integration tests passing

---

##  Deliverable 2.6: Database Integration (PostgreSQL)

**Story Points:** 13  
**Priority:** HIGH  
**Timeline:** Week 6 (Days 3-5) + Overflow

### Objective
Persistent storage for inference results and audit logs

### Files to Create

#### 1. `backend/app/database.py`
```python
"""Database configuration and connection management."""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool
import os

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://user:password@localhost:5432/medai_flow"
)

engine = create_engine(
    DATABASE_URL,
    poolclass=NullPool,  # Use for scalable deployments
    echo=os.getenv("SQL_ECHO", "false").lower() == "true"
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Session:
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

#### 2. `backend/app/models/inference.py`
```python
"""Inference result models."""
from sqlalchemy import Column, String, DateTime, Float, JSON, Integer
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import uuid

Base = declarative_base()


class InferenceResult(Base):
    """Store inference results."""
    __tablename__ = "inference_results"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(255), nullable=False, index=True)
    model_id = Column(String(255), nullable=False, index=True)
    model_version = Column(String(50), nullable=False)
    
    # Input
    image_filename = Column(String(255), nullable=False)
    image_hash = Column(String(64), nullable=False, unique=True)
    
    # Output
    predictions = Column(JSON, nullable=False)
    confidence_score = Column(Float, nullable=False)
    processing_time_ms = Column(Integer, nullable=False)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Audit
    verified_by = Column(String(255), nullable=True)
    verified_at = Column(DateTime, nullable=True)
    comments = Column(String(1000), nullable=True)
```

#### 3. `backend/app/repositories/inference_repository.py`
```python
"""Repository for inference results."""
from sqlalchemy.orm import Session
from app.models.inference import InferenceResult
from typing import List, Optional


class InferenceRepository:
    """Data access for inference results."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, result: InferenceResult) -> InferenceResult:
        """Create inference result."""
        self.db.add(result)
        self.db.commit()
        self.db.refresh(result)
        return result
    
    def get_by_id(self, inference_id: str) -> Optional[InferenceResult]:
        """Get inference by ID."""
        return self.db.query(InferenceResult).filter(
            InferenceResult.id == inference_id
        ).first()
    
    def get_by_user(self, user_id: str, limit: int = 100) -> List[InferenceResult]:
        """Get inferences for user."""
        return self.db.query(InferenceResult).filter(
            InferenceResult.user_id == user_id
        ).order_by(InferenceResult.created_at.desc()).limit(limit).all()
    
    def verify(self, inference_id: str, verified_by: str) -> Optional[InferenceResult]:
        """Mark inference as verified."""
        result = self.get_by_id(inference_id)
        if result:
            result.verified_by = verified_by
            result.verified_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(result)
        return result
```

### Alembic Migrations

#### `alembic/env.py` (partial example)
```python
"""Alembic environment configuration."""
from alembic import context
from sqlalchemy import engine_from_config, pool
from app.database import Base

target_metadata = Base.metadata

def run_migrations_online():
    """Run migrations."""
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = os.getenv("DATABASE_URL")
    
    engine = engine_from_config(configuration, prefix="sqlalchemy.", poolclass=pool.NullPool)
    
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()
```

### Acceptance Criteria
- [ ] PostgreSQL connection working
- [ ] SQLAlchemy ORM models created
- [ ] Alembic migrations working
- [ ] CRUD operations for results
- [ ] Connection pooling configured
- [ ] Query optimization (indexes)
- [ ] Integration tests passing

---

##  Deliverable 2.7: API Enhancements

**Story Points:** 8  
**Priority:** MEDIUM  
**Timeline:** Week 6 (Overflow)

### New Endpoints

#### `POST /infer/batch`
```python
@router.post("/infer/batch")
async def infer_batch(
    request: BatchInferenceRequest,
    current_user: str = Depends(get_current_user)
) -> BatchInferenceResponse:
    """Process multiple images in batch."""
    results = []
    for image in request.images:
        result = await infer(InferenceRequest(image_data=image))
        results.append(result)
    return BatchInferenceResponse(results=results)
```

#### `GET /models`
```python
@router.get("/models")
async def list_models():
    """List available models."""
    return {"models": get_available_models()}
```

#### `GET /results`
```python
@router.get("/results")
async def get_results(
    skip: int = 0,
    limit: int = 100,
    current_user: str = Depends(get_current_user)
):
    """Get past inferences for user."""
    repo = InferenceRepository(db)
    return repo.get_by_user(current_user, limit=limit)
```

### Acceptance Criteria
- [ ] Batch inference working
- [ ] Results pagination working
- [ ] Model info endpoint working
- [ ] All new endpoints documented
- [ ] Integration tests passing

---

##  Phase 2 Implementation Timeline

### Week 4
- **Days 1-2:** Input Validation (2.1)
- **Days 3-5:** Structured Logging (2.2)

### Week 5
- **Days 1-2:** Error Handling (2.3)
- **Days 3-5:** Test Coverage Expansion (2.4) - Part 1

### Week 6
- **Days 1-2:** Test Coverage Expansion (2.4) - Part 2
- **Days 3:** Observability (2.5)
- **Days 4-5:** Database Integration (2.6)

### Overflow (if needed)
- API Enhancements (2.7)

---

## 🔄 Development Workflow

### Daily Standup Checklist
- [ ] Updated todo list with progress
- [ ] All tests passing locally
- [ ] No merge conflicts
- [ ] Code review completed
- [ ] Documentation updated

### Before Committing
```bash
# 1. Run all tests
pytest tests/ -v --cov=backend

# 2. Type check
mypy backend/

# 3. Lint
ruff check backend/

# 4. Security scan
bandit -r backend/

# 5. Verify coverage
coverage report --fail-under=85
```

### Pull Request Process
1. Create feature branch: `git checkout -b feature/phase-2-{deliverable}`
2. Implement code with tests
3. Run full test suite
4. Create PR with description
5. Code review + approval
6. Merge to main
7. Verify CI/CD passes

### Release Process
1. All Phase 2 deliverables complete
2. All tests passing (500+)
3. Coverage > 85%
4. Zero critical security issues
5. Documentation updated
6. Tag release: `git tag -a v2.1.0 -m "Phase 2: Enhanced Features"`
7. Push tag: `git push origin v2.1.0`

---

##  Documentation Requirements

### For Each Deliverable
- [ ] Code comments and docstrings
- [ ] README.md updates
- [ ] API documentation (OpenAPI/Swagger)
- [ ] Architecture decision records (ADR)
- [ ] Traceability matrix updates
- [ ] Risk management file updates

### Compliance Documentation
- [ ] IEC 62304: Software verification
- [ ] ISO 14971: Risk mitigation evidence
- [ ] FDA 21 CFR 11: System validation
- [ ] HIPAA: Data handling procedures

---

## [OK] Phase 2 Success Metrics

| Metric | Target | Threshold |
|--------|--------|-----------|
| Tests Passing | 500+ | >95% pass rate |
| Coverage | 85%+ | >84% minimum |
| Security Issues | 0 critical | 0 allowed |
| Code Quality | A+ | Ruff clean |
| Type Safety | 100% | 0 mypy errors |
| Performance | P95 <500ms | <1000ms max |
| Deployment | <10 min | <15 min max |

---

##  Getting Started

### Setup Phase 2 Branch
```bash
# Create feature branch
git checkout -b feature/phase-2-complete

# Create directories
mkdir -p backend/app/validation
mkdir -p backend/app/logging backend/app/audit
mkdir -p backend/app/repositories
mkdir -p tests/unit tests/integration tests/security

# Start with 2.1 - Input Validation
```

### Next Steps After Phase 2
1. Phase 3: Clinical Features & Compliance
2. Phase 4: Production Hardening
3. Phase 5: Commercialization

---

**Document Version:** 1.0  
**Last Updated:** November 9, 2025  
**Next Phase:** Phase 3 (Clinical Features & Compliance)

