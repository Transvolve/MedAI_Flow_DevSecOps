import numpy as np

def preprocess(image_array: np.ndarray):
    # Normalize and reshape
    return image_array.astype(np.float32) / 255.0
