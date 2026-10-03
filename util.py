"""
Utility functions for image encoding, decoding, and conversion.
"""

import re
import base64
from io import BytesIO
from typing import Optional
from PIL import Image
import numpy as np


def base64_to_pil(img_base64: str) -> Image.Image:
    """
    Safely converts a base64 Data URL or raw base64 string to a PIL Image in RGB format.
    Handles transparent PNGs, JPEGs, WebP, etc., uniformly converting them to RGB.
    
    Raises:
        ValueError: If the string is empty or invalid image data.
    """
    if not img_base64 or not isinstance(img_base64, str):
        raise ValueError("Invalid image input: Expected non-empty base64 string.")

    # Strip Data URL scheme if present (e.g., 'data:image/png;base64,...')
    clean_base64 = re.sub(r"^data:image/[a-zA-Z0-9\+\.\-]+;base64,", "", img_base64.strip())

    try:
        raw_bytes = base64.b64decode(clean_base64)
        if len(raw_bytes) == 0:
            raise ValueError("Decoded image buffer is empty.")
        
        with Image.open(BytesIO(raw_bytes)) as img:
            # Convert to RGB mode (flattens alpha channels onto white background)
            if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
                rgb_img = Image.new("RGB", img.size, (255, 255, 255))
                if img.mode != "RGBA":
                    img = img.convert("RGBA")
                rgb_img.paste(img, mask=img.split()[3])
                return rgb_img
            else:
                return img.convert("RGB")
    except Exception as e:
        raise ValueError(f"Failed to decode base64 image: {str(e)}")


def pil_to_jpeg_bytes(pil_image: Image.Image, quality: int = 95) -> bytes:
    """Encodes a PIL Image into in-memory JPEG bytes."""
    buf = BytesIO()
    if pil_image.mode != "RGB":
        pil_image = pil_image.convert("RGB")
    pil_image.save(buf, format="JPEG", quality=quality)
    return buf.getvalue()


def np_to_base64(img_np: np.ndarray) -> str:
    """Converts a numpy RGB array to a base64 PNG data URL."""
    img = Image.fromarray(img_np.astype("uint8"), "RGB")
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buffered.getvalue()).decode("ascii")
