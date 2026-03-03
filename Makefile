.PHONY: help install run test clean lint format

help:
	@echo "Comandos disponibles:"
	@echo "  make install    - Instala el proyecto y dependencias"
	@echo "  make run        - Ejecuta el bot"
	@echo "  make test       - Ejecuta los tests"
	@echo "  make lint       - Ejecuta el linter"
	@echo "  make format     - Formatea el código"
	@echo "  make clean      - Limpia archivos generados"

install:
	pip install -e ".[dev]"

run:
	python -m kaillera_bot.main

run-config:
	python -m kaillera_bot.main --config config/settings.yaml

test:
	pytest tests/ -v

lint:
	flake8 src/ tests/
	mypy src/

format:
	black src/ tests/

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf build/ dist/ .eggs/
