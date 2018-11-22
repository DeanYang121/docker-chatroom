import pymysql
from chat import chatdbconf

class MysqlConnection(object):

    def __init__(self,host,user,passwd,port,db,charset):
        self.__host = chatdbconf.MYSQL_HOST
        self.__user = chatdbconf.MYSQL_USER
        self.__port = chatdbconf.MYSQL_PORT
        self.__passwd = chatdbconf.MYSQL_PASSWD
        self.__db = chatdbconf.MYSQL_DB
        self.__charset = chatdbconf.MYSQL_CHARSET
        self.__conn = None
        self.__cur = None
        self.__connect()

    def __connect(self):
        try:
            self.__conn = pymysql.connect(host=self.__host,user=self.__user,password=self.__passwd,db=self.__db,port=self.__port,charset=self.__charset)
            self.__cur = self.__conn.cursor()
        except BaseException as e:
            print(str(e))

    # def execute_rowid(self,sql,args=()):
    #     _rowid = 0
    #     if self.__cur:
    #         _rowid = self.__cur.insert_id()
    #     print("打印主键ID：",_rowid)
    #     return _rowid

    def execute(self,sql,args=(),getRowId=False):
        _cnt = 0
        if self.__cur:
            if getRowId:
                _cnt1 = self.__cur.execute(sql,args)
                _cnt = self.__cur.lastrowid
            else:
                _cnt = self.__cur.execute(sql,args)
        return _cnt

    def fetch(self,sql,args=()):
        _cnt=0
        if self.__cur:
            _cnt = self.__cur.execute(sql,args)
            _rt_list = self.__cur.fetchall()
            return _cnt, _rt_list

    def commit(self):
        if self.__conn:
            self.__conn.commit()

    def close(self):
        self.commit()
        if self.__cur:
            self.__cur.close()
            self.__cur = None

        if self.__conn:
            self.__conn.close()
            self.__conn = None

    @classmethod
    def execute_sql(cls,sql,args=(),fetch=True,getRowId=False):
        _count = 0
        _rt_list = []

        _conn = MysqlConnection(host=chatdbconf.MYSQL_HOST,port=chatdbconf.MYSQL_PORT,\
                                user=chatdbconf.MYSQL_USER,passwd=chatdbconf.MYSQL_PASSWD,\
                                db=chatdbconf.MYSQL_DB,charset=chatdbconf.MYSQL_CHARSET)
        if fetch:
            _count,_rt_list = _conn.fetch(sql,args)
        else:
            _count = _conn.execute(sql,args,getRowId)
        _conn.close()
        return _count,_rt_list

    @classmethod
    def bulker_commit_sql(cls,sql,args_lists=[]):
        _cnt = 0
        _rt_list = []
        _conn = MysqlConnection(host=chatdbconf.MYSQL_HOST,user=chatdbconf.MYSQL_DB,\
                                passwd=chatdbconf.MYSQL_PASSWD,port=chatdbconf.MYSQL_PORT,\
                                charset=chatdbconf.MYSQL_CHARSET,db=chatdbconf.MYSQL_DB, \
                                )
        for _args in args_lists:
            _cnt += _conn.execute(sql,_args)
        _conn.commit()

        return _cnt,_rt_list