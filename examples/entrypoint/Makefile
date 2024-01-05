IMAGE ?= molot-examples-entrypoint
TAG ?= latest

GITHUB_TOKEN ?= 

build:
	docker build -t $(IMAGE):$(TAG) .
.PHONY: build

run: build
	docker run --rm \
		-e GITHUB_TOKEN=$(GITHUB_TOKEN) \
		$(IMAGE):$(TAG) latest oldest
.PHONY: run
