build: clean
	python3 -m build
.PHONY: build

clean:
	rm -rf build dist
.PHONY: clean

requirements:
	python3 -m pip install \
		-r requirements.txt \
		-r requirements-test.txt
.PHONY: requirements

fix:
	ruff format .
	ruff check --fix .
.PHONY: fix

check-lint:
	ruff format --check .
	ruff check .
.PHONY: check-lint

check-type:
	mypy molot
.PHONY: check-type

check: check-lint check-type
.PHONY: check

test:
	pytest tests
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
	python3 -m pip uninstall -y molot
.PHONY: dev-uninstall

dev-install: build dev-uninstall
	python3 -m pip install dist/molot-*-py3-none-any.whl
.PHONY: dev-install
