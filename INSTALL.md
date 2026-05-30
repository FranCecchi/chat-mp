# Instalacion y ejecucion

## Requisitos

- Python 3.12
- Acceso a internet para instalar dependencias
- Token de Telegram BotFather si se va a probar el bot
- ngrok si se va a probar Telegram local con webhook

## Instalar

```bash
make install
```

Si `make install` falla porque falta `ensurepip`, instalar el paquete de sistema correspondiente y volver a correr `make install`:

```bash
sudo apt install python3.12-venv
```

## Configurar

```bash
cp .env.example .env
```

Completar en `.env` si se va a usar Telegram:

```text
TELEGRAM_BOT_TOKEN
TELEGRAM_WEBHOOK_SECRET
```

`TELEGRAM_BOT_TOKEN` se obtiene en Telegram hablando con `@BotFather`.
`TELEGRAM_WEBHOOK_SECRET` puede ser cualquier string largo y privado.

## Correr la API

```bash
make run
```

La API queda en:

```text
http://127.0.0.1:8000
```

En otra terminal, probar:

```bash
make health
```

## Registrar webhook de Telegram

Para probar Telegram localmente no hace falta deploy. Se usa ngrok como tunel temporal.

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

Para probarlo, mandar un mensaje al bot desde Telegram. En la terminal de `make run` deberia verse un `POST /telegram/webhook` y el bot deberia responder.

El comando `/start` saluda y reinicia la memoria local de esa conversacion.

## Tests

```bash
make test
```

## Comandos disponibles

```bash
make help
```
