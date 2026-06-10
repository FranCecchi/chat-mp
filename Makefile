# 1. Detección del Sistema Operativo
ifeq ($(OS),Windows_NT)
    # Configuración para Windows
    PYTHON_DIR := .venv/Scripts
    PYTHON := $(PYTHON_DIR)/python.exe
    PIP := $(PYTHON_DIR)/pip.exe
    PYTHON_SYSTEM := python
else
    # Configuración para Linux / macOS
    PYTHON_DIR := .venv/bin
    PYTHON := $(PYTHON_DIR)/python
    PIP := $(PYTHON_DIR)/pip
    PYTHON_SYSTEM := python3
endif

.PHONY: help venv install run test health webhook webhook-info webhook-delete

help:
	@echo "Targets disponibles:"
	@echo "  make install        Crear .venv e instalar dependencias"
	@echo "  make run            Correr la API en desarrollo"
	@echo "  make test           Correr tests"
	@echo "  make health         Probar GET /health"
	@echo "  make webhook URL=... Registrar webhook de Telegram"
	@echo "  make webhook-info   Ver estado del webhook de Telegram"
	@echo "  make webhook-delete Borrar webhook de Telegram"

venv:
	$(PYTHON_SYSTEM) -m venv .venv

install: venv
	$(PYTHON) -m pip install --upgrade pip
	$(PIP) install -r requirements.txt

run:
	$(PYTHON) -m uvicorn app.main:app --reload

test:
	$(PYTHON) -m pytest

health:
	curl http://127.0.0.1:8000/health

webhook:
# En Windows (CMD/PowerShell) el 'if' de Bash falla, usamos una validación nativa de Make
ifndef URL
	@echo "Error: Falta la variable URL."
	@echo "Uso: make webhook URL=https://TU_DOMINIO/telegram/webhook"
	@exit 2
endif
	$(PYTHON) -m app.telegram.manage_webhook set "$(URL)"

webhook-info:
	$(PYTHON) -m app.telegram.manage_webhook info

webhook-delete:
	$(PYTHON) -m app.telegram.manage_webhook delete