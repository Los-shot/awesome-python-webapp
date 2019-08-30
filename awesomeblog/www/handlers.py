from handlerframe import get,post,parse_post_params,APIError,APIValueError
from model import next_id,Blog,User
import time, re, hashlib, json
from aiohttp import web

COOKIE_NAME = 'awesome'
MAX_AGE = 60 * 10
SECRET_KEY = 'laliga'

def user2cookie(user,max_age):
    pass

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

_RE_EMAIL = re.compile(r'^[a-z0-9\.\-\_]+\@[a-z0-9\-\_]+(\.[a-z0-9\-\_]+){1,4}$')
_RE_SHA1 = re.compile(r'^[0-9a-f]{40}$')

@post('/api/register/user')
async def api_register_user(request):
    cookie = request.cookies.get('aka')
    print('cookie:',cookie)
    params = await parse_post_params(request)

    name:str = params.get('name',None)
    if not name or not name.strip():
        raise APIValueError('name')
    
    email:str = params.get('email',None)
    if not email or not _RE_EMAIL.match(email):
        raise APIValueError('email')

    passwd:str = params.get('passwd',None)
    if not passwd or not _RE_SHA1.match(passwd):
        raise APIValueError('passwd')

    users = await User.findAll('email', email)

    if len(users) > 0:
        raise APIError('register:failed', 'email', 'Email is already in use.')

    uid = next_id()
    sha1_passwd = '%s:%s' % (uid,passwd)
    user = User(id=uid,name=name.strip(),email=email,passwd=hashlib.sha1(sha1_passwd.encode('utf-8')).hexdigest(),image='http://www.gravatar.com/avatar/%s?d=mm&s=120' % hashlib.md5(email.encode('utf-8')).hexdigest())
    await user.save()
    user.passwd = '******'
    resp = web.Response()
    resp.set_cookie(COOKIE_NAME,user2cookie(user, MAX_AGE),max_age=MAX_AGE,httponly=True)
    resp.content_type = 'application/json'
    resp.body = json.dumps({'ret':'ok'},default = lambda obj:obj.__dict__)
    return resp

@get('/login')
def register(request):
    return {
        '__template__':'register.html'
    }