from dataclasses import dataclass
from typing import Any

from app.core.config import get_settings
from app.rag.documents import RagChunk


@dataclass(frozen=True)
class RetrievedChunk:
    content: str
    source_type: str
    source_name: str
    chunk_index: int
    metadata: dict[str, Any]
    score: float


class PgVectorStore:
    def __init__(
        self,
        database_url: str | None = None,
        embedding_dimension: int | None = None,
    ) -> None:
        settings = get_settings()
        self.database_url = database_url or settings.database_url
        self.embedding_dimension = embedding_dimension or settings.embedding_dimension

    def create_schema(self) -> None:
        psycopg, _, _ = self._imports()
        dimension = int(self.embedding_dimension)
        if dimension <= 0:
            raise ValueError("embedding_dimension must be positive.")

        with psycopg.connect(self.database_url) as conn:
            with conn.cursor() as cur:
                cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
                cur.execute(
                    f"""
                    CREATE TABLE IF NOT EXISTS rag_chunks (
                        id bigserial PRIMARY KEY,
                        source_type text NOT NULL,
                        source_name text NOT NULL,
                        chunk_index integer NOT NULL,
                        content text NOT NULL,
                        metadata jsonb NOT NULL DEFAULT '{{}}'::jsonb,
                        content_hash text NOT NULL UNIQUE,
                        embedding vector({dimension}) NOT NULL,
                        created_at timestamptz NOT NULL DEFAULT now(),
                        updated_at timestamptz NOT NULL DEFAULT now()
                    )
                    """
                )
                cur.execute(
                    """
                    CREATE INDEX IF NOT EXISTS rag_chunks_source_idx
                    ON rag_chunks (source_type, source_name)
                    """
                )
                cur.execute(
                    """
                    CREATE INDEX IF NOT EXISTS rag_chunks_embedding_idx
                    ON rag_chunks
                    USING ivfflat (embedding vector_cosine_ops)
                    WITH (lists = 100)
                    """
                )
            conn.commit()

    def upsert_chunks(
        self,
        chunks: list[RagChunk],
        embeddings: list[list[float]],
    ) -> int:
        if len(chunks) != len(embeddings):
            raise ValueError("chunks and embeddings must have the same length.")
        if not chunks:
            return 0

        psycopg, Jsonb, register_vector = self._imports()
        with psycopg.connect(self.database_url) as conn:
            register_vector(conn)
            with conn.cursor() as cur:
                for chunk, embedding in zip(chunks, embeddings, strict=True):
                    cur.execute(
                        """
                        INSERT INTO rag_chunks (
                            source_type,
                            source_name,
                            chunk_index,
                            content,
                            metadata,
                            content_hash,
                            embedding
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (content_hash) DO UPDATE SET
                            source_type = EXCLUDED.source_type,
                            source_name = EXCLUDED.source_name,
                            chunk_index = EXCLUDED.chunk_index,
                            content = EXCLUDED.content,
                            metadata = EXCLUDED.metadata,
                            embedding = EXCLUDED.embedding,
                            updated_at = now()
                        """,
                        (
                            chunk.source_type,
                            chunk.source_name,
                            chunk.chunk_index,
                            chunk.content,
                            Jsonb(chunk.metadata),
                            chunk.content_hash,
                            embedding,
                        ),
                    )
            conn.commit()
        return len(chunks)

    def search(self, query_embedding: list[float], *, limit: int) -> list[RetrievedChunk]:
        if limit <= 0:
            return []

        psycopg, _, register_vector = self._imports()
        with psycopg.connect(self.database_url) as conn:
            register_vector(conn)
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT
                        content,
                        source_type,
                        source_name,
                        chunk_index,
                        metadata,
                        1 - (embedding <=> %s) AS score
                    FROM rag_chunks
                    ORDER BY embedding <=> %s
                    LIMIT %s
                    """,
                    (query_embedding, query_embedding, limit),
                )
                rows = cur.fetchall()

        return [
            RetrievedChunk(
                content=row[0],
                source_type=row[1],
                source_name=row[2],
                chunk_index=row[3],
                metadata=dict(row[4] or {}),
                score=float(row[5]),
            )
            for row in rows
        ]

    @staticmethod
    def _imports() -> tuple[object, type, object]:
        try:
            import psycopg
            from pgvector.psycopg import register_vector
            from psycopg.types.json import Jsonb
        except ImportError as exc:
            raise RuntimeError(
                "psycopg and pgvector are required for pgvector RAG storage."
            ) from exc
        return psycopg, Jsonb, register_vector
