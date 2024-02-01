import os
import traceback
from datetime import datetime

from flask import Flask, render_template, request
from pymongo import MongoClient
import subprocess
from threading import Thread

from config import config

app = Flask(__name__)
# 环境变量配置
app.config.from_object(config['development'])
connect = MongoClient(app.config['DATABASE_URL'])
network_interface = app.config['NETWORK_INTERFACE']  # 获取网卡interface
db = connect.iftop
collection = db.flow


# 统计流量数据线程 项目启动就一直检测统计
class MyThread(Thread):
    def run(self):
        try:
            statistics()
        except Exception as e:
            print("======出错啦======")
            print(e)
            traceback.print_exc()


def statistics():
    # 运行更新后的 iftop 命令并捕获输出
    while True:
        process = subprocess.Popen(['sudo', 'iftop', '-i', network_interface, '-P', '-t', '-s', '2', '-L', '10'],
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output, _ = process.communicate()
        content = output.decode()
        splitStr = \
            content.split(
                '--------------------------------------------------------------------------------------------')[1]
        lines = splitStr.splitlines()
        if len(lines) > 1:
            lines = lines[1:]
            entityList = []
            time = datetime.now()
            for index in range(len(lines)):
                resLine = lines[index].split(" ")
                result = filter(lambda x: x != '', resLine)
                linList = list(result)
                # 判断是否换行，换行了的话需要追加到下一行重新计算
                if len(linList) < 6:
                    lines[index + 1] = linList[0] + lines[index + 1]
                    continue
                # =>表示方向对的第一行
                if linList.__contains__("=>"):
                    entity = {"ip": linList[1], "direction": linList[2], "2s": linList[3], "10s": linList[4],
                              "40s": linList[5], "time": time}
                    entityList.append(entity)
                else:
                    entity = {"ip": linList[0], "direction": linList[1], "2s": linList[2], "10s": linList[3],
                              "40s": linList[4], "time": time}
                    entityList.append(entity)
            collection.insert_many(entityList)


# 执行方法
thread = MyThread()
thread.start()


@app.route('/flask/flow', methods=['GET'])
def get_flask_flow():  # put application's code here
    return render_template('index.html')


@app.route('/flask/flow/list', methods=['GET'])
def get_flow_list():  # put application's code here
    # 页码
    page = int(request.args.get("page", 1))
    # 每页数
    limit = int(request.args.get("limit", 10))

    # 构造查询条件
    myQuery = {}

    # ip+端口
    ip = request.args.get('ip')
    if ip:
        myQuery['ip'] = {"$regex": ip, "$options": "-i"}
    # direction
    direction = request.args.get('direction')
    if direction:
        myQuery['direction'] = direction

    # 开始时间
    startTime = request.args.get('startTime')
    time = {}
    if startTime:
        time['$gte'] = datetime.strptime(startTime, "%Y-%m-%d %H:%M:%S")
    # 结束时间
    endTime = request.args.get('endTime')
    if endTime:
        time['$lte'] = datetime.strptime(endTime, "%Y-%m-%d %H:%M:%S")
    if time:
        myQuery['time'] = time

    # 查询
    resCollection = collection.find(myQuery).sort("time", -1).skip((page - 1) * limit).limit(limit)
    resList = []
    for item in resCollection:
        formatTime = item['time'].strftime("%Y-%m-%d %H:%M:%S")
        item['time'] = formatTime
        if item['direction'] == "=>":
            item['direction'] = "出网"
        else:
            item['direction'] = "入网"
        item.pop("_id")
        resList.append(item)
    # 总数
    count = collection.count_documents(myQuery)

    result = {
        "code": 0,
        "msg": "成功",
        "count": count,
        "data": resList
    }
    return result


if __name__ == '__main__':
    app.run()
