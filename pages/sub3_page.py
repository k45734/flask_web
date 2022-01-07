from flask import Blueprint
#여기서 필요한 모듈
import os
from datetime import datetime, timedelta
import requests
from flask import Flask, flash, redirect, render_template, request, session, abort, url_for
import os.path
from flask_ipblock import IPBlock
from flask_ipblock.documents import IPNetwork
import random
import bs4
import sqlite3
import threading
import telegram
import time
import subprocess
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.base import JobLookupError
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
job_defaults = { 'max_instances': 1 }
scheduler3 = BackgroundScheduler(job_defaults=job_defaults)
scheduler3.start()

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
		#return 'Hello, python !<br>Flask TEST PAGE 3!'
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
		
		#print(FLASKAPPS)
		#print(tee)
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
		#sql = "DELETE FROM database where title_name=%s"
		cur.execute(sql)
		cur.execute("select * from database")
		con.commit()
		rows = cur.fetchall()
		#print("DB:")
		#print(rows)
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
	print(FLASKAPPS)
	#print(tee)
	#print(scheduler.get_jobs())
	while True:
		cnt += 1
		test -= 1
		con = sqlite3.connect("./database.db")
		con.row_factory = sqlite3.Row
		cur = con.cursor()
		cur.execute("select * from database")
		rows = cur.fetchall()	
		parse_start = '{} 를 {} 시작합니다.'.format(FLASKAPPSNAME, int(cnt))
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
		if test == 0:
			print(parse_start)
			scheduler3.remove_job(FLASKAPPSNAME)
			test = scheduler3.print_jobs()
			logger.info('%s', test)
			break
		#time.sleep(int(FLASKTIME))
		print(parse_start)

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
		scheduler3.add_job(exec_start, trigger=CronTrigger.from_crontab(FLASKTIME), id=FLASKAPPSNAME, args=[int(FLASKAPPSREPEAT), FLASKAPPSNAME, FLASKAPPS, FLASKTIME, FLASKTELGM, FLASKTOKEN, FLASKBOTID, FLASKALIM] )
		test = scheduler3.print_jobs()
		logger.info('%s', test)
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