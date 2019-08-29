import time,uuid,sql
from sql import  Model,StringField,BooleanField,TextField,FloatField

def next_id():
    return '%015d%s000' % (int(time.time() * 1000),uuid.uuid4().hex)

class User(Model):
    __table__ = 'users'

    id = StringField(primary_key = True,default = next_id,ddl = 'varchar(50)')
    email = StringField(ddl = 'varchar(50)')
    passwd = StringField(ddl = 'varchar(50)')
    admin = BooleanField()
    name = StringField(ddl = 'varchar(50)')
    image = StringField(ddl = 'varchar(500)')
    created_at = FloatField(default = time.time)

class Blog(Model):
    __table__ = 'blogs'

    id = StringField(primary_key = True,default = next_id,ddl = 'varchar(50)')
    user_id = StringField(ddl = 'varchar(50)')
    user_name = StringField(ddl = 'varchar(50)')
    user_image = StringField(ddl = 'varchar(500)')
    name = StringField(ddl = 'varchar(50)')
    summary = StringField(ddl = 'varchar(200)')
    content = TextField()
    created_at = FloatField(default = time.time)

class Comment(Model):
    __table__ = 'comments'

    id = StringField(primary_key = True,default = next_id,ddl = 'varchar(50)')
    blog_id = StringField(ddl = 'varchar(50)')
    user_id = StringField(ddl = 'varchar(50)')
    user_name = StringField(ddl = 'varchar(50)')
    user_image = StringField(ddl = 'varchar(500)')
    content = TextField()
    created_at = FloatField(default = time.time)

##-----------------------test---------------------------##
# async def test():
#     await sql.create_pool(user = 'root',password = 'password',db = 'awesome')

    ## new a User
    # u = User(name = 'Jim',email = 'Jim@163.com',passwd = '87654321',image = 'about:blank')
    # await u.save()
    ## find a User
    # u = await User.find('001559787420784740c61235a5d4d53ab1b0a9eff452f82000')
    # print(u)
    ## find users
    # us = await User.findAll('email','Jim@163.com')
    # print(us)

# import asyncio
# asyncio.get_event_loop().run_until_complete(test())