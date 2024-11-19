from datetime import datetime, timedelta
from app import db, login_manager
from sqlalchemy import desc
from geopy.distance import geodesic
from flask_login import UserMixin
from werkzeug.security import generate_password_hash

# DB関係のスキーマ定義と、DB管理クラス DBManager を定義するためのプログラム

# 利用者管理スキーマ ("users")
#  id: 利用者ID
#  count: アクセス回数
class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    count = db.Column(db.Integer, default=0)
    grade = db.Column(db.Integer, default=0)
    faculty = db.Column(db.String(10), default="")
    club = db.Column(db.String(10), default="")

# 利用者の個別アクセスログのスキーマ ("access")
#  id: アクセスログID
#  userId: 利用者ID
#  time: アクセス時刻
class AccessLog(db.Model):
    __tablename__ = "access"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    userId = db.Column(db.Integer, default=0)
    time = db.Column(db.DateTime)

class AdminUser(db.Model, UserMixin):
    __tablename__ = "admin_user"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(255), unique = True)
    password_hash = db.Column(db.String(255))

# バスから発信されるGPSログのスキーマ ("gps")
#  id: GPSログID
#  time: 登録時刻
#  bus: バスID
#  latitude: 緯度
#  longitude: 経度
#  stop: 走行中(0)、停止中(1)
class GPSLog(db.Model):
    __tablename__ = "gps"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    time = db.Column(db.DateTime)
    bus = db.Column(db.Integer, default=0)
    latitude = db.Column(db.FLOAT(precision=32, decimal_return_scale=None), default=0.0)
    longitude = db.Column(db.FLOAT(precision=32, decimal_return_scale=None), default=0.0)
    stop = db.Column(db.SmallInteger, default=0)
    accel = db.Column(db.Float, default=0.0)
    preStop = db.Column(db.SmallInteger, default=0)

# 直近のGPS登録データをバスID単位で管理するスキーマ ("current_location")
#  id: バスID
#  gpsId: 直近のGPS情報を示す GPSログID
class CurrentLocation(db.Model):
    __tablename__ = "current_location"
    # id <= bus id
    id = db.Column(db.Integer, primary_key=True)
    gpsId = db.Column(db.Integer, default=0)

class LastStation(db.Model):
    __tablename__ = "last_station"
    busId = db.Column(db.Integer, default=-1, primary_key=True)
    stationId = db.Column(db.Integer, default=0)
    time = db.Column(db.DateTime, default=0.0)

class Section(db.Model):
    __tablename__ = "section"
    id = db.Column(db.Integer, primary_key=True, autoincrement=False)
    time = db.Column(db.Float, default=0.0)

# 混雑度の投票状況を管理するスキーマ("vote")
class Vote(db.Model):
    __tablename__ = "votes"
    id = db.Column(db.Integer, primary_key=True)
    userId = db.Column(db.Integer, default=0)
    time = db.Column(db.DateTime)
    congestion = db.Column(db.Integer, default=0)

# DB 管理用のユーティリティ関数を管理するクラス
class DBManager:
            
    # 新規利用者の作成
    # User テーブルへの登録
    def generateUser(self):
        user = User()
        db.session.add(user)
        db.session.commit()
        return user
    
    # 既存利用者の検索
    def getUser(self, id):
        user = db.session.query(User).get(id)
        return user

    # 利用者DBを取得
    def getAllUsers(self):
        users = db.session.query(User).all()
        return users

    def setUserInfo(self, id, faculty, grade, club):
        user = self.getUser(id)
        if user is None:
            return False
        user.faculty = faculty
        user.grade = grade
        user.club = club
        db.session.commit()
        return True

    # 管理者の登録
    def generateAdminUser(self, username, password):
        if self.getAdminUser(username) is not None:
            return False, "Already Exists"
        admin = AdminUser()
        admin.username = username
        admin.password_hash = generate_password_hash(password)
        db.session.add(admin)
        db.session.commit()
        return True, None

    def getAdminUser(self, username):
        return db.session.query(AdminUser).filter_by(username = username).first()

    def changePassword(self, id, password):
        admin = db.session.query(AdminUser).get(id)
        admin.password_hash = generate_password_hash(password)
        db.session.commit()

    # アクセスログの登録
    # AccessLog と User テーブルの更新
    def addAccessLog(self, user):
        log = AccessLog()
        log.userId = user.id
        log.time = datetime.now()
        user.count += 1
        db.session.add(log)
        db.session.add(user)
        db.session.commit()
        return user.count

    # アクセスログの取得
    def getAccessLog(self):
        logs = db.session.query(AccessLog).all()
        return logs
    
    # 最後に通ったバス停を取得
    def getLastStation(self, busId):
        return db.session.query(LastStation).get(busId).stationId

    # 次に通るバス停を取得
    def getNextStation(self, busId):
        return (self.getLastStation(busId) + 1) % 7

    # 最後に通ったバス停を更新
    def updateLastStation(self, busId, stationId, updateSectionTime = True, now = None):
        lastStation = db.session.query(LastStation).get(busId)
        if stationId == lastStation.stationId:
            return
        if now is None:
            now = datetime.now()
        else:
            now = datetime.fromisoformat(now)
        if updateSectionTime:
            section = db.session.query(Section).get(lastStation.stationId)
            section.time = (now - lastStation.time).total_seconds() / 60
            print(f"セクションの時間更新:{section.id}:{section.time}")
        lastStation.stationId = stationId
        lastStation.time = now
        db.session.commit()
        return lastStation.stationId
    
    # 区間ごとにかかる時間を取得
    def getTimeOfSection(self, sectionId):
        return db.session.query(Section).get(sectionId).time
        
    # 投票の登録
    def addVoteLog(self, userID, cong):
        vote = Vote()
        vote.userId = userID
        vote.time = datetime.now()
        vote.congestion = cong
        db.session.add(vote)
        db.session.commit()
        return vote
    
    # 時間指定で投票状況の取得
    # 過去t分の投票状況を取得
    def getVoteLogByTime(self, t):
        votes = db.session.query(Vote) \
            .filter(Vote.time > datetime.now() - timedelta(minutes=t)).\
            all()
        return votes
    
    # 時間指定でGPSのログ取得
    # 過去t秒のログを取得
    def getGPSLogByTime(self, busId, t, now = None):
        if now is None:
            now = datetime.now()
        logs = db.session.query(GPSLog). \
            filter(GPSLog.bus == busId). \
            filter(GPSLog.time > now - timedelta(seconds=t)). \
            all()
        return logs
    
    # 件数指定で投票状況の取得
    # n件
    def getVoteLogByNumber(self, n):
        votes = db.session.query(Vote) \
            .order_by(desc(Vote.time)).\
            limit(n).\
            all()
        return votes

    # すべての投票状況の取得
    def getAllVotes(self):
        votes = db.session.query(Vote).all()
        return votes

    # バスごとの最新のGPSデータを取得
    def getLastGps(self):
        currentLocations = self.getCurrentLocation()
        return {location[0].id: location[1] for location in currentLocations}

    # バスごとの現在地とGPS
    def getCurrentLocation(self):
        # 結果例:[(<CurrentLocation 1>, <GPSLog 2418>), (<CurrentLocation 2>, <GPSLog 2419>)]
        return db.session.query(CurrentLocation, GPSLog) \
            .join(GPSLog, CurrentLocation.gpsId == GPSLog.id) \
            .all()

    # すべてのバス情報のログを取得
    def getAllGpsLogs(self):
        gpslogs = db.session.query(GPSLog).all()
        return gpslogs

    # バスを消す
    def deactivateBus(self, busId):
        db.session.delete(db.session.query(CurrentLocation).get(busId))
        db.session.commit()
        return ""

    # GPS データの登録
    def registerGPS(self, bus, longitude, latitude, time, accel):
        gps = GPSLog()
        gps.bus = int(bus)
        gps.time = datetime.fromisoformat(time)
        gps.longitude = longitude
        gps.latitude = latitude
        gps.accel = float(accel)

        # 最後のGPSデータの取得
        lastGps = self.getCurrentLocation()
        previous_location = None
        previous_gps = None
        for data in lastGps:
            if data[0].id == int(bus):
                previous_location = data[0]
                previous_gps = data[1]
                break
        
        # 速度の算出
        if previous_gps is None:
            velocity = 0
        else:
            distance = geodesic(
                    (previous_gps.latitude, previous_gps.longitude),
                    (gps.latitude, gps.longitude)
                ).m
            timediff = (gps.time - previous_gps.time) / timedelta(seconds = 1)
            velocity = distance / timediff

        # 速度と加速度からpreStopの判定(誤差はのちのち調整)
        if abs(gps.accel) < 5 and abs(velocity) < 2:
            gps.preStop = 1
        else:
            gps.preStop = 0

        # 過去10秒間のGPSログを取得して、そのpreStopの値を取得
        # preStopの値が全て1なら、stopと判定
        logs = self.getGPSLogByTime(int(bus), 10, now = gps.time)
        keep = [log.preStop for log in logs]
        gps.stop = all(elem == 1 for elem in keep)
        print(f"時刻:{gps.time}")
        print(f"直近10秒のpreStop:{keep}")
        print(f"バス:{bus}, preStop:{gps.preStop}, Stop?:{gps.stop}")

        db.session.add(gps)

        # 結果を一時的に反映(AutoincrementのGPSのidを取得するため)
        db.session.flush()

        # CurrentLocationの更新
        if previous_location is None:
            # 登録がないバスの場合、CurrentLocation オブジェクトを生成
            current = CurrentLocation()
            current.id = bus
            db.session.add(current)
            self.updateLastStation(int(bus), 6, False)
        else:
            current = previous_location

        current.gpsId = gps.id
        db.session.commit()
        
        return gps
    
    # 過去のGPSデータの取得
    def getGPSHistory(self, d):
        history = db.session.query(GPSLog) \
            .filter(GPSLog.time > datetime.now() - timedelta(days=d)). \
            all()
        return history
    
    # バスの到着予定時刻予測
    def estArrivalTime(self, velocity, stop, station):
        pass

    # システム情報の取得
    def getSystem(self):
        return self.system

    # DB の全データ消去
    # 注意して実行すること
    def deleteAll(self):
        db.session.query(User).delete()
        db.session.query(AccessLog).delete()
        db.session.query(GPSLog).delete()
        db.session.query(CurrentLocation).delete()
        db.session.commit()

    def deleteGpsAndLocation(self):
        db.session.query(GPSLog).delete()
        db.session.query(CurrentLocation).delete()
        db.session.commit()

    # DBの初期値を設定
    def dbInit(self):
        # last_station
        db.session.query(LastStation).delete()
        for i in range(1, 4):
            last_station = LastStation()
            last_station.busId = i
            last_station.stationId = 0
            last_station.time = datetime.now()
            db.session.add(last_station)
        # section
        db.session.query(Section).delete()
        for i in range(7):
            section = Section()
            section.id = i
            section.time = 3
            db.session.add(section)
        db.session.commit()

# manager = DBManager()

"""
    def getLastUserId(self):
        id = self.system.userId
        self.system.userId += 1
        db.session.add(self.system)
        db.session.commit()
        return id

"""

@login_manager.user_loader
def load_user(user_id):
    return AdminUser.query.get(user_id)