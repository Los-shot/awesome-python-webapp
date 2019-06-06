import logging; logging.basicConfig(level=logging.INFO)#带分号的代码

import asyncio, os, json, time
from datetime import datetime

from aiohttp import web
from jinja2 import Environment, FileSystemLoader, select_autoescape

import sql,handlerframe

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
        
def init_jinja2():
    env = Environment(
        loader = FileSystemLoader('templates'),
        autoescape = select_autoescape(['html', 'xml'])
    )
    env.filters['datetimeformat'] = datetimeformat

def datetimeformat(value, format='%H:%M / %d-%m-%Y'):
    return value.strftime(format)

def add_static(app):
    pass

async def init():
    app = web.Application(middlewares = [logger_factory,response_factory])
    init_jinja2()
    handlerframe.add_routes(app,'handlers')
    add_static(app)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner,'127.0.0.1',9000)
    await site.start()
    logging.info('server start at http://127.0.0.1:9000...')

loop = asyncio.get_event_loop()
tasks = [init(),sql.create_pool(user = 'root',password = 'password',db = 'awesome')]
loop.run_until_complete(asyncio.wait(tasks))
loop.run_forever()
