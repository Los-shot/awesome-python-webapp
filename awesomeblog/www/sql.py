import aiomysql
import asyncio
import logging

async def create_pool(**kw):
    global __pool
    __pool = await aiomysql.create_pool(
        host = kw.get('host','localhost'),
        port = kw.get('port',3306),
        user = kw['user'],
        password = kw['password'],
        db = kw['db'],
        charset = kw.get('charset','utf8'),
        autocommit = kw.get('autocommit',True),
        maxsize = kw.get('maxsize',10),
        minsize  = kw.get('minsize',1),
        loop = asyncio.get_event_loop()
    )
    logging.info('create database connect pool...')

    #test connect
    # cnt = await execute('insert into user (id, name) values (?, ?)',(1,'Jack'))
    # print(cnt)
    # rs = await select('select * from user where id = %s',1)
    # print(rs)

async def select(sql,args,size = None):
    if args:
        logging.log(logging.INFO,sql.replace('?','%s'),args)
    else:
        logging.log(logging.INFO,sql)

    global __pool
    with (await __pool) as conn:
        cur = await conn.cursor(aiomysql.DictCursor)
        await cur.execute(sql.replace('?','%s'),args or ())
        if size:
            rs = await cur.fetchmany(size)
        else:
            rs = await cur.fetchall()
        await cur.close()
        logging.info('rows returned: %s' % len(rs))
        return rs

async def execute(sql,args):
    logging.log(logging.INFO,sql)
    with (await __pool) as conn:
        try:
            cur = await conn.cursor()
            await cur.execute(sql.replace('?','%s'),args)
            affected = cur.rowcount
            await cur.close()
        except BaseException as e:
            raise
        return affected

class Field(object):
    def __init__(self,column_type,primary_key,default):
        self.column_type = column_type
        self.primary_key = primary_key
        self.default = default

    def __str__(self):
        return '%s, %s:%s' % (self.__class__.__name__,self.column_type,self.name)

class StringField(Field):
    def __init__(self,primary_key = False,default = None,ddl = 'varchar(100)'):
        super().__init__(ddl,primary_key,default)

class BooleanField(Field):
    def __init__(self,default = False):
        super().__init__('bool',False,default)

class FloatField(Field):
    def __init__(self,primary_key = False,default = None):
        super().__init__('real',primary_key,default)

class TextField(Field):
    def __init__(self,primary_key = False,default = None):
        super().__init__('mediumtext',primary_key,default)

class ModelMetaclass(type):
    def __new__(cls,name,bases,attrs):
        if name == 'Model':
            return type.__new__(cls,name,bases,attrs)

        tableName = attrs.get('__table__',None) or name
        logging.info('found model: %s (table: %s)' % (name,tableName))
        mappings = dict()
        fields = []
        primaryKey = None

        for k,v in attrs.items():
            if isinstance(v,Field):
                v.name = k
                logging.info('  found mapping: %s ==>%s' % (k,v))
                mappings[k] = v
                if v.primary_key:
                    if primaryKey:
                        raise RuntimeError('Duplicate primary key for field: %s' % k)
                    primaryKey = k
                else:
                    fields.append(k)

        if not primaryKey:
            raise RuntimeError('Primary key not found')

        for k in mappings.keys():
            attrs.pop(k)

        escaped_fields = list(map(lambda f:'`%s`' % f,fields))

        attrs['__mappings__'] = mappings
        attrs['__table__'] = tableName
        attrs['__primary_key__'] = primaryKey
        attrs['__fields__'] = fields
        
        def create_args_string(length):
            ss = ''
            if length >= 1:
                ss = '%s'
                for i in range(length-1):
                    ss += ',%s'
            return ss

        attrs['__select__'] = 'select `%s`,%s from `%s`' % (primaryKey,
            ','.join(escaped_fields),tableName)
        attrs['__insert__'] = 'insert into `%s` (%s,`%s`) values (%s)' % (tableName,
            ','.join(escaped_fields),primaryKey,create_args_string(len(escaped_fields) + 1))
        attrs['__update__'] = 'update `%s` set %s where `%s` = ?' % (tableName,
            ','.join(map(lambda f:'`%s`=?' % (mappings.get(f).name or f),fields)),primaryKey)
        attrs['__delete__'] = 'delete from `%s` where `%s` = ?' % (tableName,primaryKey)
        
        return type.__new__(cls,name,bases,attrs)

class Model(dict,metaclass = ModelMetaclass):
    def __init__(self,**kw):
        super().__init__(**kw)

    def __getattr__(self,key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(r"'Model' object has no attribute '%s'" % key)
    
    def __setattr__(self,key,value):
        self[key] = value

    def getValue(self,key):
        return getattr(self,key,None)

    def getValueOrDefault(self,key):
        value = getattr(self,key,None)
        
        if value is None:
            field = self.__mappings__[key]

            if field.default is not None:
                value = field.default() if callable(field.default) else field.default
                logging.debug('using default value for %s: %s' % (key,str(value)))
                setattr(self,key,value)
        
        return value

    @classmethod
    async def find(cls,pk):
        ' find object by primary key.'
        rs = await select('%s where `%s` = ?' % (cls.__select__,cls.__primary_key__),pk,1)
        if len(rs) == 0:
            return None
        return cls(**rs[0])

    async def save(self):
        args = list(map(self.getValueOrDefault,self.__fields__))
        args.append(self.getValueOrDefault(self.__primary_key__))
        rows = await execute(self.__insert__,args)
        if rows != 1:
            logging.warn('failed to insert record: affected rows: %s' % rows)

    @classmethod
    async def findAll(cls,k,v,extra = ''):
        ' find objects by kv pair'
        rs = await select('%s where `%s` = ?%s' % (cls.__select__,k,extra),v)
        objs = []
        for v in rs:
            objs.append(cls(**v))
        return objs

    @classmethod
    async def sql_select(cls,extra = ''):
        'custom select'
        rs = await select(cls.__select__ + extra,None)
        objs = []
        for v in rs:
            objs.append(cls(**v))
        return objs

    @classmethod
    async def findNumber(cls,cntTag,extra = ''):
        rs = await select('select count(?) as cnt from %s%s' % (cls.__table__,extra),cntTag,1)
        return rs[0].get("cnt")

    async def update(self):
        args = list(map(self.getValueOrDefault,self.__fields__))
        args.append(self.getValueOrDefault(self.__primary_key__))
        rows = await execute(self.__update__,args)
        if rows != 1:
            logging.warn('failed to update record: affected rows: %s' % rows)

    @classmethod
    async def remove(cls,pk):
        ' delete object by primary key.'
        print(cls.__delete__,pk)
        rows = await execute(cls.__delete__,pk)
        if rows != 1:
            logging.warn('failed to delete record: affected rows: %s' % rows)
