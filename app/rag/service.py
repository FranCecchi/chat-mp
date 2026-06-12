import logging
from collections.abc import Sequence

from app.core.config import get_settings
from app.rag.embeddings import LocalEmbeddingClient
from app.rag.store import PgVectorStore, RetrievedChunk


logger = logging.getLogger(__name__)


class RagService:
    def __init__(
        self,
        *,
        embedding_client: LocalEmbeddingClient | None = None,
        vector_store: PgVectorStore | None = None,
        enabled: bool | None = None,
        top_k: int | None = None,
        fail_open: bool | None = None,
    ) -> None:
        settings = get_settings()
        self.enabled = settings.rag_enabled if enabled is None else enabled
        self.top_k = settings.rag_top_k if top_k is None else top_k
        self.fail_open = settings.rag_fail_open if fail_open is None else fail_open
        self.embedding_client = embedding_client or LocalEmbeddingClient(
            settings.embedding_model
        )
        self.vector_store = vector_store or PgVectorStore()

    def build_context(
        self,
        *,
        message: str,
        history: Sequence[dict[str, str]],
    ) -> str:
        if not self.enabled:
            return ""
        try:
            query_text = build_retrieval_query(message=message, history=history)
            query_embedding = self.embedding_client.embed_query(query_text)
            chunks = self.vector_store.search(query_embedding, limit=self.top_k)
            return format_retrieved_context(chunks)
        except Exception:
            if self.fail_open:
                logger.warning(
                    "RAG retrieval failed; continuing without context.",
                    exc_info=True,
                )
                return ""
            raise


def build_retrieval_query(
    *,
    message: str,
    history: Sequence[dict[str, str]],
    max_history_messages: int = 4,
) -> str:
    recent_history = history[-max_history_messages:]
    parts = [
        f"{item.get('role', 'unknown')}: {item.get('content', '')}"
        for item in recent_history
    ]
    parts.append(f"user: {message}")
    return "\n".join(part for part in parts if part.strip())


def format_retrieved_context(chunks: Sequence[RetrievedChunk]) -> str:
    if not chunks:
        return ""

    formatted_chunks: list[str] = []
    for index, chunk in enumerate(chunks, start=1):
        location = format_source_location(chunk)
        content = chunk.content[:1200]
        formatted_chunks.append(
            f"[{index}] Fuente: {chunk.source_name}{location}\n{content}"
        )

    return (
        "Contexto recuperado para fundamentar la evaluacion. "
        "Usalo solo si es relevante y conserva el formato JSON solicitado.\n\n"
        + "\n\n".join(formatted_chunks)
    )


def format_source_location(chunk: RetrievedChunk) -> str:
    if chunk.source_type == "pdf":
        page_number = chunk.metadata.get("page_number")
        return f", pagina {page_number}" if page_number else ""
    if chunk.source_type == "csv":
        row_number = chunk.metadata.get("row_number")
        return f", fila {row_number}" if row_number else ""
    return ""


rag_service = RagService()
