# Instalacion y uso

Este proyecto corre una API FastAPI con un bot de Telegram opcional. El chat usa
DeepSeek para responder y un RAG local con Postgres + pgvector para sumar contexto
desde archivos guardados en `refs/`.

## 1. Requisitos

- Python 3.12.
- Docker, para levantar Postgres con pgvector.
- Acceso a internet para instalar dependencias.
- API key de DeepSeek para probar el chat real.
- Token de Telegram BotFather solo si vas a probar Telegram.
- ngrok solo si vas a probar Telegram local con webhook.

## 2. Instalar dependencias

```bash
make install
```

Si falla porque falta `ensurepip`, instalar el paquete de sistema y volver a correr
`make install`:

```bash
sudo apt install python3.12-venv
```

La instalacion incluye dependencias pesadas para RAG local, como
`sentence-transformers`. La primera ingestion tambien puede descargar el modelo de
embeddings configurado en `.env`.

## 3. Configurar `.env`

Crear el archivo local:

```bash
cp .env.example .env
```

Para usar el chat real, completar:

```text
DEEPSEEK_API_KEY="tu-api-key"
DEEPSEEK_BASE_URL="https://api.deepseek.com"
DEEPSEEK_MODEL="deepseek-chat"
```

Para RAG local, podés dejar estos defaults:

```text
DATABASE_URL="postgresql://chatmp:chatmp@localhost:5432/chatmp"
RAG_ENABLED=true
RAG_TOP_K=5
RAG_FAIL_OPEN=true
EMBEDDING_MODEL="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
EMBEDDING_DIMENSION=384
```

Qué significan:

- `DATABASE_URL`: conexion a Postgres con pgvector.
- `RAG_ENABLED`: prende o apaga la recuperacion de contexto.
- `RAG_TOP_K`: cantidad de fragmentos recuperados por mensaje.
- `RAG_FAIL_OPEN`: si algo falla en RAG, el chat sigue sin contexto.
- `EMBEDDING_MODEL`: modelo local para crear embeddings.
- `EMBEDDING_DIMENSION`: dimension del modelo; el default MiniLM usa `384`.

Para Telegram, completar solo si vas a usar el bot:

```text
TELEGRAM_BOT_TOKEN="token-de-botfather"
TELEGRAM_WEBHOOK_SECRET="un-string-largo-privado"
```

## 4. Donde poner tus archivos para RAG

Poné tus archivos dentro de la carpeta:

```text
refs/
```

Formatos soportados ahora:

- `.pdf`: se extrae texto por pagina y se divide en fragmentos.
- `.csv`: se indexan filas sanitizadas.

El CSV no se guarda completo en el contexto. Se usan solo estos datos:

- asignatura,
- descripcion de la actividad,
- opciones de pensamiento seleccionadas,
- reflexion del alumno.

No se indexa la marca temporal.

Ejemplo de estructura:

```text
refs/
  4. Rúbrica de Movimiento de Pensamiento 2-5-26.pdf
  Chat MP IA.pdf
  ¿Qué hiciste hoy en clases_ (respuestas) - Respuestas de formulario 1.csv
```

Cada vez que agregues, borres o cambies archivos en `refs/`, volvé a correr la
ingestion:

```bash
make ingest-rag
```

## 5. Levantar la base RAG

Levantar Postgres con pgvector:

```bash
make db-up
```

Esto usa `docker-compose.yml` y deja Postgres escuchando en `localhost:5432`.

Para apagarlo:

```bash
make db-down
```

## 6. Ingerir tus archivos

Con la base levantada, correr:

```bash
make ingest-rag
```

Esto hace:

1. Lee PDFs y CSVs desde `refs/`.
2. Divide el texto en fragmentos.
3. Crea embeddings locales.
4. Crea la tabla `rag_chunks` si no existe.
5. Guarda los fragmentos en Postgres con pgvector.

La ingestion es idempotente: si la corrés varias veces, actualiza fragmentos ya
existentes usando un hash de contenido.

## 7. Correr la API

```bash
make run
```

La API queda en:

```text
http://127.0.0.1:8000
```

Probar salud:

```bash
make health
```

Probar chat por HTTP:

```bash
curl -X POST http://127.0.0.1:8000/chat/message \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "dev",
    "conversation_id": null,
    "message": "Hoy analizamos un texto y tuvimos que justificar una respuesta con evidencia."
  }'
```

El RAG no aparece en la respuesta. Se usa internamente para enriquecer los prompts
que van a DeepSeek.

## 8. Flujo normal de uso

Primera vez:

```bash
make install
cp .env.example .env
# editar .env y completar DEEPSEEK_API_KEY
make db-up
make ingest-rag
make run
```

Cuando cambian los archivos de `refs/`:

```bash
make ingest-rag
```

Cuando solo querés volver a correr la API:

```bash
make db-up
make run
```

Si querés probar sin RAG:

```text
RAG_ENABLED=false
```

## 9. Telegram local

Para probar Telegram localmente no hace falta deploy. Se usa ngrok como tunel
temporal.

Terminal 1: correr la API.

```bash
make run
```

Terminal 2: abrir ngrok.

```bash
ngrok http 8000
```

Copiar la URL HTTPS que muestra ngrok, por ejemplo:

```text
https://nervously-unbeaded-nakisha.ngrok-free.dev
```

Registrar el webhook:

```bash
make webhook URL=https://TU_URL_NGROK/telegram/webhook
```

Ver estado del webhook:

```bash
make webhook-info
```

Borrar webhook:

```bash
make webhook-delete
```

Para probarlo, mandar un mensaje al bot desde Telegram. En la terminal de
`make run` deberia verse un `POST /telegram/webhook` y el bot deberia responder.

El comando `/start` saluda y reinicia la memoria local de esa conversacion.

## 10. Tests

```bash
make test
```

Los tests no requieren Postgres ni descargar el modelo de embeddings. La parte RAG
pesada se prueba con mocks y funciones puras.

## 11. Comandos disponibles

```bash
make help
```
