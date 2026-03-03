from app.config import get_settings
from app.processors.ocr.base import OCRProvider


def get_ocr_provider() -> OCRProvider | None:
    settings = get_settings()
    if settings.ocr_provider == "none":
        return None
    if settings.ocr_provider == "paddle":
        from app.processors.ocr.paddle_ocr import PaddleOCRProvider

        return PaddleOCRProvider()
    from app.processors.ocr.rapid_ocr import RapidOCRProvider

    return RapidOCRProvider()


__all__ = ["OCRProvider", "get_ocr_provider"]
