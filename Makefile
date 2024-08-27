build: clean
	uv run python3 -m build
.PHONY: build

clean:
	rm -rf build dist
.PHONY: clean

dependencies:
	uv sync --frozen --no-install-project
.PHONY: dependencies

fix:
	uv run ruff format .
	uv run ruff check --fix .
.PHONY: fix

check-lint:
	uv run ruff format --check .
	uv run ruff check .
.PHONY: check-lint

check-type:
	uv run mypy molot
.PHONY: check-type

check: check-lint check-type
.PHONY: check

test:
	uv run pytest tests
.PHONY: test

pre: fix check test
.PHONY: pre

dist-check: build
	twine check dist/*
.PHONY: dist-check

dist-upload: check
	twine upload dist/*
.PHONY: dist-upload

dev-uninstall:
	uv run python3 -m pip uninstall -y molot
.PHONY: dev-uninstall

dev-install: build dev-uninstall
	uv pip install dist/molot-*-py3-none-any.whl
.PHONY: dev-install
