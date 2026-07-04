import asyncpg
import jinja2
import os
import ujson

pool = None
json_dumps = ujson.dumps

SQL_AUTH = 'SELECT id FROM "users" WHERE id=$1 AND password=$2'
SQL_UPD = 'UPDATE users SET "firstName"=$1, "lastName"=$2 WHERE id=$3'
SQL_ALL = 'SELECT id,"firstName","lastName" FROM users ORDER BY "firstName"'

with open(os.path.join('templates', 'user.html')) as f:
    template = jinja2.Template(f.read())


async def setup():
    global pool
    pool = await asyncpg.create_pool(
        user=os.getenv('PGUSER', 'heri'),
        password=os.getenv('PGPASS', ''),
        database='uvicorn',
        host='localhost',
        port=5432
    )


def qparse(qs):
    d = {}
    for p in qs.split(b'&'):
        k, _, v = p.partition(b'=')
        d[k.decode()] = v.decode()
    return d


async def reply(send, status, ctype, content):
    n = len(content)
    await send({
        'type': 'http.response.start',
        'status': status,
        'headers': [(b'content-type', ctype), (b'content-length', str(n).encode())]
    })
    await send({'type': 'http.response.body', 'body': content, 'more_body': False})


async def auth_login(scope, receive, send):
    q = qparse(scope['query_string'])
    id, pw = q['id'], q['password']

    conn = await pool.acquire()
    try:
        row = await conn.fetchrow(SQL_AUTH, id, pw)
    finally:
        await pool.release(conn)

    if row is None:
        content = json_dumps({'detail': 'Invalid credentials'}).encode()
        await reply(send, 401, b'application/json', content)
        return

    content = json_dumps({'session': f'token_for_{row["id"]}'}).encode()
    await reply(send, 200, b'application/json', content)


async def upsert_query(scope, receive, send):
    q = qparse(scope['query_string'])
    fn, ln, id = q['firstName'], q['lastName'], q['id']

    conn = await pool.acquire()
    try:
        await conn.execute(SQL_UPD, fn, ln, id)
    finally:
        await pool.release(conn)

    content = json_dumps({'id': id, 'firstName': fn, 'lastName': ln}).encode()
    await reply(send, 200, b'application/json', content)


async def users(scope, receive, send):
    conn = await pool.acquire()
    try:
        rows = await conn.fetch(SQL_ALL)
    finally:
        await pool.release(conn)

    content = template.render(users=rows).encode()
    await reply(send, 200, b'text/html; charset=utf-8', content)


async def handle_404(scope, receive, send):
    await reply(send, 200, b'text/plain; charset=utf-8', b'Not found')


routes = {
    '/auth/login': auth_login,
    '/webhook': upsert_query,
    '/': users,
}


async def main(scope, receive, send):
    if scope['type'] == 'lifespan':
        while True:
            msg = await receive()
            if msg['type'] == 'lifespan.startup':
                await setup()
                await send({'type': 'lifespan.startup.complete'})
            elif msg['type'] == 'lifespan.shutdown':
                await pool.close()
                await send({'type': 'lifespan.shutdown.complete'})
                return

    handler = routes.get(scope['path'], handle_404)
    await handler(scope, receive, send)
