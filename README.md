Uvicorn web/json server for benchmarking purposes

## Description

[Uvicorn](https://github.com/tomchristie/uvicorn) is a lightning fast asyncio server for Python 3.

## Implementation

Uvicorn is implemented using:

* Gunicorn for process managment.
* The uvloop event loop.
* The httptools HTTP parsing library.
* The ASGI consumer interface, for interacting with the application layer.

The asyncpg pool currently uses its default size (`min_size=10, max_size=10`) per worker, which may be too small or too large depending on benchmark concurrency. Tune it against a real load test (e.g. `wrk`/`hey`) rather than guessing.

## Who is behind this

Heri is a software engineer, photographer, father and Montréaler. Building in the open — see more projects at [studiozenkai.com](https://studiozenkai.com).
