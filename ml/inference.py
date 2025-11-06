from typing import Any

import numpy as np

try:
    import onnxruntime as ort  # type: ignore
except Exception:  # pragma: no cover - optional in CI
    ort = None  # type: ignore

from .preprocess import preprocess

_session_cache = {}


def _get_session(model_path: str) -> Any:
    if ort is None:
        raise RuntimeError("onnxruntime is not available")
    if model_path not in _session_cache:
        _session_cache[model_path] = ort.InferenceSession(model_path)
    return _session_cache[model_path]


def predict(image_array: np.ndarray, model_path: str = "model.onnx") -> Any:
    session = _get_session(model_path)
    inputs = preprocess(image_array)
    outputs = session.run(None, {"input": inputs})
    return outputs
