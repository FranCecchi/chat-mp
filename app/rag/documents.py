import csv
import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any


DEFAULT_CHUNK_SIZE = 900
DEFAULT_CHUNK_OVERLAP = 150


@dataclass(frozen=True)
class RagChunk:
    content: str
    source_type: str
    source_name: str
    chunk_index: int
    metadata: dict[str, Any]

    @property
    def content_hash(self) -> str:
        payload = "|".join(
            [
                self.source_type,
                self.source_name,
                str(self.chunk_index),
                self.content,
            ]
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def chunk_text(
    text: str,
    *,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[str]:
    normalized = " ".join(text.split())
    if not normalized:
        return []
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive.")
    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap must be non-negative and smaller than chunk_size.")

    chunks: list[str] = []
    start = 0
    while start < len(normalized):
        end = min(start + chunk_size, len(normalized))
        chunks.append(normalized[start:end].strip())
        if end == len(normalized):
            break
        start = end - overlap
    return chunks


def load_pdf_chunks(path: Path) -> list[RagChunk]:
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise RuntimeError("pypdf is required to ingest PDF files.") from exc

    reader = PdfReader(str(path))
    chunks: list[RagChunk] = []
    chunk_index = 0
    for page_number, page in enumerate(reader.pages, start=1):
        page_text = page.extract_text() or ""
        for content in chunk_text(page_text):
            chunks.append(
                RagChunk(
                    content=content,
                    source_type="pdf",
                    source_name=path.name,
                    chunk_index=chunk_index,
                    metadata={
                        "path": str(path),
                        "page_number": page_number,
                    },
                )
            )
            chunk_index += 1
    return chunks


def load_csv_chunks(path: Path) -> list[RagChunk]:
    chunks: list[RagChunk] = []
    with path.open(newline="", encoding="utf-8-sig") as csv_file:
        reader = csv.DictReader(csv_file)
        for row_number, row in enumerate(reader, start=2):
            content = build_sanitized_csv_text(row)
            if not content:
                continue
            chunks.append(
                RagChunk(
                    content=content,
                    source_type="csv",
                    source_name=path.name,
                    chunk_index=len(chunks),
                    metadata={
                        "path": str(path),
                        "row_number": row_number,
                        "subject": field_by_position(row, 1),
                    },
                )
            )
    return chunks


def build_sanitized_csv_text(row: dict[str, str | None]) -> str:
    subject = field_by_position(row, 1)
    activity = field_by_position(row, 2)
    thinking_options = field_by_position(row, 3)
    reflection = field_by_position(row, 5)

    parts = [
        ("Asignatura", subject),
        ("Actividad", activity),
        ("Opciones de pensamiento", thinking_options),
        ("Reflexion", reflection),
    ]
    return "\n".join(f"{label}: {value}" for label, value in parts if value).strip()


def field_by_position(row: dict[str, str | None], index: int) -> str:
    values = list(row.values())
    if index >= len(values):
        return ""
    value = values[index]
    return " ".join(value.split()) if value else ""


def load_reference_chunks(refs_dir: Path) -> list[RagChunk]:
    chunks: list[RagChunk] = []
    for path in sorted(refs_dir.iterdir()):
        if path.suffix.lower() == ".pdf":
            chunks.extend(load_pdf_chunks(path))
        elif path.suffix.lower() == ".csv":
            chunks.extend(load_csv_chunks(path))
    return chunks
