from flask import Blueprint
#여기서 필요한 모듈
from datetime import datetime, timedelta 
import os.path, bs4, sqlite3, threading, telegram, time, logging, subprocess, requests, os
from flask import Flask, flash, redirect, render_template, request, session, abort, url_for
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.jobstores.base import BaseJobStore, JobLookupError, ConflictingIdError
from apscheduler.triggers.cron import CronTrigger

bp3 = Blueprint('sub3', __name__, url_prefix='/sub3')
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
dfolder = os.path.dirname(os.path.abspath(__file__)) + '/log'
#데이타베이스 없으면 생성
conn = sqlite3.connect('database.db')
#print ("Opened database successfully")
conn.execute('CREATE TABLE IF NOT EXISTS database (FLASKAPPSREPEAT TEXT, FLASKAPPSNAME TEXT, FLASKAPPS TEXT, FLASKTIME TEXT, FLASKTELGM TEXT, FLASKTOKEN TEXT, FLASKBOTID TEXT, FLASKALIM TEXT)')
#print ("Table created successfully")
conn.close()
job_defaults = { 'coalesce': False, 'max_instances': 1 }
sub3_page = BackgroundScheduler(job_defaults=job_defaults)
f = open('./log/flask.log','a', encoding='utf-8')
rfh = logging.handlers.RotatingFileHandler(filename='./log/flask.log', mode='a', maxBytes=5*1024*1024, backupCount=2, encoding=None, delay=0)
logging.basicConfig(level=logging.INFO,format="[%(filename)s:%(lineno)d %(levelname)s] - %(message)s",handlers=[rfh])
logger = logging.getLogger()
sub3_page.start()

@bp3.route('/')
@bp3.route('index')
def second():
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
		FLASKAPPSREPEAT = request.args.get('FLASKAPPSREPEAT')
		con = sqlite3.connect("database.db")
		con.row_factory = sqlite3.Row
		cur = con.cursor()
		cur.execute("select * from database")
		rows = cur.fetchall()
		return render_template('program.html', rows = rows)
		
@bp3.route("edit/<FLASKAPPSNAME>", methods=['GET'])
def edit(FLASKAPPSNAME):
	if not session.get('logFlag'):
		return redirect(url_for('main.index'))
	else:
		conn = sqlite3.connect('./database.db')
		cursor = conn.cursor()
		sql = "select * from database where FLASKAPPSNAME = ?"
		cursor.execute(sql, (FLASKAPPSNAME,))
		row = cursor.fetchone()
		FLASKAPPSREPEAT = row[0]
		FLASKAPPSNAME = row[1]
		FLASKAPPS = row[2]
		FLASKTIME = row[3]
		FLASKTELGM = row[4]
		FLASKTOKEN = row[5]
		FLASKBOTID = row[6]
		FLASKALIM = row[7]
		return render_template('edit.html', FLASKAPPSNAME=FLASKAPPSNAME, FLASKAPPSREPEAT=FLASKAPPSREPEAT,FLASKAPPS=FLASKAPPS,FLASKTELGM=FLASKTELGM,FLASKTOKEN=FLASKTOKEN,FLASKBOTID=FLASKBOTID,FLASKALIM=FLASKALIM,FLASKTIME=FLASKTIME)	

@bp3.route("edit_result", methods=['POST'])
def edit_result():
	if not session.get('logFlag'):
		return redirect(url_for('main.index'))
	else:
		c = sqlite3.connect('./database.db')
		FLASKAPPSNAME = request.form['FLASKAPPSNAME']
		FLASKAPPS = request.form['FLASKAPPS']
		FLASKTIME = request.form['FLASKTIME']
		FLASKTELGM = request.form['FLASKTELGM']
		FLASKTOKEN = request.form['FLASKTOKEN']
		FLASKBOTID = request.form['FLASKBOTID']
		FLASKALIM = request.form['FLASKALIM']
		FLASKAPPSREPEAT = request.form['FLASKAPPSREPEAT']	
		FLASKAPPS2 = FLASKAPPS.replace("\\", "/")
		db = c.cursor()
		sql_update = "UPDATE database SET FLASKAPPSREPEAT=?, FLASKAPPS= ?, FLASKTIME = ?, FLASKTELGM = ?, FLASKTOKEN = ?, FLASKBOTID =?, FLASKALIM =?  WHERE FLASKAPPSNAME = ?"
		db.execute(sql_update,(FLASKAPPSREPEAT, FLASKAPPS2, FLASKTIME, FLASKTELGM, FLASKTOKEN, FLASKBOTID, FLASKALIM, FLASKAPPSNAME))
		c.commit()
		return redirect(url_for('sub3.second'))
		
@bp3.route("databasedel/<FLASKAPPSNAME>", methods=["GET"])
def databasedel(FLASKAPPSNAME):
	if not session.get('logFlag'):
		return redirect(url_for('main.index'))
	else:
		con = sqlite3.connect("./database.db")	
		con.row_factory = sqlite3.Row
		cur = con.cursor()
		sql = "DELETE FROM database WHERE FLASKAPPSNAME = '{}'".format(FLASKAPPSNAME)
		cur.execute(sql)
		cur.execute("select * from database")
		con.commit()
		rows = cur.fetchall()
		return redirect(url_for('sub3.second'))
		
def exec_start(FLASKAPPSREPEAT, FLASKAPPSNAME, FLASKAPPS, FLASKTIME, FLASKTELGM, FLASKTOKEN, FLASKBOTID, FLASKALIM):
	BASE_DIR = os.path.dirname(os.path.abspath(__file__))
	dfolder = os.path.dirname(os.path.abspath(__file__)) + '/apps'
	#텔레그램
	if FLASKTELGM == '0' :
		bot = telegram.Bot(token = FLASKTOKEN)
	cnt = 0
	i = 0
	test = int(FLASKAPPSREPEAT)
	tee = FLASKAPPS.replace("\\", "/")
	logger.info('%s을 시작합니다.', FLASKAPPSNAME)
	for ii in range(test):
		parse_start = '{} 를 {} 시작합니다.'.format(FLASKAPPSNAME, int(cnt))
		logger.info('%s', parse_start)
		parse_stop = '{} 를 {} 종료되었습니다.'.format(FLASKAPPSNAME, int(cnt))
		if FLASKTELGM == '0' :
			if FLASKALIM == '0' :
				bot.sendMessage(chat_id = FLASKBOTID, text=parse_start, disable_notification=True)
				subprocess.call(FLASKAPPS, shell=True)
				bot.sendMessage(chat_id = FLASKBOTID, text=parse_stop, disable_notification=True)
				
			else :
				bot.sendMessage(chat_id = FLASKBOTID, text=parse_start, disable_notification=False)
				subprocess.call(FLASKAPPS, shell=True)
				bot.sendMessage(chat_id = FLASKBOTID, text=parse_stop, disable_notification=False)
					
		else :
			subprocess.call(FLASKAPPS, shell=True)
		
	logger.info('%s', parse_stop)
	try:
		sub3_page.remove_job(FLASKAPPSNAME)
	except:
		pass
	logger.info('%s의 스케줄러를 종료합니다.', FLASKAPPSNAME)
	#test = sub3_page.print_jobs()
	test2 = sub3_page.get_jobs()
	for i in test2:
		aa = i.id
		logger.info('%s 가 스케줄러가 있습니다.', aa)

@bp3.route("ok/<FLASKAPPSNAME>", methods=["GET"])
def ok(FLASKAPPSNAME):
	if not session.get('logFlag'):
		return redirect(url_for('main.index'))
	else:
		conn = sqlite3.connect('./database.db')
		cursor = conn.cursor()
		sql = "select * from database where FLASKAPPSNAME = ?"
		cursor.execute(sql, (FLASKAPPSNAME,))
		row = cursor.fetchone()
		FLASKAPPSREPEAT = row[0]
		FLASKAPPSNAME = row[1]
		FLASKAPPS = row[2]
		FLASKTIME = row[3]
		FLASKTELGM = row[4]
		FLASKTOKEN = row[5]
		FLASKBOTID = row[6]
		FLASKALIM = row[7]
		try:
			sub3_page.add_job(exec_start, trigger=CronTrigger.from_crontab(FLASKTIME), id=FLASKAPPSNAME, args=[int(FLASKAPPSREPEAT), FLASKAPPSNAME, FLASKAPPS, FLASKTIME, FLASKTELGM, FLASKTOKEN, FLASKBOTID, FLASKALIM] )
			test2 = sub3_page.get_job(FLASKAPPSNAME).id
			logger.info('%s 를 스케줄러에 추가하였습니다.', test2)
		except ConflictingIdError:
			test = sub3_page.get_job(FLASKAPPSNAME).id
			test2 = sub3_page.modify_job(FLASKAPPSNAME)
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
			FLASKAPPSREPEAT = request.form['FLASKAPPSREPEAT']
			FLASKAPPS2 = FLASKAPPS.replace("\\", "/")
			with sqlite3.connect("./database.db")	as con:
				if session.get('logFlag'):
					#print("OK")
					con.row_factory = sqlite3.Row
					cur = con.cursor()
					cur.execute("INSERT INTO database (FLASKAPPSNAME, FLASKAPPS, FLASKTIME, FLASKTELGM, FLASKTOKEN, FLASKBOTID, FLASKALIM, FLASKAPPSREPEAT) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (FLASKAPPSNAME, FLASKAPPS2, FLASKTIME, FLASKTELGM, FLASKTOKEN, FLASKBOTID, FLASKALIM, FLASKAPPSREPEAT))
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