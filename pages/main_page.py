#-*- coding: utf-8 -*-
from flask import Blueprint
import sys
try:
	reload(sys)
	sys.setdefaultencoding('utf-8')
except:
	pass
import os, os.path, sqlite3, time , psutil, platform
from datetime import datetime, timedelta
from flask import Flask, flash, redirect, render_template, request, session, abort, url_for
from requests import get
import requests
import zipfile, shutil 
from distutils.dir_util import copy_tree

bp = Blueprint('main', __name__, url_prefix='/')

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
		with open(filepath, 'rt', encoding='utf-8') as fp:
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
	
	return render_template('main.html', test = test, oos = oos, oocpu = oocpu, mem_percent = mem_percent, disk_percent = disk_percent, version = version, lines = lines)

			
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
	conn = sqlite3.connect('./login.db')
	cursor = conn.cursor()
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
		conn = sqlite3.connect('./login.db')
		cursor = conn.cursor()
		sql = """
			update member
				set id = ?, pwd = ?
				where idx = ?
		"""
		
		cursor.execute(sql, (userid, userpwd, idx))
		conn.commit()
		cursor.close()
		conn.close()
		return redirect(url_for('main.index'))

@bp.route("log")
def log():
	createFolder('./log')
	filepath = './log/flask.log'
	filepath2 = './log/flaskweb.log'
	if not os.path.isfile(filepath):
		f = open('./log/flask.log','a', encoding='utf-8')
	if not os.path.isfile(filepath2):
		f = open('./log/flaskweb.log','a', encoding='utf-8')
	if not session.get('logFlag'):
		return render_template('login.html')
	else:
		if platform.system() == 'Windows':
			filepath = './log/flask.log'
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
				tltl.append(test)
					
		else:
			filepath = './log/flask.log'
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
				tltl.append(test)

		return render_template('log.html', tltl=tltl)	

@bp.route("update")
def update(file_name = None):
	if not session.get('logFlag'):
		return render_template('login.html')
	else:
		url = "https://github.com/k45734/flask_web/archive/refs/heads/main.zip"
		
		if not file_name:
			file_name = url.split('/')[-1]

		with open(file_name, "wb") as file:   
				response = get(url)               
				file.write(response.content)      
		fantasy_zip = zipfile.ZipFile('./main.zip')
		fantasy_zip.extractall('./')
		fantasy_zip.close()
		os.remove('./flask_web-main/login.db')
		org = './flask_web-main/app.py'
		org2 = './flask_web-main/pages'
		org3 = './flask_web-main/templates'
		org4 = './flask_web-main/version.txt'
		new = './'
		new2 = './pages'
		new3 = './templates'
		shutil.copy(org, new)
		copy_tree(org2, new2)
		copy_tree(org3, new3)
		shutil.copy(org4, new)
		os.remove('./main.zip')
		shutil.rmtree ('./flask_web-main')
		if os.path.exists(org):
			print("파일있다")
			shutil.copy(org, new)
			copy_tree(org2, new2)
			copy_tree(org3, new3)
			shutil.copy(org4, new)
			os.remove('./main.zip')
			shutil.rmtree ('./flask_web-main')
		else:
			print("파일없다")
			if platform.system() == 'Windows':
				os.system("flask run --reload")
			else:
				os.system("cat /dev/null > ./log/flask.log")
				os.system("chmod 777 * -R")
				os.system("kill -9 `ps -ef|grep app.py|awk '{print $1}'`")
		return redirect(url_for('main.index'))
		
@bp.route("restart")
def restart():
	if not session.get('logFlag'):
		return render_template('login.html')
	else:
		if platform.system() == 'Windows':
			os.system("flask run --reload")
		else:
			os.system("cat /dev/null > ./log/flask.log")
			os.system("chmod 777 * -R")
			os.system("kill -9 `ps -ef|grep app.py|awk '{print $1}'`")
		return redirect(url_for('main.index'))