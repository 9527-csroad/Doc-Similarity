from app.processors.embedding_processor import EmbeddingProvider
from app.processors.pdf_processor import PDFProcessor
from app.processors.ocr_processor import OCRProcessor
from app.processors.text_cleaner import TextCleaner
from app.processors.ocr import get_ocr_provider
from app.config import get_settings


def get_embedding_provider() -> EmbeddingProvider:
    """根据配置获取向量化提供者"""
    settings = get_settings()
    provider = settings.EMBEDDING_PROVIDER

    if provider == "bge":
        from app.processors.bge_embedding import BGEEmbedding
        return BGEEmbedding(model_name=settings.EMBEDDING_MODEL)
    elif provider == "openai":
        from app.processors.openai_embedding import OpenAIEmbedding
        return OpenAIEmbedding()
    elif provider == "zhipu":
        from app.processors.zhipu_embedding import ZhipuEmbedding
        return ZhipuEmbedding()
    else:
        raise ValueError(f"Unknown provider: {provider}")


__all__ = [
    "EmbeddingProvider",
    "PDFProcessor",
    "OCRProcessor",
    "TextCleaner",
    "get_ocr_provider",
    "get_embedding_provider",
]
