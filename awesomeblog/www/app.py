import logging; logging.basicConfig(level=logging.INFO)#带分号的代码

import asyncio, os, json, time, pathlib
from datetime import datetime

from aiohttp import web
from jinja2 import Environment, FileSystemLoader, select_autoescape

import sql,handlerframe
from cookieutil import COOKIE_NAME,cookie2user

env:Environment

@web.middleware
async def logger_factory(request,handler):
    logging.info('Request: %s %s' % (request.method,request.path))
    return await handler(request)

@web.middleware
async def auth_factory(request,handler):
    request.__user__ = None

    cookie_str = request.cookies.get(COOKIE_NAME)
    if cookie_str:
        user = await cookie2user(cookie_str)
        if user:
            logging.info('set current user: %s' % user.email)
            request.__user__ = user
        
    return await handler(request)

@web.middleware
async def response_factory(request,handler):
    r = await handler(request)
    if isinstance(r,web.StreamResponse):
        return r
    if isinstance(r,bytes):
        resp = web.Response(body = r)
        resp.content_type = 'application/octet-stream'
        return resp
    if isinstance(r,str):
        resp = web.Response(body = r.encode('utf-8'))
        resp.content_type = 'text/html;charset=utf-8'
        return resp
    if isinstance(r,dict):
        if r.get('__template__',None):
            template = env.get_template(r['__template__'])
            if request.path != '/signout':
                if request.__user__:
                    r['user'] = request.__user__
            body = template.render(r)
            resp = web.Response(body = body)
            resp.content_type = 'text/html'
            
            if request.path == '/signout':
                resp.del_cookie(COOKIE_NAME)
        else:
            resp = web.Response(body = json.dumps(r,default = lambda obj:obj.__dict__))
            resp.content_type = 'application/json;charset=utf-8'
        return resp
    
def init_jinja2():
    global env
    path = os.path.join(os.path.abspath('www'),'templates')
    env = Environment(
        loader = FileSystemLoader(path),
        autoescape = select_autoescape(['html', 'xml'])
    )
    env.filters['datetimeformat'] = datetimeformat

def datetimeformat(value, format='%H:%M / %d-%m-%Y'):
    date = datetime.fromtimestamp(value)
    return date.strftime(format)

def add_static(app):
    PROJECT_PATH = pathlib.Path(__file__).parent
    app.router.add_static('/static/',PROJECT_PATH / 'static')

async def init():
    app = web.Application(middlewares = [logger_factory,auth_factory,response_factory])
    init_jinja2()
    handlerframe.add_routes(app,'handlers')
    add_static(app)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner,'127.0.0.1',9000)
    await site.start()
    logging.info('server start at http://127.0.0.1:9000...')

from config import configs

loop = asyncio.get_event_loop()
tasks = [init(),sql.create_pool(host = configs['db']['host'],user = configs['db']['user'],password = configs['db']['password'],db = configs['db']['database'])]
loop.run_until_complete(asyncio.wait(tasks))
loop.run_forever()