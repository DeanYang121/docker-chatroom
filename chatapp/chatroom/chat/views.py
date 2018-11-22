from flask import session,request,make_response,send_from_directory,jsonify,url_for,render_template
from flask_socketio import emit,join_room,leave_room
from chat.redisutil import RedisUtils
from chat.models import User,Room,UserInRoom,ChatMsg,Friend,FriendMsg,GroupFile
from chat import app,socketio,files
import json
from threading import Lock
thread = None
thread_lock = Lock()
import os
import hashlib
from functools import wraps

def get_onlineuser_all_room_list():
    _cnt, _rts = UserInRoom.getAllUserRooms()
    _online = RedisUtils.getOnlineuser("online")
    _user_in_room = list(_rts)

    temp_list = []
    for val in _user_in_room:
        temp = {}
        temp2 = {}
        val = list(val)
        temp[val[0]] = val[1]
        temp2[val[0]] = val[2]
        temp_list.append(temp)
        temp_list.append(temp2)

    dic = {}
    for _ in temp_list:
        for k, v in _.items():
            dic.setdefault(k, []).append(v)

    will = [{k: v} for k, v in dic.items()]

    succ = []
    for _will in will:
        for _f in _online:
            if _f in _will.keys():
                succ.append(_will)

    result = []
    for _ in succ:
        tmp = {}
        for k,v in _.items():
            imglist = []
            roomlist = []
            for i in v:
                if i.endswith('.jpg'):
                    imglist.append(i)
                else:
                    roomlist.append(i)
            imglist = list(set(imglist))[0]
            roomlist = list(set(roomlist))
            tmp["username"] = k
            tmp["headimg"] = imglist
            tmp["room"] = roomlist
            result.append(tmp)

    return result

@socketio.on("connect",namespace="/users")
def user_connect():
    pass

@socketio.on("disconnect",namespace="/users")
def user_disconnect():
    pass

@socketio.on("sendmsg",namespace="/users")
def handle_reciveusermsg(json):
    _user = json["myname"]
    _friend = json["friend"]
    _msg = json["msg"]
    _headimg = json["headimg"]
    json["ctime"] = ""

    _sid = [RedisUtils.getSidbyUser(_user),RedisUtils.getSidbyUser(_friend)]
    json["isread"] = 0

    for _room in _sid:
        emit("recvusermsg",json,room=_room)

    _cnt = FriendMsg.setMyfriendMsg(_user,_headimg,_friend,_msg)


@socketio.on('disconnect',namespace='/chatroom')
def test_disconnect():
    ssid = request.sid

    isexist = RedisUtils.issidExist("online",ssid)
    username = RedisUtils.getUserbySid("online",ssid)
    #断开连接，将用户剔除其所在的所有的房间列表。
    _, rooms = UserInRoom.getRoomList(username)
    roomlist = [v[1] for v in rooms]
    for val in roomlist:
        leave_room(val)

    if username:
        RedisUtils.delListValue("session",username)

    if isexist:
        RedisUtils.delHSet("online",ssid)
    #获取最新在线用户的列表
    result = get_onlineuser_all_room_list()
    emit("online", result, namespace='/chatroom', broadcast=True)

@socketio.on("connect",namespace='/chatroom')
def recive_my_event():
    _cnt,_rt = ChatMsg.getInitChatMsg()
    _rt_lists = []
    _colume = ('roomid','source','headimg','destination','msg','ctime',"isimg")
    for val in _rt:
        _rt_lists.append(dict(zip(_colume,val)))
    #这里不需要广播，只需要返回给连接上来的用户，默认只会返回给默认的用户
    emit("msglist", _rt_lists)



    # global thread
    # with thread_lock:
    #     if thread is None:
    #         thread = socketio.start_background_task(target=sendOnlineUser)

@socketio.on("login",namespace='/chatroom')
def receive_loginInfo(json):
    socketId = request.sid
    username = json["username"]
    password = json["password"]

    # reconnect = json["reconnect"]
    #reconnet true 为重连的

    #1.获取用户的在线信息 如果已经登录,返回空数据 空的聊天室列表,空的在线用户信息,空的聊天消息,空的文件列表 通过一个全局的session数据去判断是否登录
    islogin = RedisUtils.isHaveVal("session", username)
    if islogin:
        pass
    else:
        password = hashlib.md5(password.encode('utf-8')).hexdigest()
        _cnt, _rts = User.getUserLoginInfo(username, password)
        if _cnt == 0:
            pass
        elif _cnt == 1:
            #对于新用户，此时数据库中还有用户的房间信息，所以无法查询到房间信息。
            #如果用户没有登录用户插入到全局的session中去

            _, rooms = UserInRoom.getRoomList(username)
            roomlist = [v[1] for v in rooms]
            if len(roomlist) == 0:
                join_room("聊天大厅")
            else:
                for val in roomlist:
                    join_room(val)


            RedisUtils.pushHset("online",socketId,username)

            #获取用户在线信息
            result = get_onlineuser_all_room_list()
            #通知用户上线
            noticeOnline = "%s上线啦,^.^" % username

            emit("online", result, namespace='/chatroom', broadcast=True)
            emit("recvonlinenotice",noticeOnline,broadcast=True)

@socketio.on('my event',namespace='/chatroom')
def handle_my_custom_event(json):
    print('收到的socket json值: ' + str(json))

@socketio.on('sendmsg',namespace='/chatroom')
def handle_receiveChatMsg_event(json):
    # _user = json["source"]
    _room = json["destination"]
    json["isread"] = 0
    emit("recvmsg", json, room=_room)
    # emit("recvmsg",json,broadcast=True)
    # print(_room,json["source"],json["headimg"],json["destination"],json["msg"])
    _rowid = ChatMsg.add_chatMsg(json["source"],json["headimg"],json["destination"],json["msg"])
    # UserInRoom.updateLastAckMsg(json["source"],_room,_rowid)
    # print('收到用户发来的消息：',json)

@app.route("/",methods=["GET"])
def index():
    return render_template('index.html')


@app.route("/chat/download/<filename>",methods=["GET"])
def download_file(filename):
    file_dir = "/home/code/chatroom/uploads/files"
    response = make_response(send_from_directory(file_dir,filename,as_attachment=True))
    response.headers["Content-Disposition"] = "attachment;filename={}".format(filename.encode().decode('latin-1'))
    return response

@app.route("/chat/showimage/<imagename>",methods=["GET"])
def getMsgImg(imagename):
    image_dir = "/home/code/chatroom/uploads/files"
    if request.method == 'GET':
        if imagename is None:
            pass
        else:
            image_data = open(os.path.join(image_dir,'%s'%imagename),"rb").read()
            response = make_response(image_data)
            response.headers['Content-Type'] = 'image/jpg'
            return response
    else:
        return json.dumps({"code":1,"error":"没有参数imagename"})

@app.route("/chat/getfilelist")
def showFileList():
    _result = []
    username = request.args.get("username",default=None)
    if username:
        _cnt,_rts = GroupFile.get_files(username)
        _colume = ('id','username','roomname','fileurl','filename','ctime')
        for val in _rts:
            _result.append(dict(zip(_colume,val)))
    return json.dumps({"code":0,"data":_result})

@app.route("/chat/uploadfile/",methods=["POST"])
def uploadGroupFile():
    if request.method == "POST" and 'file' in request.files:
        filename = request.form.get("filename",None)
        if filename != None:
            _ = files.save(request.files["file"],name=filename)
        else:
            filename = files.save(request.files["file"])
        # username = session["username"]
        username = request.form.get("username",None)
        roomname = request.form.get("someone",None)
        if username != None and roomname != None:
            #TODO 硬编码放在配置文件，读取出来。 上传进度条自己实现。
            file_path = "http://127.0.0.1/chat/download/%s"%filename
            _rowId = GroupFile.insert_file(username,roomname,file_path,filename)
            socketio.emit("recvfile",{"id":_rowId,"username":username,"roomname":roomname,"fileurl":file_path,"filename":filename},namespace='/chatroom',room=roomname)
    return json.dumps({"code":0,"data":_rowId})

@app.route("/chat/uploademoji/",methods=["POST"])
def upload():
    if request.method == "POST" and 'emojiImg' in request.files:
        filename = request.form.get("imgname","")
        username = request.form.get('username',"")
        headimg = request.form.get("headimg","")

        #房间名可以换成是用户名,实现用户之间的表情包发送
        roomname = request.form.get("someone", "")
        tofriend = request.form.get("friend","")

        if len(filename) != 0 :
            _ = files.save(request.files['emojiImg'], name=filename)
        else:
            filename = files.save(request.files['emojiImg'])
        #TODO
        imgurl = "http://127.0.0.1/chat/showimage/%s" % filename
        print("tofriend:",len(tofriend))
        if len(tofriend) == 0:
            data = {"source": username, "headimg": headimg, "destination": roomname, "msg": imgurl, "isread": 0,
                    "isimg": 1}
            socketio.emit("recvmsg", data, namespace='/chatroom', room=roomname)
            ChatMsg.add_chatMsg(username, headimg, roomname, imgurl, isimg=1)
            return jsonify({"code": 0, "data": imgurl})
        else:
            # _colume = ("id", "myname", "headimg", "friend", "msg", "ctime", "isread")
            #TODO PEP8
            data = {"myname":username,"headimg":headimg,"friend":tofriend,"msg":imgurl,"ctime":"","isimg":1,"isread":0}
            _sid = [RedisUtils.getSidbyUser(username), RedisUtils.getSidbyUser(tofriend)]
            for _room in _sid:
                socketio.emit("recvusermsg", data, namespace="/users",room=_room)

            _cnt = FriendMsg.setMyfriendMsg(username, headimg, tofriend, imgurl,isimg=1)
            return jsonify({"code": 0, "data": imgurl})

@app.route("/chat/readgroupmsgs/",methods=["POST"])
def handle_userReadGroupMsgs():
    data = request.get_data()
    _data = json.loads(data.decode("utf-8"))
    _username = _data["username"]
    _roomname = _data["roomname"]
    _cnt,_rts = ChatMsg.getUserLastMsgId(_roomname) #获取用户的某一个聊天室所接收到的消息的最大id
    if(_rts[0][0] != None):
        UserInRoom.updateLastAckMsg(_username,_roomname,_rts[0][0])
    return json.dumps({"code":0,"data":"更新用户最新消息成功"})

@app.route("/chat/userleaveroom/",methods=["POST"])
def handle_userLeaveRoom():
    data = request.get_data()
    _data = json.loads(data.decode("utf-8"))
    _username = _data["username"]
    _roomname = _data["roomname"]
    UserInRoom.setUserOutLeaveRoom(_username,_roomname)
    #前端监听用户离开房间的事件？

@app.route("/chat/readusermsgs/",methods=["POST"])
def handle_readusermsg():
    data = request.get_data()
    _data = json.loads(data.decode("utf-8"))
    _myname = _data["myname"]
    _friend = _data["friend"]
    #此处有个坑我的名字需要是朋友的名字  好友是我的名字才行 因为是朋友发给我的
    FriendMsg.setReadUserMsg(_friend,_myname)
    return json.dumps({"code":0,"data":"更新成功"})

@app.route("/chat/getsearchuser",methods=["GET"])
def handle_getSearchUser():
    username = request.args.get("username",default=False)
    _colume = ('userid','username','headimg')
    if username:
        _cnt,_rts = User.searchuser(username)
        _result = []
        for val in _rts:
            _result.append(dict(zip(_colume,val)))
        return json.dumps({"code":0,"count":_cnt,"data":_result},ensure_ascii=False)
    else:
        return json.dumps({"code":1,"data":""},ensure_ascii=False)

@app.route("/chat/getusermsglist2",methods=["GET"])
def getUserInitMsgList():
    _user = request.args.get("username",default=False)
    _colume = ("id","myname","headimg","friend","msg","ctime","isimg","isread")
    if _user:
        usermsgdictid = {}
        usermsglist = []
        _cnt,_rts = Friend.get_myfriendlist(_user)
        #获取每个朋友的前6条信息,放到usrmsglist中去 (2, (('dean',), ('dean1996',)))
        for val in _rts:
            _cnt2,_rts2 = FriendMsg.getOneFriendMsg(_user,val[0])
            if _cnt2!= 0:
                usermsgdictid[val[0]] = _rts2[0][0]
                for _val in _rts2:
                    usermsglist.append(dict(zip(_colume,_val)))
        return jsonify({"code":0,"data":usermsglist,"msgdictid":usermsgdictid})

@app.route("/chat/getoneusermsg",methods=["GET"])
def getUserOneMsgList():
    _user   = request.args.get("username",default=False)
    _friend = request.args.get("friend",default=False)
    _lastid = request.args.get("lastid",default=False)
    _colume = ("id","myname","headimg","friend","msg","ctime","isimg","isread")

    if _user and _friend and _lastid and _lastid != "undefined":
        usermsgdictid = {}
        usermsglist = []
        #获取每个朋友的前lastid之后的6条信息,放到usrmsglist中去 (2, (('dean',), ('dean1996',)))
        _cnt2,_rts2 = FriendMsg.getOneFriendMsg(_user,_friend,lastid=_lastid)
        if _cnt2 != 0:
            usermsgdictid[_friend] = _rts2[0][0]
            for _val in _rts2:
                usermsglist.append(dict(zip(_colume,_val)))
            return jsonify({"code":0,"data":usermsglist,"msgdictid":usermsgdictid})
        else:
            return jsonify({"code": 1,"error":"没有更多数据可获取"})
    else:
        return jsonify({"code":1,"data":[],"msgdictid":{}})



@app.route('/chat/getusermsglist',methods=["GET"])
def getUserMsgList():

    _user = request.args.get("username",default=False)
    _colume = ("id","myname","headimg","friend","msg","ctime","isimg","isread")
    if _user:
        userMsgList = []
        _cnt,_rts = FriendMsg.getMyfriendMsg(_user)
        for val in _rts:
            userMsgList.append(dict(zip(_colume,val)))
        return json.dumps({"code":0,"data":userMsgList},ensure_ascii=False)
    else:
        return json.dumps({"code":1,"data":"myname不能为空"},ensure_ascii=False)


@app.route('/chat/getmyusers',methods=["GET"])
def getmyusers():
    _user = request.args.get("myname",default="")
    _cnt,_rts = Friend.get_friends(_user)
    _colume = ("myname","friend","friendimg")

    friendlist = []
    for val in _rts:
        friendlist.append(dict(zip(_colume,val)))
    return json.dumps({"code":0,"data":friendlist},ensure_ascii=False)


@app.route('/chat/createmyusers/',methods=["POST"])
def createMyusers():
    data = request.get_data()
    user_data = json.loads(data.decode("utf-8"))
    myname = user_data["myname"]
    friend = user_data["friend"]
    _cnt = Friend.add_friend(myname,friend)

    if _cnt == 0:
        return jsonify({"code":1,"error":"你们已经是好友关系了~"})
    else:
        sid = RedisUtils.getSidbyUser(friend)

        _cnt,_rts = Friend.get_friends(friend)
        _colume = ("myname","friend","friendimg")

        friendlist = []
        for val in _rts:
            friendlist.append(dict(zip(_colume,val)))

        # print("打印usesMsglist：",friendlist)
        # responseData = json.dumps({"data":friendlist})
        socketio.emit("recvnewfriend",friendlist,namespace='/users',room=sid)
        return json.dumps({"code":0,"_cnt":_cnt})

@app.route('/chat/getonegroupmsglist',methods=["GET"])
def getOneGroupmsglist():
    username = request.args.get("username",default=False)
    roomname = request.args.get("roomname",default=False)
    lastid = request.args.get("lastid",default=False)
    _colume = ('roomid', 'source', 'headimg', 'destination', 'msg', 'ctime', "isimg", "isread")

    if username and roomname and lastid and lastid != "undefined":
        groupmsgid = {}
        groupmsglist = []
        _cnt,_rts = ChatMsg.getOneGroupMsg(roomname,lastid=lastid)
        if _cnt != 0:
            groupmsgid[roomname] = _rts[0][0]
            for val in _rts:
                val = list(val)
                val.append(1)
                groupmsglist.append(dict(zip(_colume,val)))
            return jsonify({"code":0,"data":groupmsglist,"groupmsgid":groupmsgid})
        else:
            return jsonify({"code": 1,"error":"没有更多数据可获取"})
    else:
        return jsonify({"code": 1, "data": [], "groupmsgid": {}})

@app.route('/chat/getchatmsglist2',methods=["GET"])
def getOneGroupChatMsg():
    username = request.args.get("username",default=False)
    _colume = ('roomid', 'source', 'headimg', 'destination', 'msg', 'ctime', "isimg", "isread")
    if username:
        #获取每个房间最后读取消息的id
        lastRowIdDict = UserInRoom.getLastAckMsgId(username)

        _cnt, _rts = UserInRoom.getRoomList(username)
        roomlist = [v[1] for v in _rts]
        _rt_list = []
        groupmsgid = {}
        for _val in roomlist:
            _cnt2,_rts2 = ChatMsg.getOneGroupMsg(_val)
            
            if _cnt2 != 0:
                groupmsgid[_val] = _rts2[0][0]
                for _rt in _rts2:
                    _rt = list(_rt)
                    if _rt[0] > lastRowIdDict.get(_rt[3]) and _rt[1] != username:
                        _rt.append(0)
                    else:
                        _rt.append(1)
                    _rt_list.append(dict(zip(_colume,_rt)))
            else:
                groupmsgid[_val] = _cnt2
        return jsonify({"code":0,"data":_rt_list,"groupmsgid":groupmsgid})
    else:
        return jsonify({"code":1,"error":"用户未登录..."})



@app.route('/chat/getchatmsglist',methods=["GET"])
def getUserChatMsgList():
    username = request.args.get("username",default=False)
    if username:
        _cnt,_rt = ChatMsg.get_chatMsg(username)

        lastRowIdDict = UserInRoom.getLastAckMsgId(username) #获取用户每个房间的最后一次确认收到消息的msgid

        # print("lastRowID",lastRowIdDict)
        # _,_rts = UserInRoom.getRoomList(username)
        # roomlist = [v[1] for v in _rts]
        _rt_lists = []
        _colume = ('roomid', 'source','headimg','destination','msg', 'ctime',"isimg","isread")
        # 对群消息的isread进行添加
        for val in _rt:
            val = list(val)
            # print(val)
            #计算那一条消息是未读的.
            if val[0] > lastRowIdDict.get(val[3]) and val[1] != username:
                val.append(0)
            else:
                val.append(1)
            # val = tuple(val)
            _rt_lists.append(dict(zip(_colume, val)))
        return json.dumps({"code":0,"data":_rt_lists},ensure_ascii=False)
    else:
        return json.dumps({"code":1,"error":"用户未登录，请先登录"})


@app.route('/chat/userjoinroom/',methods=["POST"])
def userJoinRoom():
    data = request.get_data()
    room_data = json.loads(data.decode("utf-8"))
    roomname = room_data["roomname"]
    username = room_data["username"]

    _cnt = UserInRoom.setUserInRoom(roomname,username)

    if _cnt == 0 :
        return jsonify({"code":1,"error":"你已经在房间里了~"})
    else:
        #获取目前的用户房间列表，发送回去
        userSid = RedisUtils.getSidbyUser(username)
        #将用户加入到当前聊天室
        join_room(room=roomname,sid=userSid,namespace="/chatroom")
        #更新用户所在房间的在线用户列表

        #获取用户在线信息
        result = get_onlineuser_all_room_list()
        socketio.emit("online", result, namespace='/chatroom', broadcast=True)

        _count, _rt_list = UserInRoom.getRoomList(username)
        roomlist = []
        _colume = ('roomid','roomname','username','roomimg')
        for value in _rt_list:
            roomlist.append(dict(zip(_colume,value)))

        return json.dumps({"code":0,"data":roomlist},ensure_ascii=False)


@app.route("/chat/searchroom",methods=["GET"])
def searchroom():
    _room = request.args.get("roomname",default="")
    _colume = ('roomid','roomname','roomimg')
    if _room != " ":
        _cnt,_rts = Room.searchroom(_room)
        _result = []
        for val in _rts:
            _result.append(dict(zip(_colume,val)))
        return json.dumps({"code":0,"count":_cnt,"data":_result},ensure_ascii=False)
    else:
        return json.dumps({"code":1,"data":""},ensure_ascii=False)

@app.route("/chat/deleteuser/",methods=["POST"])
def deleteUserFriend():
    data = request.get_json()
    username = data["username"]
    friend = data["friend"]

    if(username and friend):
        _cnt = Friend.deleteUserFriend(username,friend)
        if _cnt == 2:
            # usernameSid = RedisUtils.getSidbyUser(username)

            friendSid = RedisUtils.getSidbyUser(friend)

            _cnt, _rts = Friend.get_friends(friend)
            _colume = ("myname", "friend","friendimg")
            friendlist = []
            for val in _rts:
                friendlist.append(dict(zip(_colume, val)))

            socketio.emit("recvnewfriend", friendlist, namespace='/users', room=friendSid)
            #上面通知朋友他的好友列表变了
            #下面通知我自己我的好友列表变了
            _cnt1, _rts1 = Friend.get_friends(friend)
            _colume1 = ("myname", "friend")
            mylist = []
            for val in _rts1:
                mylist.append(dict(zip(_colume, val)))


            return jsonify({"code":0,"data":mylist,"msg":friend})
        else:
            return jsonify({"code":1,"error":"删除失败"})


@app.route("/chat/deleteroom/",methods=["POST"])
def deleteUserInRoom():
    data = request.get_json()
    username = data["username"]
    roomname = data["roomname"]

    if(username and roomname):
        _cnt = UserInRoom.deleteUserInRoom(username,roomname)
        if( _cnt == 1):
            # 获取用户的sid
            userSid = RedisUtils.getSidbyUser(username)
            # 将用户剔除聊天室
            leave_room(room=roomname, sid=userSid, namespace="/chatroom")

            _count, _rt_list = UserInRoom.getRoomList(username)
            roomlist = []
            _colume = ('roomid', 'roomname', 'username','roomimg')
            for value in _rt_list:
                roomlist.append(dict(zip(_colume, value)))

            #通知该房间的所有用户,该成员已退出房间
            result = get_onlineuser_all_room_list()
            socketio.emit("online",result,namespace="/chatroom",room=roomname)

            return jsonify({"code":0,"data":roomlist,"msg":roomname})
        else:
            return jsonify({"code":1,"data":"退出群聊失败"})

@app.route("/chat/createroom/",methods=["POST"])
def createRoom():
    data = request.get_data()
    room_data = json.loads(data.decode("utf-8"))
    rname = room_data["roomname"]
    rimg = room_data["roomimg"]
    ruser = room_data["username"]
    if len(rimg) < 30:
        _rimg_list = rimg.split("/")
        rimg = _rimg_list[3]
    else:
        rimg = "group3.jpg"

    rimg = "http://127.0.0.1/chat/showimage/%s"%rimg

    _cnt = Room.add_room(rname,rimg,ruser)
    if _cnt == 0:
        return  jsonify({"code":1,"error":"聊天室已经存在啦~"})
    else:
        UserInRoom.setUserInRoom(rname,ruser)
        _count, _rt_list = UserInRoom.getRoomList(ruser)
        roomlist = []
        _colume = ('roomid','roomname', 'username','roomimg')
        for value in _rt_list:
            roomlist.append(dict(zip(_colume, value)))
        sid = RedisUtils.getSidbyUser(ruser)

        join_room(room=rname,sid=sid,namespace="/chatroom")
        #获取用户在线信息
        result = get_onlineuser_all_room_list()
        socketio.emit("online", result, namespace='/chatroom', broadcast=True)

        return json.dumps({"code": 0, "data": roomlist}, ensure_ascii=False)


@app.route("/chat/getroomlist",methods=["GET"])
def getRoomList():
    _user = request.args.get('user',default=" ")
    _count, _rt_list = UserInRoom.getRoomList(_user)
    roomlist = []

    _colume = ('roomid','roomname','username','roomimg')
    for value in _rt_list:
        roomlist.append(dict(zip(_colume,value)))
    #(('聊天大厅6', 'dean'), ('聊天大厅7', 'dean'))


    return json.dumps({"code":0,"data":roomlist},ensure_ascii=False)

@app.route("/chat/userregister/",methods=["POST"])
def registeruser():
    data = request.get_json()
    username = data["registername"]
    password = data["registerpwd"]
    headimg = data["headimg"]
    if len(headimg) < 30:
        _headimg_list = headimg.split("/")
        headimg = _headimg_list[3]
    else:
        headimg = "head9.jpg"


    _cnt = User.get_user(username)
    if _cnt[0] != 0:
        return jsonify({"code":1,"msg":"用户名已存在"})
    else:
        secretpwd = hashlib.md5(password.encode('utf-8')).hexdigest()
        headimg = "http://127.0.0.1/chat/showimage/%s"%headimg
        UserInRoom.setUserInRoom("聊天大厅", username)
        _cnt = User.add_user(username,secretpwd,headimg)
        return jsonify({"code":0,"username":username,"msg":"用户注册成功"})


@app.route("/chat/userlogin/", methods=["POST"])
def userLogin():
    data = request.get_data()
    user_data = json.loads(data.decode("utf-8"))
    username = user_data["username"]
    password = user_data["password"]
    # 用户点击登录,首先判断redis全局session中是否存在，存在则提示，该用户正在被使用
    # islogin = RedisUtils.isHaveUser("online",username)
    islogin = RedisUtils.isHaveVal("session", username)
    #TODO 修改用户登录流程,判断加密密码再进行登录,并且将用户界面的头像实现修改操作,返回用户头像.
    if islogin:
        return json.dumps({'code': 1, 'isAuth': False, 'user': {'username': '', 'headimg': ''}, 'error': '用户名正在被使用...'},
                          ensure_ascii=False)
    else:
        password = hashlib.md5(password.encode('utf-8')).hexdigest()
        _cnt,_rts = User.getUserLoginInfo(username,password)
        if _cnt == 0:
            return jsonify({"code":2,'isAuth':False,'user':{'username':'','headimg':''},'error':'用户名或密码错误'})
        elif _cnt == 1:
            RedisUtils.pushListValue("session", username)
            session["username"] = username
            headimg = _rts[0][2]
            return json.dumps({'code': 0, 'isAuth': True, 'user': {'username': username, 'headimg': headimg}},
                              ensure_ascii=False)

@app.route('/chat/userlogout/',methods=["POST"])
def logout():
    # username = session.get('username')
    data = request.get_data()
    user_data = json.loads(data.decode("utf-8"))
    username = user_data["username"]


    islogin = RedisUtils.isHaveVal("session", username)
    if islogin:
        #需要通过username获取key的值
        ssid = RedisUtils.getSidbyUser(username)
        if ssid:
            RedisUtils.delHSet("online",ssid)
            # 获取最新在线用户的列表
            result = get_onlineuser_all_room_list()
            socketio.emit("online", result, namespace='/chatroom', broadcast=True)
        else:
            print("ssid为空")
        #RedisUtils.delHSet("online",)

        RedisUtils.delListValue("session", username)
        # if username:
        #     session.pop('username')
        return json.dumps({'code': 0, 'isAuth': False, 'user': {'username': '', 'headimg': ''}},
                          ensure_ascii=False)

    #return json.dumps({'code':3,'error':"还未登录..请登录"},ensure_ascii=False)
    return json.dumps({'code': 0, 'isAuth': False, 'user': {'username': '', 'headimg': ''}},
                              ensure_ascii=False)

@app.route('/chat/userData/',methods=["GET"])
def getUser():
    user = session.get("username")
    if user:
        return json.dumps({'isAuth':True,'user':user,'headimg':'xxx'})
    else:
        return json.dumps({'isAuth':False,'user':user,'headimg':'xxxx'})

#
# if __name__=="__main__":
#     print(get_onlineuser_all_room_list())







