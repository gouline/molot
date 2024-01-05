# Docker Entry Point

Molot is useful for creating entry points in your Docker images.

Let's say we want to fetch latest and oldest releases for this repository. See [entrypoint.py](./entrypoint.py) for an example implementation.

It works by fetching all releases from the API and saving them as a temporary JSON file first, which subsequent targets load to print the latest and oldest releases.

## Running

You can build and run the example Docker image like so:

```shell
make run
```

## Details

See noteworthy details that this example demonstrates below.

### Shared Dependency

Notice how `fetch` target is a dependency of both, `latest` and `oldest`? That means even if you execute both targets `./entrypoint.py latest oldest`, `fetch` will run only once before the first target that depends on it.

### Sensitive Argument

This example optionally allows you to pass `GITHUB_TOKEN` as an environment argument. Because it's configured as `sensitive=True`, it will be masked in the output.
