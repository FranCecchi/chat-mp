"""
SQLite persistence for diagnoses.
Uses asyncio.to_thread to wrap synchronous sqlite3 calls without blocking the event loop.
"""
import asyncio
import sqlite3

from app.core.config import get_settings


def _db_path() -> str:
    return get_settings().db_path


# ── Init ────────────────────────────────────────────────────────────────────

def _init_db_sync() -> None:
    conn = sqlite3.connect(_db_path())
    conn.execute("""
        CREATE TABLE IF NOT EXISTS diagnoses (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            student_name    TEXT NOT NULL,
            conversation_id TEXT NOT NULL,
            movimiento      TEXT,
            logro           TEXT,
            justificacion   TEXT,
            activity_context TEXT,
            created_at      TEXT DEFAULT (datetime('now'))
        )
    """)
    # Ensure conversation_history column exists
    cursor = conn.execute("PRAGMA table_info(diagnoses)")
    columns = [row[1] for row in cursor.fetchall()]
    if "conversation_history" not in columns:
        conn.execute("ALTER TABLE diagnoses ADD COLUMN conversation_history TEXT")
    if "feedback_status" not in columns:
        conn.execute("ALTER TABLE diagnoses ADD COLUMN feedback_status TEXT")
    if "feedback_corrected_movement" not in columns:
        conn.execute("ALTER TABLE diagnoses ADD COLUMN feedback_corrected_movement TEXT")
    conn.commit()
    conn.close()


async def init_db() -> None:
    await asyncio.to_thread(_init_db_sync)


# ── Write ────────────────────────────────────────────────────────────────────

def _save_diagnosis_sync(
    student_name: str,
    conversation_id: str,
    movimiento: str | None,
    logro: str | None,
    justificacion: str | None,
    activity_context: str | None,
    conversation_history: str | None = None,
) -> None:
    conn = sqlite3.connect(_db_path())
    conn.execute(
        """INSERT INTO diagnoses
             (student_name, conversation_id, movimiento, logro, justificacion, activity_context, conversation_history)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (student_name, conversation_id, movimiento, logro, justificacion, activity_context, conversation_history),
    )
    conn.commit()
    conn.close()


async def save_diagnosis(
    student_name: str,
    conversation_id: str,
    movimiento: str | None,
    logro: str | None,
    justificacion: str | None,
    activity_context: str | None,
    conversation_history: str | None = None,
) -> None:
    await asyncio.to_thread(
        _save_diagnosis_sync,
        student_name,
        conversation_id,
        movimiento,
        logro,
        justificacion,
        activity_context,
        conversation_history,
    )


# ── Read ─────────────────────────────────────────────────────────────────────

def _get_all_diagnoses_sync() -> list[dict]:
    conn = sqlite3.connect(_db_path())
    conn.row_factory = sqlite3.Row
    cursor = conn.execute(
        "SELECT * FROM diagnoses ORDER BY created_at DESC"
    )
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


async def get_all_diagnoses() -> list[dict]:
    return await asyncio.to_thread(_get_all_diagnoses_sync)


def _get_diagnosis_sync(diagnosis_id: int) -> dict | None:
    conn = sqlite3.connect(_db_path())
    conn.row_factory = sqlite3.Row
    cursor = conn.execute(
        "SELECT * FROM diagnoses WHERE id = ?",
        (diagnosis_id,)
    )
    row = cursor.fetchone()
    res = dict(row) if row else None
    conn.close()
    return res


async def get_diagnosis(diagnosis_id: int) -> dict | None:
    return await asyncio.to_thread(_get_diagnosis_sync, diagnosis_id)


def _submit_diagnosis_feedback_sync(
    diagnosis_id: int,
    status: str,
    corrected_movement: str | None = None
) -> None:
    conn = sqlite3.connect(_db_path())
    conn.execute(
        """UPDATE diagnoses
           SET feedback_status = ?, feedback_corrected_movement = ?
           WHERE id = ?""",
        (status, corrected_movement, diagnosis_id)
    )
    conn.commit()
    conn.close()


async def submit_diagnosis_feedback(
    diagnosis_id: int,
    status: str,
    corrected_movement: str | None = None
) -> None:
    await asyncio.to_thread(
        _submit_diagnosis_feedback_sync,
        diagnosis_id,
        status,
        corrected_movement
    )
