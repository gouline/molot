.PHONY: all build clean

all: build

build: 
	python3 setup.py develop

clean:
	rm -rf bin build include lib lib64 man share
