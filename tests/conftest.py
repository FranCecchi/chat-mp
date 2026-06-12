import pytest

from app.rag.service import rag_service


@pytest.fixture(autouse=True)
def disable_rag_singleton_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(rag_service, "enabled", False)
