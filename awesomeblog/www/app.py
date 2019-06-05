import logging; logging.basicConfig(level=logging.INFO)#带分号的代码

import asyncio, os, json, time
from datetime import datetime

from aiohttp import web

import sql

def get(path):

    '''
    Define decorator @get('/path')
    '''

    def decorator(func):
        def wrapper(*args,**kw):
            return func(*args,**kw)

        wrapper.__method__ = 'GET'
        wrapper.__route__ = path

        return wrapper

    return decorator

def index(request):
    return web.Response(body = b'<h1>Awesome</h1>',content_type = 'text/html')

async def init():
    app = web.Application()
    app.router.add_route('GET','/',index)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner,'127.0.0.1',9000)
    await site.start()
    logging.info('server start at http://127.0.0.1:9000...')

loop = asyncio.get_event_loop()
tasks = [init(),sql.create_pool(user = 'root',password = 'password',db = 'test')]
loop.run_until_complete(asyncio.wait(tasks))
loop.run_forever()
