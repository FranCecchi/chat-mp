PYTHON := .venv/bin/python
PIP := .venv/bin/pip

.PHONY: help venv install run test health models

help:
	@echo "Targets disponibles:"
	@echo "  make install        Crear .venv e instalar dependencias"
	@echo "  make run            Correr la API en desarrollo"
	@echo "  make test           Correr tests"
	@echo "  make health         Probar GET /health"
	@echo "  make models         Probar GET /v1/models"

venv:
	python3 -m venv .venv

install: venv
	$(PYTHON) -m pip install --upgrade pip
	$(PIP) install -r requirements.txt

run:
	$(PYTHON) -m uvicorn app.main:app --reload

test:
	$(PYTHON) -m pytest

health:
	curl http://127.0.0.1:8000/health

models:
	curl http://127.0.0.1:8000/v1/models
