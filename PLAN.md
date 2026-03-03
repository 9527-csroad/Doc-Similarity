# 文档相似度系统 - 重构实施计划

## 目标

在现有代码基础上，重构为**可运行的 demo**，同时保证**扩展性**和**迁移性**。

---

## 核心原则

- **demo 模式**：最少依赖，`docker compose --profile demo up` 一键启动
- **production 模式**：完整基础设施，`docker compose --profile prod up` 切换
- 所有可替换组件通过**抽象接口 + 工厂函数 + 配置切换**

---

## 一、服务抽象层（扩展性）

### 1.1 向量库抽象

```
app/services/vector/
├── base.py              # VectorStore 抽象基类
├── milvus_store.py      # Milvus 实现（production）
├── faiss_store.py       # FAISS 实现（demo）
└── __init__.py          # 工厂函数 get_vector_store()
```

- 抽象接口：`insert()`, `search()`, `delete()`
- demo 用 FAISS（纯本地，零依赖容器）
- production 用 Milvus
- 配置项：`VECTOR_STORE=faiss|milvus`

### 1.2 对象存储抽象

```
app/services/storage/
├── base.py              # ObjectStorage 抽象基类
├── minio_storage.py     # MinIO 实现（production）
├── local_storage.py     # 本地文件系统（demo）
└── __init__.py          # 工厂函数 get_storage()
```

- 抽象接口：`upload()`, `download()`, `delete()`
- demo 用本地文件系统（`./data/files/`）
- production 用 MinIO
- 配置项：`STORAGE_BACKEND=local|minio`

### 1.3 OCR 抽象

```
app/processors/ocr/
├── base.py              # OCRProvider 抽象基类
├── rapid_ocr.py         # RapidOCR 实现（轻量，demo + production 通用）
├── paddle_ocr.py        # PaddleOCR 实现（保留兼容）
└── __init__.py          # 工厂函数 get_ocr_provider()
```

- 默认使用 RapidOCR（`rapidocr-onnxruntime`），替换 PaddleOCR
- 配置项：`OCR_PROVIDER=rapid|paddle|none`
- `none` 表示跳过 OCR

---

## 二、部署模式（迁移性）

### 2.1 依赖对比

| 组件 | demo 模式 | production 模式 |
|------|-----------|----------------|
| PostgreSQL | Docker 容器 | Docker 容器 |
| Redis | Docker 容器 | Docker 容器 |
| 向量库 | FAISS（进程内） | Milvus + etcd + minio |
| 对象存储 | 本地文件系统 | MinIO |
| OCR | RapidOCR | RapidOCR / PaddleOCR |
| 任务队列 | 同步执行（跳过 Celery） | Celery |
| **容器数** | **3（app + pg + redis）** | **8** |

### 2.2 配置结构

```env
# .env
DEPLOY_MODE=demo          # demo | production

# demo 模式自动设置：
# VECTOR_STORE=faiss
# STORAGE_BACKEND=local
# OCR_PROVIDER=rapid
# TASK_MODE=sync

# production 模式自动设置：
# VECTOR_STORE=milvus
# STORAGE_BACKEND=minio
# OCR_PROVIDER=rapid
# TASK_MODE=celery
```

`DEPLOY_MODE` 提供默认值，各组件配置可单独覆盖。

### 2.3 Docker Compose profiles

```yaml
# docker-compose.yml
services:
  app:
    profiles: ["demo", "prod"]
  postgres:
    profiles: ["demo", "prod"]
  redis:
    profiles: ["demo", "prod"]
  milvus:
    profiles: ["prod"]
  etcd:
    profiles: ["prod"]
  minio:
    profiles: ["prod"]
  minio-milvus:
    profiles: ["prod"]
  celery-worker:
    profiles: ["prod"]
```

### 2.4 Dockerfile

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements/ requirements/
RUN pip install -r requirements/base.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 2.5 依赖拆分

```
requirements/
├── base.txt             # 核心依赖（FastAPI, SQLAlchemy, FAISS, RapidOCR 等）
├── production.txt       # 生产额外依赖（pymilvus, minio, celery, PaddleOCR 等）
└── dev.txt              # 开发依赖（pytest 等）
```

---

## 三、任务执行抽象

### 3.1 同步 / 异步切换

```
app/tasks/
├── base.py              # TaskExecutor 抽象
├── sync_executor.py     # 同步执行（demo，直接在请求中处理）
├── celery_executor.py   # Celery 异步执行（production）
└── __init__.py          # 工厂函数 get_executor()
```

- demo 模式：文档上传后同步处理，无需 Celery
- production 模式：投递 Celery 任务
- 配置项：`TASK_MODE=sync|celery`

---

## 四、数据库迁移

- 初始化 alembic
- 创建初始 migration（基于现有 Document 模型）
- 启动脚本中自动执行 `alembic upgrade head`

---

## 五、实施顺序

| 步骤 | 内容 | 依赖 |
|------|------|------|
| Step 1 | 向量库抽象 + FAISS 实现 | 无 |
| Step 2 | 对象存储抽象 + 本地存储实现 | 无 |
| Step 3 | OCR 抽象 + RapidOCR 实现 | 无 |
| Step 4 | 任务执行抽象 + 同步执行器 | Step 1-3 |
| Step 5 | Config 重构（DEPLOY_MODE + 组件配置） | Step 1-4 |
| Step 6 | 依赖拆分（base.txt / production.txt） | Step 5 |
| Step 7 | Dockerfile + docker-compose profiles | Step 6 |
| Step 8 | Alembic 初始化 + 初始 migration | Step 7 |
| Step 9 | 更新 services/__init__.py、processors/__init__.py | Step 1-4 |
| Step 10 | 集成验证：demo 模式一键启动 | Step 1-9 |

---

## 六、最终目录结构

```
doc-similarity-system/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── api/v1/
│   │   ├── documents.py
│   │   ├── search.py
│   │   ├── stats.py
│   │   └── config.py
│   ├── db/
│   │   └── database.py
│   ├── models/
│   │   └── document.py
│   ├── schemas/
│   │   ├── document.py
│   │   ├── search.py
│   │   └── config.py
│   ├── processors/
│   │   ├── embedding/
│   │   │   ├── base.py
│   │   │   ├── bge_embedding.py
│   │   │   ├── openai_embedding.py
│   │   │   ├── zhipu_embedding.py
│   │   │   └── __init__.py
│   │   ├── ocr/
│   │   │   ├── base.py
│   │   │   ├── rapid_ocr.py
│   │   │   ├── paddle_ocr.py
│   │   │   └── __init__.py
│   │   ├── pdf_processor.py
│   │   └── __init__.py
│   ├── services/
│   │   ├── vector/
│   │   │   ├── base.py
│   │   │   ├── faiss_store.py
│   │   │   ├── milvus_store.py
│   │   │   └── __init__.py
│   │   ├── storage/
│   │   │   ├── base.py
│   │   │   ├── local_storage.py
│   │   │   ├── minio_storage.py
│   │   │   └── __init__.py
│   │   ├── redis_service.py
│   │   └── __init__.py
│   └── tasks/
│       ├── base.py
│       ├── sync_executor.py
│       ├── celery_executor.py
│       ├── celery_app.py
│       └── __init__.py
├── alembic/
│   ├── versions/
│   └── env.py
├── data/                        # demo 本地存储目录
│   ├── files/
│   └── faiss/
├── docker/
│   └── Dockerfile
├── requirements/
│   ├── base.txt
│   ├── production.txt
│   └── dev.txt
├── scripts/
│   └── start.sh
├── alembic.ini
├── docker-compose.yml
├── .env.example
├── .gitignore
└── PLAN.md
```

---

## 七、验证标准

1. `docker compose --profile demo up` → 3 个容器启动，API 可访问
2. 上传 PDF → 同步处理完成 → 返回文档信息
3. 相似度检索 → FAISS 返回结果
4. 切换 `DEPLOY_MODE=production` → 使用 Milvus + MinIO + Celery
5. 同一份代码，仅通过环境变量切换部署模式
