from handlerframe import get

@get('/')
def index(request):
    return {
        '__template__': 'index.html',
        'data': '...'
    }