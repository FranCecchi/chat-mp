from collections.abc import Sequence


class LocalEmbeddingClient:
    def __init__(self, model_name: str) -> None:
        self.model_name = model_name
        self._model: object | None = None

    @property
    def model(self) -> object:
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
            except ImportError as exc:
                raise RuntimeError(
                    "sentence-transformers is required for local embeddings."
                ) from exc
            self._model = SentenceTransformer(self.model_name)
        return self._model

    def embed_texts(self, texts: Sequence[str]) -> list[list[float]]:
        if not texts:
            return []
        embeddings = self.model.encode(  # type: ignore[attr-defined]
            list(texts),
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return [embedding.tolist() for embedding in embeddings]

    def embed_query(self, text: str) -> list[float]:
        return self.embed_texts([text])[0]
