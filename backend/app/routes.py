from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from .security import verify_token
from .utils import latency_timer
try:
    # Lazy import to avoid CI failures if onnxruntime is not installed
    from ..ml import inference as ml_inference  # type: ignore
except Exception:  # pragma: no cover - optional dependency in CI
    ml_inference = None  # type: ignore


router = APIRouter()


class InferenceRequest(BaseModel):
    # Base64 or flat list of floats for demo purposes
    data: List[float] = Field(..., description="Normalized image data flattened")
    width: Optional[int] = Field(default=None)
    height: Optional[int] = Field(default=None)


class InferenceResponse(BaseModel):
    outputs: Any


@router.post("/infer", dependencies=[Depends(verify_token)])
@latency_timer
async def infer(request: InferenceRequest) -> Dict[str, Any]:
    if ml_inference is None:
        # Return stub response to keep API live when model runtime is unavailable
        return {"message": "Model runtime not available in this environment."}
    try:
        import numpy as np

        image_array = np.array(request.data, dtype=np.float32)
        outputs = ml_inference.predict(image_array)
        return {"outputs": outputs}
    except Exception as exc:  # pragma: no cover - defensive
        raise HTTPException(status_code=500, detail=f"Inference failed: {exc}")

