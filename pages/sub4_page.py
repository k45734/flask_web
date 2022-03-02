from flask import Blueprint
#여기서 필요한 모듈
import os, io, re, zipfile, shutil, json, time, random, base64, urllib.request, platform, logging, requests, os.path, threading, time, subprocess, sqlite3
from datetime import datetime, timedelta
import requests
from flask import Flask, flash, redirect, render_template, request, session, abort, url_for, send_file, send_from_directory
try:
	from openpyxl import Workbook
except ImportError:
	os.system('pip install openpyxl')
	from openpyxl import Workbook
bp4 = Blueprint('sub4', __name__, url_prefix='/sub4')
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
dfolder = os.path.dirname(os.path.abspath(__file__)) + '/log'
if platform.system() == 'Windows':
	at = os.path.splitdrive(os.getcwd())
	sub4db = at[0] + '/data/shop.db'
else:
	sub4db = '/data/shop.db'
#데이타베이스 없으면 생성
conn = sqlite3.connect(sub4db,timeout=60)
conn.execute('CREATE TABLE IF NOT EXISTS shop (idx integer primary key autoincrement, MY_DATE TEXT, PRODUCT_NAME TEXT, RECEIVING TEXT, SHIPPING TEXT, TOTAL TEXT)')
conn.close()

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
		con = sqlite3.connect(sub4db,timeout=60)
		con.row_factory = sqlite3.Row
		cur = con.cursor()
		cur.execute("select * from shop")
		rows = cur.fetchall()
		return render_template('stock.html', rows = rows)
		
@bp4.route("edit_result", methods=["GET"])
def edit_result():
	if not session.get('logFlag'):
		return redirect(url_for('main.index'))
	else:
		c = sqlite3.connect(sub4db,timeout=60)
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
		sql_update = "UPDATE shop SET PRODUCT_NAME= ?, RECEIVING = ?, SHIPPING = ?, TOTAL = ?, MY_DATE = ? WHERE idx = ?"
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
		c = sqlite3.connect(sub4db,timeout=60)
		db = c.cursor()
		contents = "SELECT '{}' FROM shop WHERE idx = '{}'".format(MY_DATE, idx) 
		db.execute(contents)
		return render_template('stock_edit.html',MY_DATE=MY_DATE,PRODUCT_NAME=PRODUCT_NAME,RECEIVING=RECEIVING,SHIPPING=SHIPPING,TOTAL=TOTAL,idx=idx)	
	
@bp4.route("databasedel/<idx>", methods=["GET"])
def databasedel(idx):
	if not session.get('logFlag'):
		return redirect(url_for('main.index'))
	else:
		con = sqlite3.connect(sub4db,timeout=60)	
		con.row_factory = sqlite3.Row
		cur = con.cursor()
		sql = "DELETE FROM shop WHERE idx = '{}'".format(idx)
		cur.execute(sql)
		cur.execute("select * from shop")
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
		con = sqlite3.connect(sub4db,timeout=60)
		con.row_factory = sqlite3.Row
		cur = con.cursor()
		cur.execute("select * from shop")
		rows = cur.fetchall()
		return redirect(url_for('sub4.second'))

@bp4.route("csv_download")		
def csv_download():
	file_name = f"./inventory.xlsx"
	return send_file(file_name, 
					mimetype='application/vnd.ms-excel', 
					attachment_filename='inventory.xlsx',# 다운받아지는 파일 이름. 
					as_attachment=True)

@bp4.route("csv_import")		
def csv_import():
	if not session.get('logFlag'):
		return redirect(url_for('main.index'))
	else:
		#workbook 생성하기(1개의 시트가 생성된 상태)
		workbook = Workbook()
		#현재 workbook의 활성화 된 Sheet 가져오기
		sheet = workbook.active
		sheet.title = "inventory" #해당 sheet의 sheet명 변경하기
		# cell에 직접 데이터 입력하기
		sheet['A1'] = "번호"
		sheet['B1'] = "날짜"
		sheet['C1'] = "물품명"
		sheet['D1'] = "입고"
		sheet['E1'] = "출고"
		sheet['F1'] = "합계"
		con = sqlite3.connect(sub4db,timeout=60)
		cur = con.cursor()
		bables = cur.execute('SELECT * FROM shop')
		rows = cur.fetchall()
		nh_data = []
		for table in rows:
			a = table[0]
			b = table[1]
			c = table[2]
			d = table[3]
			e = table[4]
			f = table[5]
			nh_data.extend([[a,b,c,d,e,f]])
			
		con.close()

		for i in nh_data:
			sheet.append(i)
		# 파일 저장하기
		workbook.save("./inventory.xlsx")
		return redirect(url_for('sub4.second'))
	
@bp4.route("start", methods=['POST','GET'])
def start():
	if request.method == 'POST':
		MY_DATE = request.form['MY_DATE']
		PRODUCT_NAME = request.form['PRODUCT_NAME']
		RECEIVING = request.form['RECEIVING']
		SHIPPING = request.form['SHIPPING']
		con = sqlite3.connect(sub4db,timeout=60)	
		con.row_factory = sqlite3.Row
		cur = con.cursor()
		cur.execute("select * from shop WHERE PRODUCT_NAME = '{}' ORDER BY ROWID DESC LIMIT 1".format(PRODUCT_NAME))
		rows = cur.fetchone()
		try:
			a = dict(rows)['TOTAL'] 
			
		except:
			a = 0
			
		finally:
			con.close()
			
		try:
			with sqlite3.connect(sub4db,timeout=60) as con:
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
					cur.execute("INSERT INTO shop (MY_DATE, PRODUCT_NAME, RECEIVING, SHIPPING, TOTAL) VALUES (?, ?, ?, ?, ?)", (MY_DATE, PRODUCT_NAME, RECEIVING, SHIPPING, TOTAL))
					#cur.execute("select * from database2")
					con.commit()
					rows = cur.fetchall()
	
				else:
					con.row_factory = sqlite3.Row
					cur = con.cursor()
					cur.execute("select * from shop")
					con.commit()
					rows = cur.fetchall()
					
		except:
			con.rollback()
		
		finally:
			con.close()
		return redirect(url_for('sub4.second'))