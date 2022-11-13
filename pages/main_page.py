#-*- coding: utf-8 -*-
import sys
try:
	reload(sys)
	sys.setdefaultencoding('utf-8')
except:
	pass
import os, os.path, sqlite3, time , psutil, platform, logging
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

bp = Blueprint('main', __name__, url_prefix='/')
if platform.system() == 'Windows':
	at = os.path.splitdrive(os.getcwd())
	logdata = at[0] + '/data/log'
	root = at[0] + '/data'
else:
	logdata = '/data/log'
	root = '/data'

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

#실행할때 로그 전체 삭제
filepath = logdata + '/flask.log'
#try:
#    with open(filepath, 'r+', encoding='utf-8') as f:
 #       f.truncate()
#except IOError:
 #   print('Failure')
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
	'default': SQLAlchemyJobStore(url='sqlite:////data/jobs.sqlite', tablename='main')
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
	now = time.localtime()
	test = "{}년{}월{}일{}시{}분{}초".format(now.tm_year, now.tm_mon, now.tm_mday, now.tm_hour, now.tm_min, now.tm_sec)

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
	
	if request.headers.getlist('X-Forwarded-For'):
		ip_test = request.remote_addr
	else:
		ip_test = request.headers.getlist('X-Forwarded-For')#[0]
	logger.info('%s', ip_test)
	return render_template('main.html', test = test, oos = oos, oocpu = oocpu, mem_percent = mem_percent, disk_percent = disk_percent, version = version, lines = lines, sch_save = sch_save)

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
	#con.execute("PRAGMA synchronous = OFF")
	#con.execute("PRAGMA journal_mode = MEMORY")
	con.execute("PRAGMA cache_size = 10000")
	#con.execute("PRAGMA locking_mode = EXCLUSIVE")
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
	#con.execute("PRAGMA synchronous = OFF")
	#con.execute("PRAGMA journal_mode = MEMORY")
	con.execute("PRAGMA cache_size = 10000")
	#con.execute("PRAGMA locking_mode = EXCLUSIVE")
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
	
@bp.route('user_info_edit_proc', methods=['POST'])
def user_info_edit_proc():
	idx = request.form['idx']
	userid = request.form['user']
	userpwd = request.form['passwd']
	if len(idx) == 0:
		return 'Edit Data Not Found!'
	else:
		con = sqlite3.connect('./login.db')
		#con.execute("PRAGMA synchronous = OFF")
		#con.execute("PRAGMA journal_mode = MEMORY")
		con.execute("PRAGMA cache_size = 10000")
		#con.execute("PRAGMA locking_mode = EXCLUSIVE")
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
		f = open('./log/flask.log','a', encoding='utf-8')
	if not session.get('logFlag'):
		return render_template('login.html')
	else:
		if platform.system() == 'Windows':
			filepath = logdata + '/flask.log'
			tltl = []
			with open(filepath, 'rt', encoding='cp949') as fp:
				fp.seek (0, 2)
				fsize = fp.tell()
				fp.seek (max (fsize-1024, 0), 0)
				try:
					lines = fp.readlines()
				except:
					time.sleep(1)
					lines = fp.readlines()
			lines = lines[-10:]
			for i in lines:
				test = i.strip()
				if '/log' in test:
					pass
				else:
					tltl.append(test)
					
		else:
			filepath = logdata + '/flask.log'
			tltl = []
			with open(filepath, 'rt', encoding='utf-8') as fp:
				fp.seek (0, 2)
				fsize = fp.tell()
				fp.seek (max (fsize-1024, 0), 0)
				try:
					lines = fp.readlines()
				except:
					time.sleep(1)
					lines = fp.readlines()
			lines = lines[-10:]
			for i in lines:
				test = i.strip()
				if '/log' in test:
					pass
				else:
					tltl.append(test)				
		return render_template('log.html', tltl=tltl)	

@bp.route("update")
def update(file_name = None):
	if not session.get('logFlag'):
		return render_template('login.html')
	else:
		if platform.system() == 'Windows':
			os.system("flask run --reload")
		else:
			os.system("kill -9 `ps -ef|grep supervisord|awk '{print $1}'`")
			#org = '/usr/bin/git'
			#if os.path.exists(org):
			#	print("파일있다")
			#	os.system('cd /var/local/.app')
			#	os.system("git pull")
			#else:
			#	print("파일없다")
			#	os.system("kill -9 `ps -ef|grep app.py|awk '{print $1}'`")
			#	os.system("kill -9 `ps -ef|grep supervisord|awk '{print $1}'`")
		return redirect(url_for('main.index'))
		
@bp.route("restart")
def restart():
	if not session.get('logFlag'):
		return render_template('login.html')
	else:
		if platform.system() == 'Windows':
			os.system("flask run --reload")
		else:
			os.system("cat /dev/null > " + logdata + "/flask.log")
			os.system("chmod 777 * -R")
			os.system("kill -9 `ps -ef|grep app.py|awk '{print $1}'`")
		return redirect(url_for('main.index'))
