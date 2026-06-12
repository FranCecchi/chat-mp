from pathlib import Path

from app.rag.documents import (
    build_sanitized_csv_text,
    chunk_text,
    load_csv_chunks,
)


def test_chunk_text_uses_overlap() -> None:
    chunks = chunk_text("abcdefghij", chunk_size=4, overlap=1)

    assert chunks == ["abcd", "defg", "ghij"]


def test_build_sanitized_csv_text_excludes_timestamp() -> None:
    row = {
        "Marca temporal": "10/04/2026 15:37:28",
        "1. Asignatura": "Epistemologia",
        "2. Actividad": "Leimos un texto y respondimos preguntas.",
        "3. Opciones": "Explique con mis palabras",
        "4. Sentis que te hizo pensar": "Si, mucho",
        "5. Reflexion": "Tuvimos que entender los conceptos.",
    }

    text = build_sanitized_csv_text(row)

    assert "10/04/2026" not in text
    assert "Epistemologia" in text
    assert "Leimos un texto" in text
    assert "Explique con mis palabras" in text
    assert "Tuvimos que entender" in text


def test_load_csv_chunks_adds_row_metadata(tmp_path: Path) -> None:
    csv_path = tmp_path / "respuestas.csv"
    csv_path.write_text(
        "Marca temporal,1. Asignatura,2. Actividad,3. Opciones,4. Piensa,5. Reflexion\n"
        "fecha,Epistemologia,Analizamos un paper,Identifique ideas,Si,Buscamos conclusiones\n",
        encoding="utf-8",
    )

    chunks = load_csv_chunks(csv_path)

    assert len(chunks) == 1
    assert chunks[0].source_type == "csv"
    assert chunks[0].metadata["row_number"] == 2
    assert chunks[0].metadata["subject"] == "Epistemologia"
