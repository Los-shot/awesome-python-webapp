from handlerframe import get,post,parse_post_params,getQueryString,APIError,APIValueError,Page
from model import next_id,Blog,User,Comment
import time, re, hashlib, json
from aiohttp import web
from cookieutil import COOKIE_NAME,MAX_AGE,COOKIE_KEY,user2cookie

@get('/')
async def index(request):
    blogs = await Blog.sql_select('order by created_at desc limit 20')

    return {
        '__template__': 'blogs.html',
        'blogs': blogs
    }

@get("/blog/{id}")
async def get_blog(request):
    id = request.path[6:]
    blog = await Blog.find(id)
    
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

@get('/manage')
def manage(request):
    if request.__user__:
        page = getQueryString(request,'page') or 1
        
        return {
            'page_index' : page,
            '__template__':'manage.html'
        }
    else:
        return {
            '__template__':'signin.html'
        }

async def api_manage_blogs(page_index,user_id):
    num = await Blog.findNumber('id',' where %s = \'%s\'' % ('user_id',user_id))
    page = Page(num,page_index)
    extra = ''
    if page.page_index < 100:
        extra = ' order by created_at desc limit %s,%s' % (page.offset,page.limit)
    else:
        extra = ' and created_at <= (select created_at from blogs where user_id = \'%s\' order by created_at desc limit %s,1) order by created_at desc limit %s' % (request.__user__.id,page.offset,page.limit)
    blogs = await Blog.findAll("user_id",user_id,extra)
    return (blogs,page)

async def api_manage_comments(page_index,user_id):
    num = await Comment.findNumber('id',' where %s = \'%s\'' % ('user_id',user_id))
    page = Page(num,page_index)
    extra = ''
    if page.page_index < 100:
        extra = ' order by created_at desc limit %s,%s' % (page.offset,page.limit)
    else:
        extra = ' and created_at <= (select created_at from comments where user_id = \'%s\' order by created_at desc limit %s,1) order by created_at desc limit %s' % (request.__user__.id,page.offset,page.limit)
    comments = await Comment.findAll("user_id",user_id,extra)

    for comment in comments:
        blog = await Blog.find(comment.get('blog_id'))
        comment['blog_name'] = blog.name
    return (comments,page)

async def api_manage_users(page_index):
    num = await User.findNumber('id')
    page = Page(num,page_index)
    extra = ''
    if page.page_index < 100:
        extra = ' order by created_at desc limit %s,%s' % (page.offset,page.limit)
    else:
        extra = ' and created_at <= (select created_at from users order by created_at desc limit %s,1) order by created_at desc limit %s' % (page.offset,page.limit)
    users = await User.sql_select(extra)
    return (users,page)

@post('/api/manage')
async def api_manage(request):
    result = {}

    if request.__user__:
        params = await parse_post_params(request)
        pageTag:str = params.get('pageTag','part_blog')
        page_index:int = int(params.get('pageIndex',1))
        items,page = None,None

        if pageTag == 'part_blog':
            items,page = await api_manage_blogs(page_index,request.__user__.id)
        elif pageTag == 'part_comment':
            items,page = await api_manage_comments(page_index,request.__user__.id) 
        elif pageTag == 'part_user':
            items,page = await api_manage_users(page_index)

        result["items"] = items
        result['page'] = {'page_count':page.page_count,'page_index':page.page_index}
        result['status'] = 'ok'
    else:
        result['status'] = 'fail'
        result['msg'] = 'novail'

    resp = web.Response()
    resp.content_type = 'application/json'
    resp.body = json.dumps(result,ensure_ascii = False).encode('utf-8')

    return resp

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

@post('/api/get/blog')
async def api_get_blog(request):
    result = {}

    if request.__user__:
        user = request.__user__
        params = await parse_post_params(request)
        id:str = params.get('id',None)
        blog = await Blog.find(id)

        result["blog"] = blog
        result['status'] = 'ok'
    else:
        result['status'] = 'fail'
        result['msg'] = 'novail'

    resp = web.Response()
    resp.content_type = 'application/json'
    resp.body = json.dumps(result,ensure_ascii = False).encode('utf-8')
    
    return resp

@post('/api/update/blog')
async def api_update_blog(request):
    result = {}

    if request.__user__:
        user = request.__user__
        params = await parse_post_params(request)
        name:str = params.get('name',None)
        summary:str = params.get('summary',None)
        content:str = params.get('content',None)

        id:str = params.get('id',None)

        blog = await Blog.find(id)

        blog.name = name
        blog.summary = summary
        blog.content = content

        await blog.update()

        result["id"] = blog.id
        result['status'] = 'ok'
    else:
        result['status'] = 'fail'
        result['msg'] = 'novail'

    resp = web.Response()
    resp.content_type = 'application/json'
    resp.body = json.dumps(result,ensure_ascii = False).encode('utf-8')
    
    return resp

@post('/api/delete/blog')
async def api_delete_blog(request):
    result = {}

    if request.__user__:
        user = request.__user__
        params = await parse_post_params(request)

        id:str = params.get('id',None)

        await Blog.remove(id)

        result['status'] = 'ok'
    else:
        result['status'] = 'fail'
        result['msg'] = 'novail'

    resp = web.Response()
    resp.content_type = 'application/json'
    resp.body = json.dumps(result,ensure_ascii = False).encode('utf-8')
    
    return resp

@post('/api/create/comment')
async def api_create_comment(request):
    result = {}

    if request.__user__:
        user = request.__user__
        params = await parse_post_params(request)
        blog_id:str = params.get('blog_id',None)
        content:str = params.get('content',None)

        comment = Comment(blog_id=blog_id,user_id=user.id,user_name=user.name,user_image=user.image,content=content)
        
        await comment.save()

        result["comment"] = comment
        result['status'] = 'ok'
    else:
        result['status'] = 'fail'
        result['msg'] = 'novail'

    resp = web.Response()
    resp.content_type = 'application/json'
    resp.body = json.dumps(result,ensure_ascii = False).encode('utf-8')
    
    return resp

@post('/api/get/comments')
async def api_get_comments(request):
    result = {}

    if request.__user__:
        user = request.__user__
        params = await parse_post_params(request)
        blog_id:str = params.get('blog_id',None)

        comments = await Comment.findAll("blog_id",blog_id)

        result["comments"] = comments
        result['status'] = 'ok'
    else:
        result['status'] = 'fail'
        result['msg'] = 'novail'

    resp = web.Response()
    resp.content_type = 'application/json'
    resp.body = json.dumps(result,ensure_ascii = False).encode('utf-8')
    
    return resp

@post('/api/delete/comment')
async def api_delete_comment(request):
    result = {}

    if request.__user__:
        user = request.__user__
        params = await parse_post_params(request)

        id:str = params.get('id',None)

        await Comment.remove(id)

        result['status'] = 'ok'
    else:
        result['status'] = 'fail'
        result['msg'] = 'novail'

    resp = web.Response()
    resp.content_type = 'application/json'
    resp.body = json.dumps(result,ensure_ascii = False).encode('utf-8')
    
    return resp