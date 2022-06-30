from flask import Blueprint
#여기서 필요한 모듈
from datetime import datetime, timedelta 
import os.path, bs4, sqlite3, threading, telegram, time, logging, subprocess, requests, os
from flask import Flask, flash, redirect, render_template, request, session, abort, url_for
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.jobstores.base import BaseJobStore, JobLookupError, ConflictingIdError
from apscheduler.triggers.cron import CronTrigger
import os, io, re, zipfile, shutil, json, time, random, base64, urllib.request, platform, logging, requests, os.path, threading, time, subprocess
if platform.system() == 'Windows':
	at = os.path.splitdrive(os.getcwd())
	sub3db = at[0] + '/data/database.db'
	logdata = at[0] + '/data/log'
else:
	sub3db = '/data/database.db'
	logdata = '/data/log'
bp3 = Blueprint('sub3', __name__, url_prefix='/sub3')
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
dfolder = os.path.dirname(os.path.abspath(__file__)) + '/log'
job_defaults = { 'coalesce': False, 'max_instances': 1 }
sub3_page = BackgroundScheduler(job_defaults=job_defaults)
f = open(logdata + '/flask.log','a', encoding='utf-8')
rfh = logging.handlers.RotatingFileHandler(filename=logdata + '/flask.log', mode='a', maxBytes=5*1024*1024, backupCount=2, encoding=None, delay=0)
logging.basicConfig(level=logging.INFO,format="[%(filename)s:%(lineno)d %(levelname)s] - %(message)s",handlers=[rfh])
logger = logging.getLogger()
sub3_page.start()

def exec_start(FLASKAPPSNAME, FLASKAPPS, FLASKTIME, FLASKTELGM, FLASKTOKEN, FLASKBOTID, FLASKALIM):
	msg = '{}을 시작합니다. {}'.format(FLASKAPPSNAME, FLASKAPPS)
	
	if FLASKTELGM == 'True' :
		bot = telegram.Bot(token = FLASKTOKEN)
		if FLASKALIM == 'True' :
			bot.sendMessage(chat_id = FLASKBOTID, text=msg, disable_notification=True)
			subprocess.call(FLASKAPPS, shell=True)
		else :
			bot.sendMessage(chat_id = FLASKBOTID, text=msg, disable_notification=False)
			subprocess.call(FLASKAPPS, shell=True)
	else :
		logger.info(msg)
		subprocess.call(FLASKAPPS, shell=True)
	test2 = sub3_page.get_jobs()
	for i in test2:
		aa = i.id
		logger.info('%s 가 스케줄러가 있습니다.', aa)

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
		test2 = sub3_page.get_jobs()
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
		sql = "DROP TABLE " + FLASKAPPSNAME
		cur.execute(sql)
		con.commit()
		con.close
		return redirect(url_for('sub3.second'))

@bp3.route("ok/<FLASKAPPSNAME>", methods=["GET"])
def ok(FLASKAPPSNAME):
	if not session.get('logFlag'):
		return redirect(url_for('main.index'))
	else:
		conn = sqlite3.connect(sub3db,timeout=60)
		conn.row_factory = sqlite3.Row
		cursor = conn.cursor()
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
			sub3_page.add_job(exec_start, trigger=CronTrigger.from_crontab(FLASKTIME), id=FLASKAPPSNAME, args=[FLASKAPPSNAME, FLASKAPPS, FLASKTIME, FLASKTELGM, FLASKTOKEN, FLASKBOTID, FLASKALIM] )
			test2 = sub3_page.get_job(FLASKAPPSNAME).id
			logger.info('%s 를 스케줄러에 추가하였습니다.', test2)
		except ConflictingIdError:
			test = sub3_page.get_job(FLASKAPPSNAME).id
			test2 = sub3_page.modify_job(FLASKAPPSNAME).id
			logger.info('%s가 %s 스케줄러로 수정되었습니다.', test,test2)			
		return redirect(url_for('sub3.second'))

@bp3.route("now/<FLASKAPPSNAME>", methods=["GET"])
def now(FLASKAPPSNAME):
	if not session.get('logFlag'):
		return redirect(url_for('main.index'))
	else:
		conn = sqlite3.connect(sub3db,timeout=60)
		conn.row_factory = sqlite3.Row
		cursor = conn.cursor()
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
		
@bp3.route("cancle/<FLASKAPPSNAME>", methods=["GET"])
def cancle(FLASKAPPSNAME):
	if not session.get('logFlag'):
		return redirect(url_for('main.index'))
	else:
		try:
			test = sub3_page.get_job(FLASKAPPSNAME).id
			logger.info('%s가 스케줄러에 있습니다.', test)
		except Exception as e:
			test = None
		if test == None:
			logger.info('%s의 스케줄러가 종료가 되지 않았습니다.', FLASKAPPSNAME)
		else:
			sub3_page.remove_job(FLASKAPPSNAME)
			logger.info('%s 스케줄러를 삭제하였습니다.', test)
			test2 = sub3_page.get_jobs()
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
		conn = sqlite3.connect(sub3db,timeout=60)
		conn.execute('CREATE TABLE IF NOT EXISTS ' + FLASKAPPSNAME +' (FLASKAPPSNAME TEXT, FLASKAPPS TEXT, FLASKTIME TEXT, FLASKTELGM TEXT, FLASKTOKEN TEXT, FLASKBOTID TEXT, FLASKALIM TEXT)')
		conn.close()
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