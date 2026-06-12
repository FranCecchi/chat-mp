import pytest

from app.rag.service import (
    RagService,
    build_retrieval_query,
    format_retrieved_context,
)
from app.rag.store import RetrievedChunk


class FailingEmbedder:
    def embed_query(self, text: str) -> list[float]:
        raise RuntimeError("embedding failed")


class DummyStore:
    def search(self, query_embedding: list[float], *, limit: int) -> list[RetrievedChunk]:
        return []


def test_build_retrieval_query_uses_recent_history_and_current_message() -> None:
    history = [
        {"role": "user", "content": "mensaje viejo"},
        {"role": "assistant", "content": "respuesta vieja"},
        {"role": "user", "content": "mensaje reciente"},
    ]

    query = build_retrieval_query(message="mensaje actual", history=history)

    assert "mensaje viejo" in query
    assert "mensaje reciente" in query
    assert "mensaje actual" in query


def test_format_retrieved_context_includes_sources() -> None:
    context = format_retrieved_context(
        [
            RetrievedChunk(
                content="Contenido de rubrica",
                source_type="pdf",
                source_name="rubrica.pdf",
                chunk_index=0,
                metadata={"page_number": 2},
                score=0.92,
            ),
            RetrievedChunk(
                content="Ejemplo de alumno",
                source_type="csv",
                source_name="respuestas.csv",
                chunk_index=1,
                metadata={"row_number": 4},
                score=0.88,
            ),
        ]
    )

    assert "rubrica.pdf, pagina 2" in context
    assert "respuestas.csv, fila 4" in context
    assert "Contenido de rubrica" in context


def test_rag_service_fail_open_returns_empty_context() -> None:
    service = RagService(
        embedding_client=FailingEmbedder(),  # type: ignore[arg-type]
        vector_store=DummyStore(),  # type: ignore[arg-type]
        enabled=True,
        top_k=5,
        fail_open=True,
    )

    assert service.build_context(message="hola", history=[]) == ""


def test_rag_service_strict_mode_raises() -> None:
    service = RagService(
        embedding_client=FailingEmbedder(),  # type: ignore[arg-type]
        vector_store=DummyStore(),  # type: ignore[arg-type]
        enabled=True,
        top_k=5,
        fail_open=False,
    )

    with pytest.raises(RuntimeError, match="embedding failed"):
        service.build_context(message="hola", history=[])
