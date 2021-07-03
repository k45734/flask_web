from flask import Blueprint
#여기서 필요한 모듈
import os
from datetime import datetime, timedelta
import requests
from flask import Flask, flash, redirect, render_template, request, session, abort, url_for, send_file, send_from_directory
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

bp4 = Blueprint('sub4', __name__, url_prefix='/sub4')
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
dfolder = os.path.dirname(os.path.abspath(__file__)) + '/log'
#데이타베이스 없으면 생성
conn = sqlite3.connect('./database.db')
#print ("Opened database successfully")
conn.execute('CREATE TABLE IF NOT EXISTS database2 (idx integer primary key autoincrement, MY_DATE TEXT, PRODUCT_NAME TEXT, RECEIVING TEXT, SHIPPING TEXT, TOTAL TEXT)')
#print ("Table created successfully")
conn.close()
job_defaults = { 'max_instances': 1 }
scheduler = BackgroundScheduler(job_defaults=job_defaults)
scheduler.start()

@bp4.route('/')
@bp4.route('index')
def second():
	if not session.get('logFlag'):
		return redirect(url_for('main.index'))
	else:
		idx = request.args.get('idx')
		MY_DATE = request.args.get('MY_DATE')
		PRODUCT_NAME = request.args.get('PRODUCT_NAME')
		RECEIVING = request.args.get('RECEIVING')
		SHIPPING = request.args.get('SHIPPING')
		TOTAL = request.args.get('TOTAL')
		con = sqlite3.connect("database.db")
		con.row_factory = sqlite3.Row
		cur = con.cursor()
		cur.execute("select * from database2")
		rows = cur.fetchall()
		return render_template('stock.html', rows = rows)
		
@bp4.route("edit_result", methods=["GET"])
def edit_result():
	if not session.get('logFlag'):
		return redirect(url_for('main.index'))
	else:
		c = sqlite3.connect('./database.db')
		idx = request.args.get('idx')
		MY_DATE = request.args.get('MY_DATE')
		PRODUCT_NAME = request.args.get('PRODUCT_NAME')
		RECEIVING = request.args.get('RECEIVING')
		SHIPPING = request.args.get('SHIPPING')
		if SHIPPING == 0:
			test = int(RECEIVING) - 0
		else :
			test = int(RECEIVING) - int(SHIPPING)
		TOTAL = test
		#TOTAL = request.args.get('TOTAL')
		db = c.cursor()
		sql_update = "UPDATE database2 SET PRODUCT_NAME= ?, RECEIVING = ?, SHIPPING = ?, TOTAL = ?, MY_DATE = ? WHERE idx = ?"
		db.execute(sql_update,(PRODUCT_NAME, RECEIVING, SHIPPING, TOTAL, MY_DATE, idx))
		c.commit()
		return redirect(url_for('sub4.second'))
	
@bp4.route("edit", methods=["POST", "GET"])
def edit():
	if not session.get('logFlag'):
		return redirect(url_for('main.index'))
	else:
		idx = request.args.get('idx')
		MY_DATE = request.args.get('MY_DATE')
		PRODUCT_NAME = request.args.get('PRODUCT_NAME')
		RECEIVING = request.args.get('RECEIVING')
		SHIPPING = request.args.get('SHIPPING')
		#if SHIPPING == 0:
		#	test = int(RECEIVING) - 0
		#else :
	#		test = int(RECEIVING) - int(SHIPPING)
		if not SHIPPING:
			SHIPPING = 0
		if not RECEIVING:
			RECEIVING = 0
		test = int(a) + int(RECEIVING) - int(SHIPPING)
		TOTAL = test
		#TOTAL = request.args.get('TOTAL')
		c = sqlite3.connect('./database.db')
		db = c.cursor()
		contents = "SELECT '{}' FROM database2 WHERE idx = '{}'".format(MY_DATE, idx) 
		db.execute(contents)
		return render_template('stock_edit.html',MY_DATE=MY_DATE,PRODUCT_NAME=PRODUCT_NAME,RECEIVING=RECEIVING,SHIPPING=SHIPPING,TOTAL=TOTAL,idx=idx)	
	
@bp4.route("databasedel/<idx>", methods=["GET"])
def databasedel(idx):
	if not session.get('logFlag'):
		return redirect(url_for('main.index'))
	else:
		con = sqlite3.connect("./database.db")	
		con.row_factory = sqlite3.Row
		cur = con.cursor()
		sql = "DELETE FROM database2 WHERE idx = '{}'".format(idx)
		cur.execute(sql)
		cur.execute("select * from database2")
		con.commit()
		rows = cur.fetchall()
		return redirect(url_for('sub4.second'))

@bp4.route("ok", methods=["GET","POST"])
def ok():
	if not session.get('logFlag'):
		return redirect(url_for('main.index'))
	else:
		idx = request.args.get('idx')
		MY_DATE = request.args.get('MY_DATE')
		PRODUCT_NAME = request.args.get('PRODUCT_NAME')
		RECEIVING = request.args.get('RECEIVING')
		SHIPPING = request.args.get('SHIPPING')
		TOTAL = request.args.get('TOTAL')
		con = sqlite3.connect("./database.db")
		con.row_factory = sqlite3.Row
		cur = con.cursor()
		cur.execute("select * from database2")
		rows = cur.fetchall()
		return redirect(url_for('sub4.second'))

@bp4.route("csv_download")		
def csv_download():
	file_name = f"./database.csv"
	return send_file(file_name, 
					mimetype='text/csv', 
					attachment_filename='database.csv',# 다운받아지는 파일 이름. 
					as_attachment=True)

@bp4.route("csv_import")		
def csv_import():
	if not session.get('logFlag'):
		return redirect(url_for('main.index'))
	else:	
		con = sqlite3.connect('./database.db')
		cur = con.cursor()
		bables = cur.execute('SELECT * FROM database2')
		com_te=""
		f=open("database.csv","w")
		for table in bables:
			com_te = str(table)+"\n"
			print(com_te)
			f.write(com_te)
			#save_to_file(com_te)
			f.close
		con.close()
		print("CSV file import done.")
		#time.sleep(10)
		#return send_file('database.csv' , mimetype='text/csv', attachment_filename = 'database.csv' ,as_attachment=True)
		return redirect(url_for('sub4.second'))
		#return send_from_directory('./', "database.csv")
	
@bp4.route("start", methods=['POST','GET'])
def start():
	if request.method == 'POST':
		MY_DATE = request.form['MY_DATE']
		PRODUCT_NAME = request.form['PRODUCT_NAME']
		RECEIVING = request.form['RECEIVING']
		SHIPPING = request.form['SHIPPING']
		con = sqlite3.connect("database.db")	
		con.row_factory = sqlite3.Row
		cur = con.cursor()
		cur.execute("select * from database2 WHERE PRODUCT_NAME = '{}' ORDER BY ROWID DESC LIMIT 1".format(PRODUCT_NAME))
		rows = cur.fetchone()
		try:
			a = dict(rows)['TOTAL'] 
			
		except:
			a = 0
			
		finally:
			con.close()
			
		try:
			with sqlite3.connect("database.db")	as con:
				if session.get('logFlag'):
					#print(SHIPPING)
					print(a)
					if not SHIPPING:
						SHIPPING = 0
					if not RECEIVING:
						RECEIVING = 0
					test = int(a) + int(RECEIVING) - int(SHIPPING)
					TOTAL = test
					con.row_factory = sqlite3.Row
					cur = con.cursor()
					cur.execute("INSERT INTO database2 (MY_DATE, PRODUCT_NAME, RECEIVING, SHIPPING, TOTAL) VALUES (?, ?, ?, ?, ?)", (MY_DATE, PRODUCT_NAME, RECEIVING, SHIPPING, TOTAL))
					#cur.execute("select * from database2")
					con.commit()
					rows = cur.fetchall()
	
				else:
					con.row_factory = sqlite3.Row
					cur = con.cursor()
					cur.execute("select * from database2")
					con.commit()
					rows = cur.fetchall()
					
		except:
			con.rollback()
		
		finally:
			con.close()
		return redirect(url_for('sub4.second'))