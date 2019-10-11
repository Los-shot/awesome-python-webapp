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
    s = s.replace('+','%20')
    s = unquote(s)
    segs = s.split('&')
    obj = {}

    for k in segs:
        seg = k.split('=')
        obj[seg[0]] = seg[1]

    return obj

def getQueryString(request,name):
    urlParams = request.query_string
    segs = urlParams.split('&')
    obj = {}

    for k in segs:
        seg = k.split('=')
        if seg[0] == name:
            return seg[1]

class APIError(Exception):
    pass

class APIValueError(APIError):
    pass

class Page(object):
    def __init__(self,item_count,page_index,page_size = 10):
        self.item_count = item_count
        self.page_size = page_size
        self.page_count = item_count // page_size + (1 if item_count % page_size > 0 else 0)
        if (item_count == 0) or (page_index > self.page_count):
            self.offset = 0
            self.limit = 0
            self.page_index = 1
        else:
            self.page_index = page_index
            self.offset = self.page_size * (page_index - 1)
            self.limit = self.page_size
        self.has_next = self.page_index < self.page_count
        self.has_previous = self.page_index > 1

    # def __str__(self):
    #     return 'item_count: %s, page_count: %s, page_index: %s, page_size: %s, offset: %s, limit: %s' % (self.item_count, self.page_count, self.page_index, self.page_size, self.offset, self.limit)

    # __repr__ = __str__


        