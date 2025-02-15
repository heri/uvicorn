import asyncio
import asyncpg
import jinja2
import os
import ujson
from random import randint
from operator import itemgetter
from urllib.parse import parse_qs


async def setup():
    global pool
    pool = await asyncpg.create_pool(
        user=os.getenv('PGUSER', 'heri'),
        password=os.getenv('PGPASS', ''),
        database='uvicorn',
        host='localhost',
        port=5432
    )


READ_ROW_SQL = 'SELECT * FROM "users" WHERE id = $1'
READ_USER_PASSWORD_SQL = 'SELECT * FROM "users" WHERE id = $1 AND password = $2'
WRITE_ROW_SQL = 'UPDATE users SET "firstName"=$1, "lastName"=$2 WHERE id=$3'

JSON_RESPONSE = {
    'type': 'http.response.start',
    'status': 200,
    'headers': [
        [b'content-type', b'application/json'],
    ]
}

HTML_RESPONSE = {
    'type': 'http.response.start',
    'status': 200,
    'headers': [
        [b'content-type', b'text/html; charset=utf-8'],
    ]
}

PLAINTEXT_RESPONSE = {
    'type': 'http.response.start',
    'status': 200,
    'headers': [
        [b'content-type', b'text/plain; charset=utf-8'],
    ]
}

pool = None
key = itemgetter(1)
json_dumps = ujson.dumps
template = None
path = os.path.join('templates', 'user.html')
with open(path, 'r') as template_file:
    template_text = template_file.read()
    template = jinja2.Template(template_text)

loop = asyncio.get_event_loop()
loop.run_until_complete(setup())

def get_params(scope):
    if parse_qs(query_string)[b'password']
        id = parse_qs(query_string)[b'id']
        password = parse_qs(query_string)[b'password']
        return (id, password)
    else:
        try:
            query_string = scope['query_string']
            firstName = parse_qs(query_string)[b'firstName']
            lastName = parse_qs(query_string)[b'lastName']
            id = parse_qs(query_string)[b'id']
        except (KeyError, IndexError, ValueError):
            return 1

        return (firstName, lastName, id)

async def auth_login(scope, receive, send):
    connection = await pool.acquire()
    params = get_params(scope)

    try:
        user = await connection.fetchrow(READ_USER_PASSWORD_SQL, params)
        user_id = user['id']
    finally:
        await pool.release(connection)
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    # Placeholder for actual token generation logic
    return {"session": f"token_for_{user_id}" }

async def upsert_query(scope, receive, send):
    connection = await pool.acquire()
    params = get_params(scope)

    try:
        await connection.executemany(WRITE_ROW_SQL, params)
        user = {'id': params[0], 'firstName': params[1], 'lastName': params[2] }
    finally:
        await pool.release(connection)

    content = json_dumps(user).encode('utf-8')
    await send(JSON_RESPONSE)
    await send({
        'type': 'http.response.body',
        'body': content,
        'more_body': False
    })


async def users(scope, receive, send):
    connection = await pool.acquire()
    try:
        users = await connection.fetch('SELECT * FROM users')
    finally:
        await pool.release(connection)

    users.sort(key=key)
    content = template.render(users=users).encode('utf-8')
    await send(HTML_RESPONSE)
    await send({
        'type': 'http.response.body',
        'body': content,
        'more_body': False
    })

async def handle_404(scope, receive, send):
    content = b'Not found'
    await send(PLAINTEXT_RESPONSE)
    await send({
        'type': 'http.response.body',
        'body': content,
        'more_body': False
    })


routes = {
    '/auth/login': auth_login,
    '/webhook': upsert_query,
    '/': users,
}


async def main(scope, receive, send):
    path = scope['path']
    handler = routes.get(path, handle_404)
    await handler(scope, receive, send)
