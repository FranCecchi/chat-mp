# Chat MP

Backend minimo para probar un bot de Telegram conectado a una API FastAPI.

Estado actual:

- API FastAPI.
- Endpoint de salud.
- Endpoint de chat conectado a un LLM compatible con la API de DeepSeek.
- Webhook de Telegram usando Bot API.
- Comando `/start` en Telegram.
- Memoria local en proceso para mantener contexto corto de conversación.
- Scoring, preguntas de seguimiento y clasificacion de movimientos de pensamiento.
- RAG con pgvector para sumar contexto desde `refs/`.
- Comandos `make` para correr, testear y registrar webhook.

Todavia no incluye:

- Base de datos para memoria conversacional persistente.
- LangGraph.

La memoria conversacional actual es volatil: se pierde si se reinicia el servidor. `/start` reinicia la conversacion del usuario en Telegram. Para usar el chat real hace falta configurar `DEEPSEEK_API_KEY`.

El contexto RAG se ingiere desde los archivos de `refs/` hacia Postgres con pgvector. Para desarrollo local:

```bash
make db-up
make ingest-rag
make run
```

Esas partes se agregan incrementalmente cuando se implementen.

## Instalar y correr

Ver [INSTALL.md](./INSTALL.md).
