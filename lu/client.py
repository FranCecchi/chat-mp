import json
import requests
import datetime

# ── Configuración ──────────────────────────────────────────────────────────────
MODAL_API_URL     = "https://lucia-lotumolo--educeva-chatbot-serve-dev.modal.run/v1/chat/completions"
MODEL_NAME        = "google/gemma-4-E4B-it"

MAX_TURNOS        = 3
UMBRAL_CLASIFICAR = 0.85   # score mínimo del top-1 para clasificar como "logro esperado"
UMBRAL_EXPLORAR   = 0.15   # si el top-1 está por debajo de esto → pregunta general

MOVIMIENTOS = [
    "Observar con atención y describir",
    "Explicar y dar sentido",
    "Justificar con evidencia",
    "Relacionar ideas y conceptos",
    "Considerar otras perspectivas",
    "Identificar ideas claves y llegar a conclusiones",
    "Formular preguntas propias",
    "Explorar la complejidad del tema",
    "Pensar metacognitivamente",
]

# ── Prompts ────────────────────────────────────────────────────────────────────

PROMPT_SCORER = """
Eres un evaluador educativo especializado en Movimientos de Pensamiento.
Tu tarea es leer la conversación con un alumno y puntuar del 0.0 al 1.0
cada movimiento de pensamiento según qué tanto se acerca a su Logro Esperado.

## Criterios de Logro Esperado para cada movimiento:

1. **Observar con atención y describir**
   Score 1.0 = el alumno describe de manera sistemática, detallada y completa aspectos
   específicos de un fenómeno, objeto o proceso.
   Score 0.0 = solo menciona aspectos generales sin descripción ni detalle.

2. **Explicar y dar sentido**
   Score 1.0 = el alumno construye explicaciones o interpretaciones propias que integran
   distintos aspectos; comprensión profunda y articulada, va más allá de reproducir.
   Score 0.0 = solo reproduce definiciones o información presentada sin elaboración propia.

3. **Justificar con evidencia**
   Score 1.0 = el alumno fundamenta sus ideas con dos o más evidencias concretas
   (datos, hechos, referencias) y reflexiona sobre su relevancia.
   Score 0.0 = no usa evidencia para apoyar sus ideas.

4. **Relacionar ideas y conceptos**
   Score 1.0 = el alumno vincula explícitamente lo nuevo con saberes previos, experiencias
   o aplica lo aprendido a situaciones diferentes de manera necesaria para resolver la tarea.
   Score 0.0 = presenta información aislada sin vinculación conceptual.

5. **Considerar otras perspectivas**
   Score 1.0 = el alumno explora y compara distintos puntos de vista, analiza ventajas,
   desventajas e implicaciones, y elabora una postura propia fundamentada.
   Score 0.0 = visión única, sin referencia a otras perspectivas.

6. **Identificar ideas claves y llegar a conclusiones**
   Score 1.0 = el alumno identifica lo esencial y elabora conclusiones complejas y
   fundamentadas propias, no solo reorganiza información.
   Score 0.0 = recopilación de información sin conclusiones propias.

7. **Formular preguntas propias**
   Score 1.0 = el alumno genera preguntas relevantes y desafiantes que motivan a investigar
   y profundizar más allá de lo evidente en el texto o la clase.
   Score 0.0 = no formula preguntas o solo pregunta datos literales del texto.

8. **Explorar la complejidad del tema**
   Score 1.0 = el alumno identifica múltiples factores y sus relaciones, evita
   simplificaciones, analiza tensiones y aspectos no evidentes.
   Score 0.0 = tratamiento descriptivo o meramente reproductivo del tema.

9. **Pensar metacognitivamente**
   Score 1.0 = el alumno reflexiona sobre su propio proceso de aprendizaje: qué estrategias
   usó, si le sirvieron y cómo podría mejorar; planifica y evalúa con autonomía.
   Score 0.0 = no desarrolla conciencia ni control sobre su propio proceso de aprendizaje.

## Instrucciones:
- Puntúa cada movimiento del 0.0 al 1.0 según la evidencia en la conversación.
- Si no hay información suficiente para evaluar un movimiento, asignale un score bajo (0.0–0.1).
- Los scores son independientes entre sí.

## Formato de respuesta:
Responde SIEMPRE con este JSON exacto, sin texto adicional antes ni después:

{
  "scores": {
    "Observar con atención y describir": 0.0,
    "Explicar y dar sentido": 0.0,
    "Justificar con evidencia": 0.0,
    "Relacionar ideas y conceptos": 0.0,
    "Considerar otras perspectivas": 0.0,
    "Identificar ideas claves y llegar a conclusiones": 0.0,
    "Formular preguntas propias": 0.0,
    "Explorar la complejidad del tema": 0.0,
    "Pensar metacognitivamente": 0.0
  },
  "razonamiento": "breve análisis de qué evidencias encontraste en la conversación para justificar los scores más altos y más bajos"
}

## Ejemplo de respuesta (Few-Shot):
{
  "scores": {
    "Observar con atención y describir": 0.8,
    "Explicar y dar sentido": 0.2,
    "Justificar con evidencia": 0.0,
    "Relacionar ideas y conceptos": 0.1,
    "Considerar otras perspectivas": 0.0,
    "Identificar ideas claves y llegar a conclusiones": 0.9,
    "Formular preguntas propias": 0.0,
    "Explorar la complejidad del tema": 0.4,
    "Pensar metacognitivamente": 0.0
  },
  "razonamiento": "El alumno describió sistemáticamente las células y elaboró una conclusión fundamentada sobre su estructura."
}
""".strip()


PROMPT_QUESTIONER_EXPLORAR = """
Eres un asistente educativo conversando con un alumno sobre lo que hizo en su clase.
Todavía no tenés suficiente información para identificar qué tipo de actividad realizó.

Tu tarea es hacer UNA sola pregunta general y abierta para que el alumno cuente
más detalles sobre lo que hizo, cómo lo hizo y qué le pidieron en la actividad.

## Estilo esperado:
- Cálido y cercano, como en una conversación natural.
- Abierta: que invite al alumno a elaborar y contar más.
- Evitá preguntas de sí/no.
- Una sola pregunta, clara y directa.

## Formato de respuesta:
Responde SIEMPRE con este JSON exacto, sin texto adicional antes ni después:

{
  "pregunta": "la pregunta para el alumno",
  "razonamiento": "por qué elegiste esta pregunta dado el contexto actual"
}

## Ejemplo de respuesta (Few-Shot):
{
  "pregunta": "¿Podrías contarme un poco más sobre qué hicieron exactamente con esa imagen?",
  "razonamiento": "El alumno solo mencionó que observó una imagen, necesito que explique qué le pidió la docente."
}
""".strip()


# Este prompt se completa dinámicamente con los candidatos antes de cada llamada
PROMPT_QUESTIONER_DISCRIMINAR = """
Eres un asistente educativo conversando con un alumno sobre lo que hizo en su clase.

Basándote en la conversación hasta ahora, los movimientos de pensamiento más probables son:

{candidatos}

Tu tarea es hacer UNA sola pregunta estratégica que te permita discriminar entre
estos movimientos: es decir, que según la respuesta del alumno puedas subir el score
de uno y bajar el de los otros.

## Estilo esperado:
- Preguntá por lo concreto: qué hizo exactamente, cómo lo hizo, por qué tomó esa decisión.
- Evitá preguntas de sí/no cuando sea posible; buscá que el alumno elabore su respuesta.
- Sé cálido y cercano, como en una conversación natural.
- Una sola pregunta por turno.

## Ejemplos del estilo de preguntas esperado:
- "¿Qué te pedían hacer en esas preguntas?"
- "Cuando respondieron, ¿tuvieron que relacionar las ideas del texto con temas que ya conocían?"
- "¿Alcanzaba con una explicación simple o tuvieron que pensar varias causas o relaciones?"
- "¿La actividad los animaba a ir más allá de lo que decía el texto?"
- "Cuando completaste eso, ¿tomabas la información directamente o tuviste que analizarla y elaborar tus propias conclusiones?"

## Ejemplo de lo que DEBES hacer (few-shot):

Si los candidatos son:
- Observar con atención y describir (score: 0.70)
- Explicar y dar sentido (score: 0.60)

Tu respuesta DEBE ser EXACTAMENTE así (solo el JSON):

{{"pregunta": "¿Qué detalles específicos viste que no notaste al principio, y cómo los describirías para que otro los entienda?", "razonamiento": "Esta pregunta obliga al alumno a dar una descripción detallada (fortalece el movimiento Observar) y también a interpretar o explicar por qué esos detalles son importantes (discrimina hacia Explicar)."}}

## Formato de respuesta (OBLIGATORIO):
Responde SIEMPRE con este JSON exacto, sin texto adicional antes ni después. No agregues nada más. No uses ```json. La respuesta debe empezar con {{ y terminar con }}:

{{"pregunta": "la pregunta para el alumno", "razonamiento": "por qué esta pregunta discrimina entre los candidatos actuales"}}
""".strip()


# Este prompt se completa dinámicamente con el resultado antes de cada llamada
PROMPT_CLASIFICAR = """
Eres un asistente educativo que cierra una conversación con un alumno.
Tu tarea es generar un mensaje final claro y cálido explicando el resultado.

Movimiento de pensamiento identificado: {movimiento}
Nivel de logro: {nivel_logro}

## Instrucciones según el nivel de logro:
- Si el nivel es "esperado": felicitá al alumno y explicá brevemente con 1-2 evidencias
  concretas de la conversación que muestran ese movimiento de pensamiento.
- Si el nivel es "parcial" o "no conseguido": comunicá de manera empática que la actividad
  no alcanzó a promover plenamente ese movimiento, y explicá brevemente por qué.
- Sé cálido, claro y conciso (máximo 3-4 oraciones para el alumno).
- No uses tecnicismos; hablá en un lenguaje accesible para un estudiante.

## Formato de respuesta (OBLIGATORIO):
Responde SIEMPRE con este JSON exacto, sin texto adicional antes ni después:

{{
  "mensaje_alumno": "el mensaje completo para mostrarle al alumno",
  "razonamiento": "tu análisis final de por qué llegaste a esta conclusión"
}}

## Ejemplo de respuesta (Few-Shot):
{{
  "mensaje_alumno": "Gracias por contarlo. El principal movimiento de pensamiento que trabajaste fue observar con atención y describir. En esta actividad realizaste una observación detallada del fenómeno, atendiendo a múltiples aspectos como la forma, la disposición, la cantidad y otras características visibles. Además, estableciste comparaciones y reconociste limitaciones en lo que podía observarse.",
  "razonamiento": "El alumno alcanzó el nivel esperado ('Observar con atención y describir') detallando sistemáticamente los aspectos del fenómeno."
}}
""".strip()


# ── Funciones auxiliares ───────────────────────────────────────────────────────

def llamar_modelo(historial: list, system_prompt: str) -> str:
    """Llama al modelo vía API OpenAI-compatible y devuelve el texto crudo."""
    payload = {
        "model": MODEL_NAME,
        "messages": [{"role": "system", "content": system_prompt}] + historial,
        "temperature": 0.1,
        "max_tokens": 512,
    }
    try:
        response = requests.post(MODAL_API_URL, json=payload, timeout=180)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except requests.RequestException as e:
        print(f"[ERROR] Fallo al llamar al modelo: {e}")
        return ""

def guardar_conversacion(mensaje: dict):
    """Guarda cada mensaje (alumno o asistente) en un archivo JSON."""
    try:
        with open("conversaciones.json", "r", encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        data = []

    data.append({
        "timestamp": datetime.datetime.now().isoformat(),
        "role": mensaje.get("role"),
        "content": mensaje.get("content"),
        "turno": mensaje.get("turno")
    })

    with open("conversaciones.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def parsear_json(texto: str) -> dict | None:
    """Extrae y parsea el JSON de la respuesta del modelo."""
    try:
        # El modelo a veces envuelve el JSON en ```json ... ```
        if "```" in texto:
            texto = texto.split("```")[1]
            if texto.startswith("json"):
                texto = texto[4:]
        return json.loads(texto.strip())
    except (json.JSONDecodeError, IndexError):
        print(f"[ERROR] No se pudo parsear JSON. Respuesta cruda:\n{texto}")
        return None


def obtener_top_3(scores: dict) -> list[tuple[str, float]]:
    """Devuelve los 3 movimientos con mayor score, ordenados de mayor a menor."""
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)[:3]


def score_a_nivel_logro(score: float) -> str:
    """Convierte un score numérico al nivel de logro de la rúbrica."""
    if score >= UMBRAL_CLASIFICAR:
        return "esperado"
    elif score >= 0.50:
        return "parcial"
    else:
        return "no conseguido"


def construir_prompt_questioner(top_3: list, max_score: float) -> str:
    """
    Devuelve el prompt correcto para el Questioner según el estado actual.
    La lógica (qué prompt usar) vive aquí en el código, no en los prompts.
    """
    if max_score < UMBRAL_EXPLORAR:
        # Scores muy bajos: pedir información general
        return PROMPT_QUESTIONER_EXPLORAR
    else:
        # Scores suficientes: discriminar entre top candidatos
        candidatos_texto = "\n".join(
            [f"- {mov} (score: {score:.2f})" for mov, score in top_3]
        )
        return PROMPT_QUESTIONER_DISCRIMINAR.format(candidatos=candidatos_texto)


def mostrar_resultado(datos_cls: dict | None, movimiento: str,
                      nivel_logro: str, max_score: float) -> None:
    """Muestra el resultado final al alumno con debug info."""
    print("\n" + "═" * 55)

    if datos_cls and "mensaje_alumno" in datos_cls:
        print(f"\n{datos_cls['mensaje_alumno']}")
        print(f"\n[DEBUG] Razonamiento: {datos_cls.get('razonamiento', '?')}")
    else:
        # Fallback si el JSON del clasificador falla
        if nivel_logro == "esperado":
            print(f"\n✅ Movimiento de pensamiento alcanzado: {movimiento}")
        else:
            print(f"\n❌ No se identificó un movimiento de pensamiento alcanzado.")
            if movimiento != "ninguno":
                print(f"   (Se detectaron indicios de '{movimiento}' "
                      f"pero en nivel: {nivel_logro})")

    print(f"\n[DEBUG] Score final: {max_score:.2f} | Nivel de logro: {nivel_logro}")
    print("═" * 55)


# ── Loop principal ─────────────────────────────────────────────────────────────

def main():
    historial: list[dict] = []
    turno = 0

    print("\n😊 Hola! Contame qué hiciste hoy en clases.")
    print("   (Escribí 'salir' para terminar o 'reiniciar' para empezar de nuevo)\n")

    while True:
        # Entrada del alumno
        user_input = input("Estudiante: ").strip()

        if not user_input:
            continue
        if user_input.lower() == "salir":
            print("👋 ¡Hasta luego!")
            break
        if user_input.lower() == "reiniciar":
            historial = []
            turno = 0
            print("\n🔄 Reiniciado. Contame tu nueva actividad:\n")
            continue

        historial.append({"role": "user", "content": user_input})
        guardar_conversacion({"role": "user", "content": user_input, "turno": turno})
        turno += 1

        # ── LLAMADA 1: SCORER ─────────────────────────────────────────────────
        print("\n[...evaluando actividad...]")
        respuesta_scorer = llamar_modelo(historial, PROMPT_SCORER)
        datos_scorer = parsear_json(respuesta_scorer)

        if datos_scorer is None:
            print("[ERROR] No se pudo evaluar la actividad. Intentá de nuevo.")
            historial.pop()
            turno -= 1
            continue

        scores  = datos_scorer["scores"]
        top_3   = obtener_top_3(scores)
        max_mov, max_score = top_3[0]

        # Debug del scorer
        print(f"\n[DEBUG SCORER] Turno {turno}/{MAX_TURNOS}")
        for mov, score in top_3:
            barra = "█" * int(score * 20)
            print(f"  {score:.2f} {barra:<20} {mov}")
        print(f"  Razonamiento: {datos_scorer.get('razonamiento', '?')}\n")

        # ── DECISIÓN (lógica en código, no en prompts) ────────────────────────
        debe_clasificar = (
            max_score >= UMBRAL_CLASIFICAR   # alta confianza
            or turno >= MAX_TURNOS           # se agotaron los turnos
        )

        if debe_clasificar:
            nivel_logro = score_a_nivel_logro(max_score)
            movimiento  = max_mov if max_score > UMBRAL_EXPLORAR else "ninguno"

            # ── LLAMADA 2: CLASIFICAR ─────────────────────────────────────────
            print("[...generando resultado final...]")
            prompt_cls = PROMPT_CLASIFICAR.format(
                movimiento=movimiento,
                nivel_logro=nivel_logro,
            )
            respuesta_cls = llamar_modelo(historial, prompt_cls)
            datos_cls     = parsear_json(respuesta_cls)

            mostrar_resultado(datos_cls, movimiento, nivel_logro, max_score)

            print("\n¿Querés analizar otra actividad? Escribí 'reiniciar' o 'salir'.\n")
            # Resetear para la próxima actividad
            historial = []
            turno     = 0

        else:
            # ── LLAMADA 2: QUESTIONER ─────────────────────────────────────────
            prompt_q     = construir_prompt_questioner(top_3, max_score)
            respuesta_q  = llamar_modelo(historial, prompt_q)
            datos_q      = parsear_json(respuesta_q)

            if datos_q is None:
                print("[ERROR] No se pudo generar una pregunta. Intentá de nuevo.")
                historial.pop()
                turno -= 1
                continue

            pregunta = datos_q["pregunta"]
            historial.append({"role": "assistant", "content": pregunta})
            guardar_conversacion({"role": "user", "content": user_input, "turno": turno})

            print(f"Asistente: {pregunta}")
            print(f"[DEBUG QUESTIONER] {datos_q.get('razonamiento', '?')}\n")


if __name__ == "__main__":
    main()