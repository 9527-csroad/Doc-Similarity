# Doc-Similarity Demo 本地运行指南（无 Docker）

## 模式选择

| 模式 | PostgreSQL | Redis | 数据存储位置 |
|------|------------|-------|--------------|
| **standalone** | 不需要 | 不需要 | `./data/` 目录（SQLite + 文件） |
| demo | 需要 | 需要 | PostgreSQL + Redis |

---

## Standalone 模式（K8s/容器推荐，无需数据库）

适用于无 systemd、无法安装 PostgreSQL/Redis 的环境（如 K8s Pod）。

### 步骤

```bash
cd /PPU/GeneralServices_NAS/Text/Doc-Similarity
python -m venv venv
source venv/bin/activate
pip install -r requirements/base.txt

cp .env.example .env
# .env.example 已含 DEPLOY_MODE=standalone，无需改

mkdir -p data/files data/faiss
alembic upgrade head
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

数据文件：`./data/docsim.db`（元数据）、`./data/files/`（PDF）、`./data/faiss/`（向量）、`./data/config.json`（阈值配置）。将 `data/` 挂载到持久化卷即可。

---

## Demo 模式（需 PostgreSQL + Redis）

## 一、前置条件

| 依赖 | 版本/要求 | 用途 |
|------|-----------|------|
| Python | 3.11 | 运行应用 |
| PostgreSQL | 15 | 元数据存储 |
| Redis | 任意 | 配置缓存 |

## 二、环境准备

### 2.1 PostgreSQL

```bash
# 创建用户和数据库
psql -U postgres -c "CREATE USER docsim WITH PASSWORD 'docsim123';"
psql -U postgres -c "CREATE DATABASE docsim OWNER docsim;"
```

### 2.2 Redis

确保 Redis 在 `localhost:6379` 运行。若未安装：

```bash
# Ubuntu/Debian
sudo apt install redis-server
sudo systemctl start redis

# 或直接运行
redis-server
```

## 三、项目配置

### 3.1 虚拟环境与依赖

```bash
cd /PPU/GeneralServices_NAS/Text/Doc-Similarity
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements/base.txt
```

### 3.2 环境变量

```bash
cp .env.example .env
```

`.env` 中需确认以下项（`.env.example` 已符合 Demo 要求）：

| 变量 | Demo 值 | 说明 |
|------|---------|------|
| DEPLOY_MODE | demo | 必须 |
| VECTOR_STORE | faiss | 本地向量库，无需 Milvus |
| STORAGE_BACKEND | local | 本地存储，无需 MinIO |
| TASK_MODE | sync | 同步任务，无需 Celery |
| POSTGRES_* | 见 .env.example | 与 2.1 中一致 |
| REDIS_HOST | localhost | |
| REDIS_PORT | 6379 | |

### 3.3 数据库迁移

```bash
alembic upgrade head
```

若 `alembic.ini` 中 `sqlalchemy.url` 与本地不符，可临时设置：

```bash
export DATABASE_URL="postgresql+asyncpg://docsim:docsim123@localhost:5432/docsim"
# 或直接编辑 alembic.ini 的 sqlalchemy.url
```

### 3.4 数据目录

```bash
mkdir -p data/files data/faiss
```

## 四、启动服务

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## 五、验证 Demo

| 地址 | 说明 |
|------|------|
| http://localhost:8000/health | 健康检查 |
| http://localhost:8000/docs | Swagger API 文档 |
| http://localhost:8000/api/v1/documents | 文档上传与管理 |
| http://localhost:8000/api/v1/search | 相似度检索 |

### 快速验证流程

1. 打开 http://localhost:8000/docs
2. 上传 PDF：`POST /api/v1/documents/upload`
3. 等待处理完成（sync 模式会同步返回）
4. 调用 `POST /api/v1/search/similar` 进行相似度检索

## 六、Demo 模式说明

- **FAISS**：向量存储在 `./data/faiss/`，无需 Milvus
- **本地存储**：文件存储在 `./data/files/`，无需 MinIO
- **Sync 任务**：文档解析与向量化同步执行，无需 Celery
- **PostgreSQL + Redis**：仍需本机安装并运行

## 七、常见问题

**Q: 首次启动慢？**  
A: 首次加载 BGE 模型会下载，约 2GB，需等待。

**Q: 数据库连接失败？**  
A: 检查 PostgreSQL 是否启动，用户/密码/库名是否与 `.env` 一致。

**Q: Redis 连接失败？**  
A: 检查 Redis 是否在 6379 端口运行。
