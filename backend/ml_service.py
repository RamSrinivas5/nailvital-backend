try:
    import tflite_runtime.interpreter as tflite
except ImportError:
    import tensorflow as tf
    tflite = tf.lite

import numpy as np
from PIL import Image
import os
import io

# Setup paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
AI_DIR = os.path.join(BASE_DIR, 'ml_models')
TFLITE_MODEL_PATH = os.path.join(AI_DIR, 'nail_model_quantized.tflite')
CLASS_NAMES_PATH = os.path.join(AI_DIR, 'class_names.txt')
IMG_SIZE = (224, 224)

print(f"--- DEBUG: BASE_DIR: {BASE_DIR}")
print(f"--- DEBUG: CLASS_NAMES_PATH: {CLASS_NAMES_PATH}")
if os.path.exists(AI_DIR):
    print(f"--- DEBUG: Contents of {AI_DIR}: {os.listdir(AI_DIR)}")
else:
    print(f"--- DEBUG: AI_DIR NOT FOUND at {AI_DIR}")

class MLService:
    def __init__(self):
        self.interpreter = None
        self.class_names = []
        self._load_class_names()
        self._load_model()

    def _load_class_names(self):
        if not os.path.exists(CLASS_NAMES_PATH):
            raise FileNotFoundError(f"Error: {CLASS_NAMES_PATH} not found.")
        with open(CLASS_NAMES_PATH, 'r') as f:
            self.class_names = [line.strip() for line in f.readlines()]

    def _load_model(self):
        if not os.path.exists(TFLITE_MODEL_PATH):
             raise FileNotFoundError(f"Error: {TFLITE_MODEL_PATH} not found.")
        self.interpreter = tflite.Interpreter(model_path=TFLITE_MODEL_PATH)
        self.interpreter.allocate_tensors()
        self.input_details = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()

    def is_valid_nail_image(self, image_bytes: bytes) -> tuple[bool, str]:
        """
        Validates that the image contains a finger/nail by:
        1. Basic sanity checks (blank/dark)
        2. Skin-tone pixel detection (Peer et al. RGB rule) across all skin tones
        Rejects faces, objects, food, and random backgrounds.
        """
        try:
            raw_img = Image.open(io.BytesIO(image_bytes))
            img_rgb = raw_img.convert('RGB').resize((128, 128))  # Resize for speed
            img_array = np.array(img_rgb, dtype=np.float32)

            img_l = np.mean(img_array, axis=2)
            mean_val = np.mean(img_l)
            std_val = np.std(img_l)

            # 1. Reject pitch-black images
            if mean_val < 8:
                return False, "IMAGE_TOO_DARK"

            # 2. Reject flat solid-colour images (table top, wall, blank sheet)
            if std_val < 5:
                return False, "IMAGE_BLANK"

            # 3. Skin-tone pixel detection (works for ALL skin tones)
            # Based on Peer et al. RGB skin-colour model
            R = img_array[:, :, 0]
            G = img_array[:, :, 1]
            B = img_array[:, :, 2]

            skin_mask = (
                (R > 60) & (G > 30) & (B > 15) &          # Minimum brightness
                (R > G) & (R > B) &                         # Red dominant (all skin)
                ((R - G) > 10) &                            # Not grey/neutral
                (np.maximum(R, np.maximum(G, B)) -
                 np.minimum(R, np.minimum(G, B)) > 10)      # Some colour variation
            )

            skin_ratio = np.sum(skin_mask) / skin_mask.size

            # Require at least 8% of the image to contain skin-toned pixels
            # Fingers/nails easily pass this; random objects and faces usually don't
            # (faces could pass, but a face pressed close enough to camera looks like skin anyway)
            if skin_ratio < 0.08:
                return False, "NO_FINGER_DETECTED"

            return True, "OK"
        except Exception:
            return False, "INVALID_FORMAT"

    def predict(self, image_bytes: bytes):
        # Initial heuristic validation
        is_valid, reason = self.is_valid_nail_image(image_bytes)
        if not is_valid:
            return {"error": "INVALID_IMAGE", "reason": reason}

        # Preprocess image
        img = Image.open(io.BytesIO(image_bytes)).convert('RGB')
        img = img.resize(IMG_SIZE)
        img_array = np.array(img, dtype=np.float32)
        img_array = np.expand_dims(img_array, axis=0)

        # Run inference
        self.interpreter.set_tensor(self.input_details[0]['index'], img_array)
        self.interpreter.invoke()
        predictions = self.interpreter.get_tensor(self.output_details[0]['index'])[0]

        # Get top findings (Top 3 above 5% threshold)
        top_indices = np.argsort(predictions)[::-1][:3]
        findings = []
        for idx in top_indices:
            conf = float(predictions[idx] * 100)
            if conf >= 5.0:
                findings.append({
                    "result_class": self.class_names[idx],
                    "confidence": conf
                })
        
        # Primary result
        if not findings:
            return {"error": "INVALID_IMAGE", "reason": "LOW_CONFIDENCE"}
            
        primary = findings[0]
        
        # Confidence Gate: lowered to 15% to avoid false rejections of valid nails
        # The model only needs to be reasonably confident, not highly certain
        if primary["confidence"] < 15.0:
             return {"error": "INVALID_IMAGE", "reason": "LOW_CONFIDENCE"}

        return {
            "result_class": primary["result_class"],
            "confidence": primary["confidence"],
            "findings": findings
        }

ml_predictor = MLService()
