import logging; logging.basicConfig(level=logging.INFO)#带分号的代码

import asyncio, os, json, time
from datetime import datetime

from aiohttp import web

import sql
from webframe import add_routes

async def logger_factory(app,handler):
    async def logger(request):
        logging.info('Request: %s %s' % (request.method,request.path))
        return await handler(request)
    return logger

async def response_factory(app,handler):
    async def response(request):
        r = await handler(request)
        if isinstance(r,web.StreamResponse):
            return r
        if isinstance(r,bytes):
            resp = web.Resource(body = r)
            resp.content_type = 'application/octet-stream'
            return resp
        if isinstance(r,str):
            resp = web.Response(body = r.encode('utf-8'))
            resp.content_type = 'text/html:charset=utf-8'
            return resp
        if isinstance(r,dict):
            pass
        
def index(request):
    return web.Response(body = b'<h1>Awesome</h1>',content_type = 'text/html')

def init_jinja2(app,filter = None):
    pass

def datetime_filter():
    pass

def add_static():
    pass

async def init():
    app = web.Application(middlewares = [logger_factory,response_factory])
    init_jinja2(app,filter = dict(datetime = datetime_filter))
    add_routes(app,'handlers')
    add_static(app)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner,'127.0.0.1',9000)
    await site.start()
    logging.info('server start at http://127.0.0.1:9000...')

loop = asyncio.get_event_loop()
tasks = [init(),sql.create_pool(user = 'root',password = 'password',db = 'test')]
loop.run_until_complete(asyncio.wait(tasks))
loop.run_forever()
