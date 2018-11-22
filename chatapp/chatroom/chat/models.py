from chat.chatdbutils import MysqlConnection
from chat.redisutil import RedisUtils


class GroupFile(object):
    def __init__(self,source,destination,fileurl,isgroup):
        self.source = source
        self.destination = destination
        self.fileurl = fileurl
        self.isgroup = isgroup

    @classmethod
    def insert_file(cls,source,destination,fileurl,filename):
        _sql = "insert into groupfile(source,destination,fileurl,filename) values(%s,%s,%s,%s)"
        _args = (source,destination,fileurl,filename)
        _rowId= MysqlConnection.execute_sql(_sql,_args,fetch=False,getRowId=True)
        return _rowId

    @classmethod
    def get_files(cls,username):
        _,_rts = UserInRoom.getRoomList(username)
        roomlist = [v[1] for v in _rts]
        _sql = "select id,source,destination,fileurl,filename,date_format(ctime,'%%Y-%%m-%%d %%T') as ctime from groupfile "

        for index,value in enumerate(roomlist):
            if index == 0:
                _sql = _sql + "where destination = \"%s\" "%value
            else:
                _sql = _sql + "or destination = \"%s\" "%value
        _args = ()
        _cnt1,_rts1 = MysqlConnection.execute_sql(_sql,_args,fetch=True)
        return _cnt1,_rts1

class ChatMsg(object):
    def __init__(self,source,destination,msg):
        self.source = source
        self.destination = destination
        self.msg = msg

    @classmethod
    def add_chatMsg(cls,source,sourceimg,destination,msg,isimg=0):
        _sql = "insert into chatmsg(source,sourceimg,destination,msg,isimg) values(%s,%s,%s,%s,%s)"
        _args = (source,sourceimg,destination,msg,isimg)
        _rowid = MysqlConnection.execute_sql(_sql,_args,fetch=False,getRowId=True)
        #返回插入的消息的id
        return _rowid

    @classmethod
    def get_chatMsg(cls,username):
        #根据username查询用户所在的群聊有那些userinroom
        _cnt,_rts = UserInRoom.getRoomList(username)
        roomlist = [v[1] for v in _rts]

        _sql = "select id,source,sourceimg,destination,msg,date_format(ctime,'%%Y-%%m-%%d %%T') as ctime,isimg from chatmsg "

        for index,value in enumerate(roomlist):
            if index == 0:
                _sql = _sql + "where destination = \"%s\" "%value
            else:
                _sql = _sql + "or destination = \"%s\" "%value
            # else:
            #     _sql = _sql + "or destination = %s "%value
        # print("打印一下拼接的sql语句：",_sql)
        _args = ()
        _cnt1,_rts1 = MysqlConnection.execute_sql(_sql,_args,fetch=True)
        return _cnt1,_rts1

    @classmethod
    def getOneGroupMsg(cls,roomname,lastid = 0):
        #offset 表示排序之后第offset列之后取limit个数据出来.前端需要倒排插入数据,旧的聊天记录需要放在后面concat一下.
        _sql = ""
        if lastid == 0:
            _sql = "select * from (select * from (select id, source, sourceimg, destination, msg, date_format(ctime, '%%Y-%%m-%%d %%T') as ctime, isimg from chatmsg where destination = '{0}' order by id) a order by a.id desc limit 6) b order by b.id".format(roomname)
        else:
            _sql = "select * from (select * from (select id, source, sourceimg, destination, msg, date_format(ctime, '%%Y-%%m-%%d %%T') as ctime, isimg from chatmsg where destination = '{0}' order by id) a where a.id < {1} order by a.id desc limit 6) b order by b.id".format(roomname,lastid)
        # print(_sql)
        _args = ()
        _cnt,_rts = MysqlConnection.execute_sql(_sql,_args,fetch=True)
        return _cnt,_rts

    @classmethod
    def getInitChatMsg(cls):
        #TODO 获取最新的15条消息
        _sql = "select a.id,a.source,b.header,a.destination,a.msg,date_format(a.ctime,'%%Y-%%m-%%d %%T') as ctime,isimg from chatmsg a,user b where a.source = b.name and a.destination = '聊天大厅' order by a.id limit 15"
        _args = ()
        _cnt,_rts = MysqlConnection.execute_sql(_sql,_args,fetch=True)
        return _cnt,_rts

    @classmethod
    def getUserLastMsgId(cls,roomname):
        _sql = "select MAX(id) from chatmsg where destination=%s"
        _args = (roomname,)
        _cnt,_rts = MysqlConnection.execute_sql(_sql,_args,fetch=True)
        return _cnt,_rts

class User(object):
    def __init__(self,name,header):
        self.name = name
        self.header = header
        self.redis = RedisUtils()

    @classmethod
    def add_user(cls,name,pwd,header):
        _sql = "insert into user(name,pwd,header) value(%s,%s,%s)"
        _args = (name,pwd,header)
        _cnt = MysqlConnection.execute_sql(_sql,_args,fetch=False)
        return _cnt


    @classmethod
    def get_user(cls,name):
        _sql = "select id from user where name=%s"
        _args = (name,)
        _cnt = MysqlConnection.execute_sql(_sql,_args,fetch=False)
        return _cnt

    @classmethod
    def searchuser(cls,name):
        _sql = "select id,name,header from user where name like '%%%%%s%%%%'"%name
        _args = ()
        _count,_rt_lists = MysqlConnection.execute_sql(_sql,_args,fetch=True)
        return _count,_rt_lists

    @classmethod
    def getUserLoginInfo(cls,username,password):
        _sql = "select id,name,header from user where name = %s and pwd = %s"
        _args = (username,password)
        _cnt,_rts = MysqlConnection.execute_sql(_sql,_args,fetch=True)
        return _cnt,_rts


class Room(object):
    def __init__(self,rname,rimg,username):
        self.rname = rname
        self.rimg = rimg
        self.username = username

    def has_room(self):
        _sql = "select count(*) from room where rname=%s"
        _args = (self.rname,)
        _cnt = MysqlConnection.execute_sql(_sql,_args,fetch=True)
        return _cnt[1][0][0]

    @classmethod
    def add_room(cls,rname,rimg,username):
        _sql = "insert into room(rname,rimg,username)value(%s,%s,%s)"
        _args = (rname,rimg,username)
        _roomUtil = Room(rname,rimg,username)
        _cnt1 = _roomUtil.has_room()

        if _cnt1 != 0:
            return 0
        else:
            _cnt = MysqlConnection.execute_sql(_sql, _args, fetch=False)
            UserInRoom.setUserInRoom(rname,username)
            return _cnt[0]
            #貌似永远返回1

    @classmethod
    def searchroom(cls,rname):
        _sql = "select id,rname,rimg from room where rname like '%%%%%s%%%%'"%rname
        _args = ()
        _count,_rt_lists = MysqlConnection.execute_sql(_sql,_args,fetch=True)
        return _count,_rt_lists


class UserInRoom(object):
    def __init__(self,roomname,username):
        self.roomname = roomname
        self.username = username

    @classmethod
    def getRoomList(cls,username):
        _sql = ""
        _args = ()
        # print("username为空吗？",username)
        if username == "":
            _sql = "select id,rname,username,rimg from room where id = 1 "
        else:
            _sql = "select a.id,a.roomname,a.username,b.rimg from userinroom a,room b where a.username=%s and a.roomname = b.rname order by id"
            _args = (username,)
            #不要点号，才能获取全部数据，不然会报错
        _count, _rt_list = MysqlConnection.execute_sql(_sql,_args,fetch=True)
        # print("打印房间列表：",_rt_list)

        return _count,_rt_list

    def has_user(self):
        _sql = "select count(*) from userinroom where username=%s and roomname=%s"
        _args = (self.username,self.roomname)
        _rt = MysqlConnection.execute_sql(_sql,_args,fetch=True)
        return _rt[1][0][0]

    @classmethod
    def setUserInRoom(cls,roomname,username):
        _Util = UserInRoom(roomname,username)

        _cnt1 = _Util.has_user()
        if _cnt1 != 0:
            # _sql1 = "update userinroom set count=%s where username=%s and roomname=%s"
            # _args1 = (1,username,roomname)
            # _cnt = MysqlConnection.execute_sql(_sql1,_args1,fetch=False)
            # # return "你已经在房间里了~"
            # return _cnt[0] - 1 #成功的话是0
            return 0
        else:
            _sql2 = "insert into userinroom(roomname,username) values(%s,%s)"
            _arg2 = (roomname,username)
            _cnt2 = MysqlConnection.execute_sql(_sql2,_arg2,fetch=False)
            return _cnt2[0] #成功的话是1

    @classmethod
    def getAllUserRooms(cls):
        # _sql = "select username,roomname from userinroom"
        _sql = "select a.username,b.header,a.roomname from userinroom a,user b where a.username = b.name"
        _args = ()
        _cnt,_rts = MysqlConnection.execute_sql(_sql,_args,fetch=True)
        return _cnt,_rts

    @classmethod
    def updateLastAckMsg(cls,source,destination,msgid):
        _sql = "update userinroom set last_ack_msgid=%s where username=%s and roomname=%s"
        _args = (msgid,source,destination)
        _cnt = MysqlConnection.execute_sql(_sql,_args,fetch=False)
        return _cnt

    @classmethod
    def setUserOutLeaveRoom(cls,username,roomname):
        _sql = "update userinroom set last_ack_msgid = 1 where username=%s and roomname=%s"
        _args = (username,roomname)
        _cnt = MysqlConnection.execute_sql(_sql,_args,fetch=False)
        return _cnt

    #最后一条消息的时间
    @classmethod
    def getLastAckMsgId(cls,username):
        _sql = "select last_ack_msgid,roomname from userinroom where username = %s"
        _args = (username,)
        _,_rts = MysqlConnection.execute_sql(_sql,_args,fetch=True)
        rts = {}
        for v in _rts:
            rts[v[1]] = v[0]
        return rts

    @classmethod
    def deleteUserInRoom(cls,username,roomname):
        _sql = "delete from userinroom where username = %s and roomname = %s"
        _args = (username,roomname)
        _cnt = MysqlConnection.execute_sql(_sql,_args,fetch=False)
        return _cnt[0]

class FriendMsg(object):
    def __init__(self,source,touser,msg):
        self.source = source
        self.touser = touser
        self.msg    = msg

    @classmethod
    def setMyfriendMsg(cls,myname,sourceimg,friend,msg,isimg=0):
        _sql = "insert into friendmsg(source,sourceimg,touser,msg,isimg) values(%s,%s,%s,%s,%s)"
        _args = (myname,sourceimg,friend,msg,isimg)
        _cnt = MysqlConnection.execute_sql(_sql,_args,fetch=False)
        return _cnt

    @classmethod
    def getMyfriendMsg(cls,myname):
        _sql = "select id,source,sourceimg,touser,msg,date_format(ctime,'%%Y-%%m-%%d %%T') as ctime,isimg,isread from friendmsg where source = %s or touser = %s"
        _args = (myname,myname)
        _cnt,_rts = MysqlConnection.execute_sql(_sql,_args,fetch=True)
        return _cnt,_rts

    @classmethod
    def getOneFriendMsg(cls,myname,friend,lastid = 0):
        #offset 表示排序之后第offset列之后取limit个数据出来.前端需要倒排插入数据,旧的聊天记录需要放在后面concat一下.
        _sql = ""
        if lastid == 0:
            _sql = "select * from (select * from (select id, source, sourceimg, touser, msg, date_format(ctime, '%%Y-%%m-%%d %%T') as ctime, isimg, isread from friendmsg where source = '{0}' and touser = '{1}' or source = '{2}' and touser = '{3}' order by id) a order by a.id desc limit 6) b order by b.id".format(myname,friend,friend,myname)
        else:
            _sql = "select * from (select * from (select id, source, sourceimg, touser, msg, date_format(ctime, '%%Y-%%m-%%d %%T') as ctime, isimg, isread from friendmsg where source = '{0}' and touser = '{1}' or source = '{2}' and touser = '{3}' order by id) a where a.id < {4} order by a.id desc limit 6) b order by b.id".format(myname,friend,friend,myname,lastid)
        # print(_sql)
        _args = ()
        _cnt,_rts = MysqlConnection.execute_sql(_sql,_args,fetch=True)
        return _cnt,_rts

    @classmethod
    def setReadUserMsg(cls,myname,friend):
        _sql = "update friendmsg set isread = 1 where isread = 0 and source=%s and touser=%s"
        _args = (myname,friend)
        _cnt = MysqlConnection.execute_sql(_sql,_args,fetch=False)
        return _cnt

class Friend(object):
    def __init__(self, myname, friend):
        self.myname = myname
        self.friend = friend

    def isExist(self):
        _sql = "select count(*) from friend where myname =%s and friend=%s"
        _args = (self.myname, self.friend)
        _rt = MysqlConnection.execute_sql(_sql, _args, fetch=True)
        return _rt[1][0][0]

    @classmethod
    def add_friend(cls, myname, friend):

        _util = Friend(myname, friend)
        _isexist = _util.isExist()

        if _isexist != 0:
            return 0
        else:
            _sql1 = "insert into friend(myname,friend) values (%s,%s)"
            _args1 = (myname, friend)
            _sql2 = "insert into friend(myname,friend) values (%s,%s)"
            _args2 = (friend,myname)
            _cnt1 = MysqlConnection.execute_sql(_sql1, _args1, fetch=False)
            _cnt2 = MysqlConnection.execute_sql(_sql2, _args2, fetch=False)
            return _cnt2[0]  # 成功返回1

    @classmethod
    def get_friends(cls, myname):
        _sql = "select a.myname,a.friend,b.header from friend a,user b where a.myname = %s and a.friend = b.name "
        _args = (myname,)
        _cnt, _rts = MysqlConnection.execute_sql(_sql, _args, fetch=True)
        return _cnt, _rts

    @classmethod
    def get_myfriendlist(cls,myname):
        _sql = "select friend from friend where myname = %s"
        _args = (myname,)
        _cnt,_rts = MysqlConnection.execute_sql(_sql,_args,fetch=True)
        return _cnt,_rts

    @classmethod
    def deleteUserFriend(cls,username,friend):
        _sql = "delete from friend where myname = %s and friend = %s"
        _args1 = (username,friend)
        _args2 = (friend,username)
        _cnt1 = MysqlConnection.execute_sql(_sql,_args1,fetch=False)
        _cnt2 = MysqlConnection.execute_sql(_sql,_args2,fetch=False)
        return _cnt1[0]+_cnt2[0]

if __name__ == "__main__":
      # UserInRoom.deleteUserInRoom("dean","1111") #未删除数据:(0, []) 删除成功:(1, [])
    # print(User.searchuser("1111"))
    #   _str = "/static/media/head0.jpg"
    #   re = _str.split("/")
    #   print(re)
    # print(UserInRoom.getAllUserRooms())
#     Room.add_room("测试群","sdf","deanyang")
#     _cnt, _rts = UserInRoom.getRoomList("dean")
#     roomlist = [v[1] for v in _rts]
#     print(_cnt,roomlist)
    # _cnt,_rts = ChatMsg.get_chatMsg("dean")
    # print(_cnt,_rts)
    # _cnt,_rts = ChatMsg.getUserLastMsgId("dean","聊天大厅")
    # print(_rts[0][0])
    # print(UserInRoom.getLastAckMsgId("deanyang"))
    #lastid传字符串还是数值没所谓
    # print(FriendMsg.getOneFriendMsg("deanyang","dean1996","7"))
      # (3, ((4, 'deanyang', 'http://192.168.79.128:9002/chat/showimage/head8.jpg', 'dean1996', '问问',
      #       '2018-10-30 19:41:45', 0, 1), (
      #      5, 'dean1996', 'http://192.168.79.128:9002/chat/showimage/head4.jpg', 'deanyang', '问问',
      #      '2018-10-30 19:41:51', 0, 1), (
      #      6, 'dean1996', 'http://192.168.79.128:9002/chat/showimage/head4.jpg', 'deanyang', 'a啊啊啊的',
      #      '2018-10-30 19:41:54', 0, 1)))
    # print(Friend.get_myfriendlist("deanyang"))
    print(ChatMsg.getOneGroupMsg("聊天大厅",8))
