# Doc-Similarity 本地运行指南（无 Docker）

**当前对外 API**：仅 `POST /api/v2/books/*`（上传 / 相似查询 / 热门）。书籍指纹依赖 **FAISS**，请设置 `VECTOR_STORE=faiss`（standalone/demo 默认即可）。

## 模式选择

| 模式 | PostgreSQL | Redis | 数据存储 |
|------|------------|-------|----------|
| **standalone** | 不需要 | 不需要 | `./data/`（SQLite + 本地文件 + FAISS） |
| demo | 需要 | 需要 | PostgreSQL + Redis + 本地 FAISS |

---

## Standalone 模式

适用于无 PostgreSQL/Redis 的环境。

```bash
cd /PPU/GeneralServices_NAS/Text/Doc-Similarity
python -m venv .venv
source .venv/bin/activate
pip install -r requirements/base.txt

cp .env.example .env
# 确认 DEPLOY_MODE=standalone、VECTOR_STORE=faiss

mkdir -p data/files data/faiss data/texts
alembic upgrade head
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**数据目录**：

| 路径 | 用途 |
|------|------|
| `./data/docsim.db` | 元数据（SQLite） |
| `./data/texts/` | 上传书籍全文 `.txt` |
| `./data/faiss/fingerprint_merged.*` | merged 指纹索引 |
| `./data/faiss/fingerprint_pooled.*` | pooled 指纹索引 |
| `./data/files/` | 历史/其它本地文件（可选） |

将 `data/` 挂卷即可持久化。

---

## Demo 模式（PostgreSQL + Redis）

### 前置条件

| 依赖 | 用途 |
|------|------|
| Python 3.11 | 运行应用 |
| PostgreSQL 15 | 元数据 |
| Redis | 配置缓存（若仍被其它模块使用） |

### PostgreSQL

```bash
psql -U postgres -c "CREATE USER docsim WITH PASSWORD 'docsim123';"
psql -U postgres -c "CREATE DATABASE docsim OWNER docsim;"
```

### 环境与启动

```bash
cd /PPU/GeneralServices_NAS/Text/Doc-Similarity
python -m venv .venv
source .venv/bin/activate
pip install -r requirements/base.txt
cp .env.example .env
```

`.env` 中建议确认：

| 变量 | 说明 |
|------|------|
| DEPLOY_MODE | demo |
| VECTOR_STORE | faiss（书籍指纹必需） |
| STORAGE_BACKEND | local |
| TASK_MODE | sync |
| POSTGRES_* | 与库一致 |

```bash
mkdir -p data/files data/faiss data/texts
alembic upgrade head
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

---

## 验证

| 地址 | 说明 |
|------|------|
| http://localhost:8000/health | 健康检查 |
| http://localhost:8000/docs | Swagger |
| `POST /api/v2/books/upload` | 见 `接口文档.md` |

**快速流程**：在 `/docs` 中调用 `books/upload`（需可访问的 `pdf_url`、`txt_url`），再调用 `books/search`。

---

## 说明

- **BGE**：首次加载会拉模型，体积约 2GB，耗时较长。
- **书籍接口与 Milvus**：当前指纹双索引仅 FAISS 实现；`VECTOR_STORE=milvus` 时书籍相关接口不可用。
- **常见问题**：数据库连不上 → 检查 PostgreSQL 与 `.env`；Redis 连不上 → 检查 6379。
