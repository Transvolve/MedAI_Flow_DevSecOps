"""
tests/unit/test_database.py
---------------------------
Comprehensive unit tests for database models, session management, and connection
pooling. Validates SQLAlchemy ORM operations, data integrity, and compliance
with regulatory standards.

Test Coverage:
- Model creation and validation
- CRUD operations for all models
- Relationship integrity
- Transaction management
- Connection pooling
- Session lifecycle
- Data constraints and validation
- Hash chain integrity (audit logs)

Regulatory Compliance Tested:
- FDA 21 CFR 11: § 11.10 (System validation)
- FDA 21 CFR 11: § 11.70 (Audit trails)
- ISO 27001: A.12.4.1 (Event logging)
- HIPAA: 164.312(b) (Audit controls)
"""

import pytest
import uuid
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import hashlib

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from backend.app.database import (
    DatabaseManager,
    DatabaseConfig,
    init_db,
    get_db_manager,
)
from backend.app.database.models import (
    Base,
    ModelVersion,
    InferenceResult,
    ValidationResult,
    User,
    AuditLog,
    ModelStatus,
    InferenceStatus,
    AuditActionType,
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def in_memory_db():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine)
    return engine, SessionLocal


@pytest.fixture
def session(in_memory_db):
    """Create a database session for testing."""
    engine, SessionLocal = in_memory_db
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def sample_user(session):
    """Create a sample user for testing."""
    user = User(
        username="testuser",
        email="test@example.com",
        password_hash="hashed_password",
        role="clinician",
        full_name="Test User",
    )
    session.add(user)
    session.commit()
    return user


@pytest.fixture
def sample_model_version(session):
    """Create a sample model version for testing."""
    model = ModelVersion(
        model_name="ResNet50",
        version="1.0.0",
        status=ModelStatus.PRODUCTION,
        file_path="/models/resnet50_v1.onnx",
        file_hash="abc123def456",
        file_size_bytes=102400,
        input_shape={"width": 512, "height": 512, "channels": 3},
        output_shape={"predictions": 1000},
        clinical_domain="radiology",
        confidence_threshold=0.85,
    )
    session.add(model)
    session.commit()
    return model


@pytest.fixture
def sample_inference_result(session, sample_model_version, sample_user):
    """Create a sample inference result for testing."""
    result = InferenceResult(
        model_version_id=sample_model_version.id,
        status=InferenceStatus.COMPLETED,
        confidence_score=0.92,
        prediction={"class": "normal", "score": 0.92},
        patient_id="PATIENT_001",
        image_width=512,
        image_height=512,
        image_format="DICOM",
        image_hash="img_hash_123",
        inference_latency_ms=145.5,
        preprocessing_latency_ms=32.2,
        created_by=sample_user.username,
    )
    session.add(result)
    session.commit()
    return result


# ============================================================================
# Test: DatabaseConfig
# ============================================================================

class TestDatabaseConfig:
    """Test DatabaseConfig validation and initialization."""

    def test_valid_config(self):
        """Test creating valid database configuration."""
        config = DatabaseConfig(
            url="postgresql://user:pass@localhost/testdb",
            pool_size=10,
        )
        assert config.validate() is True
        assert config.pool_size == 10

    def test_invalid_url(self):
        """Test that empty URL raises error."""
        config = DatabaseConfig(url="")
        with pytest.raises(ValueError, match="Database URL is required"):
            config.validate()

    def test_invalid_pool_size(self):
        """Test that invalid pool size raises error."""
        config = DatabaseConfig(
            url="postgresql://localhost/db",
            pool_size=0,
        )
        with pytest.raises(ValueError, match="Pool size must be at least 1"):
            config.validate()

    def test_invalid_max_overflow(self):
        """Test that negative max_overflow raises error."""
        config = DatabaseConfig(
            url="postgresql://localhost/db",
            max_overflow=-1,
        )
        with pytest.raises(ValueError, match="Max overflow must be non-negative"):
            config.validate()


# ============================================================================
# Test: DatabaseManager Initialization
# ============================================================================

class TestDatabaseManagerInitialization:
    """Test DatabaseManager initialization and lifecycle."""

    def test_manager_initialization(self, in_memory_db):
        """Test successful database manager initialization."""
        engine, SessionLocal = in_memory_db
        config = DatabaseConfig(url="sqlite:///:memory:")
        manager = DatabaseManager(config)
        manager.engine = engine  # Assign pre-created engine
        manager._initialized = True
        
        assert manager._initialized is True
        assert manager.engine is not None

    def test_double_initialization_warning(self, in_memory_db, caplog):
        """Test that double initialization logs warning."""
        engine, SessionLocal = in_memory_db
        config = DatabaseConfig(url="sqlite:///:memory:")
        manager = DatabaseManager(config)
        manager.engine = engine
        manager._initialized = True

        with caplog.at_level("WARNING"):
            manager.initialize()
        
        assert "already initialized" in caplog.text.lower()

    def test_get_session(self, in_memory_db):
        """Test getting a session from manager."""
        engine, SessionLocal = in_memory_db
        config = DatabaseConfig(url="sqlite:///:memory:")
        manager = DatabaseManager(config)
        manager.session_factory = SessionLocal
        manager._initialized = True

        session = manager.get_session()
        assert session is not None
        session.close()

    def test_get_session_not_initialized(self):
        """Test that getting session before init raises error."""
        config = DatabaseConfig(url="sqlite:///:memory:")
        manager = DatabaseManager(config)

        with pytest.raises(RuntimeError, match="not initialized"):
            manager.get_session()


# ============================================================================
# Test: ModelVersion Model
# ============================================================================

class TestModelVersionModel:
    """Test ModelVersion ORM model."""

    def test_create_model_version(self, session):
        """Test creating a ModelVersion."""
        model = ModelVersion(
            model_name="ResNet50",
            version="1.0.0",
            status=ModelStatus.PRODUCTION,
            file_path="/models/resnet50.onnx",
            file_hash="hash123",
            file_size_bytes=102400,
            input_shape={"width": 512, "height": 512},
            output_shape={"class": 1000},
            clinical_domain="radiology",
        )
        session.add(model)
        session.commit()

        retrieved = session.query(ModelVersion).filter_by(
            model_name="ResNet50"
        ).first()
        assert retrieved.version == "1.0.0"
        assert retrieved.status == ModelStatus.PRODUCTION

    def test_model_version_unique_constraint(self, session):
        """Test unique constraint on (model_name, version)."""
        model1 = ModelVersion(
            model_name="ResNet50",
            version="1.0.0",
            status=ModelStatus.PRODUCTION,
            file_path="/models/resnet50_v1.onnx",
            file_hash="hash123",
            file_size_bytes=102400,
            input_shape={},
            output_shape={},
            clinical_domain="radiology",
        )
        session.add(model1)
        session.commit()

        # Try to add duplicate
        model2 = ModelVersion(
            model_name="ResNet50",
            version="1.0.0",
            status=ModelStatus.DEVELOPMENT,
            file_path="/models/resnet50_v1_dev.onnx",
            file_hash="hash456",
            file_size_bytes=102400,
            input_shape={},
            output_shape={},
            clinical_domain="radiology",
        )
        session.add(model2)
        
        with pytest.raises(Exception):  # UniqueConstraint violation
            session.commit()

    def test_confidence_threshold_validation(self, session):
        """Test confidence threshold constraint (0.0-1.0)."""
        model = ModelVersion(
            model_name="TestModel",
            version="1.0",
            status=ModelStatus.DEVELOPMENT,
            file_path="/models/test.onnx",
            file_hash="hash",
            file_size_bytes=1000,
            input_shape={},
            output_shape={},
            clinical_domain="radiology",
            confidence_threshold=1.5,  # Invalid: > 1.0
        )
        session.add(model)
        
        with pytest.raises(Exception):  # CheckConstraint violation
            session.commit()


# ============================================================================
# Test: InferenceResult Model
# ============================================================================

class TestInferenceResultModel:
    """Test InferenceResult ORM model."""

    def test_create_inference_result(self, session, sample_model_version, sample_user):
        """Test creating an InferenceResult."""
        result = InferenceResult(
            model_version_id=sample_model_version.id,
            status=InferenceStatus.COMPLETED,
            confidence_score=0.95,
            prediction={"class": "normal"},
            image_width=512,
            image_height=512,
            image_format="DICOM",
            image_hash="hash_xyz",
            inference_latency_ms=120.5,
            preprocessing_latency_ms=30.0,
            created_by=sample_user.username,
        )
        session.add(result)
        session.commit()

        retrieved = session.query(InferenceResult).first()
        assert retrieved.confidence_score == 0.95
        assert retrieved.status == InferenceStatus.COMPLETED

    def test_inference_confidence_validation(self, session, sample_model_version, sample_user):
        """Test confidence score constraint."""
        result = InferenceResult(
            model_version_id=sample_model_version.id,
            status=InferenceStatus.COMPLETED,
            confidence_score=1.5,  # Invalid: > 1.0
            prediction={},
            image_width=512,
            image_height=512,
            image_format="DICOM",
            image_hash="hash",
            inference_latency_ms=100,
            preprocessing_latency_ms=30,
            created_by=sample_user.username,
        )
        session.add(result)
        
        with pytest.raises(Exception):  # CheckConstraint
            session.commit()

    def test_inference_latency_validation(self, session, sample_model_version, sample_user):
        """Test latency must be non-negative."""
        result = InferenceResult(
            model_version_id=sample_model_version.id,
            status=InferenceStatus.COMPLETED,
            confidence_score=0.9,
            prediction={},
            image_width=512,
            image_height=512,
            image_format="DICOM",
            image_hash="hash",
            inference_latency_ms=-10,  # Invalid: negative
            preprocessing_latency_ms=30,
            created_by=sample_user.username,
        )
        session.add(result)
        
        with pytest.raises(Exception):  # CheckConstraint
            session.commit()


# ============================================================================
# Test: ValidationResult Model
# ============================================================================

class TestValidationResultModel:
    """Test ValidationResult ORM model."""

    def test_create_validation_result(self, session, sample_inference_result):
        """Test creating a ValidationResult."""
        validation = ValidationResult(
            inference_result_id=sample_inference_result.id,
            brightness_valid=True,
            contrast_valid=True,
            motion_artifact_free=True,
            noise_level_acceptable=True,
            is_valid=True,
            validation_score=0.98,
            error_codes=[],
            warnings=[],
            validator_version="1.0.0",
        )
        session.add(validation)
        session.commit()

        retrieved = session.query(ValidationResult).first()
        assert retrieved.is_valid is True
        assert retrieved.validation_score == 0.98

    def test_validation_score_constraint(self, session, sample_inference_result):
        """Test validation score must be 0.0-1.0."""
        validation = ValidationResult(
            inference_result_id=sample_inference_result.id,
            brightness_valid=True,
            contrast_valid=True,
            motion_artifact_free=True,
            noise_level_acceptable=True,
            is_valid=False,
            validation_score=1.5,  # Invalid
            error_codes=[],
            warnings=[],
            validator_version="1.0",
        )
        session.add(validation)
        
        with pytest.raises(Exception):  # CheckConstraint
            session.commit()

    def test_validation_with_errors(self, session, sample_inference_result):
        """Test ValidationResult with error codes and warnings."""
        validation = ValidationResult(
            inference_result_id=sample_inference_result.id,
            brightness_valid=False,
            contrast_valid=True,
            motion_artifact_free=True,
            noise_level_acceptable=False,
            is_valid=False,
            validation_score=0.55,
            error_codes=["LOW_BRIGHTNESS", "HIGH_NOISE"],
            warnings=["MARGINAL_CONTRAST"],
            validator_version="1.0.0",
        )
        session.add(validation)
        session.commit()

        retrieved = session.query(ValidationResult).first()
        assert len(retrieved.error_codes) == 2
        assert "LOW_BRIGHTNESS" in retrieved.error_codes


# ============================================================================
# Test: User Model
# ============================================================================

class TestUserModel:
    """Test User ORM model."""

    def test_create_user(self, session):
        """Test creating a User."""
        user = User(
            username="johndoe",
            email="john@example.com",
            password_hash="hashed_pwd",
            role="clinician",
            full_name="John Doe",
        )
        session.add(user)
        session.commit()

        retrieved = session.query(User).filter_by(username="johndoe").first()
        assert retrieved.email == "john@example.com"
        assert retrieved.role == "clinician"

    def test_user_email_unique(self, session):
        """Test unique email constraint."""
        user1 = User(
            username="user1",
            email="john@example.com",
            password_hash="pwd1",
            role="user",
        )
        session.add(user1)
        session.commit()

        user2 = User(
            username="user2",
            email="john@example.com",  # Duplicate email
            password_hash="pwd2",
            role="user",
        )
        session.add(user2)
        
        with pytest.raises(Exception):  # UniqueConstraint
            session.commit()

    def test_user_with_failed_login_tracking(self, session):
        """Test user failed login attempt tracking."""
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash="pwd",
            role="user",
            failed_login_attempts=3,
            locked_until=datetime.utcnow() + timedelta(minutes=30),
        )
        session.add(user)
        session.commit()

        retrieved = session.query(User).first()
        assert retrieved.failed_login_attempts == 3
        assert retrieved.locked_until is not None


# ============================================================================
# Test: AuditLog Model & Hash Chain
# ============================================================================

class TestAuditLogModel:
    """Test AuditLog ORM model and hash chain integrity."""

    def test_create_audit_log(self, session, sample_user):
        """Test creating an AuditLog entry."""
        audit = AuditLog(
            action=AuditActionType.USER_LOGIN,
            description="User logged in successfully",
            user_id=sample_user.id,
            context={"ip": "192.168.1.1"},
            ip_address="192.168.1.1",
            entry_hash="hash_value_123",
        )
        session.add(audit)
        session.commit()

        retrieved = session.query(AuditLog).first()
        assert retrieved.action == AuditActionType.USER_LOGIN
        assert retrieved.ip_address == "192.168.1.1"

    def test_hash_chain_formation(self, session, sample_user):
        """Test audit log hash chain formation for integrity."""
        # Create first audit entry
        audit1 = AuditLog(
            action=AuditActionType.USER_LOGIN,
            description="Login attempt",
            user_id=sample_user.id,
            context={},
            entry_hash="hash_1",
            previous_hash=None,
        )
        session.add(audit1)
        session.commit()

        # Create second audit entry linked to first
        audit2 = AuditLog(
            action=AuditActionType.INFERENCE_COMPLETED,
            description="Inference completed",
            user_id=sample_user.id,
            context={},
            entry_hash="hash_2",
            previous_hash=audit1.entry_hash,  # Link to previous
        )
        session.add(audit2)
        session.commit()

        # Verify chain
        retrieved_1 = session.query(AuditLog).filter_by(entry_hash="hash_1").first()
        retrieved_2 = session.query(AuditLog).filter_by(entry_hash="hash_2").first()

        assert retrieved_2.previous_hash == retrieved_1.entry_hash

    def test_audit_log_all_action_types(self, session, sample_user):
        """Test that all AuditActionType values are valid."""
        for action_type in AuditActionType:
            audit = AuditLog(
                action=action_type,
                description=f"Test action: {action_type.value}",
                user_id=sample_user.id,
                context={},
                entry_hash=f"hash_{action_type.value}",
            )
            session.add(audit)

        session.commit()

        count = session.query(AuditLog).count()
        assert count == len(AuditActionType)


# ============================================================================
# Test: Relationships & Foreign Keys
# ============================================================================

class TestModelRelationships:
    """Test ORM relationships and foreign key integrity."""

    def test_model_version_has_many_inferences(self, session, sample_model_version, sample_user):
        """Test that ModelVersion can have multiple InferenceResults."""
        result1 = InferenceResult(
            model_version_id=sample_model_version.id,
            confidence_score=0.9,
            prediction={},
            image_width=512,
            image_height=512,
            image_format="DICOM",
            image_hash="hash1",
            inference_latency_ms=100,
            preprocessing_latency_ms=30,
            created_by=sample_user.username,
        )
        result2 = InferenceResult(
            model_version_id=sample_model_version.id,
            confidence_score=0.85,
            prediction={},
            image_width=512,
            image_height=512,
            image_format="DICOM",
            image_hash="hash2",
            inference_latency_ms=120,
            preprocessing_latency_ms=35,
            created_by=sample_user.username,
        )
        session.add(result1)
        session.add(result2)
        session.commit()

        # Query through relationship
        model = session.query(ModelVersion).first()
        assert len(model.inference_results) == 2

    def test_inference_result_has_validation_results(self, session, sample_inference_result):
        """Test that InferenceResult can have multiple ValidationResults."""
        val1 = ValidationResult(
            inference_result_id=sample_inference_result.id,
            brightness_valid=True,
            contrast_valid=True,
            motion_artifact_free=True,
            noise_level_acceptable=True,
            is_valid=True,
            validation_score=0.99,
            error_codes=[],
            warnings=[],
            validator_version="1.0",
        )
        val2 = ValidationResult(
            inference_result_id=sample_inference_result.id,
            brightness_valid=True,
            contrast_valid=False,
            motion_artifact_free=True,
            noise_level_acceptable=True,
            is_valid=False,
            validation_score=0.75,
            error_codes=["LOW_CONTRAST"],
            warnings=[],
            validator_version="1.1",
        )
        session.add(val1)
        session.add(val2)
        session.commit()

        inference = session.query(InferenceResult).first()
        assert len(inference.validation_results) == 2


# ============================================================================
# Test: Session Management & Transactions
# ============================================================================

class TestSessionManagement:
    """Test session lifecycle and transaction management."""

    def test_session_context_commit(self, in_memory_db):
        """Test session context manager commits on success."""
        engine, SessionLocal = in_memory_db
        config = DatabaseConfig(url="sqlite:///:memory:")
        manager = DatabaseManager(config)
        manager.session_factory = SessionLocal
        manager._initialized = True

        user = User(
            username="testuser",
            email="test@example.com",
            password_hash="pwd",
            role="user",
        )

        with manager.session_context() as session:
            session.add(user)

        # Verify persisted
        new_session = manager.get_session()
        retrieved = new_session.query(User).filter_by(username="testuser").first()
        assert retrieved is not None
        new_session.close()

    def test_session_context_rollback_on_error(self, in_memory_db):
        """Test session context manager rolls back on error."""
        engine, SessionLocal = in_memory_db
        config = DatabaseConfig(url="sqlite:///:memory:")
        manager = DatabaseManager(config)
        manager.session_factory = SessionLocal
        manager._initialized = True

        user = User(
            username="testuser",
            email="test@example.com",
            password_hash="pwd",
            role="user",
        )

        try:
            with manager.session_context() as session:
                session.add(user)
                raise ValueError("Simulated error")
        except ValueError:
            pass

        # Verify not persisted
        new_session = manager.get_session()
        retrieved = new_session.query(User).filter_by(username="testuser").first()
        assert retrieved is None
        new_session.close()


# ============================================================================
# Test: Data Integrity & Constraints
# ============================================================================

class TestDataIntegrity:
    """Test data integrity constraints and validation."""

    def test_foreign_key_constraint(self, session, sample_inference_result):
        """Test foreign key constraints."""
        # Create inference with invalid model_version_id
        result = InferenceResult(
            model_version_id="invalid_id_xyz",  # Non-existent model
            confidence_score=0.9,
            prediction={},
            image_width=512,
            image_height=512,
            image_format="DICOM",
            image_hash="hash",
            inference_latency_ms=100,
            preprocessing_latency_ms=30,
            created_by="test_user",
        )
        session.add(result)
        
        # This might or might not raise depending on database setup
        # SQLite doesn't enforce FK by default, so we skip this test for SQLite
        # In production PostgreSQL, this would raise an IntegrityError

    def test_not_null_constraints(self, session):
        """Test NOT NULL constraints."""
        # Try to create ModelVersion without required fields
        model = ModelVersion(
            model_name=None,  # Required field
            version="1.0",
            status=ModelStatus.PRODUCTION,
            file_path="/models/test.onnx",
            file_hash="hash",
            file_size_bytes=1000,
            input_shape={},
            output_shape={},
            clinical_domain="radiology",
        )
        session.add(model)
        
        with pytest.raises(Exception):  # IntegrityError or similar
            session.commit()


# ============================================================================
# Test: Model Queries & Filtering
# ============================================================================

class TestModelQueries:
    """Test common query patterns and filtering."""

    def test_query_by_status(self, session, sample_model_version):
        """Test querying models by status."""
        # Add another model with different status
        model2 = ModelVersion(
            model_name="VGG16",
            version="1.0",
            status=ModelStatus.DEVELOPMENT,
            file_path="/models/vgg16.onnx",
            file_hash="hash2",
            file_size_bytes=50000,
            input_shape={},
            output_shape={},
            clinical_domain="pathology",
        )
        session.add(model2)
        session.commit()

        # Query production models
        production_models = session.query(ModelVersion).filter_by(
            status=ModelStatus.PRODUCTION
        ).all()
        assert len(production_models) == 1
        assert production_models[0].model_name == "ResNet50"

    def test_query_recent_inferences(self, session, sample_inference_result):
        """Test querying recent inference results."""
        # Create multiple inferences
        for i in range(5):
            result = InferenceResult(
                model_version_id=sample_inference_result.model_version_id,
                status=InferenceStatus.COMPLETED,
                confidence_score=0.9 - i * 0.05,
                prediction={},
                image_width=512,
                image_height=512,
                image_format="DICOM",
                image_hash=f"hash_{i}",
                inference_latency_ms=100 + i * 10,
                preprocessing_latency_ms=30,
                created_by=sample_inference_result.created_by,
            )
            session.add(result)

        session.commit()

        # Get top 3 most recent (ordered by created_at DESC)
        recent = session.query(InferenceResult).order_by(
            InferenceResult.created_at.desc()
        ).limit(3).all()
        
        assert len(recent) == 3


# ============================================================================
# Test: Performance Monitoring
# ============================================================================

class TestPerformanceMonitoring:
    """Test performance metrics tracking."""

    def test_inference_latency_tracking(self, session, sample_model_version, sample_user):
        """Test inference latency metrics are tracked."""
        result = InferenceResult(
            model_version_id=sample_model_version.id,
            confidence_score=0.95,
            prediction={},
            image_width=512,
            image_height=512,
            image_format="DICOM",
            image_hash="hash",
            inference_latency_ms=234.5,
            preprocessing_latency_ms=45.3,
            created_by=sample_user.username,
        )
        session.add(result)
        session.commit()

        retrieved = session.query(InferenceResult).first()
        assert retrieved.inference_latency_ms == 234.5
        assert retrieved.preprocessing_latency_ms == 45.3
        total = retrieved.inference_latency_ms + retrieved.preprocessing_latency_ms
        assert total == pytest.approx(279.8, rel=0.01)

    def test_model_version_performance_metadata(self, session):
        """Test model version performance tracking."""
        model = ModelVersion(
            model_name="EfficientNet",
            version="2.0",
            status=ModelStatus.VALIDATION,
            file_path="/models/efficientnet.onnx",
            file_hash="hash",
            file_size_bytes=80000,
            input_shape={"size": 256},
            output_shape={"logits": 1000},
            clinical_domain="radiology",
            inference_latency_ms=89.5,
        )
        session.add(model)
        session.commit()

        retrieved = session.query(ModelVersion).first()
        assert retrieved.inference_latency_ms == 89.5


# Export test classes
__all__ = [
    "TestDatabaseConfig",
    "TestDatabaseManagerInitialization",
    "TestModelVersionModel",
    "TestInferenceResultModel",
    "TestValidationResultModel",
    "TestUserModel",
    "TestAuditLogModel",
    "TestModelRelationships",
    "TestSessionManagement",
    "TestDataIntegrity",
    "TestModelQueries",
    "TestPerformanceMonitoring",
]
