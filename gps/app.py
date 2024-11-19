from flask import Blueprint
from flask import render_template
from flask import request
from app import db
from schema.models import DBManager
import csv
from geopy.distance import geodesic

blueprint = Blueprint(
    "gps",
    __name__,
    template_folder="templates",
    static_folder="static",
    )

# GPS の送信データを模擬的に生成するテスト入力用ページ
# 本番システムでは削除
@blueprint.route("/")
def index():
    return render_template("gps/index.html")

# GPS データの登録用のエンドポイントの実装
# GET, POST のいずれも受付ける。
# 下記の引数を受け付ける
#  bus: バスID
#  longitude: 経度
#  latitude: 緯度
#  stop: バスの停止状態(0:走行中 or 1:停止中)
@blueprint.route("/register", methods=["GET", "POST"])
def register():
    # DB 管理用のクラス
    manager = DBManager()

    if request.method == "GET":
        # GET 用の引数抽出
        bus = request.args.get("bus")
        longitude = request.args.get("longitude")
        latitude = request.args.get("latitude")
        accel = request.args.get("accel")
        time = request.args.get("time")
    elif request.method == "POST":
        # POST 用の引数抽出
        bus = request.form.get("bus")
        longitude = request.form.get("longitude")
        latitude = request.form.get("latitude")
        accel = request.form.get("accel")
        time = request.form.get("time")

    # manager を使って、GPS データを登録
    manager.registerGPS(bus, longitude, latitude, time, accel)

    locations = manager.getLastGps()
    # バス停の更新処理

    with open("csv/station.csv", encoding = "utf-8") as f:
        stations = list(csv.reader(f))

    for location in locations.values():
        if location.stop == 1:
            distances = [
                geodesic(
                    (stations[i][1], stations[i][2]),
                    (location.latitude, location.longitude)
                ).m
                for i in range(7)
            ]
            nearest_distance = min(distances)
            # バス停の範囲外で止まっても何もしない バス停の範囲で止まった場合：
            if nearest_distance <= 20:                    
                nearest_station = distances.index(nearest_distance)
                lastStation = manager.getLastStation(location.bus)
                flag = True
                # 経済学部に停まった場合は行き帰りを判定して適切なほうを選ぶ
                if nearest_station == 2 or nearest_station == 4:
                    # 体育館から来た場合帰りだと考えられる
                    if lastStation == 3:
                        nearest_station = 4
                    # それ以外は行きだと考えられる
                    else:
                        nearest_station = 2
                # 行き帰りで2度通るバス停に止まった場合最後に止まったバス停から判定
                # 帰りならば更新しない
                elif nearest_station == 1:
                    if lastStation in [2, 3, 4]:
                        flag = False
                elif nearest_station == 0:
                    if lastStation in [1, 2, 3, 4]:
                        flag = False
                elif nearest_station == 5:
                    if lastStation == 6:
                        flag = False

                if flag:
                    manager.updateLastStation(location.bus, nearest_station, now = time)
        else:
            nextstation = manager.getNextStation(location.bus)
            station_latitude = stations[nextstation][1]
            station_longitude = stations[nextstation][2]
            distance = geodesic(
                (station_latitude, station_longitude),
                (location.latitude, location.longitude)
            ).m
            if distance < 20:
                manager.updateLastStation(location.bus, nextstation, now = time)
        
    print({location.bus: manager.getLastStation(location.bus) for location in locations.values()})

    # 返却値は、gps/index.html を送信
    return render_template("gps/index.html")

# バスを無効化
@blueprint.route("/deactivate")
def deactivate():
    # DB 管理用のクラス
    manager = DBManager()
    busId = request.args.get("busId")
    manager.deactivateBus(int(busId))
    return ""

@blueprint.route("/test_gps")
def test():
    manager = DBManager()
    manager.deleteGpsAndLocation()
    manager.dbInit()
    return render_template("gps/test.html", domain = request.host)