import io

import numpy as np
from PIL import Image

from app.processors.ocr.base import OCRProvider


class RapidOCRProvider(OCRProvider):
    def __init__(self):
        from rapidocr_onnxruntime import RapidOCR

        self.ocr = RapidOCR()

    def extract_text_from_image(self, image_bytes: bytes) -> str:
        image = Image.open(io.BytesIO(image_bytes))
        image_array = np.array(image)
        result, _ = self.ocr(image_array)
        if not result:
            return ""
        return "\n".join([line[1] for line in result if len(line) > 1])
