import argparse
import hashlib
import json
import uuid
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import get_settings
from app.models import Document
from app.tasks.pipeline import process_document_pipeline


def import_dataset(dataset_dir: Path, output_path: Path) -> None:
    settings = get_settings()
    engine = create_engine(settings.sync_database_url)
    Session = sessionmaker(bind=engine)

    files = sorted([p for p in dataset_dir.iterdir() if p.is_file() and p.suffix.lower() == ".pdf"])
    rows = []

    with Session() as session:
        for file_path in files:
            content = file_path.read_bytes()
            raw_file_hash = hashlib.sha256(content).hexdigest()
            file_hash = raw_file_hash

            doc = None
            if settings.FILE_HASH_DEDUP:
                doc = session.query(Document).filter(Document.file_hash == file_hash).first()
            created = False

            if not doc:
                if not settings.FILE_HASH_DEDUP:
                    file_hash = hashlib.sha256(
                        f"{raw_file_hash}:{uuid.uuid4().hex}".encode("utf-8")
                    ).hexdigest()
                doc = Document(
                    filename=f"{file_hash}.pdf",
                    original_filename=file_path.name,
                    file_size=len(content),
                    file_hash=file_hash,
                    status="pending",
                    doc_metadata={"source_file_hash": raw_file_hash},
                )
                session.add(doc)
                session.commit()
                session.refresh(doc)
                created = True

            if created or doc.status != "completed":
                process_document_pipeline(doc.id, content)
                session.refresh(doc)

            rows.append(
                {
                    "source_file": file_path.name,
                    "document_id": doc.id,
                    "status": doc.status,
                    "created": created,
                }
            )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dataset-dir",
        default="data/test_dataset1",
        help="PDF目录",
    )
    parser.add_argument(
        "--output",
        default="data/test_dataset1/document_ids.json",
        help="映射输出文件",
    )
    args = parser.parse_args()

    import_dataset(Path(args.dataset_dir), Path(args.output))


if __name__ == "__main__":
    main()
