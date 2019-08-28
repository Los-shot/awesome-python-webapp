import asyncio,inspect,logging,functools
from urllib.parse import unquote

def get(path):

    '''
    Define decorator @get('/path')
    '''

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args,**kw):
            return func(*args,**kw)

        wrapper.__method__ = 'GET'
        wrapper.__route__ = path

        return wrapper

    return decorator

def post(path):

    '''
    Define decorator @post('/path')
    '''

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args,**kw):
            return func(*args,**kw)

        wrapper.__method__ = 'POST'
        wrapper.__route__ = path

        return wrapper

    return decorator

class RequestHandler():
    def __init__(self,app,fn):
        self._app = app
        self._func = fn

    async def __call__(self,request,**kw):
        return await self._func(request,**kw)

def add_route(app,fn):
    method = getattr(fn,'__method__',None)
    path = getattr(fn,'__route__',None)
    if path is None or method is None:
        raise ValueError('@get or @post not defined in %s.' % str(fn))
    if not asyncio.iscoroutinefunction(fn) and not inspect.isgeneratorfunction(fn):
        fn = asyncio.coroutine(fn)
    logging.info('add route %s %s => %s(%s)' % (method,path,fn.__name__,', '.join(inspect.signature(fn).parameters.keys())))
    app.router.add_route(method,path,RequestHandler(app,fn))

def add_routes(app,module_name):
    n = module_name.rfind(',')
    if n == (-1):
        mod = __import__(module_name,globals(),locals())
    else:
        name = module_name[n+1:]
        mod = getattr(__import__(module_name[:n],globals(),locals(),[name]),name)
    for attr in dir(mod):
        if attr.startswith('_'):
            continue
        fn = getattr(mod,attr)
        if callable(fn):
            method = getattr(fn,'__method__',None)
            path = getattr(fn,'__route__',None)
            if method and path:
                add_route(app,fn)

async def parse_post_params(request):
    sb = await request.content.read()
    s = sb.decode('utf-8')
    s = unquote(s)
    segs = s.split('&')
    obj = {}

    for k in segs:
        seg = k.split('=')
        obj[seg[0]] = seg[1]

    return obj