#-*- coding: utf-8 -*-
import sys
try:
	reload(sys)
	sys.setdefaultencoding('utf-8')
except:
	pass
from flask import Flask, flash, redirect, render_template, request, session, abort, url_for, Blueprint
import os.path, json, os, re, time, logging, io, subprocess, platform, telegram, threading, sqlite3, random,psutil
from datetime import datetime, timedelta

try:
	import requests
except ImportError:
	os.system('pip install requests')
	import requests

try:
	from bs4 import BeautifulSoup as bs
except ImportError:
	os.system('pip install BeautifulSoup4')
	from bs4 import BeautifulSoup as bs

try:
	import telegram
except ImportError:
	os.system('pip install python-telegram-bot')
	import telegram
try: #python3
	from urllib.request import urlopen
except: #python2
	from urllib2 import urlopen
	#from urllib.request import urlopen 
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry


from pages.main_page import scheduler
from pages.main_page import logger
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.base import JobLookupError, ConflictingIdError
from apscheduler.triggers.cron import CronTrigger
from apscheduler.executors.pool import ThreadPoolExecutor, ProcessPoolExecutor
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore

if platform.system() == 'Windows':
	at = os.path.splitdrive(os.getcwd())
	sub3db = at[0] + '/data/db/database.db'
else:
	sub3db = '/data/db/database.db'
	
bp3 = Blueprint('sub3', __name__, url_prefix='/sub3')
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
dfolder = os.path.dirname(os.path.abspath(__file__)) + '/log'

#DB최적화
def db_optimization():
	try:
		con = sqlite3.connect(sub3db,timeout=60)		
		con.execute('VACUUM')
		con.commit()
		logger.info('DB최적화를 진행하였습니다.')
	except:
		con.rollback()	
	finally:	
		con.close()
	comp = '완료'
	return comp
	
def proc_test(name):
	# name 예: "python /data/webtoon_server.py --gbun adult"
	targets = name.split() 
	logger.info('종료 시도 대상: %s', name)

	for proc in psutil.process_iter():
		try:
			cmdline = proc.cmdline()
			# 실행 명령어 리스트에 'adult' 혹은 'normal'이 정확히 포함된 프로세스만 골라냅니다.
			if all(t in cmdline for t in targets):
				pid = proc.pid
				parent = psutil.Process(pid)
				for child in parent.children(recursive=True):
					child.kill()
				parent.kill()
				logger.info('PID %s 프로세스를 종료했습니다.', pid)
		except (psutil.NoSuchProcess, psutil.AccessDenied):
			pass
	return '종료 완료'
	
def exec_start(FLASKAPPSNAME, FLASKAPPS, FLASKTIME, FLASKTELGM, FLASKTOKEN, FLASKBOTID, FLASKALIM):
	
	is_running = False
	current_command = FLASKAPPS.strip()
	for proc in psutil.process_iter():
		try:
			full_cmd_line = " ".join(proc.cmdline())
			#cmdline = proc.cmdline()
			# 실행하려는 명령어의 모든 단어가 현재 프로세스의 cmdline에 들어있는지 확인
			if current_command in full_cmd_line:
				if proc.pid != os.getpid() and proc.pid != os.getppid():
					is_running = True
					break
		except (psutil.NoSuchProcess, psutil.AccessDenied):
			continue

	if is_running:
		logger.info(f"[{FLASKAPPSNAME}] 이미 동일한 프로세스가 실행 중이므로 스케줄 실행을 건너뜁니다.")
		return '이미 실행 중'
	msg = '{}을 시작합니다. {}'.format(FLASKAPPSNAME, FLASKAPPS)
	msg_end = '{}을 완료합니다. {}'.format(FLASKAPPSNAME, FLASKAPPS)
	#ss = proc_test(FLASKAPPS)
	logger.info(msg)
	if FLASKTELGM == 'True' :
		bot = telegram.Bot(token = FLASKTOKEN)
		if FLASKALIM == 'True' :
			bot.sendMessage(chat_id = FLASKBOTID, text=msg, disable_notification=True)
			try:
				subprocess.Popen(FLASKAPPS, shell=True)
			except Exception as e:
				logger.error(f"실행 오류: {e}")
			return '완료'
		else :
			bot.sendMessage(chat_id = FLASKBOTID, text=msg, disable_notification=False)
			try:
				subprocess.Popen(FLASKAPPS, shell=True)	
			except Exception as e:
				logger.error(f"실행 오류: {e}")
			return '완료'	
	else:
		try:
			subprocess.Popen(FLASKAPPS, shell=True)
		except Exception as e:
			logger.error(f"실행 오류: {e}")
		return '완료'
	logger.info(msg_end)
	#DB최적화
	#db_optimization()
	comp = '완료'
	return comp		
@bp3.route('/')
@bp3.route('index')
def second():
	if not session.get('logFlag'):
		return redirect(url_for('main.index'))
	else:
		con = sqlite3.connect(sub3db,timeout=60)
		con.row_factory = sqlite3.Row
		cur = con.cursor()
		cur.execute("SELECT * FROM sqlite_master WHERE type='table'")
		tableser = cur.fetchall()
		rows = []
		for tt in tableser:
			cur.execute("SELECT * FROM " + tt[1])
			mytable = cur.fetchall()
			rows.append(mytable[0])
		con.close()
		tltl = []
		test2 = scheduler.get_jobs()
		for i in test2:
			aa = i.id
			tltl.append(aa)
		return render_template('program.html', rows = rows, tltl = tltl)
		
@bp3.route("edit/<FLASKAPPSNAME>", methods=['GET'])
def edit(FLASKAPPSNAME):
	if not session.get('logFlag'):
		return redirect(url_for('main.index'))
	else:
		conn = sqlite3.connect(sub3db,timeout=60)
		conn.row_factory = sqlite3.Row
		cursor = conn.cursor()
		sql = "select * from " + FLASKAPPSNAME + " where FLASKAPPSNAME = ?"
		cursor.execute(sql, (FLASKAPPSNAME,))
		row = cursor.fetchone()
		FLASKAPPSNAME = row['FLASKAPPSNAME']
		FLASKAPPS = row['FLASKAPPS']
		FLASKTIME = row['FLASKTIME']
		FLASKTELGM = row['FLASKTELGM']
		FLASKTOKEN = row['FLASKTOKEN']
		FLASKBOTID = row['FLASKBOTID']
		FLASKALIM = row['FLASKALIM']
		cursor.close()
		return render_template('edit.html', FLASKAPPSNAME=FLASKAPPSNAME, FLASKAPPS=FLASKAPPS,FLASKTELGM=FLASKTELGM,FLASKTOKEN=FLASKTOKEN,FLASKBOTID=FLASKBOTID,FLASKALIM=FLASKALIM,FLASKTIME=FLASKTIME)	

@bp3.route("edit_result/<FLASKAPPSNAME>", methods=['POST'])
def edit_result(FLASKAPPSNAME):
	if not session.get('logFlag'):
		return redirect(url_for('main.index'))
	else:
		FLASKAPPS = request.form['FLASKAPPS']
		FLASKTIME = request.form['FLASKTIME']
		FLASKTELGM = request.form['FLASKTELGM']
		FLASKTOKEN = request.form['FLASKTOKEN']
		FLASKBOTID = request.form['FLASKBOTID']
		FLASKALIM = request.form['FLASKALIM']
		FLASKAPPS2 = FLASKAPPS.replace("\\", "/")
		conn = sqlite3.connect(sub3db,timeout=60)
		cursor = conn.cursor()
		try:
			sql_update = "UPDATE " + FLASKAPPSNAME + " SET FLASKAPPS= ?, FLASKTIME = ?, FLASKTELGM = ?, FLASKTOKEN = ?, FLASKBOTID =?, FLASKALIM =?  WHERE FLASKAPPSNAME = ?"
			cursor.execute(sql_update,(FLASKAPPS2, FLASKTIME, FLASKTELGM, FLASKTOKEN, FLASKBOTID, FLASKALIM, FLASKAPPSNAME))
			conn.commit()
		except:
			conn.rollback()
		finally:	
			conn.close()
		return redirect(url_for('sub3.second'))
		
@bp3.route("databasedel/<FLASKAPPSNAME>", methods=["GET"])
def databasedel(FLASKAPPSNAME):
	if not session.get('logFlag'):
		return redirect(url_for('main.index'))
	else:
		print(FLASKAPPSNAME)
		con = sqlite3.connect(sub3db,timeout=60)	
		con.row_factory = sqlite3.Row
		cur = con.cursor()
		try:
			sql = "DROP TABLE " + FLASKAPPSNAME
			cur.execute(sql)
			con.commit()
		except:
			con.rollback()
		finally:	
			con.close()	
		return redirect(url_for('sub3.second'))

@bp3.route("ok/<FLASKAPPSNAME>", methods=["GET"])
def ok(FLASKAPPSNAME):
	if not session.get('logFlag'):
		return redirect(url_for('main.index'))
	else:
		con = sqlite3.connect(sub3db,timeout=60)
		#con.execute("PRAGMA synchronous = OFF")
		#con.execute("PRAGMA journal_mode = MEMORY")
		con.execute("PRAGMA cache_size = 10000")
		#con.execute("PRAGMA locking_mode = EXCLUSIVE")
		con.execute("PRAGMA locking_mode = NORMAL")
		con.execute("PRAGMA temp_store = MEMORY")
		con.execute("PRAGMA auto_vacuum = 1")
		con.execute("PRAGMA journal_mode=WAL")
		con.execute("PRAGMA synchronous=NORMAL")
		con.row_factory = sqlite3.Row
		cursor = con.cursor()
		sql = 'select * from ' + FLASKAPPSNAME + ' where FLASKAPPSNAME = ?'
		cursor.execute(sql, (FLASKAPPSNAME,))
		row = cursor.fetchone()
		FLASKAPPSNAME = row['FLASKAPPSNAME']
		FLASKAPPS = row['FLASKAPPS']
		FLASKTIME = row['FLASKTIME']
		FLASKTELGM = row['FLASKTELGM']
		FLASKTOKEN = row['FLASKTOKEN']
		FLASKBOTID = row['FLASKBOTID']
		FLASKALIM = row['FLASKALIM']
		try:
			scheduler.add_job(exec_start, trigger=CronTrigger.from_crontab(FLASKTIME), id=FLASKAPPSNAME, args=[FLASKAPPSNAME, FLASKAPPS, FLASKTIME, FLASKTELGM, FLASKTOKEN, FLASKBOTID, FLASKALIM],max_instances=10,replace_existing=True)
			test2 = scheduler.get_job(FLASKAPPSNAME).id
			logger.info('%s 를 스케줄러에 추가하였습니다.', test2)
		except ConflictingIdError:
			test = scheduler.get_job(FLASKAPPSNAME).id
			test2 = scheduler.modify_job(FLASKAPPSNAME).id
			logger.info('%s가 %s 스케줄러로 수정되었습니다.', test,test2)			
		return redirect(url_for('sub3.second'))

@bp3.route("now/<FLASKAPPSNAME>", methods=["GET"])
def now(FLASKAPPSNAME):
	if not session.get('logFlag'):
		return redirect(url_for('main.index'))
	else:
		con = sqlite3.connect(sub3db,timeout=60)
		#con.execute("PRAGMA synchronous = OFF")
		#con.execute("PRAGMA journal_mode = MEMORY")
		con.execute("PRAGMA cache_size = 10000")
		#con.execute("PRAGMA locking_mode = EXCLUSIVE")
		con.execute("PRAGMA locking_mode = NORMAL")
		con.execute("PRAGMA temp_store = MEMORY")
		con.execute("PRAGMA auto_vacuum = 1")
		con.execute("PRAGMA journal_mode=WAL")
		con.execute("PRAGMA synchronous=NORMAL")
		con.row_factory = sqlite3.Row
		cursor = con.cursor()
		sql = 'select * from ' + FLASKAPPSNAME + ' where FLASKAPPSNAME = ?'
		cursor.execute(sql, (FLASKAPPSNAME,))
		row = cursor.fetchone()
		FLASKAPPSNAME = row['FLASKAPPSNAME']
		FLASKAPPS = row['FLASKAPPS']
		FLASKTIME = row['FLASKTIME']
		FLASKTELGM = row['FLASKTELGM']
		FLASKTOKEN = row['FLASKTOKEN']
		FLASKBOTID = row['FLASKBOTID']
		FLASKALIM = row['FLASKALIM']
		exec_start(FLASKAPPSNAME, FLASKAPPS, FLASKTIME, FLASKTELGM, FLASKTOKEN, FLASKBOTID, FLASKALIM)
		return redirect(url_for('sub3.second'))

@bp3.route("kill/<FLASKAPPSNAME>", methods=["GET"])
def kill(FLASKAPPSNAME):
	if not session.get('logFlag'):
		return redirect(url_for('main.index'))
	else:
		con = sqlite3.connect(sub3db,timeout=60)
		#con.execute("PRAGMA synchronous = OFF")
		#con.execute("PRAGMA journal_mode = MEMORY")
		con.execute("PRAGMA cache_size = 10000")
		#con.execute("PRAGMA locking_mode = EXCLUSIVE")
		con.execute("PRAGMA locking_mode = NORMAL")
		con.execute("PRAGMA temp_store = MEMORY")
		con.execute("PRAGMA auto_vacuum = 1")
		con.execute("PRAGMA journal_mode=WAL")
		con.execute("PRAGMA synchronous=NORMAL")
		con.row_factory = sqlite3.Row
		cursor = con.cursor()
		sql = 'select * from ' + FLASKAPPSNAME + ' where FLASKAPPSNAME = ?'
		cursor.execute(sql, (FLASKAPPSNAME,))
		row = cursor.fetchone()
		FLASKAPPSNAME = row['FLASKAPPSNAME']
		FLASKAPPS = row['FLASKAPPS']
		FLASKTIME = row['FLASKTIME']
		FLASKTELGM = row['FLASKTELGM']
		FLASKTOKEN = row['FLASKTOKEN']
		FLASKBOTID = row['FLASKBOTID']
		FLASKALIM = row['FLASKALIM']
		proc_test(FLASKAPPS)
		return redirect(url_for('sub3.second'))
		
@bp3.route("cancle/<FLASKAPPSNAME>", methods=["GET"])
def cancle(FLASKAPPSNAME):
	if not session.get('logFlag'):
		return redirect(url_for('main.index'))
	else:
		try:
			test = scheduler.get_job(FLASKAPPSNAME).id
			logger.info('%s가 스케줄러에 있습니다.', test)
		except Exception as e:
			test = None
		if test == None:
			logger.info('%s의 스케줄러가 종료가 되지 않았습니다.', FLASKAPPSNAME)
		else:
			scheduler.remove_job(FLASKAPPSNAME)
			logger.info('%s 스케줄러를 삭제하였습니다.', test)
			test2 = scheduler.get_jobs()
			for i in test2:
				aa = i.id
				logger.info('%s 가 스케줄러가 있습니다.', aa)

		logger.info('%s 를 스케줄러를 삭제하였습니다.', test)
		return redirect(url_for('sub3.second'))
		
@bp3.route("start", methods=['POST'])
def start():
	if not session.get('logFlag'):
		return redirect(url_for('main.index'))
	else:
		FLASKAPPSNAME = request.form['FLASKAPPSNAME']
		FLASKAPPS = request.form['FLASKAPPS']
		FLASKTIME = request.form['FLASKTIME']
		FLASKTELGM = request.form['FLASKTELGM']
		FLASKTOKEN = request.form['FLASKTOKEN']
		FLASKBOTID = request.form['FLASKBOTID']
		FLASKALIM = request.form['FLASKALIM']
		FLASKAPPS2 = FLASKAPPS.replace("\\", "/")
		#데이타베이스 없으면 생성
		con = sqlite3.connect(sub3db,timeout=60)
		con.execute('CREATE TABLE IF NOT EXISTS ' + FLASKAPPSNAME +' (FLASKAPPSNAME TEXT, FLASKAPPS TEXT, FLASKTIME TEXT, FLASKTELGM TEXT, FLASKTOKEN TEXT, FLASKBOTID TEXT, FLASKALIM TEXT)')
		#con.execute("PRAGMA synchronous = OFF")
		#con.execute("PRAGMA journal_mode = MEMORY")
		con.execute("PRAGMA cache_size = 10000")
		#con.execute("PRAGMA locking_mode = EXCLUSIVE")
		con.execute("PRAGMA locking_mode = NORMAL")
		con.execute("PRAGMA temp_store = MEMORY")
		con.execute("PRAGMA auto_vacuum = 1")
		con.execute("PRAGMA journal_mode=WAL")
		con.execute("PRAGMA synchronous=NORMAL")
		con.close()
		try:		
			print(FLASKAPPSNAME)
			con = sqlite3.connect(sub3db,timeout=60)
			cur = con.cursor()
			cur.execute("INSERT OR REPLACE INTO " + FLASKAPPSNAME + "  (FLASKAPPSNAME, FLASKAPPS, FLASKTIME, FLASKTELGM, FLASKTOKEN, FLASKBOTID, FLASKALIM) VALUES (?, ?, ?, ?, ?, ?, ?)", (FLASKAPPSNAME, FLASKAPPS2, FLASKTIME, FLASKTELGM, FLASKTOKEN, FLASKBOTID, FLASKALIM))
			con.commit()		
		except:
			con.rollback()
			
		finally:
			con.close()
			
	return redirect(url_for('sub3.second'))