SYSTEM_PYTHON ?= python3

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
	mv dist/main dist/ai-git-tools

run:
	./dist/ai-git-tools

clean:
	rm -rf build dist __pycache__ *.spec

.PHONY: all env run build run clean