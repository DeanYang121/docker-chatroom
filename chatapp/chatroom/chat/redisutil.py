import redis,time
import json

class RedisUtils(object):

    def __init__(self):
        self.__conn = redis.StrictRedis(host='redis1',port=6379,decode_responses=True)
        self.chan_sub = 'session'
        self.chan_pub = 'session'

    #操作redis的hset
    def hget(self,rhash,key):
        _rts = self.__conn.hget(rhash,key)
        return _rts

    def hset(self,rhash,key,val):
        self.__conn.hset(rhash,key,val)

    def hdelete(self,rhash,key):
        self.__conn.hdel(rhash,key)

    def hgetleng(self,rhash):
        _cnts = self.__conn.hlen(rhash)
        return _cnts

    def hgetAllkeys(self,rhash):
        _rts = self.__conn.hkeys(rhash)
        return _rts

    def hexistKey(self,rhash,key):
        return self.__conn.hexists(rhash,key)

    def hgetAllVal(self,rhash):
        _rts = self.__conn.hvals(rhash)
        return _rts

    def hgetAll(self,rhash):
        _rts = self.__conn.hgetall(rhash)
        return _rts


    #操作redis的list

    def get(self,key):
        return self.__conn.get(key)

    def set(self,key,value):
        self.__conn.set(key,value)

    def GetListAll(self,key):
        _counts = self.__conn.llen(key)
        _rt = self.__conn.lrange(key,0,-1)
        return _counts,_rt

    # 这里需要将session的数据发送到指定的频道，数据格式是list，追加进去
    def PushList(self, key, value):
        self.__conn.lpush(key, value)

    def DelListVal(self,key,value):
        self.__conn.lrem(key,0,value)

    def public(self,msg):
        self.__conn.publish(self.chan_pub,msg)

    def subscribe(self):
        pub = self.__conn.pubsub()
        pub.subscribe(self.chan_sub)
        #pub.parse_response()
        while True:
            for msg in pub.listen():
                #print(pickle.loads(msg['data']))
                # print(msg)
                 if msg['type'] == 'message':
                     # cat = msg['channel']
                     hat = json.loads(msg['data'])
                     return  hat

    @classmethod
    def isHaveVal(cls, key, username):
        __utils = RedisUtils()
        _cnt, _results = __utils.GetListAll(key)
        # print("打印线上用户信息：",_results)
        if username in _results:
            return True
        else:
            return False

    @classmethod
    def pushListValue(cls,key,value):
        __utils = RedisUtils()
        __utils.PushList(key,value)

    @classmethod
    def delListValue(cls,key,value):
        __utils = RedisUtils()
        __utils.DelListVal(key,value)

    #设置在线用户信息
    @classmethod
    def pushHset(cls,rhash,key,value):
        _utils = RedisUtils()
        _utils.hset(rhash,key,value)

    @classmethod
    def delHSet(cls,rhash,key):
        _utils = RedisUtils()
        _utils.hdelete(rhash,key)

    @classmethod
    def isHaveUser(cls,rhash,username):
        _utils = RedisUtils()
        _rts = _utils.hgetAllVal(rhash)
        if username in _rts:
            return True
        else:
            return False

    @classmethod
    def getSidbyUser(cls,username):
        _utils = RedisUtils()
        _rts = _utils.hgetAll("online")
        new_dict = {v: k for k, v in _rts.items()}
        ssid = new_dict.get(username,"")
        return ssid

    @classmethod
    def getUserbySid(cls,rhash,sid):
        _utils = RedisUtils()
        _rt = _utils.hget(rhash,sid)
        return _rt

    @classmethod
    def issidExist(cls,rhash,sid):
        _utils = RedisUtils()
        _rt = _utils.hexistKey(rhash,sid)
        return _rt

    #获取在线用户的信息
    @classmethod
    def getOnlineuser(cls,rhash):
        _utils = RedisUtils()
        _rt = _utils.hgetAllVal(rhash)
        return _rt



# if __name__=="__main__":
    # _redis = RedisUtils()
    # _redis.hset("online","123","dean123")
    # _redis.hset("online", "1234", "dean1")
    # _redis.hset("online", "1232", "dean")
    # _redis.hset("online", "1231", "dean12")
    # print(RedisUtils.getOnlineuser("online"))
    # ['dean123', 'dean1', 'dean', 'dean12']





    # print(RedisUtils.getUserbySid("online","0a633b83b2724403b8df03745cea6b0f"))

    # print(_redis.hgetAllVal("online"))
    # RedisUtils().getSidbyUser("deanyang")
    # for val in ["dean","yang","du","huan","love"]:
    #     _redis.sessionPublic(val)
    # onlines,results = _redis.sessionGet("session")
    # print("打印userSession数据：",onlines,type(results))
    # for val in ["hello","world","中国","世界","宇宙～@"]:
    #     _redis.PushListVal("session",val)
    #
    # online_counts, results = _redis.GetListVal("session")
    # print("在线用户人数%s,session内容 %s："%(online_counts,results))

    # print("开始删除用户信息：world")
    # _redis.DelListVal("session","world")
    # _redis.DelListVal("session","中国")
    # print("删除之后的值：")
    # online_counts, results = _redis.GetListAll("session")
    #
    # print(results)
