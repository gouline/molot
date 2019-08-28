.PHONY: all build check clean

all: build

build: 
	python3 setup.py sdist bdist_wheel

check: build
	twine check dist/*

upload: check
	twine upload dist/*

clean:
	rm -rf build dist
