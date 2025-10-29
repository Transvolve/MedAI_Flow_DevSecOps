import onnxruntime as ort
import numpy as np
from .preprocess import preprocess

def predict(image_array: np.ndarray, model_path="model.onnx"):
    session = ort.InferenceSession(model_path)
    inputs = preprocess(image_array)
    outputs = session.run(None, {"input": inputs})
    return outputs
