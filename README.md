# Chatbot Conversacional para Clasificación de Movimientos de Pensamiento

## 1. Descripción general

El proyecto consiste en un sistema conversacional que permite a estudiantes o docentes describir actividades realizadas en clase. A partir de ese relato, el sistema realiza preguntas de seguimiento y clasifica la actividad dentro de distintos **movimientos de pensamiento**, usando como base una rúbrica pedagógica y ejemplos provistos por especialistas.

El sistema no debe funcionar como un chatbot genérico, sino como un **asistente guiado**, orientado a:

- comprender qué actividad se realizó;
- identificar qué tipo de pensamiento promovió;
- hacer preguntas aclaratorias cuando falte información;
- clasificar el movimiento de pensamiento;
- justificar la clasificación;
- marcar casos ambiguos para revisión humana.

Fuentes iniciales del conocimiento pedagógico:

- `4. Rúbrica de Movimiento de Pensamiento 2-5-26.pdf`
- `Chat MP IA.pdf`
- `¿Qué hiciste hoy en clases_ (respuestas) - Respuestas de formulario 1.csv`

La rúbrica define los movimientos de pensamiento y sus niveles de logro: **logro esperado**, **logro parcial** y **logro no conseguido**.

El documento de ejemplos contiene diálogos esperados entre estudiante e IA para casos positivos, parciales y negativos de promoción de movimientos de pensamiento.

---

## 2. Objetivo del sistema

Construir un backend conversacional capaz de:

1. Recibir mensajes de usuarios.
2. Mantener conversaciones multi-turno.
3. Hacer preguntas de seguimiento.
4. Consultar una base documental mediante RAG.
5. Clasificar actividades según una rúbrica de movimientos de pensamiento.
6. Guardar conversaciones, respuestas y clasificaciones.
7. Usar un modelo local desplegado en RunPod.
8. Permitir fine-tuning futuro con ejemplos revisados por profesoras.

---

## 3. Alcance del MVP

El MVP estará enfocado en conversación por texto.

Incluye:

- chat multi-turno;
- backend en FastAPI;
- flujo conversacional con LangGraph;
- RAG con LangChain;
- PostgreSQL + PGVector;
- modelo local en RunPod;
- clasificación estructurada en JSON;
- guardado de conversaciones;
- carga inicial de rúbrica y ejemplos;
- revisión humana de casos ambiguos.

No incluye inicialmente:

- audio;
- imágenes;
- OCR;
- multimodalidad;
- dashboard avanzado;
- analíticas complejas;
- integración con LMS;
- roles institucionales avanzados;
- fine-tuning completo desde el día uno.

---

## 4. Stack tecnológico

### 4.1 Backend

```text
FastAPI
```

FastAPI será el framework principal del backend.

Responsabilidades:

- exponer endpoints HTTP;
- recibir mensajes del chat;
- manejar sesiones conversacionales;
- conectar con LangGraph;
- llamar al sistema RAG;
- llamar al modelo en RunPod;
- validar respuestas del modelo;
- persistir mensajes y clasificaciones.

---

### 4.2 Orquestación conversacional

```text
LangGraph
```

LangGraph se usará para manejar el flujo multi-turno de la conversación.

El sistema no será una llamada simple al modelo, sino un workflow con estados.

Estados principales:

```text
START
↓
WAITING_INITIAL_INPUT
↓
ANALYZING_ACTIVITY
↓
RETRIEVING_RAG_CONTEXT
↓
DECIDING_NEXT_STEP
↓
ASKING_FOLLOWUP
↓
WAITING_FOLLOWUP_RESPONSE
↓
CLASSIFYING
↓
CONFIRMING_OR_SAVING
↓
COMPLETED
```

LangGraph permitirá controlar:

- cuándo preguntar más;
- cuándo clasificar;
- cuándo marcar revisión humana;
- cuántos turnos máximos permitir;
- qué información se guarda entre turnos;
- qué contexto se recupera del RAG;
- cómo se actualiza el estado de la conversación.

---

### 4.3 RAG e integración IA

```text
LangChain
```

LangChain se usará como capa de integración para:

- cargar documentos;
- dividir documentos en chunks;
- generar embeddings;
- consultar PGVector;
- construir retrievers;
- componer prompts;
- parsear salidas JSON;
- conectar con el modelo local.

---

### 4.4 Base de datos

```text
PostgreSQL + PGVector
```

PostgreSQL será la base principal del sistema.

PGVector se usará para almacenar embeddings y realizar búsqueda semántica sobre:

- rúbrica;
- ejemplos docentes;
- casos positivos;
- casos negativos;
- respuestas reales;
- documentos pedagógicos futuros.

Aunque SQLite sería más simple, se decide usar PostgreSQL + PGVector porque el proyecto busca incorporar RAG de forma real y útil.

Ventajas:

- datos relacionales y embeddings en una sola base;
- mejor camino a producción;
- mejor soporte para concurrencia;
- integración directa con RAG;
- arquitectura más defendible para portfolio freelance y mercado laboral.

---

### 4.5 Modelo de lenguaje

```text
Modelo local desplegado en RunPod
```

El modelo se ejecutará en RunPod, expuesto como endpoint HTTP.

Primera etapa:

```text
Modelo instructivo local + RAG + prompts estructurados
```

Etapa posterior:

```text
Modelo fine-tuneado con conversaciones revisadas por profesoras
```

Modelos posibles:

- Llama;
- Qwen;
- Mistral;
- Gemma.

---

## 5. Arquitectura general

```text
Usuario
   ↓
Telegram / Web Chat
   ↓
FastAPI Backend
   ↓
LangGraph Conversation Workflow
   ↓
LangChain RAG Pipeline
   ↓
PostgreSQL + PGVector
   ↓
RunPod Model Endpoint
   ↓
Modelo local / fine-tuneado
   ↓
Clasificación JSON
   ↓
Base de datos
```

Versión más detallada:

```text
Usuario
   ↓
Chat Interface
   ↓
POST /chat/message
   ↓
FastAPI
   ↓
Conversation Service
   ↓
LangGraph
   ├── receive_message
   ├── normalize_input
   ├── retrieve_rag_context
   ├── analyze_activity
   ├── decide_next_step
   ├── generate_followup_question
   ├── classify_movement
   └── save_result
   ↓
LangChain Retriever
   ↓
PostgreSQL + PGVector
   ↓
RunPod Endpoint
   ↓
Modelo local
```

---

## 6. Por qué usar RAG

RAG se usará para que el modelo no dependa únicamente de su entrenamiento interno.

El modelo deberá consultar:

- rúbrica;
- niveles de logro;
- ejemplos positivos;
- ejemplos negativos;
- diálogos esperados;
- respuestas reales;
- criterios de clasificación.

Esto permite:

- mayor trazabilidad;
- actualización de criterios sin reentrenar;
- respuestas más alineadas con la guía docente;
- mejor justificación de clasificaciones;
- menor riesgo de invención;
- uso práctico de LangChain, LangGraph y RAG como arquitectura moderna.

---

## 7. Documentos que van al RAG

### 7.1 Rúbrica

La rúbrica debe cargarse como fuente prioritaria.

Cada movimiento debe dividirse en chunks por:

```text
movimiento
definición
logro esperado
logro parcial
logro no conseguido
```

Ejemplo conceptual:

```json
{
  "type": "rubric",
  "movement": "Justificar con evidencia",
  "level": "logro esperado",
  "content": "La actividad requiere que los estudiantes fundamenten sus ideas mediante el uso de dos o más evidencias pertinentes..."
}
```

---

### 7.2 Ejemplos conversacionales

Cada caso debe cargarse como documento separado.

Estructura sugerida:

```json
{
  "type": "example_dialogue",
  "case_id": "caso_7",
  "movement": "Justificar con evidencia",
  "outcome": "promueve",
  "student_input": "Hoy analizamos el impacto de los desmontes...",
  "assistant_question": "¿Usaste algún dato, ejemplo o referencia concreta?",
  "expected_response": "El movimiento trabajado fue justificar con evidencia..."
}
```

---

### 7.3 Casos negativos

Los casos negativos son especialmente importantes porque enseñan al sistema a no sobreclasificar.

Ejemplo:

```json
{
  "type": "negative_example",
  "movement": "Explicar y dar sentido",
  "reason": "La actividad solo reformula superficialmente el texto.",
  "expected_classification": "no promovido"
}
```

---

### 7.4 Respuestas reales de estudiantes

El CSV de respuestas reales puede usarse como fuente secundaria.

Uso recomendado:

```text
Rúbrica = autoridad principal
Ejemplos docentes = referencia fuerte
CSV real = lenguaje real y casos de prueba
```

El CSV servirá para:

- evaluar prompts;
- crear casos de prueba;
- detectar lenguaje natural de estudiantes;
- enriquecer ejemplos;
- construir dataset futuro para fine-tuning.

---

## 8. Movimientos de pensamiento

Los movimientos definidos en la rúbrica son:

1. Observar con atención y describir.
2. Explicar y dar sentido.
3. Justificar con evidencia.
4. Relacionar ideas y conceptos.
5. Considerar otras perspectivas.
6. Identificar ideas claves y llegar a conclusiones.
7. Formular preguntas propias.
8. Explorar la complejidad del tema.
9. Pensar metacognitivamente.

---

## 9. Criterios por movimiento

### 9.1 Observar con atención y describir

Implica observar partes y características de un fenómeno, describiéndolo de forma detallada y completa.

Indicadores:

- descripción de forma;
- tamaño;
- disposición;
- cantidad;
- características visibles;
- diferencias entre partes;
- observación sistemática.

No alcanza con:

- nombrar partes;
- copiar etiquetas;
- reconocer elementos generales;
- dibujar sin describir;
- identificar sin caracterizar.

---

### 9.2 Explicar y dar sentido

Implica construir significados o interpretaciones propias sobre un fenómeno, proceso o concepto.

Indicadores:

- explicar con palabras propias;
- interpretar;
- reorganizar información;
- explicar causas;
- explicar funcionamiento;
- explicar propósito;
- conectar conceptos.

No alcanza con:

- cambiar algunas palabras del texto;
- copiar definiciones;
- repetir información;
- hacer una reformulación superficial.

---

### 9.3 Justificar con evidencia

Implica fundamentar afirmaciones usando datos, hechos, referencias o ejemplos relevantes.

Indicadores:

- uso de datos;
- informes;
- evidencias concretas;
- ejemplos pertinentes;
- relación entre evidencia y argumento;
- fundamentación explícita.

No alcanza con:

- dar una opinión;
- contar una experiencia aislada;
- mencionar algo observado sin conectarlo con evidencia;
- afirmar sin respaldo.

---

### 9.4 Relacionar ideas y conceptos

Implica conectar conocimientos nuevos con saberes previos o aplicar conceptos a situaciones nuevas.

Indicadores:

- conectar temas vistos antes;
- aplicar ideas a otro contexto;
- explicar relaciones entre conceptos;
- transferir conocimiento;
- integrar conceptos en una red de sentido.

No alcanza con:

- repetir el texto;
- organizar información;
- mencionar conceptos sin vincularlos;
- listar datos aislados.

---

### 9.5 Considerar otras perspectivas

Implica reconocer y analizar diferentes miradas, enfoques o intereses.

Indicadores:

- comparar perspectivas;
- analizar ventajas y desventajas;
- reconocer implicancias;
- tomar postura fundamentada;
- evaluar enfoques diferentes.

No alcanza con:

- completar un cuadro copiando información;
- listar perspectivas sin analizarlas;
- reconocer posturas de forma superficial;
- presentar una única mirada.

---

### 9.6 Identificar ideas claves y llegar a conclusiones

Implica distinguir lo esencial de lo secundario y elaborar conclusiones propias.

Indicadores:

- identificar ideas principales;
- sintetizar;
- distinguir lo central de lo accesorio;
- construir conclusiones;
- fundamentar conclusiones.

No alcanza con:

- recopilar información;
- listar datos;
- hacer conclusiones superficiales;
- reorganizar información sin elaboración propia.

---

### 9.7 Formular preguntas propias

Implica crear preguntas que promuevan indagación, curiosidad y búsqueda de sentido.

Indicadores:

- preguntas propias;
- preguntas investigables;
- preguntas que van más allá del texto;
- preguntas relevantes;
- preguntas desafiantes;
- preguntas que abren nuevas líneas de exploración.

No alcanza con:

- preguntas literales;
- preguntas obvias;
- preguntas fuertemente guiadas por la docente;
- preguntas solo para verificar comprensión básica.

---

### 9.8 Explorar la complejidad del tema

Implica analizar múltiples factores, relaciones y tensiones de un fenómeno.

Indicadores:

- múltiples causas;
- relaciones entre factores;
- dimensiones conectadas;
- tensiones;
- análisis profundo;
- evitar explicaciones simplificadas.

No alcanza con:

- describir varios factores por separado;
- listar aspectos sin conectarlos;
- reproducir información;
- hacer un tratamiento meramente descriptivo.

---

### 9.9 Pensar metacognitivamente

Implica reflexionar sobre el propio proceso de aprendizaje.

Indicadores:

- identificar estrategias usadas;
- evaluar si sirvieron;
- pensar cómo mejorar;
- monitorear la comprensión;
- planificar próximas acciones;
- analizar el propio proceso.

No alcanza con:

- contar qué se hizo;
- listar pasos realizados;
- decir si el trabajo quedó completo o no;
- mencionar estrategias sin evaluarlas.

---

## 10. Flujo conversacional esperado

### 10.1 Inicio

El usuario describe la actividad.

```text
Usuario:
Hoy en clase leímos un texto y respondimos preguntas.
```

El sistema analiza si hay información suficiente.

---

### 10.2 Pregunta de seguimiento

Si falta información, el sistema pregunta.

```text
IA:
¿Para responder tuvieron que interpretar y relacionar ideas, o las respuestas estaban directamente en el texto?
```

---

### 10.3 Respuesta del usuario

```text
Usuario:
Más que nada estaban en el texto. Las copiamos.
```

---

### 10.4 Clasificación

```text
IA:
Gracias por contarlo. En este caso, la actividad se basa principalmente en recuperar información explícita. No se evidencia un movimiento de pensamiento significativo porque no requirió interpretar, relacionar ideas, justificar ni elaborar conclusiones propias.
```

---

## 11. Lógica de decisión

El sistema debe decidir entre:

```text
preguntar más
clasificar
marcar revisión humana
```

### Preguntar más cuando:

```text
confidence < 0.75
```

o:

```text
missing_information no está vacío
```

o:

```text
hay varios movimientos candidatos con puntajes similares
```

---

### Clasificar cuando:

```text
confidence >= 0.75
```

y:

```text
hay evidencia suficiente en el relato
```

---

### Marcar revisión humana cuando:

```text
confidence < 0.65
```

o:

```text
el caso es ambiguo
```

o:

```text
el usuario da respuestas contradictorias
```

o:

```text
se alcanza el máximo de preguntas sin claridad
```

---

## 12. Cantidad máxima de turnos

Para evitar conversaciones largas o confusas:

```text
Máximo recomendado: 3 preguntas de seguimiento
```

Si luego de 3 preguntas no hay claridad:

```json
{
  "needs_review": true,
  "reason": "No se obtuvo información suficiente para clasificar con confianza."
}
```

---

## 13. Salida esperada del modelo

El modelo debe devolver siempre JSON estructurado.

Ejemplo cuando todavía falta información:

```json
{
  "detected_activity": "Lectura de texto y respuesta de preguntas",
  "candidate_movements": [
    {
      "name": "Explicar y dar sentido",
      "score": 0.42,
      "evidence": [
        "El usuario menciona que respondió preguntas sobre un texto."
      ]
    },
    {
      "name": "Identificar ideas claves y llegar a conclusiones",
      "score": 0.38,
      "evidence": [
        "Podría haber identificación de ideas, pero no hay evidencia de conclusiones propias."
      ]
    }
  ],
  "missing_information": [
    "No queda claro si las respuestas requerían interpretación o copia literal."
  ],
  "next_question": "¿Las respuestas estaban directamente en el texto o tuvieron que explicarlas con sus propias palabras?",
  "ready_to_classify": false,
  "final_classification": null,
  "needs_review": false
}
```

Ejemplo cuando ya puede clasificar:

```json
{
  "detected_activity": "Comparación de estrategias de resolución",
  "candidate_movements": [
    {
      "name": "Relacionar ideas y conceptos",
      "score": 0.78,
      "evidence": [
        "El estudiante conectó estrategias distintas para resolver un problema."
      ]
    },
    {
      "name": "Justificar con evidencia",
      "score": 0.82,
      "evidence": [
        "El estudiante explicó cuál estrategia era más clara y por qué."
      ]
    }
  ],
  "missing_information": [],
  "next_question": null,
  "ready_to_classify": true,
  "final_classification": {
    "movement": "Justificar con evidencia",
    "level": "logro esperado",
    "confidence": 0.82,
    "justification": "La actividad requiere fundamentar una elección usando razones explícitas.",
    "needs_review": false
  }
}
```

---

## 14. Diseño de LangGraph

### 14.1 Estado conversacional

```python
from typing import Optional, List, Dict
from pydantic import BaseModel

class ConversationState(BaseModel):
    conversation_id: str
    user_id: str
    messages: List[Dict]
    current_state: str
    retrieved_context: Optional[str] = None
    detected_activity: Optional[str] = None
    candidate_movements: List[Dict] = []
    missing_information: List[str] = []
    next_question: Optional[str] = None
    final_classification: Optional[Dict] = None
    followup_count: int = 0
    needs_review: bool = False
```

---

### 14.2 Nodos principales

```text
receive_message
normalize_input
retrieve_rag_context
analyze_activity
decide_next_step
generate_followup_question
classify_movement
validate_output
save_message
save_classification
```

---

### 14.3 Flujo conceptual

```text
receive_message
   ↓
normalize_input
   ↓
retrieve_rag_context
   ↓
analyze_activity
   ↓
decide_next_step
   ├── ask_more → generate_followup_question → save_message
   ├── classify → classify_movement → validate_output → save_classification
   └── review → save_classification_with_review_flag
```

---

## 15. Diseño del RAG

### 15.1 Pipeline de ingesta

```text
PDF / CSV / DOCX
   ↓
loader
   ↓
limpieza de texto
   ↓
chunking
   ↓
embeddings
   ↓
PostgreSQL + PGVector
```

---

### 15.2 Chunking recomendado

Para la rúbrica:

```text
1 chunk por movimiento y nivel de logro
```

Ejemplo:

```text
Movimiento: Formular preguntas propias
Nivel: logro esperado
Contenido: La actividad fomenta de manera explícita la formulación de preguntas relevantes y desafiantes...
```

Para ejemplos:

```text
1 chunk por caso conversacional
```

Ejemplo:

```text
Caso 17
Movimiento: Formular preguntas propias
Resultado: promueve
Diálogo completo
Respuesta esperada
```

Para respuestas reales:

```text
1 chunk por respuesta completa del formulario
```

---

### 15.3 Metadata por chunk

Para rúbrica:

```json
{
  "source": "rubrica_movimientos.pdf",
  "type": "rubric",
  "movement": "Formular preguntas propias",
  "level": "logro esperado",
  "case_id": null,
  "outcome": "expected"
}
```

Para ejemplos:

```json
{
  "source": "chat_mp_ia.pdf",
  "type": "example_dialogue",
  "movement": "Justificar con evidencia",
  "case_id": "caso_7",
  "outcome": "promueve"
}
```

Para respuestas reales:

```json
{
  "source": "respuestas_formulario.csv",
  "type": "real_student_response",
  "movement": null,
  "level": null,
  "reviewed": false
}
```

---

### 15.4 Retrieval

Configuración inicial:

```text
top_k = 4
```

Distribución ideal:

```text
2 chunks de rúbrica
2 chunks de ejemplos
```

El prompt debería recibir:

- relato del usuario;
- historial resumido de la conversación;
- chunks relevantes de rúbrica;
- ejemplos similares;
- lista de movimientos posibles;
- formato JSON obligatorio.

---

## 16. Prompt base del sistema

```text
Sos un asistente pedagógico especializado en identificar movimientos de pensamiento en actividades escolares.

Tu tarea es analizar relatos de actividades realizadas en clase y guiar al usuario con preguntas simples hasta obtener información suficiente para clasificar la actividad.

Usá únicamente los movimientos de pensamiento definidos en la rúbrica.

No inventes información.
No asumas que una actividad promueve pensamiento solo porque menciona una acción compleja.
Diferenciá entre logro esperado, logro parcial y logro no conseguido.

Si falta información, hacé una sola pregunta clara.
Si ya hay información suficiente, clasificá la actividad.
Siempre justificá la clasificación con evidencia del relato del usuario.
Siempre devolvé JSON válido.
```

---

## 17. Fine-tuning

El fine-tuning no reemplaza al RAG.

Ambos cumplen funciones distintas:

```text
RAG:
Consulta criterios, rúbricas y ejemplos actualizados.

Fine-tuning:
Enseña al modelo el estilo de razonamiento, clasificación y respuesta esperada.
```

### Estrategia recomendada

Primera etapa:

```text
RAG + prompts + JSON estricto
```

Segunda etapa:

```text
conversaciones revisadas por profesoras
↓
dataset curado
↓
fine-tuning
↓
modelo especializado
```

El dataset de fine-tuning debería incluir:

```json
{
  "conversation": [
    {
      "role": "student",
      "content": "Hoy comparamos dos formas de resolver un problema..."
    },
    {
      "role": "assistant",
      "content": "¿Tuvieron que justificar cuál era mejor?"
    },
    {
      "role": "student",
      "content": "Sí, explicamos cuál era más clara y por qué."
    }
  ],
  "expected_output": {
    "movement": "Justificar con evidencia",
    "level": "logro esperado",
    "confidence": 0.86,
    "evidence": [
      "compararon dos formas",
      "justificaron una elección"
    ],
    "needs_review": false
  }
}
```

---

## 18. Modelo de datos

### 18.1 users

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY,
    name TEXT,
    role TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT now()
);
```

Roles posibles:

```text
student
teacher
admin
```

---

### 18.2 conversations

```sql
CREATE TABLE conversations (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    status TEXT NOT NULL,
    current_state TEXT NOT NULL,
    summary TEXT,
    followup_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now()
);
```

---

### 18.3 messages

```sql
CREATE TABLE messages (
    id UUID PRIMARY KEY,
    conversation_id UUID NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT now()
);
```

Roles:

```text
user
assistant
system
```

---

### 18.4 thinking_movements

```sql
CREATE TABLE thinking_movements (
    id UUID PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT now()
);
```

---

### 18.5 movement_rubric_levels

```sql
CREATE TABLE movement_rubric_levels (
    id UUID PRIMARY KEY,
    movement_id UUID NOT NULL,
    level TEXT NOT NULL,
    criteria TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT now()
);
```

Niveles:

```text
expected
partial
not_achieved
```

---

### 18.6 classifications

```sql
CREATE TABLE classifications (
    id UUID PRIMARY KEY,
    conversation_id UUID NOT NULL,
    movement_id UUID,
    level TEXT,
    confidence NUMERIC,
    justification TEXT,
    evidence JSONB,
    needs_review BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT now()
);
```

---

### 18.7 rag_documents

```sql
CREATE TABLE rag_documents (
    id UUID PRIMARY KEY,
    source_name TEXT NOT NULL,
    source_type TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT now()
);
```

---

### 18.8 rag_chunks

```sql
CREATE TABLE rag_chunks (
    id UUID PRIMARY KEY,
    document_id UUID NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB,
    embedding VECTOR,
    created_at TIMESTAMP DEFAULT now()
);
```

---

## 19. Endpoints principales

### 19.1 Enviar mensaje al chat

```http
POST /chat/message
```

Request:

```json
{
  "user_id": "uuid",
  "conversation_id": "uuid",
  "message": "Hoy comparamos dos textos y explicamos diferencias."
}
```

Response:

```json
{
  "conversation_id": "uuid",
  "reply": "¿Tuvieron que explicar por qué esas diferencias eran importantes o solo identificarlas?",
  "state": "ASKING_FOLLOWUP",
  "classification": null
}
```

---

### 19.2 Obtener conversación

```http
GET /conversations/{conversation_id}
```

---

### 19.3 Obtener mensajes

```http
GET /conversations/{conversation_id}/messages
```

---

### 19.4 Obtener clasificación

```http
GET /conversations/{conversation_id}/classification
```

---

### 19.5 Cargar documentos al RAG

```http
POST /admin/rag/documents
```

---

### 19.6 Reprocesar embeddings

```http
POST /admin/rag/reindex
```

---

### 19.7 Revisar clasificación

```http
POST /admin/classifications/{classification_id}/review
```

---

## 20. Estructura de carpetas

```text
app/
├── main.py
├── api/
│   ├── chat.py
│   ├── conversations.py
│   ├── classifications.py
│   └── admin.py
├── core/
│   ├── config.py
│   ├── database.py
│   └── logging.py
├── models/
│   ├── user.py
│   ├── conversation.py
│   ├── message.py
│   ├── movement.py
│   ├── classification.py
│   └── rag.py
├── schemas/
│   ├── chat.py
│   ├── conversation.py
│   ├── classification.py
│   └── rag.py
├── services/
│   ├── conversation_service.py
│   ├── model_service.py
│   ├── rag_service.py
│   ├── classification_service.py
│   └── movement_service.py
├── graph/
│   ├── state.py
│   ├── nodes.py
│   └── workflow.py
├── rag/
│   ├── loaders.py
│   ├── chunking.py
│   ├── embeddings.py
│   └── retriever.py
├── prompts/
│   ├── analyze_activity.txt
│   ├── generate_followup.txt
│   ├── classify_movement.txt
│   └── system.txt
└── tests/
    ├── test_chat_flow.py
    ├── test_rag.py
    └── test_classification.py
```

---

## 21. RunPod

RunPod será usado para desplegar el modelo local como endpoint.

### Responsabilidad de RunPod

```text
recibir prompt
↓
ejecutar modelo local
↓
devolver JSON
```

### Responsabilidad de FastAPI

```text
recibir mensaje
↓
manejar conversación
↓
consultar RAG
↓
armar prompt
↓
llamar a RunPod
↓
validar respuesta
↓
guardar resultado
```

RunPod no debe manejar la lógica de negocio. Solo debe servir el modelo.

---

## 22. Validación de respuestas

Toda respuesta del modelo debe validarse con Pydantic.

Si el JSON es inválido:

```text
1. reintentar con prompt de corrección;
2. si falla, marcar revisión humana;
3. guardar error para debugging.
```

---

## 23. Revisión humana

La revisión humana es importante porque se trata de un sistema pedagógico.

Casos que requieren revisión:

- baja confianza;
- ambigüedad entre movimientos;
- clasificación contradictoria;
- usuario no da suficiente información;
- salida inválida del modelo;
- caso nuevo no cubierto por ejemplos;
- posible error de interpretación.

---

## 24. MVP

El MVP debe incluir:

```text
FastAPI backend
LangGraph workflow
LangChain RAG
PostgreSQL + PGVector
Carga de rúbrica
Carga de ejemplos docentes
Chat por texto
Modelo local en RunPod
Salida JSON validada
Guardado de conversación
Guardado de clasificación
Marcado de revisión humana
```

---

## 25. Roadmap

### Fase 1 — MVP técnico

```text
- FastAPI
- PostgreSQL + PGVector
- ingesta de rúbrica
- RAG básico
- LangGraph multi-turno
- modelo en RunPod
- clasificación JSON
```

---

### Fase 2 — Validación pedagógica

```text
- cargar más ejemplos docentes
- probar con respuestas reales
- revisar clasificaciones con profesoras
- ajustar prompts
- ajustar chunking y retrieval
```

---

### Fase 3 — Dataset

```text
- guardar conversaciones reales
- agregar correcciones docentes
- construir dataset supervisado
- separar train / validation / test
```

---

### Fase 4 — Fine-tuning

```text
- entrenar modelo con ejemplos curados
- comparar contra modelo base
- medir precisión por movimiento
- mantener RAG como fuente actualizable
```

---

### Fase 5 — Producto

```text
- panel docente
- gestión de aulas
- reportes
- métricas por movimiento
- exportación de resultados
- despliegue estable
```

---

## 26. Métricas de evaluación

### 26.1 Métricas técnicas

```text
- porcentaje de JSON válido
- latencia promedio
- cantidad de turnos por conversación
- tasa de fallback a revisión humana
```

### 26.2 Métricas pedagógicas

```text
- accuracy por movimiento
- acuerdo con profesoras
- falsos positivos
- falsos negativos
- confusión entre movimientos similares
```

### 26.3 Métricas de RAG

```text
- relevancia de chunks recuperados
- cobertura de la rúbrica
- recuperación de ejemplos similares
- calidad de justificación usando contexto
```

---

## 27. Decisiones de arquitectura

### Decisión 1: usar FastAPI

Motivo:

```text
Compatible con Python, IA, Pydantic, LangChain y LangGraph.
```

---

### Decisión 2: usar LangGraph

Motivo:

```text
El sistema necesita conversación multi-turno con estados y decisiones controladas.
```

---

### Decisión 3: usar LangChain

Motivo:

```text
Facilita la implementación de RAG, retrievers, prompts y parsers.
```

---

### Decisión 4: usar PostgreSQL + PGVector

Motivo:

```text
Permite guardar datos relacionales y embeddings en una sola base.
```

---

### Decisión 5: usar RAG desde el inicio

Motivo:

```text
La rúbrica y los ejemplos docentes son conocimiento externo que debe poder actualizarse sin reentrenar el modelo.
```

---

### Decisión 6: usar RunPod para el modelo

Motivo:

```text
Permite correr un modelo local o fine-tuneado en GPU sin depender de APIs cerradas.
```

---

### Decisión 7: postergar fine-tuning completo

Motivo:

```text
Primero se necesitan ejemplos revisados y dataset confiable.
```

---

## 28. Resumen ejecutivo

El sistema será un backend conversacional educativo que clasifica actividades escolares según movimientos de pensamiento.

La arquitectura elegida es:

```text
FastAPI
+ LangGraph
+ LangChain
+ PostgreSQL/PGVector
+ RAG
+ RunPod
+ modelo local
+ fine-tuning futuro
```

La rúbrica funciona como fuente normativa.

Los ejemplos docentes funcionan como casos guía.

Las respuestas reales sirven para evaluación y futuro entrenamiento.

El objetivo del MVP no es construir un chatbot libre, sino un flujo conversacional controlado que haga buenas preguntas, clasifique con evidencia y permita revisión humana.
