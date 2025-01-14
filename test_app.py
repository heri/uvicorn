import asyncio
import pytest
from app import main, setup

@pytest.fixture(scope='module')
async def setup_db():
    await setup()

@pytest.mark.asyncio
async def test_upsert_query(setup_db):
    scope = {'type': 'http', 'path': '/webhook', 'query_string': b'firstName=John&lastName=Doe&id=1'}
    receive = lambda: None
    send = lambda message: message

    response = await main(scope, receive, send)
    assert response['status'] == 200
    assert response['headers'][0] == [b'content-type', b'application/json']
    assert response['body'] == b'{"id":"1","firstName":"John","lastName":"Doe"}'

@pytest.mark.asyncio
async def test_users(setup_db):
    scope = {'type': 'http', 'path': '/', 'query_string': b''}
    receive = lambda: None
    send = lambda message: message

    response = await main(scope, receive, send)
    assert response['status'] == 200
    assert response['headers'][0] == [b'content-type', b'text/html; charset=utf-8']
    assert b'<html>' in response['body']

@pytest.mark.asyncio
async def test_handle_404(setup_db):
    scope = {'type': 'http', 'path': '/nonexistent', 'query_string': b''}
    receive = lambda: None
    send = lambda message: message

    response = await main(scope, receive, send)
    assert response['status'] == 200
    assert response['headers'][0] == [b'content-type', b'text/plain']
    assert response['body'] == b'Not found'