import argparse
import asyncio
from pathlib import Path

from app.core.config import get_settings
from app.rag.documents import load_reference_chunks
from app.rag.embeddings import LocalEmbeddingClient
from app.rag.store import PgVectorStore


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ingest reference files into pgvector.")
    parser.add_argument(
        "--refs-dir",
        default="refs",
        help="Directory containing PDF and CSV reference files.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=32,
        help="Number of chunks to embed and upsert per batch.",
    )
    return parser.parse_args()


async def main() -> int:
    args = parse_args()
    refs_dir = Path(args.refs_dir)
    if not refs_dir.exists():
        print(f"Reference directory not found: {refs_dir}")
        return 1
    if args.batch_size <= 0:
        print("--batch-size must be positive.")
        return 2

    settings = get_settings()
    chunks = load_reference_chunks(refs_dir)
    if not chunks:
        print(f"No reference chunks found in {refs_dir}.")
        return 0

    store = PgVectorStore()
    store.create_schema()
    embedder = LocalEmbeddingClient(settings.embedding_model)

    indexed = 0
    for start in range(0, len(chunks), args.batch_size):
        batch = chunks[start : start + args.batch_size]
        embeddings = embedder.embed_texts([chunk.content for chunk in batch])
        indexed += store.upsert_chunks(batch, embeddings)

    print(f"Ingested {indexed} chunks from {refs_dir}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
