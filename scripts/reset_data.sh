#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

# 校验目录合法性
if [[ ! -f "$SCRIPT_DIR/alembic.ini" ]] || [[ ! -f "$SCRIPT_DIR/.env" ]]; then
    echo "错误：未找到项目标识文件，脚本目录异常：$SCRIPT_DIR" >&2
    exit 1
fi

cd "$SCRIPT_DIR"

# 检查 alembic 可用性
if ! command -v alembic &>/dev/null; then
    echo "错误：alembic 未安装或不在 PATH 中" >&2
    exit 1
fi

echo "即将清空以下数据（不可恢复）："
echo "  - data/docsim.db"
echo "  - data/faiss/ 全部索引文件"
echo "  - data/files/ 全部上传文件"
echo "  - data/texts/ 全部文本文件"
echo ""
read -r -p "确认执行？输入 yes 继续：" confirm
if [[ "$confirm" != "yes" ]]; then
    echo "已取消。"
    exit 0
fi

echo "=== 清空数据库 ==="
rm -f data/docsim.db

echo "=== 清空 FAISS 索引 ==="
rm -f data/faiss/index.bin \
      data/faiss/meta.json \
      data/faiss/fingerprint_merged.bin \
      data/faiss/fingerprint_merged_meta.json \
      data/faiss/fingerprint_pooled.bin \
      data/faiss/fingerprint_pooled_meta.json

echo "=== 清空文件存储 ==="
if [[ -d data/files ]]; then
    find data/files -mindepth 1 -delete
fi
if [[ -d data/texts ]]; then
    find data/texts -mindepth 1 -delete
fi

echo "=== 重建数据库 ==="
alembic upgrade head

echo "Done."
