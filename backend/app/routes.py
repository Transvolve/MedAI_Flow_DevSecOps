"""
routes.py
----------
Primary API routes for MedAI_Flow_DevSecOps, including:
- Model inference endpoint (secured)
- Authentication management (logout)
- Role-based access control (admin-only example)
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
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


# -----------------------------------------------------------------------------
# Router Initialization
# -----------------------------------------------------------------------------
router = APIRouter()


# -----------------------------------------------------------------------------
# Pydantic Models
# -----------------------------------------------------------------------------
class InferenceRequest(BaseModel):
    """Input payload for ML inference."""
    data: List[float] = Field(..., description="Normalized image data (flattened)")
    width: Optional[int] = Field(default=None, description="Image width")
    height: Optional[int] = Field(default=None, description="Image height")


class InferenceResponse(BaseModel):
    """Model output response."""
    outputs: Any


# -----------------------------------------------------------------------------
# Machine Learning Inference Endpoint
# -----------------------------------------------------------------------------
@router.post("/infer", dependencies=[Depends(get_current_user)], tags=["inference"])
@latency_timer
async def infer(request: InferenceRequest) -> Dict[str, Any]:
    """
    Perform model inference using ONNX runtime or return stub if unavailable.
    Requires authentication.
    """
    if ml_inference is None:
        # Return stub response if ONNX runtime unavailable
        return {"message": "Model runtime not available in this environment."}

    try:
        import numpy as np  # type: ignore

        image_array = np.array(request.data, dtype=np.float32)
        outputs = ml_inference.predict(image_array)
        return {"outputs": outputs}
    except Exception as exc:  # pragma: no cover - defensive
        raise HTTPException(status_code=500, detail=f"Inference failed: {exc}")


# -----------------------------------------------------------------------------
# Authentication: Logout (JWT Revocation)
# -----------------------------------------------------------------------------
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


# -----------------------------------------------------------------------------
# Admin-Only Secure Endpoint
# -----------------------------------------------------------------------------
@router.get("/admin/secure", tags=["admin"], dependencies=[Depends(requires_role(["admin"]))])
def admin_secure() -> Dict[str, Any]:
    """
    Example admin-only endpoint protected via role-based access control (RBAC).

    Accessible only to users with role='admin'.
    """
    return {"ok": True, "message": "Admin access granted"}


