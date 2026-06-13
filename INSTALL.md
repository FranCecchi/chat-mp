# Instalacion y ejecucion

Esta guia deja corriendo Chat MP con Open WebUI local, Google GenAI y las referencias del proyecto como contexto RAG.

## Requisitos

- Python 3.12.
- Docker Desktop instalado y funcionando.
- WSL/Ubuntu con integracion de Docker habilitada, si se usa Windows.
- Una API key de Google GenAI.
- Al menos 15-20 GB libres para Docker.

En WSL, verificar que Docker responde:

```bash
docker info
```

Si falla con `/var/run/docker.sock`, abrir Docker Desktop y activar:

```text
Settings -> Resources -> WSL Integration -> Enable integration
```

Luego reiniciar WSL desde PowerShell:

```powershell
wsl --shutdown
```

## 1. Instalar Dependencias Del Backend

Desde la carpeta del repo:

```bash
cd ~/chatmp/chat-mp
make install
```

Si `make install` falla porque falta `ensurepip`, instalar el paquete de sistema y volver a correrlo:

```bash
sudo apt install python3.12-venv
make install
```

## 2. Configurar Variables De Entorno

Crear `.env` desde el ejemplo:

```bash
cp .env.example .env
```

Editar `.env`:

```bash
nano .env
```

Completar:

```text
GOOGLE_GENAI_API_KEY="tu-api-key"
GOOGLE_GENAI_MODEL="gemini-3.1-flash-lite"
GOOGLE_GENAI_DEFAULT_MAX_OUTPUT_TOKENS=600
OPENWEBUI_API_KEY=""
```

Notas:

- `gemini-3.1-flash-lite` es el modelo recomendado para buena velocidad.
- `GOOGLE_GENAI_DEFAULT_MAX_OUTPUT_TOKENS=600` limita respuestas largas si Open WebUI no manda limite.
- `OPENWEBUI_API_KEY` puede quedar vacia para pruebas locales.

## 3. Correr El Backend

```bash
cd ~/chatmp/chat-mp
.venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Dejar esa terminal abierta.

En otra terminal, probar:

```bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/v1/models
```

La respuesta de modelos debe incluir:

```text
gemini-3.1-flash-lite
```

## 4. Correr Open WebUI

Usar este comando completo en Bash/WSL:

```bash
docker run -d \
  -p 3000:8080 \
  --add-host=host.docker.internal:host-gateway \
  -v open-webui:/app/backend/data \
  -e RAG_SYSTEM_CONTEXT=True \
  --name open-webui \
  ghcr.io/open-webui/open-webui:main-slim
```

Abrir:

```text
http://localhost:3000
```

La primera vez puede tardar un poco. Si aparece un `500` mientras arranca, esperar 30-60 segundos y refrescar.

Comandos utiles:

```bash
docker ps
docker logs open-webui --tail 80
docker start open-webui
docker stop open-webui
```

Si hay que recrear el contenedor sin borrar datos:

```bash
docker rm -f open-webui
docker run -d \
  -p 3000:8080 \
  --add-host=host.docker.internal:host-gateway \
  -v open-webui:/app/backend/data \
  -e RAG_SYSTEM_CONTEXT=True \
  --name open-webui \
  ghcr.io/open-webui/open-webui:main-slim
```

## 5. Conectar Open WebUI Al Backend

En Open WebUI, crear el primer usuario/admin si lo pide.

Luego ir a:

```text
Admin Panel -> Settings -> Connections
```

Crear o editar una conexion OpenAI-compatible:

```text
API Base URL: http://host.docker.internal:8000/v1
API Key: dejar vacio
```

Guardar y refrescar la lista de modelos. Debe aparecer:

```text
gemini-3.1-flash-lite
```

Activar streaming si aparece la opcion:

```text
Stream Response / Streaming: enabled
```

Para reducir llamadas extra y mejorar velocidad, desactivar si estan encendidas:

```text
Title generation
Follow-up suggestions
Tags
Auto-summary
```

## 6. Cargar Referencias Para RAG

Ir a:

```text
Workspace -> Knowledge
```

Crear una Knowledge Base:

```text
Chat MP Referencias
```

Subir los archivos de `refs/`:

```text
refs/Chat MP IA.pdf
refs/4. Rubrica de Movimiento de Pensamiento 2-5-26.pdf
refs/Que hiciste hoy en clases_ (respuestas) - Respuestas de formulario 1.csv
```

Los nombres pueden verse con acentos en el sistema de archivos; subir los archivos correspondientes desde la carpeta `refs`.

Config recomendada en documentos/RAG, si Open WebUI muestra estas opciones:

```text
Chunk Size: 1500-2000
Chunk Overlap: 150-250
Hybrid Search: enabled
File Context: enabled
Tools / Function calling: disabled
```

## 7. Hacer Que Las Referencias Se Usen Siempre

Para no tener que escribir `#` manualmente en cada chat:

1. Ir a:

```text
Workspace -> Models
```

2. Crear un modelo nuevo:

```text
Nombre: Chat MP con referencias
Base model: gemini-3.1-flash-lite
```

3. En la seccion de Knowledge/Documents/RAG, adjuntar:

```text
Chat MP Referencias
```

4. En el system prompt del modelo personalizado, usar:

```text
Usa las referencias cargadas como contexto principal para responder. Si la respuesta no esta suficientemente respaldada por las referencias, dilo explicitamente. No inventes criterios ni rubricas.
```

5. Guardar.

En chats nuevos, seleccionar:

```text
Chat MP con referencias
```

Asi Open WebUI usa las referencias automaticamente sin escribir `#`.

## 8. Uso Diario

Arrancar backend:

```bash
cd ~/chatmp/chat-mp
.venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Arrancar Open WebUI si no esta corriendo:

```bash
docker start open-webui
```

Abrir:

```text
http://localhost:3000
```

Elegir:

```text
Chat MP con referencias
```

## 9. Troubleshooting

Si Open WebUI no abre:

```bash
docker ps -a
docker logs open-webui --tail 120
```

Si el modelo no aparece:

```bash
curl http://127.0.0.1:8000/v1/models
```

Si devuelve otro modelo, revisar `.env` y reiniciar el backend.

Si Open WebUI no puede conectar al backend, revisar que el backend este corriendo con:

```bash
.venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Si Docker dice que el nombre ya existe:

```bash
docker start open-webui
```

Si Docker dice que el puerto 3000 esta ocupado:

```bash
docker ps -a
```

Si se quiere borrar todo Open WebUI y empezar de cero:

```bash
docker rm -f open-webui
docker volume rm open-webui
```

Luego volver a correr el comando de la seccion 4.

## 10. Tests Del Backend

```bash
make test
```
