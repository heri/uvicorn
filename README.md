Uvicorn web/json server for benchmarking purposes

## Description

[Uvicorn](https://github.com/tomchristie/uvicorn) is a lightning fast asyncio server for Python 3.

## Implementation

Uvicorn is implemented using:

* Gunicorn for process managment.
* The uvloop event loop.
* The httptools HTTP parsing library.
* The ASGI consumer interface, for interacting with the application layer.
