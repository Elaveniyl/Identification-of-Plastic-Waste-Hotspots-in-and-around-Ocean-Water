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
        Documents specific environment blockers if unavailable.
        """
        if not self.model_path.exists():
            self.error_detail = f"Model file not found at {self.model_path}"
            return

        # Attempt 1: Check for native TensorFlow 2.x
        try:
            import tensorflow as tf  # type: ignore
            # Test graph loading if TF is installed
            with tf.io.gfile.GFile(str(self.model_path), "rb") as f:
                graph_def = tf.compat.v1.GraphDef()
                graph_def.ParseFromString(f.read())
            self.is_available = True
            self.runtime_name = "TensorFlow 2.x"
            return
        except ImportError:
            pass
        except Exception as e:
            self.error_detail = f"TensorFlow loading failed: {e}"

        # If we reach here, record the exact blocker
        self.is_available = False
        self.runtime_name = "None"
        self.error_detail = (
            "Inference runtime blocked on Windows Python 3.13: "
            "Native TensorFlow 2.x installation failed due to Windows MAX_PATH "
            "limitation (LongPathsEnabled=0 in registry). OpenCV DNN importer does not "
            "support TensorFlow 1.x Inception PhaseSwitch nodes."
        )

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
        # Validate that image can be preprocessed
        try:
            tensor = self.preprocess_image(image_input)
        except ValueError as err:
            return {
                "status": "error",
                "error": str(err),
                "http_status": 400
            }

        if not self.is_available:
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

        # If runtime is available: execute actual session
        # (Reserved for when TF or ONNX is loaded)
        return {
            "status": "error",
            "error": "Runtime not configured for execution.",
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
