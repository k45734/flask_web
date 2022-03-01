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
bp3 = Blueprint('sub3', __name__, url_prefix='/sub3')
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
dfolder = os.path.dirname(os.path.abspath(__file__)) + '/log'
job_defaults = { 'coalesce': False, 'max_instances': 1 }
sub3_page = BackgroundScheduler(job_defaults=job_defaults)
f = open('./log/flask.log','a', encoding='utf-8')
rfh = logging.handlers.RotatingFileHandler(filename='./log/flask.log', mode='a', maxBytes=5*1024*1024, backupCount=2, encoding=None, delay=0)
logging.basicConfig(level=logging.INFO,format="[%(filename)s:%(lineno)d %(levelname)s] - %(message)s",handlers=[rfh])
logger = logging.getLogger()
sub3_page.start()
if platform.system() == 'Windows':
	at = os.path.splitdrive(os.getcwd())
	sub3db = at[0] + '/data/database.db'
else:
	sub3db = '/data/database.db'
try:
	#DB 변경
	conn = sqlite3.connect(sub3db)
	cursor = conn.cursor()
	cursor.execute("select * from database")
	row = cursor.fetchone()
	print(len(row))
	if len(row) == 8:
		cursor.execute("DROP TABLE database")
		con.commit()
	else:
		print(len(row))
except:
	pass
		
def exec_start(FLASKAPPSNAME, FLASKAPPS, FLASKTIME, FLASKTELGM, FLASKTOKEN, FLASKBOTID, FLASKALIM):
	msg = '{}을 시작합니다. {}'.format(FLASKAPPSNAME, FLASKAPPS)
	
	if FLASKTELGM == '0' :
		bot = telegram.Bot(token = FLASKTOKEN)
		if FLASKALIM == '0' :
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
	#데이타베이스 없으면 생성
	conn = sqlite3.connect(sub3db)
	#print ("Opened database successfully")
	conn.execute('CREATE TABLE IF NOT EXISTS database (FLASKAPPSNAME TEXT, FLASKAPPS TEXT, FLASKTIME TEXT, FLASKTELGM TEXT, FLASKTOKEN TEXT, FLASKBOTID TEXT, FLASKALIM TEXT)')
	#print ("Table created successfully")
	conn.close()
	if not session.get('logFlag'):
		return redirect(url_for('main.index'))
	else:
		FLASKAPPSNAME = request.args.get('FLASKAPPSNAME')
		FLASKAPPS = request.args.get('FLASKAPPS')
		FLASKTIME = request.args.get('FLASKTIME')
		FLASKTELGM = request.args.get('FLASKTELGM')
		FLASKTOKEN = request.args.get('FLASKTOKEN')
		FLASKBOTID = request.args.get('FLASKBOTID')
		FLASKALIM = request.args.get('FLASKALIM')
		con = sqlite3.connect(sub3db)
		con.row_factory = sqlite3.Row
		cur = con.cursor()
		cur.execute("select * from database")
		rows = cur.fetchall()
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
		conn = sqlite3.connect(sub3db)
		cursor = conn.cursor()
		sql = "select * from database where FLASKAPPSNAME = ?"
		cursor.execute(sql, (FLASKAPPSNAME,))
		row = cursor.fetchone()
		FLASKAPPSNAME = row[0]
		FLASKAPPS = row[1]
		FLASKTIME = row[2]
		FLASKTELGM = row[3]
		FLASKTOKEN = row[4]
		FLASKBOTID = row[5]
		FLASKALIM = row[6]
		return render_template('edit.html', FLASKAPPSNAME=FLASKAPPSNAME, FLASKAPPS=FLASKAPPS,FLASKTELGM=FLASKTELGM,FLASKTOKEN=FLASKTOKEN,FLASKBOTID=FLASKBOTID,FLASKALIM=FLASKALIM,FLASKTIME=FLASKTIME)	

@bp3.route("edit_result", methods=['POST'])
def edit_result():
	if not session.get('logFlag'):
		return redirect(url_for('main.index'))
	else:
		c = sqlite3.connect(sub3db)
		FLASKAPPSNAME = request.form['FLASKAPPSNAME']
		FLASKAPPS = request.form['FLASKAPPS']
		FLASKTIME = request.form['FLASKTIME']
		FLASKTELGM = request.form['FLASKTELGM']
		FLASKTOKEN = request.form['FLASKTOKEN']
		FLASKBOTID = request.form['FLASKBOTID']
		FLASKALIM = request.form['FLASKALIM']
		FLASKAPPS2 = FLASKAPPS.replace("\\", "/")
		db = c.cursor()
		sql_update = "UPDATE database SET FLASKAPPS= ?, FLASKTIME = ?, FLASKTELGM = ?, FLASKTOKEN = ?, FLASKBOTID =?, FLASKALIM =?  WHERE FLASKAPPSNAME = ?"
		db.execute(sql_update,(FLASKAPPS2, FLASKTIME, FLASKTELGM, FLASKTOKEN, FLASKBOTID, FLASKALIM, FLASKAPPSNAME))
		c.commit()
		return redirect(url_for('sub3.second'))
		
@bp3.route("databasedel/<FLASKAPPSNAME>", methods=["GET"])
def databasedel(FLASKAPPSNAME):
	if not session.get('logFlag'):
		return redirect(url_for('main.index'))
	else:
		con = sqlite3.connect(sub3db)	
		con.row_factory = sqlite3.Row
		cur = con.cursor()
		sql = "DELETE FROM database WHERE FLASKAPPSNAME = '{}'".format(FLASKAPPSNAME)
		cur.execute(sql)
		cur.execute("select * from database")
		con.commit()
		rows = cur.fetchall()
		return redirect(url_for('sub3.second'))

@bp3.route("ok/<FLASKAPPSNAME>", methods=["GET"])
def ok(FLASKAPPSNAME):
	if not session.get('logFlag'):
		return redirect(url_for('main.index'))
	else:
		conn = sqlite3.connect(sub3db)
		cursor = conn.cursor()
		sql = "select * from database where FLASKAPPSNAME = ?"
		cursor.execute(sql, (FLASKAPPSNAME,))
		row = cursor.fetchone()
		FLASKAPPSNAME = row[0]
		FLASKAPPS = row[1]
		FLASKTIME = row[2]
		FLASKTELGM = row[3]
		FLASKTOKEN = row[4]
		FLASKBOTID = row[5]
		FLASKALIM = row[6]
		try:
			sub3_page.add_job(exec_start, trigger=CronTrigger.from_crontab(FLASKTIME), id=FLASKAPPSNAME, args=[FLASKAPPSNAME, FLASKAPPS, FLASKTIME, FLASKTELGM, FLASKTOKEN, FLASKBOTID, FLASKALIM] )
			test2 = sub3_page.get_job(FLASKAPPSNAME).id
			logger.info('%s 를 스케줄러에 추가하였습니다.', test2)
		except ConflictingIdError:
			test = sub3_page.get_job(FLASKAPPSNAME).id
			test2 = sub3_page.modify_job(FLASKAPPSNAME).id
			logger.info('%s가 %s 스케줄러로 수정되었습니다.', test,test2)			
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
			#sub3_page.shutdown()
			logger.info('%s 스케줄러를 삭제하였습니다.', test)
			test2 = sub3_page.get_jobs()
			for i in test2:
				aa = i.id
				logger.info('%s 가 스케줄러가 있습니다.', aa)

		logger.info('%s 를 스케줄러를 삭제하였습니다.', test)
		return redirect(url_for('sub3.second'))
		
@bp3.route("start", methods=['POST','GET'])
def start():
	if request.method == 'POST':
		try:
			FLASKAPPSNAME = request.form['FLASKAPPSNAME']
			FLASKAPPS = request.form['FLASKAPPS']
			FLASKTIME = request.form['FLASKTIME']
			FLASKTELGM = request.form['FLASKTELGM']
			FLASKTOKEN = request.form['FLASKTOKEN']
			FLASKBOTID = request.form['FLASKBOTID']
			FLASKALIM = request.form['FLASKALIM']
			FLASKAPPS2 = FLASKAPPS.replace("\\", "/")
			with sqlite3.connect(sub3db)	as con:
				if session.get('logFlag'):
					#print("OK")
					con.row_factory = sqlite3.Row
					cur = con.cursor()
					cur.execute("INSERT INTO database (FLASKAPPSNAME, FLASKAPPS, FLASKTIME, FLASKTELGM, FLASKTOKEN, FLASKBOTID, FLASKALIM) VALUES (?, ?, ?, ?, ?, ?, ?)", (FLASKAPPSNAME, FLASKAPPS2, FLASKTIME, FLASKTELGM, FLASKTOKEN, FLASKBOTID, FLASKALIM))
					cur.execute("select * from database")
					con.commit()
					rows = cur.fetchall()
				else:
					#print("NO")
					con.row_factory = sqlite3.Row
					cur = con.cursor()
					cur.execute("select * from database")
					con.commit()
					rows = cur.fetchall()
					
		except:
			con.rollback()
			
		finally:
			con.close()
			return redirect(url_for('sub3.second'))