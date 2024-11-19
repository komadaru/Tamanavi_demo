from flask import Blueprint
from flask import render_template
from flask import request
from flask import redirect
from flask import url_for
from flask import make_response
from flask import jsonify
from flask import render_template, request, redirect
from flask import flash
from flask_login import login_required, login_user, logout_user
from werkzeug.security import check_password_hash
from app import db
from schema.models import DBManager

import pandas as pd
import io

blueprint = Blueprint(
    "admin",
    __name__,
    template_folder="templates",
    static_folder="static",
    )

@blueprint.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == "POST":
        username = request.form.get('username')
        password = request.form.get('password')
        manager = DBManager()
        [result, reason] = manager.generateAdminUser(username, password)
        if not result:
            if reason == "Already Exists":
                flash("ユーザー名がすでに使われています。")
            return render_template('admin/signup.html')    
        return redirect(url_for('admin.login'))
    else:
        return render_template('admin/signup.html')

@blueprint.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        username = request.form.get('username')
        password = request.form.get('password')
        manager = DBManager()
        user = manager.getAdminUser(username)
        if user is None:
            flash("ユーザーが存在しません。")
            return redirect(url_for('admin.index'))
        if check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('admin.index'))
        else:
            flash("パスワードが違います。")
            return render_template('admin/login.html')
    else:
        return render_template('admin/login.html')

@blueprint.route('/logout')
@login_required
def logout():
    logout_user()
    flash("ログアウトしました。")
    return redirect(url_for('admin.login'))

@blueprint.route("/")
@login_required
def index():
    # DB 管理用クラス
    manager = DBManager()

    # 最近の GPS データの取得
    # 複数のバスに対応するため、それぞれのバスの直近データを dict で返却
    locations = manager.getLastGps()

    # 利用者のアクセスログの取得
    logs = manager.getAccessLog()

    # 投票ログの取得
    votes = manager.getAllVotes()

    """
    table = "<table>"
    for log in logs:
        timeString = log.time.strftime("%Y/%m/%d %H:%M:%S.%f")
        table += "<tr><td>%d</td><td>%s</td></tr>" % (log.userId, timeString)
                     
    table += "</table>"
    """

    response = make_response(render_template("admin/index.html",
                                             logs = logs,
                                             locations = locations,
                                             votes = votes))
    
    return response

@blueprint.route("/deleteAll")
@login_required
def deleteAll():
    # DB 管理用クラス
    manager = DBManager()

    manager.deleteAll()

    return ""

@blueprint.route("/outputUsers")
@login_required
def outputUsers():
    # DB 管理用クラス
    manager = DBManager()

    export_type = request.args.get("export_type")

    users = manager.getAllUsers()

    # Excel生成とダウンロード
    df = pd.DataFrame([[user.id, user.count, user.faculty, user.grade, user.club]
                        for user in users],
                        columns=["ID", "アクセス回数", "学部", "学年", "サークル種別"])

    if export_type == "excel":
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer) as writer:
            df.to_excel(writer, index=False)
        
        buffer.seek(0)
        data=buffer.read()
        
        response = make_response()

        response.data = data

        response.headers['Content-Disposition'] = 'attachment; filename=users.xlsx'
        response.mimetype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'

        return response
    
    elif export_type == "json" or export_type is None:
        return jsonify(df.T.to_dict())
    
    else:
        return jsonify({"errorReason": "invalid export type"})

@blueprint.route("/outputLogs")
@login_required
def outputLogs():
    #DB管理用クラス
    manager = DBManager()

    export_type = request.args.get("export_type")

    logs = manager.getAccessLog()

    # Excel生成とダウンロード
    df = pd.DataFrame([[log.userId, str(log.time)] for log in logs],
                      columns=["ユーザーID", "アクセス日時"])
    
    if export_type == "excel":
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer) as writer:
            df.to_excel(writer, index=False)
        
        buffer.seek(0)
        data=buffer.read()

        response = make_response()

        response.data = data

        response.headers['Content-Disposition'] = 'attachment; filename=logs.xlsx'
        response.mimetype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'

        return response
       
    elif export_type == "json" or export_type is None:
        return jsonify(df.T.to_dict())
    
    else:
        return jsonify({"errorReason": "invalid export type"})

@blueprint.route("/outputVotes")
@login_required
def outputVotes():
    #DB管理用クラス
    manager = DBManager()

    export_type = request.args.get("export_type")

    votes = manager.getAllVotes()

    # Excel生成とダウンロード
    df = pd.DataFrame([[vote.userId, str(vote.time), vote.congestion] for vote in votes],
                      columns=["ユーザーID", "投票日時", "混雑度"])
    
    if export_type == "excel":
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer) as writer:
            df.to_excel(writer, index=False)
        
        buffer.seek(0)
        data=buffer.read()

        response = make_response()

        response.data = data

        response.headers['Content-Disposition'] = 'attachment; filename=votes.xlsx'
        response.mimetype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'

        return response
       
    elif export_type == "json" or export_type is None:
        return jsonify(df.T.to_dict())
    
    else:
        return jsonify({"errorReason": "invalid export type"})

@blueprint.route("/outputGpsLogs")
@login_required
def outputGpsLogs():
    #DB管理用クラス
    manager = DBManager()

    export_type = request.args.get("export_type")

    gpslogs = manager.getAllGpsLogs()

    # Excel生成とダウンロード
    df = pd.DataFrame([[gpslog.id, str(gpslog.time), gpslog.bus, gpslog.latitude, gpslog.longitude, gpslog.stop] for gpslog in gpslogs],
                      columns=["ID", "送信日時", "バスID", "緯度", "経度", "走行中(0)、停止中(1)"])
    
    if export_type == "excel":
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer) as writer:
            df.to_excel(writer, index=False)
        
        buffer.seek(0)
        data=buffer.read()

        response = make_response()

        response.data = data

        response.headers['Content-Disposition'] = 'attachment; filename=gpslogs.xlsx'
        response.mimetype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'

        return response
       
    elif export_type == "json" or export_type is None:
        return jsonify(df.T.to_dict())
    
    else:
        return jsonify({"errorReason": "invalid export type"})

@blueprint.route("/dbInit")
@login_required
def dbInit():
    manager = DBManager()
    manager.dbInit()
    return ""