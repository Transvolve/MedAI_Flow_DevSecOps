"""
database/models.py
-----------------
SQLAlchemy ORM models for MedAI Flow backend, including:
- InferenceResult: Medical image inference results with clinical metadata
- AuditLog: Tamper-proof audit trail of all operations
- User: User account management with role-based access control
- ModelVersion: Model version tracking and metadata management
- ValidationResult: Clinical validation results tied to inferences

Regulatory Compliance:
- FDA 21 CFR 11: § 11.10 (System validation)
- FDA 21 CFR 11: § 11.70 (Audit trails)
- ISO 27001: A.12.4.1 (Event logging)
- ISO 13485: 4.2.3.2 (Document control)
- HIPAA: 164.312(b) (Audit controls)
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Column, String, Integer, Float, DateTime, Boolean, ForeignKey,
    Text, JSON, Enum, Index, UniqueConstraint, CheckConstraint,
    func, LargeBinary, desc
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import enum
import uuid

# SQLAlchemy declarative base for all models
Base = declarative_base()


class ModelStatus(str, enum.Enum):
    """Model versioning status for compliance tracking."""
    DEVELOPMENT = "development"
    VALIDATION = "validation"
    PRODUCTION = "production"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


class InferenceStatus(str, enum.Enum):
    """Inference result status for clinical workflow."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REVIEWED = "reviewed"
    APPROVED = "approved"


class AuditActionType(str, enum.Enum):
    """Types of audit-logged actions for compliance."""
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    MODEL_LOADED = "model_loaded"
    INFERENCE_STARTED = "inference_started"
    INFERENCE_COMPLETED = "inference_completed"
    RESULT_RETRIEVED = "result_retrieved"
    RESULT_MODIFIED = "result_modified"
    DATA_EXPORT = "data_export"
    CONFIGURATION_CHANGED = "configuration_changed"
    ACCESS_DENIED = "access_denied"


class ModelVersion(Base):
    """
    Model versioning table for tracking ML model versions, compliance,
    and regulatory metadata.

    Regulatory Purpose:
    - FDA 21 CFR 11: Document versioning and change control
    - ISO 13485: Configuration management
    - IEC 62304: Software version identification
    """
    __tablename__ = "model_versions"
    __table_args__ = (
        Index("idx_model_status", "status"),
        Index("idx_model_created", "created_at"),
    )

    # Primary Key
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # Model Metadata
    model_name = Column(String(255), nullable=False)
    version = Column(String(50), nullable=False)
    status = Column(Enum(ModelStatus), default=ModelStatus.DEVELOPMENT, nullable=False)

    # File & Checksum
    file_path = Column(String(512), nullable=False)
    file_hash = Column(String(64), nullable=False)  # SHA-256
    file_size_bytes = Column(Integer, nullable=False)

    # Performance Metadata
    input_shape = Column(JSON, nullable=False)
    output_shape = Column(JSON, nullable=False)
    inference_latency_ms = Column(Float, nullable=True)

    # Clinical Metadata
    clinical_domain = Column(String(100), nullable=False)  # e.g., "radiology", "pathology"
    confidence_threshold = Column(Float, default=0.85, nullable=False)

    # Compliance Tracking
    validation_status = Column(String(50), nullable=True)
    fda_submission_id = Column(String(100), nullable=True)
    iso_certification = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    deployed_at = Column(DateTime, nullable=True)
    deprecated_at = Column(DateTime, nullable=True)

    # Relationships
    inference_results = relationship("InferenceResult", back_populates="model_version")
    audit_logs = relationship("AuditLog", back_populates="model_version")

    # Constraints
    __table_args__ = (
        UniqueConstraint("model_name", "version", name="uq_model_version"),
        CheckConstraint("file_size_bytes > 0", name="ck_file_size_positive"),
        CheckConstraint(
            "confidence_threshold >= 0.0 AND confidence_threshold <= 1.0",
            name="ck_confidence_valid"),
    )

    def __repr__(self) -> str:
        return f"<ModelVersion {self.model_name} v{self.version} ({self.status})>"


class InferenceResult(Base):
    """
    Inference results table for storing medical AI predictions with clinical
    metadata and regulatory tracking.

    Regulatory Purpose:
    - FDA 21 CFR 11: Data integrity and audit trail
    - HIPAA: Patient medical record management
    - ISO 27001: Sensitive data handling
    """
    __tablename__ = "inference_results"
    __table_args__ = (
        Index("idx_inference_status", "status"),
        Index("idx_inference_created", "created_at"),
        Index("idx_inference_patient", "patient_id"),
        Index("idx_inference_model", "model_version_id"),
    )

    # Primary Key
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # Model Reference
    model_version_id = Column(String(36), ForeignKey("model_versions.id"), nullable=False)

    # Inference Metadata
    status = Column(Enum(InferenceStatus), default=InferenceStatus.COMPLETED, nullable=False)
    confidence_score = Column(Float, nullable=False)
    prediction = Column(JSON, nullable=False)

    # Clinical Data
    patient_id = Column(String(100), nullable=True)  # De-identified patient reference
    study_date = Column(DateTime, nullable=True)
    anatomical_region = Column(String(100), nullable=True)

    # Image Metadata
    image_width = Column(Integer, nullable=False)
    image_height = Column(Integer, nullable=False)
    image_format = Column(String(20), nullable=False)
    image_hash = Column(String(64), nullable=False)  # For deduplication

    # Performance Metrics
    inference_latency_ms = Column(Float, nullable=False)
    preprocessing_latency_ms = Column(Float, nullable=False)

    # User & Audit
    created_by = Column(String(100), nullable=False)
    reviewed_by = Column(String(100), nullable=True)
    review_comments = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    reviewed_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)  # Data retention policy

    # Relationships
    model_version = relationship("ModelVersion", back_populates="inference_results")
    audit_logs = relationship("AuditLog", back_populates="inference_result")
    validation_results = relationship("ValidationResult", back_populates="inference_result")

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "confidence_score >= 0.0 AND confidence_score <= 1.0",
            name="ck_confidence_score_valid"),
        CheckConstraint("inference_latency_ms >= 0", name="ck_latency_positive"),
        CheckConstraint("preprocessing_latency_ms >= 0", name="ck_prep_latency_positive"),
    )

    def __repr__(self) -> str:
        return f"<InferenceResult {self.id} (confidence: {self.confidence_score})>"


class ValidationResult(Base):
    """
    Clinical validation results tied to inferences for quality assurance
    and regulatory compliance tracking.

    Regulatory Purpose:
    - FDA 21 CFR 11: § 11.10 (System validation)
    - ISO 13485: 8.2.4 (Control of monitoring and measuring)
    """
    __tablename__ = "validation_results"
    __table_args__ = (
        Index("idx_validation_inference", "inference_result_id"),
        Index("idx_validation_created", "created_at"),
    )

    # Primary Key
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # Inference Reference
    inference_result_id = Column(
        String(36), ForeignKey("inference_results.id"),
        nullable=False)

    # Validation Rules Applied
    brightness_valid = Column(Boolean, nullable=False)
    contrast_valid = Column(Boolean, nullable=False)
    motion_artifact_free = Column(Boolean, nullable=False)
    noise_level_acceptable = Column(Boolean, nullable=False)

    # Overall Result
    is_valid = Column(Boolean, nullable=False)
    validation_score = Column(Float, nullable=False)
    error_codes = Column(JSON, default=list, nullable=False)
    warnings = Column(JSON, default=list, nullable=False)

    # Metadata
    validator_version = Column(String(50), nullable=False)
    validation_timestamp = Column(DateTime, server_default=func.now(), nullable=False)

    # Relationships
    inference_result = relationship("InferenceResult", back_populates="validation_results")

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "validation_score >= 0.0 AND validation_score <= 1.0",
            name="ck_validation_score_valid"),
    )

    def __repr__(self) -> str:
        return f"<ValidationResult {self.id} (valid: {self.is_valid})>"


class User(Base):
    """
    User account management with role-based access control and audit trail.

    Regulatory Purpose:
    - ISO 27001: A.9.2 (User access management)
    - ISO 27001: A.9.4.3 (Password management)
    - FDA 21 CFR 11: § 11.100 (Access controls)
    """
    __tablename__ = "users"
    __table_args__ = (
        Index("idx_user_email", "email"),
        Index("idx_user_created", "created_at"),
        UniqueConstraint("email", name="uq_user_email"),
    )

    # Primary Key
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # User Identity
    username = Column(String(100), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)

    # Security
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    role = Column(String(50), nullable=False)  # 'admin', 'clinician', 'viewer'

    # Profile
    full_name = Column(String(255), nullable=True)
    organization = Column(String(255), nullable=True)

    # Access Control
    last_login_at = Column(DateTime, nullable=True)
    failed_login_attempts = Column(Integer, default=0, nullable=False)
    locked_until = Column(DateTime, nullable=True)
    password_changed_at = Column(DateTime, nullable=True)

    # Audit
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, onupdate=func.now(), nullable=False, server_default=func.now())
    deactivated_at = Column(DateTime, nullable=True)

    # Relationships
    audit_logs = relationship("AuditLog", back_populates="user")

    # Constraints
    __table_args__ = (
        CheckConstraint("email LIKE '%@%'", name="ck_email_format"),
        CheckConstraint("failed_login_attempts >= 0", name="ck_failed_logins_positive"),
    )

    def __repr__(self) -> str:
        return f"<User {self.username} ({self.role})>"


class AuditLog(Base):
    """
    Tamper-proof audit trail for all operations, including a hash chain for
    integrity verification.

    Regulatory Purpose:
    - FDA 21 CFR 11: § 11.70 (Audit trails)
    - FDA 21 CFR 11: § 11.70(e) (Audit trail location)
    - HIPAA: 164.312(b) (Audit controls)
    - ISO 27001: A.12.4.1 (Event logging)
    """
    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("idx_audit_action", "action"),
        Index("idx_audit_user", "user_id"),
        Index("idx_audit_created", "created_at"),
        Index("idx_audit_hash", "entry_hash"),
    )

    # Primary Key
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # Audit Details
    action = Column(Enum(AuditActionType), nullable=False)
    description = Column(Text, nullable=False)

    # User & References
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    model_version_id = Column(String(36), ForeignKey("model_versions.id"), nullable=True)
    inference_result_id = Column(String(36), ForeignKey("inference_results.id"), nullable=True)

    # Context Data (JSONified for flexibility)
    context = Column(JSON, default=dict, nullable=False)
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(512), nullable=True)

    # Integrity Verification (Hash Chain)
    entry_hash = Column(String(64), nullable=False)  # SHA-256 of this entry
    previous_hash = Column(String(64), nullable=True)  # Link to previous entry (hash chain)
    hash_chain_verified = Column(Boolean, default=False, nullable=False)

    # Timestamp
    created_at = Column(
        DateTime, server_default=func.now(), nullable=False,
        index=True)

    # Relationships
    user = relationship("User", back_populates="audit_logs")
    model_version = relationship("ModelVersion", back_populates="audit_logs")
    inference_result = relationship("InferenceResult", back_populates="audit_logs")

    def __repr__(self) -> str:
        return f"<AuditLog {self.id} ({self.action.value})>"


# Export all models
__all__ = [
    "Base",
    "ModelVersion",
    "InferenceResult",
    "ValidationResult",
    "User",
    "AuditLog",
    "ModelStatus",
    "InferenceStatus",
    "AuditActionType",
]
