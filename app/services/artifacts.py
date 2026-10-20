from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from app.core.config import get_settings
from app.schemas import UploadedArtifact


TABULAR_SUFFIXES = {".csv", ".xlsx", ".xls", ".parquet"}
DOCUMENT_SUFFIXES = {".txt", ".md", ".pdf", ".docx"}


def classify_artifact(path: Path) -> str:
    # Simple routing: documents go to RAG, tabular files go to the data analysis path.
    suffix = path.suffix.lower()
    if suffix in TABULAR_SUFFIXES:
        return "tabular"
    if suffix in DOCUMENT_SUFFIXES:
        return "document"
    return "unknown"


async def save_upload(file: UploadFile) -> UploadedArtifact:
    # Store uploaded files with a UUID prefix so repeated filenames do not overwrite each other.
    settings = get_settings()
    file_id = str(uuid4())
    filename = file.filename or f"{file_id}.bin"
    target = settings.upload_dir / f"{file_id}_{filename}"
    content = await file.read()
    target.write_bytes(content)
    return UploadedArtifact(
        file_id=file_id,
        filename=filename,
        content_type=file.content_type,
        path=str(target),
        artifact_type=classify_artifact(target),
    )
