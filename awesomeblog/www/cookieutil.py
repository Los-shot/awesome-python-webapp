import time,hashlib,logging
from model import User

COOKIE_NAME = 'awesome'
MAX_AGE = 60 * 60 * 24
COOKIE_KEY = 'laliga'

def user2cookie(user,max_age):
    expires = str(int(time.time()) + MAX_AGE)
    s = '%s-%s-%s-%s' % (user.id,user.passwd,expires,COOKIE_KEY)
    L = [user.id,expires,hashlib.sha1(s.encode('utf-8')).hexdigest()]
    return '-'.join(L)

async def cookie2user(cookie_str:str):
    '''
    Parse cookie and load user if cookie is valid.
    '''
    try:
        L = cookie_str.split('-')
        if len(L) != 3:
            return None

        uid,expires,sha1 = L
        if int(expires) < time.time():
            return None

        user = await User.find(uid)
        if not user:
            return None
        
        s = '%s-%s-%s-%s' % (user.id,user.passwd,expires,COOKIE_KEY)
        if sha1 != hashlib.sha1(s.encode('utf-8')).hexdigest():
            logging.info('invalid sha1')
            return None
        
        user.passwd = '******'
        
        return user
    except Exception as e:
        logging.log(e);
        return None

    




