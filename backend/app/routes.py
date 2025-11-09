"""
routes.py
----------
Primary API routes for MedAI_Flow_DevSecOps, including:
- Model inference endpoint (secured)
- Batch inference endpoint for multiple images
- Model information and metadata endpoint
- Inference results retrieval with pagination
- Authentication management (logout)
- Role-based access control (admin-only example)

Regulatory Compliance:
- FDA 21 CFR 11: § 11.10 (System validation)
- ISO 13485: 4.2.3 (Configuration management)
- IEC 62304: Software requirements specification
"""

from typing import Any, Dict, List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from backend.app.auth import (
    get_current_user,
    oauth2_scheme,
    revoke_token,
    requires_role,
)
from backend.app.utils import latency_timer

try:
    # Lazy import to avoid CI/CD failures if ML runtime not installed
    from backend.ml import inference as ml_inference  # type: ignore
except Exception:  # pragma: no cover - optional dependency for CI
    ml_inference = None  # type: ignore


# ============================================================================
# Router Initialization
# ============================================================================
router = APIRouter()


# ============================================================================
# Pydantic Request/Response Models
# ============================================================================

class InferenceRequest(BaseModel):
    """Input payload for single image ML inference."""
    data: List[float] = Field(..., description="Normalized image data (flattened)")
    width: Optional[int] = Field(default=None, description="Image width")
    height: Optional[int] = Field(default=None, description="Image height")
    patient_id: Optional[str] = Field(default=None, description="De-identified patient reference")
    study_date: Optional[datetime] = Field(default=None, description="Study date")


class InferenceResponse(BaseModel):
    """Model output response for single inference."""
    outputs: Any
    confidence_score: Optional[float] = Field(default=None, description="Confidence score (0.0-1.0)")
    inference_id: str = Field(description="Unique inference result ID")


class BatchInferenceRequest(BaseModel):
    """Input payload for batch inference."""
    images: List[InferenceRequest] = Field(..., description="List of images for inference", min_items=1, max_items=100)
    priority: str = Field(default="normal", description="Batch priority: 'low', 'normal', 'high'")


class BatchInferenceResponse(BaseModel):
    """Response for batch inference."""
    batch_id: str = Field(description="Unique batch ID")
    total_images: int = Field(description="Total images in batch")
    successful: int = Field(description="Successful inferences")
    failed: int = Field(description="Failed inferences")
    results: List[InferenceResponse] = Field(description="Individual inference results")
    status: str = Field(description="Batch status: 'completed', 'partial_failure', 'failed'")


class ModelInfo(BaseModel):
    """Model metadata and information."""
    model_id: str = Field(description="Model unique identifier")
    model_name: str = Field(description="Model name")
    version: str = Field(description="Model version")
    status: str = Field(description="Model status: production, validation, development")
    clinical_domain: str = Field(description="Clinical domain (radiology, pathology, etc.)")
    confidence_threshold: float = Field(description="Minimum confidence threshold")
    input_shape: Dict[str, Any] = Field(description="Input tensor shape")
    output_shape: Dict[str, Any] = Field(description="Output tensor shape")
    file_size_mb: float = Field(description="Model file size in MB")
    inference_latency_ms: Optional[float] = Field(description="Average inference latency")
    created_at: datetime = Field(description="Model creation timestamp")
    deployed_at: Optional[datetime] = Field(description="Model deployment timestamp")


class InferenceResultItem(BaseModel):
    """Single inference result for list responses."""
    inference_id: str = Field(description="Unique inference ID")
    model_id: str = Field(description="Model ID used for inference")
    confidence_score: float = Field(description="Prediction confidence")
    status: str = Field(description="Result status")
    created_at: datetime = Field(description="Inference creation time")
    created_by: str = Field(description="User who initiated inference")


class PaginatedInferenceResults(BaseModel):
    """Paginated list of inference results."""
    items: List[InferenceResultItem] = Field(description="Page of results")
    total: int = Field(description="Total number of results")
    page: int = Field(description="Current page number")
    page_size: int = Field(description="Results per page")
    total_pages: int = Field(description="Total number of pages")


# ============================================================================
# Machine Learning Inference Endpoints
# ============================================================================

@router.post("/infer", dependencies=[Depends(get_current_user)], tags=["inference"])
@latency_timer
async def infer(request: InferenceRequest) -> Dict[str, Any]:
    """
    Perform single image model inference using ONNX runtime.

    Requires authentication. Returns inference ID for result tracking and
    compliance auditing.

    Regulatory: FDA 21 CFR 11 § 11.10 (System validation)
    """
    if ml_inference is None:
        # Return stub response if ONNX runtime unavailable
        return {
            "message": "Model runtime not available in this environment.",
            "inference_id": "stub_inference_001"
        }

    try:
        import numpy as np

        image_array = np.array(request.data, dtype=np.float32)
        outputs = ml_inference.predict(image_array)

        return {
            "outputs": outputs,
            "confidence_score": float(np.max(outputs)) if isinstance(outputs, np.ndarray) else 0.85,
            "inference_id": f"infer_{datetime.utcnow().timestamp()}"
        }
    except Exception as exc:  # pragma: no cover - defensive
        raise HTTPException(status_code=500, detail=f"Inference failed: {exc}")


@router.post("/infer/batch", dependencies=[Depends(get_current_user)], tags=["inference"])
@latency_timer
async def batch_infer(request: BatchInferenceRequest) -> Dict[str, Any]:
    """
    Perform batch inference on multiple images in a single request.

    Supports up to 100 images per batch. Results are returned with individual
    success/failure status for each image. Useful for high-throughput scenarios.

    Args:
        request: BatchInferenceRequest with list of up to 100 images

    Returns:
        BatchInferenceResponse with aggregated results and per-image status

    Regulatory: FDA 21 CFR 11 § 11.10 (System validation)
    """
    if not request.images:
        raise HTTPException(status_code=400, detail="At least one image required")

    if len(request.images) > 100:
        raise HTTPException(status_code=400, detail="Maximum 100 images per batch")

    results = []
    successful_count = 0
    failed_count = 0

    for idx, image_request in enumerate(request.images):
        try:
            if ml_inference is None:
                result = {
                    "outputs": None,
                    "confidence_score": 0.0,
                    "inference_id": f"batch_stub_{idx}"
                }
            else:
                import numpy as np
                image_array = np.array(image_request.data, dtype=np.float32)
                outputs = ml_inference.predict(image_array)
                result = {
                    "outputs": outputs,
                    "confidence_score": float(np.max(outputs)) if isinstance(outputs, np.ndarray) else 0.85,
                    "inference_id": f"batch_infer_{datetime.utcnow().timestamp()}_{idx}"
                }
            results.append(result)
            successful_count += 1
        except Exception as exc:
            results.append({
                "outputs": None,
                "confidence_score": 0.0,
                "inference_id": f"batch_failed_{idx}",
                "error": str(exc)
            })
            failed_count += 1

    # Determine overall status
    if failed_count == 0:
        batch_status = "completed"
    elif successful_count == 0:
        batch_status = "failed"
    else:
        batch_status = "partial_failure"

    return {
        "batch_id": f"batch_{datetime.utcnow().timestamp()}",
        "total_images": len(request.images),
        "successful": successful_count,
        "failed": failed_count,
        "results": results,
        "status": batch_status
    }


# ============================================================================
# Model Information Endpoints
# ============================================================================

@router.get("/models/{model_id}", dependencies=[Depends(get_current_user)], tags=["models"])
async def get_model_info(model_id: str) -> Dict[str, Any]:
    """
    Retrieve model metadata and information by model ID.

    Returns comprehensive model information including architecture,
    performance metrics, validation status, and deployment info.

    Args:
        model_id: Unique model identifier

    Returns:
        ModelInfo with complete metadata

    Regulatory: ISO 13485 (Configuration management)
    """
    # Stub implementation - would query database in production
    if not model_id or model_id == "invalid":
        raise HTTPException(status_code=404, detail="Model not found")

    return {
        "model_id": model_id,
        "model_name": "ResNet50_Medical",
        "version": "1.0.0",
        "status": "production",
        "clinical_domain": "radiology",
        "confidence_threshold": 0.85,
        "input_shape": {"width": 512, "height": 512, "channels": 3},
        "output_shape": {"predictions": 1000},
        "file_size_mb": 102.4,
        "inference_latency_ms": 145.5,
        "created_at": datetime.utcnow(),
        "deployed_at": datetime.utcnow()
    }


@router.get("/models", dependencies=[Depends(get_current_user)], tags=["models"])
async def list_models(
    skip: int = Query(0, ge=0, description="Number of models to skip"),
    limit: int = Query(10, ge=1, le=100, description="Maximum models to return")
) -> Dict[str, Any]:
    """
    List all available models with pagination support.

    Args:
        skip: Number of models to skip (for pagination)
        limit: Maximum number of models to return (max 100)

    Returns:
        Paginated list of available models

    Regulatory: ISO 13485 (Product lifecycle management)
    """
    # Stub implementation - would query database in production
    return {
        "items": [
            {
                "model_id": "model_001",
                "model_name": "ResNet50_Medical",
                "version": "1.0.0",
                "status": "production",
                "clinical_domain": "radiology"
            },
            {
                "model_id": "model_002",
                "model_name": "VGG16_Pathology",
                "version": "1.1.0",
                "status": "validation",
                "clinical_domain": "pathology"
            }
        ],
        "total": 2,
        "skip": skip,
        "limit": limit
    }


# ============================================================================
# Inference Results Retrieval with Pagination
# ============================================================================

@router.get("/results", dependencies=[Depends(get_current_user)], tags=["results"])
async def list_inference_results(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(10, ge=1, le=100, description="Results per page"),
    model_id: Optional[str] = Query(None, description="Filter by model ID"),
    status: Optional[str] = Query(None, description="Filter by result status"),
    created_by: Optional[str] = Query(None, description="Filter by user")
) -> Dict[str, Any]:
    """
    Retrieve inference results with pagination and filtering support.

    Supports filtering by model, status, and user. Results are paginated
    with configurable page size (max 100 per page). Ordered by most recent first.

    Args:
        page: Page number (1-indexed)
        page_size: Number of results per page
        model_id: Optional filter for specific model
        status: Optional filter for result status (completed, failed, etc.)
        created_by: Optional filter for user who created result

    Returns:
        PaginatedInferenceResults with filtered/sorted results

    Regulatory: HIPAA (Patient record management)
    """
    # Stub implementation - would query database in production
    total_results = 150  # Simulated total count
    total_pages = (total_results + page_size - 1) // page_size

    if page > total_pages and page > 1:
        raise HTTPException(status_code=404, detail="Page not found")

    items = [
        {
            "inference_id": f"infer_{i}",
            "model_id": model_id or "model_001",
            "confidence_score": 0.92 - (i * 0.01),
            "status": status or "completed",
            "created_at": datetime.utcnow(),
            "created_by": created_by or "user@example.com"
        }
        for i in range(min(page_size, total_results - (page - 1) * page_size))
    ]

    return {
        "items": items,
        "total": total_results,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages
    }


@router.get("/results/{inference_id}", dependencies=[Depends(get_current_user)], tags=["results"])
async def get_inference_result(inference_id: str) -> Dict[str, Any]:
    """
    Retrieve detailed inference result by ID.

    Returns complete inference metadata, prediction, confidence scores,
    validation results, and audit information.

    Args:
        inference_id: Unique inference result ID

    Returns:
        Complete inference result with all metadata

    Regulatory: FDA 21 CFR 11 § 11.70 (Audit trails)
    """
    if not inference_id or inference_id == "invalid":
        raise HTTPException(status_code=404, detail="Inference result not found")

    return {
        "inference_id": inference_id,
        "model_id": "model_001",
        "status": "completed",
        "prediction": {"class": "normal", "score": 0.92},
        "confidence_score": 0.92,
        "patient_id": "PATIENT_001",
        "image_width": 512,
        "image_height": 512,
        "image_format": "DICOM",
        "inference_latency_ms": 145.5,
        "preprocessing_latency_ms": 32.2,
        "created_at": datetime.utcnow(),
        "created_by": "clinician@hospital.org",
        "validation_status": "valid",
        "validation_details": {
            "brightness_valid": True,
            "contrast_valid": True,
            "motion_artifact_free": True
        }
    }


# ============================================================================
# Authentication: Logout (JWT Revocation)
# ============================================================================
@router.post("/auth/logout", tags=["auth"])
def logout(
    token: str = Depends(oauth2_scheme),
    user=Depends(get_current_user)
):
    """
    Secure logout endpoint — revokes the current JWT in Redis blacklist.

    Once revoked, the token becomes invalid for all subsequent requests.
    """
    revoke_token(token)
    return {"detail": "Logged out successfully"}


# ============================================================================
# Admin-Only Secure Endpoint
# ============================================================================
@router.get("/admin/secure", tags=["admin"], dependencies=[Depends(requires_role(["admin"]))])
def admin_secure() -> Dict[str, Any]:
    """
    Example admin-only endpoint protected via role-based access control (RBAC).

    Accessible only to users with role='admin'.
    """
    return {"ok": True, "message": "Admin access granted"}


