PYTHON ?= python
PARSER := $(PYTHON) -m schedule_parser

.PHONY: install parse test lint build dev

install:
	$(PYTHON) -m pip install -e parser/[dev]

parse:
	$(PARSER) parse

test:
	$(PYTHON) -m pytest parser/tests

lint:
	$(PYTHON) -m ruff check parser/src parser/tests

build:
	npm --prefix web install
	npm --prefix web run build

dev:
	npm --prefix web run dev
