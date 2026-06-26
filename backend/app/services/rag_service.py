import csv
import logging
from pathlib import Path
from pypdf import PdfReader

logger = logging.getLogger("uvicorn.error")


class RagService:
    def __init__(self) -> None:
        self._rubric_text: str = ""
        self._dialogs_text: str = ""
        self._csv_examples_text: str = ""
        self._is_loaded: bool = False

        # Resolve paths relative to workspace root
        # File is in backend/app/services/rag_service.py
        self.base_dir = Path(__file__).resolve().parent.parent.parent.parent
        self.refs_dir = self.base_dir / "refs"

    def load_documents(self) -> None:
        """Loads and parses PDF and CSV files from the refs directory."""
        if self._is_loaded:
            return

        logger.info("Initializing Pedagogical Grounding (RAG) Service...")

        # 1. Parse Rubrics PDF
        rubric_path = self.refs_dir / "4. Rúbrica de Movimiento de Pensamiento 2-5-26.pdf"
        if rubric_path.exists():
            try:
                reader = PdfReader(rubric_path)
                pages_text = []
                for i, page in enumerate(reader.pages):
                    pages_text.append(f"--- Rúbrica Página {i+1} ---\n" + (page.extract_text() or ""))
                self._rubric_text = "\n\n".join(pages_text)
                logger.info(f"Loaded rubric PDF: {len(self._rubric_text)} chars")
            except Exception as e:
                logger.error(f"Error reading rubric PDF: {e}")
                self._rubric_text = "Error al cargar la rúbrica oficial."
        else:
            logger.warning(f"Rubric PDF not found at {rubric_path}")
            self._rubric_text = "Rúbrica oficial no disponible."

        # 2. Parse Dialog Examples PDF
        dialogs_path = self.refs_dir / "Chat MP IA.pdf"
        if dialogs_path.exists():
            try:
                reader = PdfReader(dialogs_path)
                pages_text = []
                for i, page in enumerate(reader.pages):
                    pages_text.append(f"--- Diálogos Página {i+1} ---\n" + (page.extract_text() or ""))
                self._dialogs_text = "\n\n".join(pages_text)
                logger.info(f"Loaded dialogs PDF: {len(self._dialogs_text)} chars")
            except Exception as e:
                logger.error(f"Error reading dialogs PDF: {e}")
                self._dialogs_text = "Error al cargar los flujos conversacionales de ejemplo."
        else:
            logger.warning(f"Dialogs PDF not found at {dialogs_path}")
            self._dialogs_text = "Flujos de ejemplo no disponibles."

        # 3. Parse CSV Survey Responses
        csv_path = self.refs_dir / "¿Qué hiciste hoy en clases_ (respuestas) - Respuestas de formulario 1.csv"
        if csv_path.exists():
            try:
                examples = []
                with open(csv_path, mode="r", encoding="utf-8-sig", errors="ignore") as f:
                    reader = csv.reader(f)
                    # Skip header
                    header = next(reader, None)
                    for row in reader:
                        if len(row) >= 6:
                            subject = row[1].strip()
                            activity = row[2].strip()
                            actions = row[3].strip()
                            made_think = row[4].strip()
                            explanation = row[5].strip()

                            if activity:
                                examples.append(
                                    f"- Asignatura: {subject}\n"
                                    f"  Actividad: {activity}\n"
                                    f"  Acciones reportadas: {actions}\n"
                                    f"  ¿Hizo pensar?: {made_think}\n"
                                    f"  Explicación: {explanation}"
                                )
                self._csv_examples_text = "\n\n".join(examples)
                logger.info(f"Loaded CSV responses: {len(examples)} examples")
            except Exception as e:
                logger.error(f"Error reading CSV responses: {e}")
                self._csv_examples_text = "Error al cargar las respuestas reales del formulario."
        else:
            logger.warning(f"CSV responses not found at {csv_path}")
            self._csv_examples_text = "Respuestas del formulario no disponibles."

        self._is_loaded = True

    def get_grounding_context(self) -> str:
        """Returns the formatted grounding context string for system prompt injection."""
        if not self._is_loaded:
            self.load_documents()

        context = (
            "===================================================================\n"
            "CONTEXTO PEDAGÓGICO DE REFERENCIA (DOCUMENTACIÓN OFICIAL)\n"
            "===================================================================\n\n"
            "1. RÚBRICA OFICIAL DE EVALUACIÓN:\n"
            "Usa esta rúbrica para identificar los movimientos de pensamiento "
            "y evaluar si se logró el Logro esperado, Logro parcial o Logro no conseguido:\n"
            f"{self._rubric_text}\n\n"
            "-------------------------------------------------------------------\n\n"
            "2. FLUJOS CONVERSACIONALES DE EJEMPLO:\n"
            "Sigue de cerca estos ejemplos de preguntas y respuestas para interactuar con "
            "el estudiante. Nota cómo el asistente hace preguntas indagatorias breves y no "
            "clasifica de forma apresurada sino hasta corroborar las evidencias de la rúbrica:\n"
            f"{self._dialogs_text}\n\n"
            "-------------------------------------------------------------------\n\n"
            "3. EJEMPLOS REALES DE ACTIVIDADES Y CLASIFICACIONES DE ESTUDIANTES:\n"
            "Úsalos como ejemplos de pocas pasadas (few-shot) para guiar tu comprensión "
            "de las descripciones de los alumnos:\n"
            f"{self._csv_examples_text}\n\n"
            "==================================================================="
        )
        return context


rag_service = RagService()
