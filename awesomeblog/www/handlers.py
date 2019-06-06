from handlerframe import get

@get('/')
def index(request):
    return '<h1>Awesome</h1>'
    # return web.Response(body=b'<h1>Awesome</h1>')
    # return {
    # '__template__': 'index.html',
    # 'data': '...'
    # }