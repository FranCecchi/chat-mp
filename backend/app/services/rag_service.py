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
        self._feedback_text: str = ""
        self._is_loaded: bool = False


        # Resolve paths relative to workspace root
        # File is in backend/app/services/rag_service.py
        self.base_dir = Path(__file__).resolve().parent.parent.parent.parent
        self.refs_dir = self.base_dir / "refs"

    def load_documents(self, force: bool = False) -> None:
        """Loads and parses PDF and CSV files from the refs directory."""
        if self._is_loaded and not force:
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

        # 4. Parse Teacher Feedback Examples JSON
        feedback_path = self.refs_dir / "feedback_examples.json"
        self._feedback_text = ""
        if feedback_path.exists():
            try:
                import json
                with open(feedback_path, mode="r", encoding="utf-8") as f:
                    feedback_list = json.load(f)
                
                feedback_examples = []
                for item in feedback_list:
                    convo_turns = []
                    for turn in item.get("conversation", []):
                        role = "Alumno" if turn.get("role") == "user" else "Asistente"
                        convo_turns.append(f"{role}: {turn.get('content')}")
                    convo_str = "\n".join(convo_turns)
                    
                    if item.get("is_correct"):
                        example_str = (
                            "### EJEMPLO DE DIAGNÓSTICO CORRECTO (VERIFICADO POR EL DOCENTE)\n"
                            f"Conversación:\n{convo_str}\n\n"
                            f"Clasificación correcta del docente: {item.get('corrected_movement')} ({item.get('corrected_logro')})\n"
                            f"Justificación pedagógica: {item.get('justification')}"
                        )
                    else:
                        err_reason = item.get("error_explanation")
                        err_reason_str = f"   -> Razón del error cometido: {err_reason}\n" if err_reason else ""
                        example_str = (
                            "### EJEMPLO DE CORRECCIÓN DE DIAGNÓSTICO (RETROALIMENTACIÓN DOCENTE - ERROR ANTERIOR DE LA IA)\n"
                            "[CRÍTICO: La IA cometió un error en este diálogo. Analiza el error para no repetirlo.]\n\n"
                            f"Conversación:\n{convo_str}\n\n"
                            f"❌ CLASIFICACIÓN ERRÓNEA ANTERIOR (Asistente): {item.get('original_movement')} ({item.get('original_logro')})\n"
                            f"{err_reason_str}"
                            f"✅ CLASIFICACIÓN CORRECTA DEFINITIVA (Docente): {item.get('corrected_movement')} ({item.get('corrected_logro')})\n"
                            f"   -> Justificación pedagógica correcta: {item.get('justification')}"
                        )
                    feedback_examples.append(example_str)
                self._feedback_text = "\n\n".join(feedback_examples)
                logger.info(f"Loaded feedback JSON responses: {len(feedback_examples)} examples")
            except Exception as e:
                logger.error(f"Error reading feedback JSON: {e}")
                self._feedback_text = "Error al cargar los ejemplos de retroalimentación docente."
        else:
            self._feedback_text = ""

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
        )
        
        if self._feedback_text:
            context += (
                "-------------------------------------------------------------------\n\n"
                "4. EJEMPLOS DE CORRECCIONES Y VERIFICACIONES DE CONVERSACIONES REALIZADAS POR DOCENTES:\n"
                "Estudia estos ejemplos para aprender de tus errores previos y no volver a cometerlos. "
                "Si ves un ejemplo de corrección, prioriza la clasificación correcta sugerida por el docente "
                "ante patrones de conversación similares:\n"
                f"{self._feedback_text}\n\n"
            )
            
        context += "==================================================================="
        return context

    def append_feedback_to_json(
        self,
        activity_context: str,
        is_correct: bool,
        original_movement: str | None,
        original_logro: str | None,
        corrected_movement: str | None,
        corrected_logro: str | None,
        justification: str,
        error_explanation: str | None,
        conversation: list[dict]
    ) -> None:
        """Appends a new teacher feedback example (correct or corrected) to feedback_examples.json."""
        feedback_path = self.refs_dir / "feedback_examples.json"
        
        import datetime
        timestamp = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        
        new_entry = {
            "timestamp": timestamp,
            "activity_context": activity_context,
            "is_correct": is_correct,
            "original_movement": original_movement,
            "original_logro": original_logro,
            "corrected_movement": corrected_movement,
            "corrected_logro": corrected_logro,
            "justification": justification,
            "error_explanation": error_explanation,
            "conversation": conversation
        }
        
        import json
        feedback_list = []
        if feedback_path.exists():
            try:
                with open(feedback_path, mode="r", encoding="utf-8") as f:
                    feedback_list = json.load(f)
            except Exception as e:
                logger.error(f"Error loading existing feedback JSON: {e}")
                
        feedback_list.append(new_entry)
        
        try:
            with open(feedback_path, mode="w", encoding="utf-8") as f:
                json.dump(feedback_list, f, ensure_ascii=False, indent=2)
            logger.info(f"Successfully appended feedback example to JSON at {feedback_path}")
        except Exception as e:
            logger.error(f"Error writing feedback JSON: {e}")
            raise e
            
        self.load_documents(force=True)


rag_service = RagService()
