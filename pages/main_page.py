#-*- coding: utf-8 -*-
import sys
try:
	reload(sys)
	sys.setdefaultencoding('utf-8')
except:
	pass

from flask import Flask
from flask import Blueprint
import os
from datetime import datetime, timedelta
import requests
from flask import Flask, flash, redirect, render_template, request, session, abort, url_for
import os.path
from flask_ipblock import IPBlock
from flask_ipblock.documents import IPNetwork
import sqlite3
import time
from flask_sqlalchemy import SQLAlchemy
import psutil
import platform
from requests import get  
import zipfile
import os       
import shutil
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
	#mem = psutil.virtual_memory()
	#mem_total = mem.total
	#mem_percent = mem.percent
	#memswap = psutil.swap_memory()
	#memswap_total = memswap.total
	#memswap_percent = memswap.percent
	#disk1 = psutil.disk_usage(path='/')
	#disk_percent = disk1.percent
	if platform.system() == 'Windows':
		s = os.path.splitdrive(os.getcwd())
		root = s[0]
	else:
		root = '/'
	
	tmp = psutil.virtual_memory()
	tmp2 = psutil.disk_usage(root)
	oos = platform.platform()
	oocpu = platform.processor()
	mem_percent = u'전체 : %s   사용량 : %s   남은량 : %s  (%s%%)' % (sizeof_fmt(tmp[0], suffix='B'), sizeof_fmt(tmp[3], suffix='B'), sizeof_fmt(tmp[1], suffix='B'), tmp[2])
	disk_percent = u'전체 : %s   사용량 : %s   남은량 : %s  (%s%%) - 드라이브 (%s)' % (sizeof_fmt(tmp2[0], suffix='B'), sizeof_fmt(tmp2[1], suffix='B'), sizeof_fmt(tmp2[2], suffix='B'), tmp2[3], root)
	#raspi_dict = {'메모리':mem_percent, '가상메모리':memswap_percent, '디스크':disk_percent}
	return render_template('main.html', test = test, oos = oos, oocpu = oocpu, mem_percent = mem_percent, disk_percent = disk_percent)
	#return render_template('logout.html')
			
@bp.route('login')
def login():
	return render_template('login.html')
	
@bp.route('logout')
def logout():
	session.clear()
	#return redirect(url_for('index'))
	return index()

@bp.route('login_proc', methods=['post'])
def login_proc():
	##폼에서 넘어온 데이터를 가져와 정해진 유저네임과 암호를 비교하고 참이면 세션을 저장한다.
	##회원정보를 DB구축해서 추출하서 비교하는 방법으로 구현 가능 - 여기서는 바로 적어 줌
	#if request.form['password'] == 'test' and request.form['username'] == 'test' :
	#	session['logged_in'] = True #세선 해제는 어떻게?
	#else:
	#	flash('유저네임이나 암호가 맞지 않습니다.')
	#return index()
	#print(request.form['user'])
	userid = request.form['user']
	userpwd = request.form['passwd']
	if len(userid) == 0 or len(userpwd) == 0:
		return redirect(url_for('main.index'))
		#return userid
	else:
		con = sqlite3.connect('./login.db')
		cursor = con.cursor()
		sql = "select idx, id, pwd from member where id = ?"
		cursor.execute(sql, (userid,))
		rows = cursor.fetchall()
		for rs in rows:
			print(rs)
			#print(userid)
			if userid == rs[1] and userpwd == rs[2]:
				session['logFlag'] = True
				session['idx'] = rs[0]
				session['userid'] = userid
				return redirect(url_for('main.index'))
				#return 'eeeeee'
			else:
				print("ttt")
				return redirect(url_for('main.index'))
	return redirect(url_for('main.index'))			
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
	#print(request.form['user'])
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
	if not os.path.isfile(filepath):
		f = open('./log/flask.log','a', encoding='utf-8')
	if not session.get('logFlag'):
		return render_template('login.html')
	else:
		filepath = './log/flask.log'
		with open(filepath, 'rt', encoding='utf-8') as fp:
			line = fp.readline()
			cnt = 1
			tltl = []
			while line:
				test = line.strip()
				line = fp.readline()
				tltl.append(test)
				cnt += 1
			return render_template('log.html', tltl=tltl)	

@bp.route("update")
def update(file_name = None):
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
	new = './'
	new2 = './pages'
	new3 = './templates'
	shutil.copy(org, new)
	copy_tree(org2, new2)
	copy_tree(org3, new3)
	os.remove('./main.zip')
	shutil.rmtree ('./flask_web-main')
	return redirect(url_for('main.index'))