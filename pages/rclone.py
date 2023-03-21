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
	sub3db = at[0] + '/data/rclone.db'
else:
	sub3db = '/data/rclone.db'
	
rclone = Blueprint('rclone', __name__, url_prefix='/rclone')
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
#프로세스확인
def proc_test(name):
	if platform.system() == 'Windows':
		py = "python"
		a2 = name.split()
		if py in a2:
			aa = a2[1]
			try:
				bb = a2[2]
			except:
				bb = None
		else:
			aa = a2[0]
			try:
				bb = a2[1]
			except:
				bb = None
	else:
		py = "python"
		a2 = name.split()
		if py in a2:
			aa = a2[1]
			try:
				bb = a2[2]
			except:
				bb = None
		else:
			aa = a2[0]
			try:
				bb = a2[1]
			except:
				bb = None
	logger.info('%s %s',aa, bb)
	for proc in psutil.process_iter():
		# 프로세스 이름, PID값 가져오기
		processName = proc.name()
		processID = proc.pid
		 #[:6] 
		try:
			commandLine = proc.cmdline()
			for i in commandLine:
				# 동일한 프로세스 확인. code 확인
				if len(a2) >= 3:
					if bb in i:	
						logger.info(bb)
						parent_pid = processID  #PID
						parent = psutil.Process(parent_pid)  # PID 찾기
						#print(parent)
						for child in parent.children(recursive=True):  #자식-부모 종료
							child.kill()
						parent.kill()
				else:
					if aa in i:
						logger.info(aa)
						parent_pid = processID  #PID
						parent = psutil.Process(parent_pid)  # PID 찾기
						#print(parent)
						for child in parent.children(recursive=True):  #자식-부모 종료
							child.kill()
						parent.kill()
							
				#else:
				#	pass
					#print(processName, ' ', commandLine, ' - ', processID)
		except:
			pass
		
	msg = '{} {} 동일 프로세스 확인 완료....'.format(aa,bb)
	return msg
	
def exec_start(RCLONENAME, RCLONE_CONFIG, FLASKTIME, RCLONE_LOCAL, RCLONE_REMOTE,RCLONE_C_M, RCLONE_include):
	if RCLONE_C_M == 'move':
		FLASKAPPS = '/data/rclone ' + RCLONE_C_M + ' ' + RCLONE_LOCAL + ' ' + RCLONE_REMOTE + ' -L --config ' + RCLONE_CONFIG + ' ' + RCLONE_include + ' --log-level INFO --stats 10s --stats-file-name-length 0 --transfers=1 --checkers=8 --delete-after --drive-chunk-size=32M --bwlimit "1M"'
	else:
		FLASKAPPS = '/data/rclone ' + RCLONE_C_M + ' ' + RCLONE_LOCAL + ' ' + RCLONE_REMOTE + ' -L --config ' + RCLONE_CONFIG + ' ' + RCLONE_include + ' --log-level INFO --min-size 1m --min-age 1m --stats 10s --stats-file-name-length 0 --transfers=1 --checkers=8 --delete-after --drive-chunk-size=32M --bwlimit "1M"'
	print(FLASKAPPS)
	logger.info(FLASKAPPS)	
	subprocess.call(FLASKAPPS, shell=True)
	comp = '완료'
	return comp	
	
@rclone.route('/')
@rclone.route('index')
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
		return render_template('rclone.html', rows = rows, tltl = tltl)
		
@rclone.route("edit/<RCLONENAME>", methods=['GET'])
def edit(RCLONENAME):
	if not session.get('logFlag'):
		return redirect(url_for('main.index'))
	else:
		conn = sqlite3.connect(sub3db,timeout=60)
		conn.row_factory = sqlite3.Row
		cursor = conn.cursor()
		sql = "select * from " + RCLONENAME + " where RCLONENAME = ?"
		cursor.execute(sql, (RCLONENAME,))
		row = cursor.fetchone()
		RCLONENAME = row['RCLONENAME']
		FLASKTIME = row['FLASKTIME']
		RCLONE_CONFIG = row['RCLONE_CONFIG']
		RCLONE_REMOTE = row['RCLONE_REMOTE']
		RCLONE_LOCAL = row['RCLONE_LOCAL']
		RCLONE_C_M = row['RCLONE_C_M']
		RCLONE_include = row['RCLONE_include']
		cursor.close()
		return render_template('rclone_edit.html', RCLONE_C_M=RCLONE_C_M, RCLONE_include=RCLONE_include, RCLONENAME=RCLONENAME, RCLONE_CONFIG=RCLONE_CONFIG,RCLONE_REMOTE=RCLONE_REMOTE,RCLONE_LOCAL=RCLONE_LOCAL,FLASKTIME=FLASKTIME)	

@rclone.route("edit_result/<RCLONENAME>", methods=['POST'])
def edit_result(RCLONENAME):
	if not session.get('logFlag'):
		return redirect(url_for('main.index'))
	else:
		RCLONENAME = request.form['RCLONENAME']
		FLASKTIME = request.form['FLASKTIME']
		RCLONE_REMOTE = request.form['RCLONE_REMOTE']
		RCLONE_CONFIG = request.form['RCLONE_CONFIG']
		RCLONE_LOCAL = request.form['RCLONE_LOCAL']
		RCLONE_C_M = request.form['RCLONE_C_M']
		RCLONE_include = request.form['RCLONE_include']
		conn = sqlite3.connect(sub3db,timeout=60)
		cursor = conn.cursor()
		try:
			sql_update = "UPDATE " + RCLONENAME + " SET RCLONE_C_M = ? , RCLONE_include = ?, FLASKTIME = ?, RCLONE_REMOTE = ?, RCLONE_CONFIG = ?, RCLONE_LOCAL =? WHERE RCLONENAME = ?"
			cursor.execute(sql_update,(RCLONE_C_M, RCLONE_include, FLASKTIME, RCLONE_REMOTE, RCLONE_CONFIG, RCLONE_LOCAL, RCLONENAME))
			conn.commit()
		except:
			conn.rollback()
		finally:	
			conn.close()
		return redirect(url_for('rclone.second'))
		
@rclone.route("databasedel/<RCLONENAME>", methods=["GET"])
def databasedel(RCLONENAME):
	if not session.get('logFlag'):
		return redirect(url_for('main.index'))
	else:
		print(RCLONENAME)
		con = sqlite3.connect(sub3db,timeout=60)	
		con.row_factory = sqlite3.Row
		cur = con.cursor()
		try:
			sql = "DROP TABLE " + RCLONENAME
			cur.execute(sql)
			con.commit()
		except:
			con.rollback()
		finally:	
			con.close()	
		return redirect(url_for('rclone.second'))

@rclone.route("ok/<RCLONENAME>", methods=["GET"])
def ok(RCLONENAME):
	if not session.get('logFlag'):
		return redirect(url_for('main.index'))
	else:
		con = sqlite3.connect(sub3db,timeout=60)
		con.execute("PRAGMA cache_size = 10000")
		con.execute("PRAGMA locking_mode = NORMAL")
		con.execute("PRAGMA temp_store = MEMORY")
		con.execute("PRAGMA auto_vacuum = 1")
		con.execute("PRAGMA journal_mode=WAL")
		con.execute("PRAGMA synchronous=NORMAL")
		con.row_factory = sqlite3.Row
		cursor = con.cursor()
		sql = 'select * from ' + RCLONENAME + ' where RCLONENAME = ?'
		cursor.execute(sql, (RCLONENAME,))
		row = cursor.fetchone()
		RCLONENAME = row['RCLONENAME']
		RCLONE_CONFIG = row['RCLONE_CONFIG']
		FLASKTIME = row['FLASKTIME']
		RCLONE_LOCAL = row['RCLONE_LOCAL']
		RCLONE_REMOTE = row['RCLONE_REMOTE']
		RCLONE_C_M = row['RCLONE_C_M']
		RCLONE_include= row['RCLONE_include']
		try:
			scheduler.add_job(exec_start, trigger=CronTrigger.from_crontab(FLASKTIME), id=RCLONENAME, args=[RCLONENAME, RCLONE_CONFIG, FLASKTIME, RCLONE_LOCAL, RCLONE_REMOTE,RCLONE_C_M, RCLONE_include] )
			test2 = scheduler.get_job(RCLONENAME).id
			logger.info('%s 를 스케줄러에 추가하였습니다.', test2)
		except ConflictingIdError:
			test = scheduler.get_job(RCLONENAME).id
			test2 = scheduler.modify_job(RCLONENAME).id
			logger.info('%s가 %s 스케줄러로 수정되었습니다.', test,test2)			
		return redirect(url_for('rclone.second'))

@rclone.route("now/<RCLONENAME>", methods=["GET"])
def now(RCLONENAME):
	if not session.get('logFlag'):
		return redirect(url_for('main.index'))
	else:
		con = sqlite3.connect(sub3db,timeout=60)
		con.execute("PRAGMA cache_size = 10000")
		con.execute("PRAGMA locking_mode = NORMAL")
		con.execute("PRAGMA temp_store = MEMORY")
		con.execute("PRAGMA auto_vacuum = 1")
		con.execute("PRAGMA journal_mode=WAL")
		con.execute("PRAGMA synchronous=NORMAL")
		con.row_factory = sqlite3.Row
		cursor = con.cursor()
		sql = 'select * from ' + RCLONENAME + ' where RCLONENAME = ?'
		cursor.execute(sql, (RCLONENAME,))
		row = cursor.fetchone()
		RCLONENAME = row['RCLONENAME']
		RCLONE_CONFIG = row['RCLONE_CONFIG']
		FLASKTIME = row['FLASKTIME']
		RCLONE_LOCAL = row['RCLONE_LOCAL']
		RCLONE_REMOTE = row['RCLONE_REMOTE']
		RCLONE_C_M = row['RCLONE_C_M']
		RCLONE_include= row['RCLONE_include']
		exec_start(RCLONENAME, RCLONE_CONFIG, FLASKTIME, RCLONE_LOCAL, RCLONE_REMOTE,RCLONE_C_M,RCLONE_include)
		return redirect(url_for('rclone.second'))
		
@rclone.route("cancle/<RCLONENAME>", methods=["GET"])
def cancle(RCLONENAME):
	if not session.get('logFlag'):
		return redirect(url_for('main.index'))
	else:
		try:
			test = scheduler.get_job(RCLONENAME).id
			logger.info('%s가 스케줄러에 있습니다.', test)
		except Exception as e:
			test = None
		if test == None:
			logger.info('%s의 스케줄러가 종료가 되지 않았습니다.', RCLONENAME)
		else:
			scheduler.remove_job(RCLONENAME)
			logger.info('%s 스케줄러를 삭제하였습니다.', test)
			test2 = scheduler.get_jobs()
			for i in test2:
				aa = i.id
				logger.info('%s 가 스케줄러가 있습니다.', aa)

		logger.info('%s 를 스케줄러를 삭제하였습니다.', test)
		return redirect(url_for('rclone.second'))
		
@rclone.route("start", methods=['POST'])
def start():
	if not session.get('logFlag'):
		return redirect(url_for('main.index'))
	else:
		RCLONENAME = request.form['RCLONENAME']
		FLASKTIME = request.form['FLASKTIME']
		RCLONE_CONFIG = request.form['RCLONE_CONFIG']
		RCLONE_LOCAL = request.form['RCLONE_LOCAL']
		RCLONE_REMOTE = request.form['RCLONE_REMOTE']
		RCLONE_C_M = request.form['RCLONE_C_M']
		RCLONE_include= request.form['RCLONE_include']
		#데이타베이스 없으면 생성
		try:
			con = sqlite3.connect(sub3db,timeout=60)
			con.execute('CREATE TABLE IF NOT EXISTS ' + RCLONENAME + ' (RCLONENAME TEXT, FLASKTIME TEXT, RCLONE_CONFIG TEXT, RCLONE_LOCAL TEXT, RCLONE_REMOTE TEXT, RCLONE_C_M TEXT, RCLONE_include TEXT)')
			con.execute("PRAGMA cache_size = 10000")
			con.execute("PRAGMA locking_mode = NORMAL")
			con.execute("PRAGMA temp_store = MEMORY")
			con.execute("PRAGMA auto_vacuum = 1")
			con.execute("PRAGMA journal_mode=WAL")
			con.execute("PRAGMA synchronous=NORMAL")
			con.close()
		except:
			return redirect(url_for('rclone.second'))
		try:		
			print(RCLONENAME)
			con = sqlite3.connect(sub3db,timeout=60)
			cur = con.cursor()
			cur.execute("INSERT OR REPLACE INTO " + RCLONENAME + "  (RCLONENAME, FLASKTIME, RCLONE_CONFIG, RCLONE_LOCAL, RCLONE_REMOTE,RCLONE_C_M,RCLONE_include) VALUES (?, ?, ?, ?, ?, ? , ?)", (RCLONENAME, FLASKTIME, RCLONE_CONFIG, RCLONE_LOCAL, RCLONE_REMOTE,RCLONE_C_M,RCLONE_include))
			con.commit()		
		except:
			con.rollback()
			
		finally:
			con.close()
			
	return redirect(url_for('rclone.second'))
