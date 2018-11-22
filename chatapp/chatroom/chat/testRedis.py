import redis

if __name__=="__main__":
    _redis = redis.Redis(host='127.0.0.1', port=6379)
    #hash操作 key-value添加
    _redis.hset("online","ssid12345","dean")
    _redis.hset("online", "ssid1234", "dean1")
    _redis.hset("online", "ssid123", "dean2")
    _redis.hset("online", "ssid12", "dean3")
    _redis.hset("online", "ssid1", "dean4")
    _redis.hset("online", "ssid", "dean5")
    # print("打印全部的key-value",_redis.hgetall("online"))
    # print("打印key为ssid的value：",_redis.hget("online","ssid")) #打印ssid的username
    # b'dean5'


    # 在name对应的hash中批量设置键值对,mapping:字典
    # dic = {"a1": "aa", "b1": "bb"}
    # r.hmset("dic_name", dic)
    # print(r.hget("dic_name", "b1"))  # 输出:bb

    # 在name对应的hash中获取多个key的值
    # li = ["a1", "b1"]
    # print(r.hmget("dic_name", li))
    # print(_redis.hmget("online", "ssid", "ssid1"))
    # [b'dean5', b'dean4']

    # # hlen(name) 获取hash中键值对的个数
    # print(_redis.hlen("online"))

    # # #hkeys(name) 获取hash中所有的key的值
    # print(_redis.hkeys("online"))
    #[b'ssid12345', b'ssid1234', b'ssid123', b'ssid12', b'ssid1', b'ssid']
    # # #hvals(name) 获取hash中所有的value的值
    # print(_redis.hvals("online"))
    # #删除指定name对应的key所在的键值对
    # _redis.hdel("online","ssid")

    # # 检查name对应的hash是否存在当前传入的key
    print(_redis.hexists("online", "ssid"))  # 输出:True

    _redis.hgetall("online")

