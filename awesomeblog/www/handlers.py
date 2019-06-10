from handlerframe import get
class A():
    def __init__(self,name,email):
        self.name = name
        self.email = email

@get('/')
def index(request):
    return {
        '__template__': 'test.html',
        'users': [A('Jack','Jack@163.com'),A('Mike','Mike@qq.com')]
    }