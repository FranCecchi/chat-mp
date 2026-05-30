# Chat MP

Backend minimo para probar un bot de Telegram conectado a una API FastAPI.

Estado actual:

- API FastAPI.
- Endpoint de salud.
- Endpoint de chat con respuesta placeholder.
- Webhook de Telegram usando Bot API.
- Comando `/start` en Telegram.
- Memoria local en proceso para mantener contexto corto de conversación.
- Comandos `make` para correr, testear y registrar webhook.

Todavia no incluye:

- Modelo LLM.
- RAG.
- Base de datos.
- LangGraph.
- Clasificacion pedagogica real.

La memoria actual es volatil: se pierde si se reinicia el servidor. `/start` reinicia la conversacion del usuario en Telegram.

Esas partes se agregan incrementalmente cuando se implementen.

## Instalar y correr

Ver [INSTALL.md](./INSTALL.md).
