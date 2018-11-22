

def solute():
    # d = (("dean","聊天大厅"),("dean","react交流群"),("dean","聊天2群"),("dean123","聊天大厅"),("dean1996","聊天大厅"))
    d = (('dean','head5.jpg','聊天大厅'),('dean','head5.jpg','聊天2群'),('dean123','head1.jpg','聊天大厅'),('dean1996','head3.jpg','聊天大厅'))

    f = ['dean', 'dean123', 'dean1996']

    _d = list(d)

    print(_d)
    temp_list = []

    for val in d:
        temp = {}
        temp2 = {}
        val = list(val)
        temp[val[0]] = val[1]
        temp2[val[0]] = val[2]
        temp_list.append(temp)
        temp_list.append(temp2)

    print("temp_list",temp_list)

    # singleElem = list(set(temp_list))

    result2 = [{"username": "dean", "headimg":"head5.jpg","roomname": ["聊天大厅", "react交流群"]}, {"username": "dean1996","headimg":"head5.jpg","room": "聊天大厅"}]

    dic = {}

    for _ in temp_list:
        for k, v in _.items():
            dic.setdefault(k, []).append(v)

    will = [{k: v} for k, v in dic.items()]
    print("will",will)

    #筛选,去除掉不在线的用户的信息
    succ = []
    for _will in will:
        for _f in f:
            if _f in _will.keys():
                succ.append(_will)

    print("succ",succ)

    rts = []
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
            imglist = list(set(imglist))
            roomlist = list(set(roomlist))
            tmp["username"] = k
            tmp["headimg"] = imglist
            tmp["roomname"] = roomlist
            rts.append(tmp)
    print("最终结果:",rts)



    #{'dean': 'react交流群', 'dean123': '聊天大厅', 'dean1996': '聊天大厅'}
    #['dean', 'dean123', 'dean1996']



    result = [{"username":"dean","roomname":["聊天大厅","react交流群"]},{"username":"dean1996","room":"聊天大厅"}]




    #
    # d = [{"username": "dean", "roomname": "聊天大厅"}, {"usename": "dean", "roomname": "react交流群"},
    #  {'username': "dean123", 'roomname': "聊天大厅"}]



if __name__=="__main__":
    solute()




