from flask import Blueprint
from flask import render_template
from flask import request
from flask import jsonify
from flask import make_response
from app import db
from schema.models import DBManager
from datetime import datetime
from collections import Counter

blueprint = Blueprint(
    "navi",
    __name__,
    template_folder="templates",
    static_folder="static",
    )

# /navi/ のエンドポイントを作成する関数
@blueprint.route("/")
def index():
    # DB 管理クラス
    manager = DBManager()

    # cookie から利用者IDを取得
    id = request.cookies.get('userId')
    if id == None:
        # 新規利用者の作成
        user = manager.generateUser()
        id = user.id
    else:
        try:
            # 文字列から整数への変換が必要
            id = int(id)
            
            # 利用者の検索
            user = manager.getUser(id)
            if user == None:
                # 利用者の検索に失敗したら、利用者を再作成
                user = manager.generateUser()
                id = user.id
        except Exception as e:
            # id を整数に変換することが失敗した場合
            user = manager.generateUser()
            id = user.id

    # 最近の GPS データの取得
    locations = manager.getLastGps()

    # 利用者のアクセスログの保存
    manager.addAccessLog(user)

    # cookie の期限設定
    expires = int(datetime.now().timestamp()) + 30000000

    response = make_response(render_template("navi/index.html",
                                             locations = locations))
    
    # cookie の設定
    response.set_cookie('userId', value='%d' % id, expires=expires)

    return response

# 定期的に呼び出すバスの位置情報取得用のエンドポイント
@blueprint.route("/getGps")
def getGps():
    # DB 管理クラス
    manager = DBManager()
    
    # 最近の GPS データの取得
    locations = manager.getLastGps()

    response = [
        {
            "bus": location.bus,
            "latitude": location.latitude,
            "longitude": location.longitude
        }
        for location in locations.values()
    ]

    return jsonify(response)

"""
@blueprint.route("/estTime")
def estTime():
    # DB 管理クラス
    manager = DBManager()
    try:
        destStation = int(request.args.get("destStation"))
    except (TypeError, ValueError):
        return jsonify({"errorReason": "Requested Station ID is not integer"})
    if destStation < 0 or destStation > 6:
        return jsonify({"errorReason": "Station ID out of range (0 - 6)"})
    lastGps = manager.getLastGps()
    times = dict(zip(lastGps.keys(), [0] * len(lastGps)))
    for busId in lastGps.keys():
        currentStation = manager.getNextStation(busId)
        while currentStation != destStation:
            times[busId] += manager.getTimeOfSection(currentStation)
            currentStation = (currentStation + 1) % 7
    return jsonify(times)
"""
@blueprint.route("/estTime")
def estTime():
    # DB 管理クラス
    manager = DBManager()
    lastGps = manager.getLastGps()
    times = dict(zip(list(range(7)), [dict(zip(lastGps.keys(), [0] * len(lastGps))) for _ in range(7)]))
    for destStation in range(7):
        for busId in lastGps.keys():
            currentStation = manager.getNextStation(busId)
            while currentStation != destStation:
                times[destStation][busId] += manager.getTimeOfSection(currentStation)
                currentStation = (currentStation + 1) % 7
                
    return jsonify(times)


@blueprint.route("/lastStation")
def lastStation():
    # DB 管理クラス
    manager = DBManager()
    busIds = manager.getLastGps().keys()
    return jsonify({busId: manager.getLastStation(busId) for busId in busIds})

@blueprint.route("/vote", methods = ["POST"])
def vote():
    # DB 管理クラス
    manager = DBManager()

    userId = request.cookies.get('userId')
    congestion = request.form.get("congestion")

    manager.addVoteLog(userId, congestion)

    return jsonify({userId: congestion})

@blueprint.route("/realTimeCongestion")
def realTimeCongestion():
    # DB 管理クラス
    manager = DBManager()
    votes = manager.getVoteLogByTime(20)
    congestions = [vote.congestion for vote in votes]
    congestions = dict(Counter(congestions))
    return jsonify(congestions)

@blueprint.route("/congestionHistory")
def congestionHistory():
    # DB 管理クラス
    manager = DBManager()
    votes = manager.getVoteLogByNumber(1000)
    votes = [
        {
            "weekday": vote.time.weekday(),
            "time": vote.time,
            "congestion": vote.congestion
        }
        for vote in votes]
    
    congestionsByDay = [0] * 7
    for vote in votes:
        for d in range(7):
            if vote["weekday"] == d and vote["congestion"] >= 3:
                congestionsByDay[d] += 1
    
    congestionsByTime = [dict(zip(range(8, 20), [0] * 15)) for _ in range(7)]
    
    for vote in votes:
        for d in range(7):
            for t in range(8, 20):
                if vote["weekday"] == d and vote["time"].hour == t and vote["congestion"] >= 3:
                    congestionsByTime[d][t] += 1
    
    return jsonify({
        "byDay": congestionsByDay,
        "byTime": congestionsByTime
    })