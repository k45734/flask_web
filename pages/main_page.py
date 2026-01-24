#-*- coding: utf-8 -*-
import sys
try:
    reload(sys)
    sys.setdefaultencoding('utf-8')
except:
    pass
import os, os.path, sqlite3, time , psutil, platform, logging, re, json, subprocess, collections
from datetime import datetime, timedelta
from flask import Flask, flash, redirect, render_template, request, session, abort, url_for, Blueprint
import requests
import zipfile, shutil 
from logging.handlers import RotatingFileHandler
from pytz import timezone
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.base import JobLookupError, ConflictingIdError
from apscheduler.triggers.cron import CronTrigger
from apscheduler.executors.pool import ThreadPoolExecutor, ProcessPoolExecutor
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore

# [페이지 기능]
try:
    from flask_paginate import Pagination, get_page_args
except ImportError:
    os.system('pip install flask_paginate')
    from flask_paginate import Pagination, get_page_args

bp = Blueprint('main', __name__, url_prefix='/')

# --- [로그 설정 및 필터 엔진] ---
if platform.system() == 'Windows':
    at = os.path.splitdrive(os.getcwd())
    logdata = at[0] + '/data/log'
    root = at[0] + '/data'
    ip_client = at[0] + '/data/db/ip_list.db'
else:
    logdata = '/data/log'
    root = '/data'
    ip_client = '/data/db/ip_list.db'

os.makedirs(logdata, exist_ok=True)
filepath = logdata + '/flask.log'

# Werkzeug 로그 및 시스템 로그에서 특정 경로(/get_raw_logs) 제외 필터
class NoRawLogFilter(logging.Filter):
    def filter(self, record):
        msg = record.getMessage()
        # 제외하고 싶은 경로들을 여기에 등록합니다.
        exclude_paths = ['/get_raw_logs', '/log', '/static/']
        return not any(path in msg for path in exclude_paths)

# 핸들러 설정
fileMaxByte = 1024 * 500
rfh = RotatingFileHandler(filename=filepath, mode='a', maxBytes=fileMaxByte, backupCount=5, encoding='utf-8', delay=0)
logging.basicConfig(level=logging.INFO, format="[%(asctime)s %(filename)s:%(lineno)d %(levelname)s] - %(message)s", datefmt='%Y-%m-%d %H:%M:%S', handlers=[rfh])

logger = logging.getLogger()
# 필터 적용 (시스템 로거 + 웹 서버 로거)
logger.addFilter(NoRawLogFilter())
logging.getLogger('werkzeug').addFilter(NoRawLogFilter())
logging.getLogger('apscheduler.executors.default').setLevel(logging.WARNING)

# --- [스케줄러 설정] ---
jobstores = {'default': SQLAlchemyJobStore(url='sqlite:////data/db/jobs.sqlite', tablename='main')}
executors = {'default': ThreadPoolExecutor(max_workers=50), 'processpool': ProcessPoolExecutor(max_workers=30)}
job_defaults = {'coalesce': True, 'max_instances': 1, 'misfire_grace_time': 15*60}
scheduler = BackgroundScheduler(jobstores=jobstores, job_defaults=job_defaults, executors=executors, timezone='Asia/Seoul') 
scheduler.start()

# --- [유틸리티 함수] ---
def sizeof_fmt(num, suffix='Bytes'):
    for unit in ['', 'K', 'M', 'G', 'T', 'P', 'E', 'Z']:
        if abs(num) < 1024.0: return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Y', suffix)

def ip_cli(IP, DATE):
    with sqlite3.connect(ip_client, timeout=60) as con:
        con.execute('CREATE TABLE IF NOT EXISTS IP_LIST (idx integer primary key autoincrement, 접속IP TEXT, 접속날짜 TEXT)')
        con.execute("INSERT INTO IP_LIST (접속IP, 접속날짜) VALUES (?, ?)", (IP, DATE))
        con.commit()

def mydate():
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

# --- [라우트 설정] ---
@bp.route("/")
@bp.route("index")
def index():
    date = mydate()
    ip = request.remote_addr
    ip_cli(ip, date)
    
    sys_root = os.path.splitdrive(os.getcwd())[0] if platform.system() == 'Windows' else '/'
    verfile = './version.txt'
    enc = 'cp949' if platform.system() == 'Windows' else 'utf-8'
    
    try:
        with open(verfile, 'rt', encoding=enc) as fp: lines = fp.readline()
    except: lines = "Unknown"

    try:
        version = requests.get('https://raw.githubusercontent.com/k45734/flask_web/main/version.txt', timeout=5).text
    except: version = "Error"

    oos, oocpu = platform.platform(), platform.machine()
    memory_percent = f"{psutil.virtual_memory().percent}%"
    disk_percent = f"{psutil.disk_usage(sys_root).percent}%"
    
    sch_save = [{'NAME': j.id, 'TIME': j.next_run_time} for j in scheduler.get_jobs()]
    data = vnstat_tr()
    
    return render_template('main.html', test=date, oos=oos, oocpu=oocpu, memory_percent=memory_percent, disk_percent=disk_percent, version=version, lines=lines, sch_save=sch_save, data=data)

@bp.route('get_raw_logs')
def get_raw_logs():
    try:
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                # 마지막 100줄만 신속하게 읽기
                last_lines = collections.deque(f, maxlen=100)
                return "".join(last_lines)
        return "로그 파일이 없습니다."
    except Exception as e: return f"Error: {e}"

@bp.route("log")
def log():
    if not session.get('logFlag'): return redirect(url_for('main.login'))
    tltl = []
    try:
        with open(filepath, 'rt', encoding='utf-8') as fp:
            lines = fp.readlines()
            for i in lines:
                clean = i.strip()
                # 로그 화면에서도 시스템 호출 로그는 숨김
                if clean and not any(p in clean for p in ['/get_raw_logs', '/log']):
                    tltl.append(clean)
    except: pass
    return render_template('log.html', tltl=tltl[-30:])

@bp.route("restart")
def restart():
    if not session.get('logFlag'): return redirect(url_for('main.index'))
    logger.info("== [시스템] 엔진 재시작 프로세스 가동 ==")
    os.execv(sys.executable, ['python'] + sys.argv)

# ... (나머지 vnstat_tr, login, logout, update_server 등 기존 로직 유지) ...
def vnstat_tr():
    # 기존 vnstat_tr 코드와 동일
    data = []
    # ... (생략)
    return data