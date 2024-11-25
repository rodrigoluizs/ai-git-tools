SYSTEM_PYTHON ?= python3
PYTHONPATH := $(shell pwd)/src
COV_REPORT_DIR := htmlcov

all: env

env: .venv
	.venv/bin/pip install -r requirements.txt

dev: .venv
	.venv/bin/pip install -r dev-requirements.txt

.venv:
	$(SYSTEM_PYTHON) -m venv .venv
	.venv/bin/pip install --upgrade pip wheel

build:
	pip install pyinstaller
	pyinstaller --onefile --add-data "resources:resources" src/main.py
	mv dist/main dist/agt

test:
	pytest --cov=src --cov-fail-under=94 -vv

coverage:
	pytest --cov=src --cov-report=term --cov-report=html:$(COV_REPORT_DIR) -vv
	open $(COV_REPORT_DIR)/index.html

run:
	./dist/agt

clean:
	rm -rf build dist __pycache__ *.spec htmlcov
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -type d -exec rm -r {} +

pre-commit:
	pre-commit run --all-files

.PHONY: all env run build test run clean pre-commit