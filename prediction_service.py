"""
Prediction Service Module

Manages model graph inspection, preprocessing, and single-instance inference execution.
Ensures OS-agnostic path handling, avoids graph reloading on every request,
and provides transparent status reporting without fabricating results.
"""

from io import BytesIO
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Union
import numpy as np
from PIL import Image

PROJECT_ROOT = Path(__file__).parent.resolve()
MODEL_PATH = PROJECT_ROOT / "tf_files" / "retrained_graph.pb"
LABELS_PATH = PROJECT_ROOT / "tf_files" / "retrained_labels.txt"


class PredictionService:
    """
    Singleton service managing image classification inference.
    """

    INPUT_WIDTH: int = 299
    INPUT_HEIGHT: int = 299
    INPUT_CHANNELS: int = 3

    def __init__(self):
        self.model_path = MODEL_PATH
        self.labels_path = LABELS_PATH
        self.labels: List[str] = self._load_labels()
        self.is_available: bool = False
        self.runtime_name: Optional[str] = None
        self.error_detail: Optional[str] = None
        self._initialize_runtime()

    def _load_labels(self) -> List[str]:
        """Loads class labels from retrained_labels.txt."""
        if not self.labels_path.exists():
            return ["paper", "metal", "cardboard", "trash", "glass", "plastic"]
        with open(self.labels_path, "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]

    def _initialize_runtime(self) -> None:
        """
        Attempts to initialize an available inference engine.
        Loads retrained_graph.pb into a persistent TensorFlow compat.v1 Session.
        """
        if not self.model_path.exists():
            self.error_detail = f"Model file not found at {self.model_path}"
            return

        try:
            import tensorflow.compat.v1 as tf  # type: ignore
            tf.disable_v2_behavior()

            graph_def = tf.GraphDef()
            with open(self.model_path, "rb") as f:
                graph_def.ParseFromString(f.read())

            self.graph = tf.Graph()
            with self.graph.as_default():
                tf.import_graph_def(graph_def, name="")
                self.session = tf.Session(graph=self.graph)
                self.softmax_tensor = self.graph.get_tensor_by_name("final_result:0")

            self.is_available = True
            self.runtime_name = "TensorFlow 2.x (compat.v1 GraphDef)"
            self.error_detail = None
            return
        except Exception as e:
            self.is_available = False
            self.runtime_name = "None"
            self.error_detail = f"TensorFlow initialization failed: {e}"

    def preprocess_image(self, image_input: Union[Image.Image, bytes]) -> np.ndarray:
        """
        Preprocesses image for Inception v3 input tensor:
        1. Decodes to RGB mode.
        2. Resizes to 299x299 (bilinear).
        3. Normalizes float pixels to [-1.0, 1.0] via (pixel - 128.0) / 128.0.
        4. Expands to batch shape (1, 299, 299, 3).
        
        Raises:
            ValueError: If input data is corrupt or cannot be read.
        """
        try:
            if isinstance(image_input, bytes):
                img = Image.open(BytesIO(image_input))
            elif isinstance(image_input, Image.Image):
                img = image_input
            else:
                raise ValueError("Unsupported image input type.")

            if img.mode != "RGB":
                img = img.convert("RGB")

            # Inception v3 spatial resolution requirement: 299x299
            img = img.resize((self.INPUT_WIDTH, self.INPUT_HEIGHT), Image.Resampling.BILINEAR)

            arr = np.array(img, dtype=np.float32)
            # Inception v3 normalization: (x - 128) / 128 -> [-1.0, 1.0]
            norm_arr = (arr - 128.0) / 128.0
            return np.expand_dims(norm_arr, axis=0)
        except Exception as e:
            raise ValueError(f"Image preprocessing failed: {str(e)}")

    def predict(self, image_input: Union[Image.Image, bytes]) -> Dict[str, Any]:
        """
        Executes prediction on image. Returns verified result or structured runtime report.
        Never fabricates predictions.
        """
        if not self.is_available or not hasattr(self, "session"):
            return {
                "status": "unavailable",
                "error": "Inference engine currently unavailable on this host.",
                "detail": self.error_detail,
                "model_file": self.model_path.name,
                "expected_dimensions": f"{self.INPUT_WIDTH}x{self.INPUT_HEIGHT}x{self.INPUT_CHANNELS}",
                "labels": self.labels,
                "remediation": (
                    "To enable live model inference on Windows: Enable LongPathsEnabled=1 in "
                    "HKLM:\\SYSTEM\\CurrentControlSet\\Control\\FileSystem, or run within Docker/Linux."
                ),
                "http_status": 503
            }

        try:
            if isinstance(image_input, bytes):
                img = Image.open(BytesIO(image_input))
            elif isinstance(image_input, Image.Image):
                img = image_input
            else:
                return {
                    "status": "error",
                    "error": "Unsupported image input type.",
                    "http_status": 400
                }

            if img.mode != "RGB":
                img = img.convert("RGB")

            # Encode as JPEG bytes for DecodeJpeg/contents:0 tensor
            buf = BytesIO()
            img.save(buf, format="JPEG")
            jpeg_bytes = buf.getvalue()

            raw_preds = self.session.run(
                self.softmax_tensor,
                {"DecodeJpeg/contents:0": jpeg_bytes}
            )[0]

            pred_dict = {
                self.labels[i]: round(float(raw_preds[i]), 6)
                for i in range(min(len(self.labels), len(raw_preds)))
            }
            top_idx = int(np.argmax(raw_preds))
            top_label = self.labels[top_idx] if top_idx < len(self.labels) else "unknown"
            top_score = float(raw_preds[top_idx])

            return {
                "status": "success",
                "result": f"{top_label} ({top_score:.2%})",
                "top_label": top_label,
                "top_score": round(top_score, 6),
                "predictions": pred_dict,
                "http_status": 200
            }
        except Exception as e:
            return {
                "status": "error",
                "error": f"Prediction execution failed: {str(e)}",
                "http_status": 500
            }

    def get_status(self) -> Dict[str, Any]:
        """Returns diagnostic status of the prediction subsystem."""
        return {
            "model_path": str(self.model_path),
            "model_exists": self.model_path.exists(),
            "model_size_mb": round(self.model_path.stat().st_size / (1024 * 1024), 2) if self.model_path.exists() else 0,
            "labels": self.labels,
            "is_available": self.is_available,
            "runtime_name": self.runtime_name,
            "error_detail": self.error_detail
        }


# Module singleton
prediction_service = PredictionService()
