from handlerframe import get,post,parse_post_params
from model import Blog
import time

@get('/')
def index(request):
    summary = 'Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.'
    blogs = [
        Blog(id='1', name='Test Blog', summary=summary, created_at=time.time()-120),
        Blog(id='2', name='Something New', summary=summary, created_at=time.time()-3600),
        Blog(id='3', name='Learn Swift', summary=summary, created_at=time.time()-7200)
    ]
    return {
        '__template__': 'blogs.html',
        'blogs': blogs
    }

class A():
    def __init__(self,name,age):
        self.name = name
        self.age = age

@get('/api/users/{name}')
def get_api_users(request):
    name = request.match_info.get('name','nobody')
    return {'users':[A(name,12),A('mike',20)]}

@post('/api/register/user')
async def api_register_user(request):
    params = await parse_post_params(request)
    return {'users':[A(params.get('name'),12),A('mike',20)]}

@get('/login')
def register(request):
    return {
        '__template__':'register.html'
    }