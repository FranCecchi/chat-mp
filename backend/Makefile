PYTHON := .venv/bin/python
PIP := .venv/bin/pip

.PHONY: help venv install run

help:
	@echo "Targets disponibles:"
	@echo "  make install        Crear .venv e instalar dependencias"
	@echo "  make run            Correr la API en desarrollo"

venv:
	python3 -m venv .venv

install: venv
	$(PYTHON) -m pip install --upgrade pip
	$(PIP) install -r requirements.txt

run:
	$(PYTHON) -m uvicorn app.main:app --reload
