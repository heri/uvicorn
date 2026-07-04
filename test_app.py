import pytest
import pytest_asyncio
from app import main, setup


@pytest_asyncio.fixture(scope='module')
async def setup_db():
    await setup()


class Send:
    def __init__(self):
        self.msgs = []

    async def __call__(self, msg):
        self.msgs.append(msg)


async def call(scope):
    send = Send()
    await main(scope, lambda: None, send)
    return send.msgs[0], send.msgs[1]


@pytest.mark.asyncio(loop_scope='module')
async def test_upsert_query(setup_db):
    scope = {'type': 'http', 'path': '/webhook', 'query_string': b'firstName=John&lastName=Doe&id=1'}
    start, body = await call(scope)
    assert start['status'] == 200
    assert start['headers'][0] == (b'content-type', b'application/json')
    assert body['body'] == b'{"id":"1","firstName":"John","lastName":"Doe"}'


@pytest.mark.asyncio(loop_scope='module')
async def test_users(setup_db):
    scope = {'type': 'http', 'path': '/', 'query_string': b''}
    start, body = await call(scope)
    assert start['status'] == 200
    assert start['headers'][0] == (b'content-type', b'text/html; charset=utf-8')
    assert b'<html>' in body['body']


@pytest.mark.asyncio(loop_scope='module')
async def test_handle_404(setup_db):
    scope = {'type': 'http', 'path': '/nonexistent', 'query_string': b''}
    start, body = await call(scope)
    assert start['status'] == 200
    assert start['headers'][0] == (b'content-type', b'text/plain; charset=utf-8')
    assert body['body'] == b'Not found'
