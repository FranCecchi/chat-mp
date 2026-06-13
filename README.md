# Chat MP

Backend FastAPI para usar Chat MP desde una instancia local de Open WebUI.

Estado actual:

- API FastAPI.
- Endpoint de salud.
- API compatible con OpenAI en `/v1`.
- Backend de modelo vía Google GenAI.
- Streaming SSE para `/v1/chat/completions`.

No incluye:

- Bot o webhook de Telegram.
- UI propia.
- RAG.
- Base de datos.
- LangGraph.

Open WebUI mantiene el historial de conversación y lo envía en `messages`. Este backend no guarda memoria por usuario.

## Instalar y correr

Ver [INSTALL.md](./INSTALL.md).
