.PHONY: dependencies
dependencies:
	uv sync --frozen --no-install-project --all-extras

.PHONY: build
build: clean
	uv run python3 -m build

.PHONY: clean
clean:
	rm -rf build dist

.PHONY: fix
fix:
	uv run ruff format .
	uv run ruff check --fix .

.PHONY: check-lint
check-lint:
	uv run ruff format --check .
	uv run ruff check .

.PHONY: check-type
check-type:
	uv run mypy molot

.PHONY: check
check: check-lint check-type

.PHONY: test
test:
	uv run pytest tests

.PHONY: pre
pre: fix check test

.PHONY: dist-check
dist-check: build
	uv run twine check dist/*

.PHONY: dist-upload
dist-upload: check
	uv run twine upload dist/*

.PHONY: dev-uninstall
dev-uninstall:
	uv pip uninstall molot

.PHONY: dev-install
dev-install: build dev-uninstall
	uv pip install dist/molot-*-py3-none-any.whl
