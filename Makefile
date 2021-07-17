build: clean
	python3 setup.py sdist bdist_wheel

clean:
	rm -rf build dist

requirements:
	pip3 install -r requirements.txt 
	pip3 install -r requirements-test.txt
.PHONY: requirements

lint:
	pylint molot
.PHONY: lint

type:
	mypy molot
.PHONY: type

# TODO: implement tests
# test:
# 	python3 -m unittest tests
# .PHONY: test

check: build
	twine check dist/*
.PHONY: check

upload: check
	twine upload dist/*
.PHONY: upload

dev-install: build
	pip3 uninstall -y molot && pip3 install dist/molot-*-py3-none-any.whl
.PHONY: dev-install
