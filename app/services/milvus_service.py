from pymilvus import connections, Collection, FieldSchema, CollectionSchema, DataType, utility
from typing import List, Tuple
from app.config import get_settings

COLLECTION_NAME = "document_vectors"


class MilvusService:
    """Milvus 向量数据库服务"""

    def __init__(self):
        settings = get_settings()
        connections.connect(
            alias="default",
            host=settings.MILVUS_HOST,
            port=settings.MILVUS_PORT
        )
        self.dim = settings.EMBEDDING_DIM
        self._ensure_collection()

    def _ensure_collection(self):
        """确保 Collection 存在"""
        if utility.has_collection(COLLECTION_NAME):
            self.collection = Collection(COLLECTION_NAME)
            return

        fields = [
            FieldSchema(name="id", dtype=DataType.VARCHAR, max_length=36, is_primary=True),
            FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=self.dim),
        ]
        schema = CollectionSchema(fields, description="Document vectors")
        self.collection = Collection(COLLECTION_NAME, schema)

        # 创建索引
        index_params = {
            "metric_type": "COSINE",
            "index_type": "IVF_FLAT",
            "params": {"nlist": 1024}
        }
        self.collection.create_index("vector", index_params)
        self.collection.load()

    def insert(self, doc_id: str, vector: List[float]):
        """插入向量"""
        self.collection.insert([[doc_id], [vector]])

    def search(self, vector: List[float], top_k: int = 10) -> List[Tuple[str, float]]:
        """搜索相似向量"""
        self.collection.load()
        results = self.collection.search(
            data=[vector],
            anns_field="vector",
            param={"metric_type": "COSINE", "params": {"nprobe": 16}},
            limit=top_k,
            output_fields=["id"]
        )

        matches = []
        for hit in results[0]:
            matches.append((hit.id, hit.score))
        return matches

    def delete(self, doc_id: str):
        """删除向量"""
        self.collection.delete(f'id == "{doc_id}"')
