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

fix-fmt:
	black .
.PHONY: fix-fmt

fix-imports:
	isort .
.PHONY: fix-imports

fix: fix-fmt fix-imports
.PHONY: fix

check-fmt:
	black --check .
.PHONY: check-fmt

check-imports:
	isort --check .
.PHONY: check-imports

check-lint-python:
	pylint molot
.PHONY: check-lint-python

check-type:
	mypy molot
.PHONY: check-type

check: check-fmt check-imports check-lint-python check-type
.PHONY: check

test:
	python3 -m unittest tests
.PHONY: test

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
