import io

import numpy as np
from PIL import Image
from paddleocr import PaddleOCR

from app.processors.ocr.base import OCRProvider


class PaddleOCRProvider(OCRProvider):
    def __init__(self):
        self.ocr = PaddleOCR(use_angle_cls=True, lang="ch")

    def extract_text_from_image(self, image_bytes: bytes) -> str:
        image = Image.open(io.BytesIO(image_bytes))
        image_array = np.array(image)
        result = self.ocr.ocr(image_array, cls=True)
        if not result or not result[0]:
            return ""
        return "\n".join([line[1][0] for line in result[0]])
