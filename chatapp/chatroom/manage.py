#encoding:utf-8
from chat import app,socketio


if __name__ == "__main__":
    socketio.run(app,host="0.0.0.0",port="9002")
#    app.run(host="0.0.0.0",port="9002",debug=True)