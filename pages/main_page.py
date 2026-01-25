#-*- coding: utf-8 -*-
import sys
try:
	reload(sys)
	sys.setdefaultencoding('utf-8')
except:
	pass
import os, os.path, sqlite3, time , psutil, platform, logging,re,json,subprocess,collections
from datetime import datetime, timedelta
from flask import Flask, flash, redirect, render_template, request, session, abort, url_for, Blueprint
from requests import get
import requests
import zipfile, shutil 
#from distutils.dir_util import copy_tree
from logging.handlers import RotatingFileHandler
from pytz import timezone
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.base import JobLookupError, ConflictingIdError
from apscheduler.triggers.cron import CronTrigger
from apscheduler.executors.pool import ThreadPoolExecutor, ProcessPoolExecutor
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
#페이지 기능
try:
	from flask_paginate import Pagination, get_page_args
except ImportError:
	os.system('pip install flask_paginate')
	from flask_paginate import Pagination, get_page_args
bp = Blueprint('main', __name__, url_prefix='/')
if platform.system() == 'Windows':
	at = os.path.splitdrive(os.getcwd())
	logdata = at[0] + '/data/log'
	root = at[0] + '/data'
	ip_client = at[0] + '/data/db/ip_list.db'
else:
	logdata = '/data/log'
	root = '/data'
	ip_client = '/data/db/ip_list.db'

def sizeof_fmt(num, suffix='Bytes'):
	for unit in ['', 'K', 'M', 'G', 'T', 'P', 'E', 'Z']:
		if abs(num) < 1024.0:
			return "%3.1f%s%s" % (num, unit, suffix)
		num /= 1024.0
	return "%.1f%s%s" % (num, 'Y', suffix)
	
def createFolder(directory):
	try:
		if not os.path.exists(directory):
			os.makedirs(directory)
	except OSError:
		print ('Error: Creating directory. ' +  directory)
	comp = '완료'
	return comp
	
def ip_cli(IP,DATE):
	#데이타베이스 없으면 생성
	con = sqlite3.connect(ip_client,timeout=60)
	con.execute('CREATE TABLE IF NOT EXISTS IP_LIST (idx integer primary key autoincrement, 접속IP TEXT, 접속날짜 TEXT)')
	con.execute("PRAGMA cache_size = 10000")
	con.execute("PRAGMA locking_mode = NORMAL")
	con.execute("PRAGMA temp_store = MEMORY")
	con.execute("PRAGMA auto_vacuum = 1")
	con.execute("PRAGMA journal_mode=WAL")
	con.execute("PRAGMA synchronous=NORMAL")
	con.close()
	#try:
	with sqlite3.connect(ip_client,timeout=60) as con:
		con.row_factory = sqlite3.Row
		cur = con.cursor()
		cur.execute("INSERT INTO IP_LIST (접속IP, 접속날짜) VALUES (?, ?)", (IP,DATE))
		con.commit()
	#except:
	#	con.rollback()
	#finally:
		#con.close()
	print(IP,DATE)
	return

def mydate():
	now = datetime.now()
	date = now.strftime('%Y-%m-%d %H:%M:%S')
	return date
	
filepath = logdata + '/flask.log'

#실행할때 웹툰DB 목록 중복
check = root + '/empty.txt'
try:
	os.remove(check)
except:
	pass
if not os.path.isfile(filepath):
	f = open(filepath,'a', encoding='utf-8')
class NoRawLogFilter(logging.Filter):
    def filter(self, record):
        msg = record.getMessage()
        # /get_raw_logs 및 /log 호출 로그는 기록하지 않음
        exclude_list = ['/get_raw_logs', '/log','192.168.0.1 ']
        return not any(path in msg for path in exclude_list)
		
fileMaxByte = 10*1024*1024
rfh = logging.handlers.RotatingFileHandler(filename=filepath, mode='a', maxBytes=fileMaxByte, backupCount=10, encoding='utf-8', delay=0)
logging.basicConfig(level=logging.INFO,format="[%(asctime)s %(filename)s:%(lineno)d %(levelname)s] - %(message)s",datefmt='%Y-%m-%d %H:%M:%S',handlers=[rfh])
logger = logging.getLogger()
logging.getLogger('werkzeug').addFilter(NoRawLogFilter())
logging.getLogger('apscheduler.executors.default').setLevel(logging.WARNING)
jobstores = {
	'default': SQLAlchemyJobStore(url='sqlite:////data/db/jobs.sqlite', tablename='main')
	}
executors = {
	'default': ThreadPoolExecutor(max_workers=50),
	'processpool': ProcessPoolExecutor(max_workers=30)
	}
job_defaults = {
	'coalesce': True,
	'max_instances': 1,
	'misfire_grace_time': 15*60
	}
scheduler = BackgroundScheduler(jobstores=jobstores, job_defaults=job_defaults,executors=executors, timezone='Asia/Seoul') 
scheduler.start()

@bp.route("/")
@bp.route("index")
def index():
	date = mydate()
	ip = request.remote_addr
	#접속자 DB저장
	ip_cli(ip,date)
	
	if platform.system() == 'Windows':
		s = os.path.splitdrive(os.getcwd())
		root = s[0]
	else:
		root = '/'
	#현재버젼
	verfile = './version.txt'
	if platform.system() == 'Windows':
		with open(verfile, 'rt', encoding='cp949') as fp:
			lines = fp.readline()
	else:
		with open(verfile, 'rt', encoding='utf-8') as fp:
			lines = fp.readline()
			
	#최신버젼
	with requests.Session() as s:
		url = 'https://raw.githubusercontent.com/k45734/flask_web/main/version.txt'
		req1 = s.get(url)
		version = req1.text
	tmp = psutil.virtual_memory()
	tmp2 = psutil.disk_usage(root)
	oos = platform.platform()
	oocpu = platform.machine()
	memory_percent = f"{psutil.virtual_memory().percent}%"
	disk_percent = f"{psutil.disk_usage('/').percent}%"
	sch_save = []
	sch_list = scheduler.get_jobs()
	for i in sch_list:
		job_id = i.id
		job_next_time  = i.next_run_time
		keys = ['NAME','TIME']
		values = [job_id, job_next_time]
		dt = dict(zip(keys, values))
		sch_save.append(dt)
	data = vnstat_tr()
	logger.info('%s', data)
	return render_template('main.html', test = date, oos = oos, oocpu = oocpu, memory_percent = memory_percent, disk_percent = disk_percent, version = version, lines = lines, sch_save = sch_save, data = data)

@bp.route("cancle/<FLASKAPPSNAME>", methods=["GET"])
def cancle(FLASKAPPSNAME):
	if not session.get('logFlag'):
		return redirect(url_for('main.index'))
	else:
		scheduler.remove_job(FLASKAPPSNAME)
		logger.info('%s 스케줄러를 삭제하였습니다.', FLASKAPPSNAME)
		return redirect(url_for('main.index'))
			
@bp.route('login')
def login():
	return render_template('login.html')
	
@bp.route('logout')
def logout():
	session.clear()
	return index()

@bp.route('login_proc', methods=['post'])
def login_proc():
	userid = request.form['user']
	userpwd = request.form['passwd']	
	con = sqlite3.connect('./login.db')
	con.execute("PRAGMA cache_size = 10000")
	con.execute("PRAGMA locking_mode = NORMAL")
	con.execute("PRAGMA temp_store = MEMORY")
	con.execute("PRAGMA auto_vacuum = 1")
	con.execute("PRAGMA journal_mode=WAL")
	con.execute("PRAGMA synchronous=NORMAL")
	cursor = con.cursor()
	sql = "select idx, id, pwd from member where id = ?"
	cursor.execute(sql, (userid,))
	rows = cursor.fetchall()
	if rows :	
		for rs in rows:
			if userid == rs[1] and userpwd == rs[2]:
				session['logFlag'] = True
				session['idx'] = rs[0]
				session['userid'] = userid
				return redirect(url_for('main.index'))
						
			else:
				return redirect(url_for('main.login'))
		
	else:	
		return redirect(url_for('main.login'))		
		
@bp.route('user_info_edit/<int:edit_idx>', methods=['GET'])
def getUser(edit_idx):
	if session.get('logFlag') != True:
		return redirect(url_for(login))
	con = sqlite3.connect('./login.db')
	con.execute("PRAGMA cache_size = 10000")
	con.execute("PRAGMA locking_mode = NORMAL")
	con.execute("PRAGMA temp_store = MEMORY")
	con.execute("PRAGMA auto_vacuum = 1")
	con.execute("PRAGMA journal_mode=WAL")
	con.execute("PRAGMA synchronous=NORMAL")
	cursor = con.cursor()
	sql = "select id from member where idx = ?"
	cursor.execute(sql, (edit_idx,))
	row = cursor.fetchone()
	edit_id = row[0]
	return render_template('users/user_info.html', edit_idx=edit_idx, edit_id=edit_id)

@bp.route('ip_list', methods=['GET'])
def ip_list_get():
	if not session.get('logFlag'):
		return redirect(url_for('main.index'))
	else:
		per_page = 10
		page, _, offset = get_page_args(per_page=per_page)
		con = sqlite3.connect(ip_client,timeout=60)
		con.execute("PRAGMA cache_size = 10000")
		con.execute("PRAGMA locking_mode = NORMAL")
		con.execute("PRAGMA temp_store = MEMORY")
		con.execute("PRAGMA auto_vacuum = 1")
		con.execute("PRAGMA journal_mode=WAL")
		con.execute("PRAGMA synchronous=NORMAL")
		con.row_factory = sqlite3.Row
		cur = con.cursor()
		cur.execute("select * from IP_LIST")
		total2 = cur.fetchall()
		total = len(total2)
		cur.execute('select * from IP_LIST ORDER BY idx DESC LIMIT ' + str(per_page) + ' OFFSET ' + str(offset))
		wow = cur.fetchall()		
		return render_template('ip_list.html', wow = wow, pagination=Pagination(page=page, total=total, per_page=per_page))

		
@bp.route('user_info_edit_proc', methods=['POST'])
def user_info_edit_proc():
	idx = request.form['idx']
	userid = request.form['user']
	userpwd = request.form['passwd']
	if len(idx) == 0:
		return 'Edit Data Not Found!'
	else:
		con = sqlite3.connect('./login.db')
		con.execute("PRAGMA cache_size = 10000")
		con.execute("PRAGMA locking_mode = NORMAL")
		con.execute("PRAGMA temp_store = MEMORY")
		con.execute("PRAGMA auto_vacuum = 1")
		con.execute("PRAGMA journal_mode=WAL")
		con.execute("PRAGMA synchronous=NORMAL")
		cursor = con.cursor()
		sql = """
			update member
				set id = ?, pwd = ?
				where idx = ?
		"""
		
		cursor.execute(sql, (userid, userpwd, idx))
		con.commit()
		cursor.close()
		con.close()
		return redirect(url_for('main.index'))

def vnstat_tr():
	data = []
	if platform.system() == 'Windows':
		download_data = u'윈도우모드는 지원안함'
		upload_data = u'윈도우모드는 지원안함'
		update_vnstat = u'윈도우모드는 지원안함'
		keys = ['DOWNLOAD','UPLOAD','DATE']
		values = [download_data, upload_data,update_vnstat]
		dt = dict(zip(keys, values))
		data.append(dt)
	else:
		try:
			vnstat_start = '/usr/bin/vnstat --json d -i eth0 > /data/vnstat.json'
			subprocess.call(vnstat_start, shell=True)
			with open('/data/vnstat.json', 'r', encoding='utf8') as f:
				f = f.read()
				my_data = json.loads(f)
				#data_in_check = my_data['interfaces'][0]['traffic']['total']['rx']
				#data_in_check2 = my_data['interfaces'][0]['traffic']['total']['tx']
				#data_in_check3 = my_data['interfaces'][0]['updated']['date']
				#data_in_check4 = my_data['interfaces'][0]['updated']['time']
				data_in_check = my_data['interfaces'][0]['traffic']['day'][-1]
				data_in_check2 = data_in_check['timestamp']
				data_in_check3 = data_in_check['rx']
				data_in_check4 = data_in_check['tx']
				last_update = datetime.fromtimestamp(data_in_check2).strftime('%Y-%m-%d')
				download_data = u'다운로드 데이터 %s' % (sizeof_fmt(data_in_check3))
				upload_data = u'업로드 데이터 %s' % (sizeof_fmt(data_in_check4))
				now = datetime.now()
				#update_vnstat_old = u'%s-%s-%s %s:%s' % (data_in_check3['year'],data_in_check3['month'],data_in_check3['day'],data_in_check4['hour'],data_in_check4['minute'])
				#update_vnstat = now.strptime(update_vnstat_old, "%Y-%m-%d %H:%M").strftime("%Y-%m-%d %H:%M")
				keys = ['DOWNLOAD','UPLOAD','DATE']
				values = [download_data, upload_data,last_update]
				dt = dict(zip(keys, values))
				data.append(dt)
		except:	
			pass
	return data
	
@bp.route("log")
def log():
    createFolder(logdata)
    filepath = logdata + '/flask.log'
    if not os.path.isfile(filepath):
        f = open(filepath, 'a', encoding='utf-8')
        f.close() # 파일 생성 후 닫기

    if not session.get('logFlag'):
        return render_template('login.html')
    else:
        tltl2 = []
        with open(filepath, 'rt', encoding='utf-8') as fp:
            lines = fp.readlines()
            for i in lines:
                clean_line = i.strip()
                # [보정] /log 호출 기록 제외 및 알맹이가 없는 줄 제외
                if clean_line and '/log' not in clean_line and '/get_raw_logs' not in clean_line:
                    # [추가 보정] Flask 배너 메시지의 특수 문자나 과도한 공백 제거
                    # 예: "* Running on..." 앞의 공백 제거
                    tltl2.append(clean_line)
        
        tltl = tltl2[-30:]
        return render_template('log.html', tltl=tltl)
		
@bp.route("xml")
def xml():
	filepath = root + '/rss.xml'
	if not os.path.isfile(filepath):
		return redirect(url_for('main.index'))
	else:
		f = open(filepath, 'r')
		return f

@bp.route('get_raw_logs')
def get_raw_logs():
    # [보정] 절대 경로와 OS별 경로 차이를 고려하여 설정
    if platform.system() == 'Windows':
        log_path = os.getcwd() + '/data/log/flask.log'
    else:
        log_path = '/data/log/flask.log'
        
    try:
        # [핵심] deque를 사용하면 파일 전체를 메모리에 올리지 않고 마지막 줄만 "번개"처럼 읽습니다.
        if os.path.exists(log_path):
            with open(log_path, 'r', encoding='utf-8') as f:
                # 마지막 100줄만 추출
                last_lines = collections.deque(f, maxlen=100)
                return "".join(last_lines)
        else:
            return "로그 파일이 아직 생성되지 않았습니다."
    except Exception as e:
        return f"로그 파일을 읽는 중 오류 발생: {str(e)}"
		
@bp.route("restart")
def restart():
    if not session.get('logFlag'):
        return redirect(url_for('main.index'))
    
    print("== [시스템] 엔진 재시작 프로세스 가동 ==")
    # 현재 실행 중인 파이썬 경로와 인자값을 그대로 다시 실행합니다.
    os.execv(sys.executable, ['python'] + sys.argv)

@bp.route("update_server")
def update_server():
    if not session.get('logFlag'):
        return redirect(url_for('main.index'))
    
    # [보정] recursive=1 파라미터를 추가하여 모든 하위 폴더 구조를 한 번에 가져옵니다.
    api_url = "https://api.github.com/repos/k45734/flask_web/git/trees/main?recursive=1"
    raw_base_url = "https://raw.githubusercontent.com/k45734/flask_web/main/"
    
    logger.info("== [업데이트] 전수 조사 및 전체 동기화 시작 ==")
    
    try:
        response = requests.get(api_url, timeout=15)
        if response.status_code != 200:
            logger.error(f"GitHub API 연결 실패: {response.status_code}")
            return f"<script>alert('GitHub API 연결 실패'); history.back();</script>"
        
        tree_list = response.json().get('tree', [])
        success_count = 0

        for item in tree_list:
            # 파일(blob) 타입만 처리하며, DB 파일은 제외합니다.
            if item['type'] == 'blob':
                file_path = item['path']
                
                if file_path.endswith(('.db', '.sqlite', '.log')):
                    continue
                
                # [핵심] 하위 폴더가 있다면 자동으로 생성합니다.
                dir_name = os.path.dirname(file_path)
                if dir_name:
                    os.makedirs(dir_name, exist_ok=True)
                
                download_url = raw_base_url + file_path
                file_res = requests.get(download_url, timeout=15)
                
                if file_res.status_code == 200:
                    save_full_path = os.path.join(os.getcwd(), file_path)
                    with open(save_full_path, 'wb') as f: # 바이너리 모드로 저장하여 인코딩 깨짐 방지
                        f.write(file_res.content)
                        f.flush()
                        os.fsync(f.fileno())
                    
                    success_count += 1
                    logger.info(f" -> [업데이트 완료] {file_path}")

        if success_count > 0:
            logger.info(f"== [성공] 총 {success_count}개 파일 전체 최신화 완료. 엔진 재시작! ==")
            time.sleep(2)
            # 시스템 재시작
            os.execv(sys.executable, [sys.executable] + sys.argv)
        else:
            return "<script>alert('업데이트할 새 파일을 찾지 못했습니다.'); history.back();</script>"

    except Exception as e:
        logger.error(f"Full Recursive Update Error: {e}")
        return f"<script>alert('오류 발생: {e}'); history.back();</script>"