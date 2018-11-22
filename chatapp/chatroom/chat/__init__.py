#encoding: utf-8
from flask import Flask
from flask_socketio import SocketIO
import redis
from flask_session import Session
from flask_uploads import UploadSet,configure_uploads,ALL


app = Flask(__name__)
app.debug = True
#文件上传
files = UploadSet('files',ALL)
#设置上传文件的地址
app.config['UPLOADS_DEFAULT_DEST'] = './uploads'
#上传文件的初始化
configure_uploads(app,files)
app.config['SECRET_KEY'] = '\xef\xd0\xb7\xdfC~i\xfcU\x13\x1e\x7fn\xfb$wm\xef\x90\xa4\xc3\x80\x9b\xe7\xb1X\xd8)\xd4\xde\xfa\xd1'
app.config["SESSION_TYPE"] = 'redis'
app.config["SESSION_PERMANENT"] = False #设置为true关闭浏览器则失效，默认为true
app.config["SESSION_USE_SIGNER"] = False #是否对发送到浏览器上session的cookie值进行加密
app.config["SESSION_KEY_PREFIX"] = 'session:' #保存到session中的值前缀
app.config["SESSION_REDIS"] = redis.Redis(host='redis1',port="6379")
async_mode = None
Session(app)
socketio = SocketIO(app,async_mode=async_mode)


from chat import views
