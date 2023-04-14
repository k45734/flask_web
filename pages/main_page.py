#-*- coding: utf-8 -*-
import sys
try:
	reload(sys)
	sys.setdefaultencoding('utf-8')
except:
	pass
import os, os.path, sqlite3, time , psutil, platform, logging,re,json
from datetime import datetime, timedelta
from flask import Flask, flash, redirect, render_template, request, session, abort, url_for, Blueprint
from requests import get
import requests
import zipfile, shutil 
from distutils.dir_util import copy_tree
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
fileMaxByte = 1024*500
rfh = logging.handlers.RotatingFileHandler(filename=filepath, mode='a', maxBytes=fileMaxByte, backupCount=5, encoding='utf-8', delay=0)
logging.basicConfig(level=logging.INFO,format="[%(asctime)s %(filename)s:%(lineno)d %(levelname)s] - %(message)s",datefmt='%Y-%m-%d %H:%M:%S',handlers=[rfh])
logger = logging.getLogger()
logging.getLogger('apscheduler.executors.default').setLevel(logging.WARNING)
jobstores = {
	'default': SQLAlchemyJobStore(url='sqlite:////data/db/jobs.sqlite', tablename='main')
	}
executors = {
	'default': ThreadPoolExecutor(max_workers=20),
	'processpool': ProcessPoolExecutor(max_workers=10)
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
	mem_percent = u'전체 : %s   사용량 : %s   남은량 : %s  (%s%%)' % (sizeof_fmt(tmp[0], suffix='B'), sizeof_fmt(tmp[3], suffix='B'), sizeof_fmt(tmp[1], suffix='B'), tmp[2])
	disk_percent = u'전체 : %s   사용량 : %s   남은량 : %s  (%s%%) - 드라이브 (%s)' % (sizeof_fmt(tmp2[0], suffix='B'), sizeof_fmt(tmp2[1], suffix='B'), sizeof_fmt(tmp2[2], suffix='B'), tmp2[3], root)
	sch_save = []
	sch_list = scheduler.get_jobs()
	for i in sch_list:
		job_id = i.id
		job_next_time  = i.next_run_time
		keys = ['NAME','TIME']
		values = [job_id, job_next_time]
		dt = dict(zip(keys, values))
		sch_save.append(dt)
	return render_template('main.html', test = date, oos = oos, oocpu = oocpu, mem_percent = mem_percent, disk_percent = disk_percent, version = version, lines = lines, sch_save = sch_save)

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

@bp.route("log")
def log():
	createFolder(logdata)
	filepath = logdata + '/flask.log'
	if not os.path.isfile(filepath):
		f = open(filepath,'a', encoding='utf-8')
	if not session.get('logFlag'):
		return render_template('login.html')
	else:
		filepath = logdata + '/flask.log'
		tltl2 = []
		with open(filepath, 'rt', encoding='utf-8') as fp:
			lines = fp.readlines()
			for i in lines:
				if '/log' in i:
					pass
				else:
					tltl2.append(i)
		tltl = tltl2[-20:]
		#vnstat 트래픽 윈도우 않됨
		if platform.system() == 'Windows':
			vnstat_data = '윈도우모드'
		else:
			for i in range(1,10):
				vnstat_start = '/usr/bin/vnstat --json -i eth0 > /data/vnstat.json'
				os.system(vnstat_start)
				if os.path.isfile(vnstat_start):
					with open('/data/vnstat.json', 'r', encoding='utf8') as f:
						f = f.read()
						my_data = json.loads(f)
						data_in_check = my_data['interfaces'][0]['traffic']['total']['rx']
						data_in_check2 = my_data['interfaces'][0]['traffic']['total']['tx']
						download_data = '다운로드 데이터 {}'.format(sizeof_fmt(data_in_check, suffix='G'))
						upload_data = '업로드 데이터 {}'.format(sizeof_fmt(data_in_check2, suffix='G'))
						logger.info('%s %s', download_data,upload_data)
					break
				else:
					pass
		return render_template('log.html', tltl=tltl, download_data=download_data, upload_data=upload_data)	
	
@bp.route("restart")
def restart():
	if not session.get('logFlag'):
		return render_template('login.html')
	else:
		if platform.system() == 'Windows':
			os.system("flask run --reload")
		else:
			os.system("kill -9 `ps -ef|grep supervisord|awk '{print $1}'`")
		return redirect(url_for('main.index'))
