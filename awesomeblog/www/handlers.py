from handlerframe import get,post,parse_post_params,APIError,APIValueError
from model import next_id,Blog,User
import time, re, hashlib, json
from aiohttp import web
from cookieutil import COOKIE_NAME,MAX_AGE,COOKIE_KEY,user2cookie

@get('/')
async def index(request):
    blogs = []
    if request.__user__:
        blogs = await Blog.findAll('user_id',request.__user__.id)

    summary1 = '每个注册用户可以创建新的博客，但是不能修改已有日志，如果想要修改已有日志，需取得管理员权限，请与543751914@qq.com联系'
    summary2 = 'Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.'
    summary3 = 'blog作业断断续续做了好长时间，另加自己没有web前端基础，花了一些时间简单学习了下html、css、vue,也没深入，所有blog页面也只是跟教程的原汁原味，另因为没有看廖大大源码的缘故，根据python blog教程有好多细节的改动，比如aiohttp，每个细节都做了推敲，包括注册、登录、注销等等'
    
    test = [
        Blog(id='1', name='公共日志', summary=summary1, created_at=time.time()-120),
        Blog(id='2', name='Test Blog', summary=summary2, created_at=time.time()-3600),
        Blog(id='3', name='作业心得', summary=summary3, created_at=time.time()-7200)
    ]
    
    blogs.append(test[0])
    blogs.append(test[1])
    blogs.append(test[2])

    return {
        '__template__': 'blogs.html',
        'blogs': blogs
    }

@get("/blog/{id}")
async def get_blog(request):
    id = request.path[6:]
    blog = await Blog.find(id)

    if blog:
        pass
    else:
        summary1 = '每个注册用户可以创建新的博客，但是不能修改已有日志，如果想要修改已有日志，需取得管理员权限，请与543751914@qq.com联系'
        blog = Blog(id='1', name='公共日志', summary=summary1, created_at=time.time()-120)
    
    return {
        '__template__': 'blog.html',
        'blog': blog
    }

@get('/register')
def register(request):
    return {
        '__template__':'register.html'
    }

_RE_EMAIL = re.compile(r'^[a-z0-9\.\-\_]+\@[a-z0-9\-\_]+(\.[a-z0-9\-\_]+){1,4}$')
_RE_SHA1 = re.compile(r'^[0-9a-f]{40}$')

@post('/api/register/user')
async def api_register_user(request):
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
    
    resp = web.Response()
    resp.set_cookie(COOKIE_NAME,user2cookie(user, MAX_AGE),max_age=MAX_AGE,httponly=True)
    user.passwd = '******'
    resp.content_type = 'application/json'
    resp.body = json.dumps(user,ensure_ascii = False).encode('utf-8')
    
    return resp

@get('/registerSucc')
async def registerSucc(request):
    return {
        '__template__':'registerSucc.html'
    }

@get('/signin')
def signin(request):
    return {
        '__template__':'signin.html'
    }

@post('/api/signin/user')
async def api_signin_user(request):
    params = await parse_post_params(request)

    email:str = params.get('email',None)

    if not email or not _RE_EMAIL.match(email):
        raise APIValueError('email')

    passwd:str = params.get('passwd',None)

    if not passwd or not _RE_SHA1.match(passwd):
        raise APIValueError('passwd')

    users = await User.findAll('email', email)

    if len(users) == 0:
        raise APIValueError('email','email not exist.')
    user = users[0]
    sha1 = hashlib.sha1()
    sha1.update(user.id.encode('utf-8'))
    sha1.update(b':')
    sha1.update(passwd.encode('utf-8'))
    if sha1.hexdigest() != user.passwd:
        raise APIValueError('passwd','Invalid password')
    
    resp = web.Response()
    resp.set_cookie(COOKIE_NAME,user2cookie(user, MAX_AGE),max_age=MAX_AGE,httponly=True)
    user.passwd = '******'
    resp.content_type = 'application/json'
    resp.body = json.dumps(user,ensure_ascii = False).encode('utf-8')
    
    return resp

@get('/signout')
async def signout_user(request):
    return {
        '__template__':'signin.html'
    }

@get('/manage/blog')
def manage_blog_edit(request):
    if request.__user__:
        return {
            '__template__':'manage_blog_edit.html'
        }
    else:
        return {
            '__template__':'signin.html'
        }

@post('/api/create/blog')
async def api_create_blog(request):
    result = {}

    if request.__user__:
        user = request.__user__
        params = await parse_post_params(request)
        name:str = params.get('name',None)
        summary:str = params.get('summary',None)
        content:str = params.get('content',None)

        blog = Blog(user_id=user.id,user_name=user.name,user_image=user.image,name=name,summary=summary,content=content)
        
        await blog.save()

        result["id"] = blog.id
        result['status'] = 'ok'
    else:
        result['status'] = 'fail'
        result['msg'] = 'novail'

    resp = web.Response()
    resp.content_type = 'application/json'
    resp.body = json.dumps(result,ensure_ascii = False).encode('utf-8')
    
    return resp

