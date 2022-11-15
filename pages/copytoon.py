from flask import Blueprint
#-*- coding: utf-8 -*-
import sys
try:
	reload(sys)
	sys.setdefaultencoding('utf-8')
except:
	pass
from flask import Flask, flash, redirect, render_template, request, session, abort, url_for, Blueprint
import os, io, re, zipfile, shutil, json, time, random, base64, urllib.request, platform, logging, requests, os.path, threading, time, subprocess, datetime
import urllib.request as urllib2

try:
	from bs4 import BeautifulSoup as bs
except ImportError:
	os.system('pip install BeautifulSoup4')
	from bs4 import BeautifulSoup as bs

try:
	import sqlite3
except ImportError:
	os.system('pip install sqlite3')
	import sqlite3


from datetime import datetime, timedelta
from pages.main_page import scheduler
from pages.main_page import logger
from apscheduler.triggers.cron import CronTrigger

#페이지 기능
try:
	from flask_paginate import Pagination, get_page_args
except ImportError:
	os.system('pip install flask_paginate')
	from flask_paginate import Pagination, get_page_args
	
if platform.system() == 'Windows':
	at = os.path.splitdrive(os.getcwd())
	webtoondb = at[0] + '/data/webtoon_new.db'

else:
	webtoondb = '/data/webtoon_new.db'

	
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
webtoon = Blueprint('webtoon', __name__, url_prefix='/webtoon')

def mydate():
	nowDatetime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
	return nowDatetime

#DB최적화
def db_optimization():
	try:
		con = sqlite3.connect(webtoondb,timeout=60)		
		con.execute('VACUUM')
		con.commit()
		logger.info('DB최적화를 진행하였습니다.')
	except:
		con.rollback()	
	finally:	
		con.close()	
	comp = '완료'
	return comp	

	
def cleanText(readData):
	#텍스트에 포함되어 있는 특수 문자 제거
	text = readData.replace('/', '')
	text = re.sub('[-\\/:*?\"<>|]', '', text).strip()
	text = re.sub("\s{2,}", ' ', text)
	return text	
	
def url_to_image(title, subtitle, webtoon_image, webtoon_number):
	header = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.101 Safari/537.36"}
	req = requests.get(webtoon_image,headers=header)	
	title2 = title.strip()
	subtitle2 = subtitle.strip()
	parse = cleanText(title2)
	parse2 = cleanText(subtitle2)
	if platform.system() == 'Windows':
		at = os.path.splitdrive(os.getcwd())
		root = at[0] + '/data'
	else:
		root = '/data'
	packege = 'webtoon'
	filename = webtoon_number + '.jpg'
	dfolder = root + '/' + packege
	fifi = dfolder + '/' + parse + '/' + parse2 + '/' + filename
	#폴더 없으면 만들다
	if not os.path.exists('{}/{}/{}'.format(dfolder,parse,parse2)):
		os.makedirs('{}/{}/{}'.format(dfolder,parse,parse2))
	if not os.path.exists('{}/{}'.format(dfolder,parse)):
		os.makedirs('{}/{}'.format(dfolder,parse))
	if not os.path.exists('{}'.format(dfolder)):
		os.makedirs('{}'.format(dfolder))
	if not os.path.isfile(fifi):
		with open(fifi, 'wb') as code:
			code.write(req.content)
	comp = '완료'
	return comp	
	
def manazip(title, subtitle,cbz):
	title2 = title.strip()
	subtitle2 = subtitle.strip()
	parse = cleanText(title2)
	parse2 = cleanText(subtitle2)
	if platform.system() == 'Windows':
		at = os.path.splitdrive(os.getcwd())
		root = at[0] + '/data'
	else:
		root = '/data'
	packege = 'webtoon'
	dfolder = root + '/' + packege
	if os.path.isdir(dfolder + '/{}/{}'.format(parse,parse2)):
		if cbz == '0':
			fantasy_zip = zipfile.ZipFile(dfolder + '/{}/{}.cbz'.format(parse,parse2), 'w')   
		else:
			fantasy_zip = zipfile.ZipFile(dfolder + '/{}/{}.zip'.format(parse,parse2), 'w')   
		for folder, subfolders, files in os.walk(dfolder + '/{}/{}'.format(parse,parse2)):                     
			for file in files:
				if file.endswith('.jpg'):
					fantasy_zip.write(os.path.join(folder, file), os.path.relpath(os.path.join(folder,file), dfolder + '/{}/{}'.format(parse,parse2)), compress_type = zipfile.ZIP_DEFLATED)                     
		fantasy_zip.close()
	time.sleep(1)
	try:
		shutil.rmtree(dfolder + '/{}/{}'.format(parse,parse2))
	except:
		pass
	comp = '완료'
	return comp	
	
def add_c(title, subtitle,webtoon_site, webtoon_url,webtoon_image,webtoon_number,complete,gbun):
	if gbun == 'adult':
		DB_NAME = 'TOON'
	else:
		DB_NAME = 'TOON_NORMAL'
	try:
		#데이타베이스 없으면 생성
		con = sqlite3.connect(webtoondb,timeout=60)
		sql = 'CREATE TABLE IF NOT EXISTS ' + DB_NAME + ' (TITLE TEXT, SUBTITLE TEXT, WEBTOON_SITE TEXT, WEBTOON_URL TEXT, WEBTOON_IMAGE TEXT, WEBTOON_IMAGE_NUMBER TEXT, COMPLETE TEXT)'
		con.execute(sql)
		con.execute("PRAGMA cache_size = 10000")
		con.execute("PRAGMA locking_mode = NORMAL")
		con.execute("PRAGMA temp_store = MEMORY")
		con.execute("PRAGMA auto_vacuum = 1")
		con.execute("PRAGMA journal_mode=WAL")
		con.execute("PRAGMA synchronous=NORMAL")
		con.close()
		time.sleep(3) 
		con = sqlite3.connect(webtoondb,timeout=60)
		cur = con.cursor()
		sql = "select * from TOON where WEBTOON_IMAGE = ? and TITLE = ? and SUBTITLE = ?"
		cur.execute(sql, (webtoon_image,title, subtitle))
		row = cur.fetchone()
		if row != None:
			pass
		else:
			cur.execute("INSERT OR REPLACE INTO TOON (TITLE, SUBTITLE, WEBTOON_SITE, WEBTOON_URL, WEBTOON_IMAGE, WEBTOON_IMAGE_NUMBER, COMPLETE) VALUES (?, ?, ?, ?, ?, ?, ?)", (title, subtitle,webtoon_site, webtoon_url,webtoon_image,webtoon_number,complete))
			con.commit()
	except:
		con.rollback()
	finally:		
		con.close()
	comp = '완료'
	return comp

def add_d(subtitle, title,webtoon_image,gbun):
	if gbun == 'adult':
		DB_NAME = 'TOON'
	else:
		DB_NAME = 'TOON_NORMAL'
	try:
		#데이타베이스 없으면 생성
		con = sqlite3.connect(webtoondb,timeout=60)
		sql = 'CREATE TABLE IF NOT EXISTS ' + DB_NAME + ' (TITLE TEXT, SUBTITLE TEXT, WEBTOON_SITE TEXT, WEBTOON_URL TEXT, WEBTOON_IMAGE TEXT, WEBTOON_IMAGE_NUMBER TEXT, COMPLETE TEXT)'
		con.execute(sql)
		con.execute("PRAGMA cache_size = 10000")
		con.execute("PRAGMA locking_mode = NORMAL")
		con.execute("PRAGMA temp_store = MEMORY")
		con.execute("PRAGMA auto_vacuum = 1")
		con.execute("PRAGMA journal_mode=WAL")
		con.execute("PRAGMA synchronous=NORMAL")
		con.close()
		time.sleep(3) 
		#마지막 실행까지 작업안했던 결과물 저장
		con = sqlite3.connect(webtoondb,timeout=60)
		cur = con.cursor()
		sql = 'UPDATE ' + DB_NAME + ' SET COMPLETE = ? WHERE SUBTITLE = ? AND TITLE = ? AND WEBTOON_IMAGE = ?'
		cur.execute(sql,('True',subtitle, title,webtoon_image))
		con.commit()
	except:
		con.rollback()
	finally:	
		con.close()	
	comp = '완료'
	return comp	
	
#텔레그램 메시지 암호화 복호화후 DB 저장하기...
def tel_send_message(list):
	if platform.system() == 'Windows':
		at = os.path.splitdrive(os.getcwd())
		root = at[0] + '/data'
	else:
		root = '/data'
	logger.info('웹툰 DB정보를 받아옵니다.')
	file_path = root + '/last_num.json'
	try:
		with open(file_path, "r") as json_file:
			json_data = json.load(json_file)
	except:
		pass
	last_num = []
	with requests.Session() as s:
		url2 = 'https://t.me/s/webtoonalim'
		req = s.get(url2)
		html = req.text
		soup = bs(html, "html.parser")
		aa = soup.find("div",{"class":"tgme_widget_message"})
		aa1 = soup.findAll("div",{"class":"tgme_widget_message"})
		mm = soup.findAll("div",{"class":"tgme_widget_message_text"})
		lastpage1 = aa1[19]['data-post']
		page_num = lastpage1.strip("webtoonalim/")
		last_num.append(page_num)
		#현재페이지의 갯수
		try:
			ll = int(json_data[0])
		except:
			ll = 0	
		total = int(page_num)
		while True:
			if total <= ll:
				break
			else:
				PAGE_INFO = {'before': total }
				logger.info('%s',PAGE_INFO)
				print(PAGE_INFO)
				req = s.post(url2, data=PAGE_INFO)
				html = req.text
				soup = bs(html, "html.parser")
				mm = soup.findAll("div",{"class":"tgme_widget_message_text"})
				for i in mm:
					aa = i.text
					try:
						sitename_bytes = base64.b64decode(aa)
						sitename = sitename_bytes.decode('utf-8')
						aac = sitename.split('\n\n')
						if len(aac) != 6:
							gbun = aac[6]
						else:
							gbun = 'adult'
						title = aac[0]
						subtitle = aac[1]
						webtoon_site = aac[2]
						webtoon_url = aac[3]
						webtoon_image = aac[4]
						webtoon_number = aac[5]
						complete = "False" #처음에 등록할때 무조건 False 로 등록한다.	
						add_c(title, subtitle,webtoon_site, webtoon_url,webtoon_image,webtoon_number,complete,gbun)
						
					except:	
						continue
			total -= 20
	file_path = root + '/last_num.json'
	with open(file_path, 'w') as outfile:
		json.dump(last_num, outfile)		
	logger.info('웹툰 DB정보를 종료합니다.')
	comp = '완료'
	
	return comp

@webtoon.route('db_list_reset', methods=['POST'])	
def db_list_reset():
	if not session.get('logFlag'):
		return redirect(url_for('main.index'))
	else:
		if platform.system() == 'Windows':
			at = os.path.splitdrive(os.getcwd())
			root = at[0] + '/data'
		else:
			root = '/data'
		file_path = root + '/last_num.json'
		try:
			os.remove(file_path)
		except:
			pass
	logger.info('웹툰 리스트를 처음부터 갱신합니다.')
	comp = '완료'
	return comp
	
#다운해보자
def down(compress,cbz,alldown,title, subtitle,gbun):
	if gbun == 'adult':
		DB_NAME = 'TOON'
	else:
		DB_NAME = 'TOON_NORMAL'
	logger.info('웹툰 다운로드합니다.')
	try:
		con = sqlite3.connect(webtoondb,timeout=60)
		con.execute("PRAGMA cache_size = 10000")
		con.execute("PRAGMA locking_mode = NORMAL")
		con.execute("PRAGMA temp_store = MEMORY")
		con.execute("PRAGMA auto_vacuum = 1")
		con.execute("PRAGMA journal_mode=WAL")
		con.execute("PRAGMA synchronous=NORMAL")
		con.row_factory = sqlite3.Row
		cur2 = con.cursor()
		if alldown == 'True':
			sql2 = 'select TITLE,SUBTITLE, group_concat(WEBTOON_IMAGE),group_concat(WEBTOON_IMAGE_NUMBER),group_concat(COMPLETE) from ' + DB_NAME + ' group by TITLE,SUBTITLE'
		else:
			sql2 = 'select TITLE,SUBTITLE, group_concat(WEBTOON_IMAGE),group_concat(WEBTOON_IMAGE_NUMBER),group_concat(COMPLETE) from ' + DB_NAME + ' WHERE TITLE="' + title  + '" and SUBTITLE="' + subtitle + '" group by SUBTITLE'
		print(sql2)
		cur2.execute(sql2)
		itrows = cur2.fetchall()
		for i in itrows:
			title = i['TITLE']
			subtitle = i['SUBTITLE']
			webtoon_image = i[2]
			webtoon_image_number = i[3]
			complete = i[4]
			image_url_last = webtoon_image.split(',')
			image_number_last = webtoon_image_number.split(',')
			complete_last = complete.split(',')
			cnt = complete_last.count('False')
			if cnt >= 1:
				for ii,iii in zip(image_url_last,image_number_last):
					print(title, subtitle, ii,iii)
					url_to_image(title, subtitle,ii,iii)	
					add_d(subtitle, title,ii)
				if compress == '0':
					print('다운완료후 압축하자')
					manazip(title, subtitle,cbz)
					
				else:
					pass
			else:
				print('다운완료되었다')
		con.close()	
	except:
		logger.info('정보가없습니다.')
	logger.info('웹툰 다운로드를 종료합니다.')	
@webtoon.route('/')
@webtoon.route('index')
def index():
	if not session.get('logFlag'):
		return redirect(url_for('main.index'))
	else:
		#데이타베이스 없으면 생성
		con = sqlite3.connect(webtoondb,timeout=60)
		sql = "CREATE TABLE IF NOT EXISTS TOON (TITLE TEXT, SUBTITLE TEXT, WEBTOON_SITE TEXT, WEBTOON_URL TEXT, WEBTOON_IMAGE TEXT, WEBTOON_IMAGE_NUMBER TEXT, COMPLETE TEXT)"
		con.execute(sql)
		con.execute("PRAGMA cache_size = 10000")
		con.execute("PRAGMA locking_mode = NORMAL")
		con.execute("PRAGMA temp_store = MEMORY")
		con.execute("PRAGMA auto_vacuum = 1")
		con.execute("PRAGMA journal_mode=WAL")
		con.execute("PRAGMA synchronous=NORMAL")
		con.close()
		con = sqlite3.connect(webtoondb,timeout=60)
		sql = "CREATE TABLE IF NOT EXISTS TOON_NORMAL (TITLE TEXT, SUBTITLE TEXT, WEBTOON_SITE TEXT, WEBTOON_URL TEXT, WEBTOON_IMAGE TEXT, WEBTOON_IMAGE_NUMBER TEXT, COMPLETE TEXT)"
		con.execute(sql)
		con.execute("PRAGMA cache_size = 10000")
		con.execute("PRAGMA locking_mode = NORMAL")
		con.execute("PRAGMA temp_store = MEMORY")
		con.execute("PRAGMA auto_vacuum = 1")
		con.execute("PRAGMA journal_mode=WAL")
		con.execute("PRAGMA synchronous=NORMAL")
		con.close()
		time.sleep(3)
		rows = []
		rows2 = []
		con = sqlite3.connect(webtoondb,timeout=60)
		con.execute("PRAGMA cache_size = 10000")
		con.execute("PRAGMA locking_mode = NORMAL")
		con.execute("PRAGMA temp_store = MEMORY")
		con.execute("PRAGMA auto_vacuum = 1")
		con.execute("PRAGMA journal_mode=WAL")
		con.execute("PRAGMA synchronous=NORMAL")
		con.row_factory = sqlite3.Row
		cur = con.cursor()
		#성인웹툰
		cur.execute('select group_concat(TITLE),group_concat(SUBTITLE), group_concat(WEBTOON_IMAGE),group_concat(WEBTOON_IMAGE_NUMBER),group_concat(COMPLETE) from TOON group by TITLE')
		TOTAL = cur.fetchall()
		cur.execute('select * from TOON WHERE COMPLETE = "False"')
		false_toon = cur.fetchall()
		cur.execute('select * from TOON WHERE COMPLETE = "True"')
		true_toon = cur.fetchall()
		keys = ['TOTAL','False','True']
		values = [len(TOTAL), len(false_toon), len(true_toon)]
		dt = dict(zip(keys, values))
		rows.append(dt)
		#일반웹툰
		cur.execute('select group_concat(TITLE),group_concat(SUBTITLE), group_concat(WEBTOON_IMAGE),group_concat(WEBTOON_IMAGE_NUMBER),group_concat(COMPLETE) from TOON_NORMAL group by TITLE')
		TOTAL = cur.fetchall()
		cur.execute('select * from TOON_NORMAL WHERE COMPLETE = "False"')
		false_toon_normal = cur.fetchall()
		cur.execute('select * from TOON_NORMAL WHERE COMPLETE = "True"')
		true_toon_normal = cur.fetchall()
		keys = ['TOTAL','False','True']
		values = [len(TOTAL), len(false_toon_normal), len(true_toon_normal)]
		dt = dict(zip(keys, values))
		rows2.append(dt)
		return render_template('webtoon.html', rows = rows, rows2 = rows2)	

@webtoon.route('index_list/<gbun>', methods=["GET","POST"])
def index_list(gbun):
	print(gbun)
	if not session.get('logFlag'):
		return redirect(url_for('main.index'))
	else:
		#gbun = request.args.get('gbun')
		#print(len(gbun), gbun)
		if gbun == 'adult':
			DB_NAME = 'TOON'
		else:
			DB_NAME = 'TOON_NORMAL'
		per_page = 10
		page, _, offset = get_page_args(per_page=per_page)
		con = sqlite3.connect(webtoondb,timeout=60)
		con.execute("PRAGMA cache_size = 10000")
		con.execute("PRAGMA locking_mode = NORMAL")
		con.execute("PRAGMA temp_store = MEMORY")
		con.execute("PRAGMA auto_vacuum = 1")
		con.execute("PRAGMA journal_mode=WAL")
		con.execute("PRAGMA synchronous=NORMAL")
		con.row_factory = sqlite3.Row
		cur = con.cursor()
		cur.execute('select TITLE,SUBTITLE from ' + DB_NAME + ' group by TITLE,SUBTITLE')
		total2 = cur.fetchall()
		total = len(total2)
		cur.execute('select TITLE,SUBTITLE from ' + DB_NAME + ' group by TITLE,SUBTITLE ORDER BY TITLE,SUBTITLE DESC LIMIT ' + str(per_page) + ' OFFSET ' + str(offset))
		wow = cur.fetchall()		
		return render_template('webtoon_list.html', gbun = gbun, wow = wow, pagination=Pagination(page=page, total=total, per_page=per_page))

@webtoon.route('db_redown', methods=['POST'])
def db_redown():
	if not session.get('logFlag'):
		return redirect(url_for('main.index'))
	else:
		gbun = request.form['gbun']
		if gbun == 'adult':
			DB_NAME = 'TOON'
		else:
			DB_NAME = 'TOON_NORMAL'
		try:
			con = sqlite3.connect(webtoondb,timeout=60)
			cur = con.cursor()
			sql = 'UPDATE ' + DB_NAME + ' SET COMPLETE = ?'
			cur.execute(sql,('False',))
			con.commit()
		except:
			con.rollback()
		finally:		
			con.close()
		return redirect(url_for('main.index'))
	comp = '완료'
	return comp

@webtoon.route("now", methods=["POST"])
def now():
	if not session.get('logFlag'):
		return redirect(url_for('main.index'))
	else:
		gbun = request.form['gbun']
		alldown = 'True'
		title = None
		subtitle = None
		compress = request.form['compress']
		cbz = request.form['cbz']
		down(compress,cbz,alldown,title, subtitle,gbun)
	return redirect(url_for('webtoon.index'))

@webtoon.route("index_list/<gbun>/one_now", methods=["GET"])
def one_now(gbun):
	if not session.get('logFlag'):
		return redirect(url_for('main.index'))
	else:
		alldown = 'False'
		gbun = request.args.get('gbun')
		title = request.args.get('title')
		subtitle = request.args.get('subtitle')
		compress = request.args.get('compress')
		cbz = request.args.get('cbz')
		down(compress,cbz,alldown,title, subtitle,gbun)
		print(compress,cbz,alldown,title, subtitle,gbun)
	return redirect(url_for('webtoon.index'))
	
@webtoon.route('webtoon_list', methods=['POST'])
def dozi_list():
	if session.get('logFlag') != True:
		return redirect(url_for('main.index'))
	else:
		list = '웹툰DB'
		start_time = request.form['start_time']
		try:
			scheduler.add_job(tel_send_message, trigger=CronTrigger.from_crontab(start_time), id='webtoon_list', args=[list])
			test = scheduler.get_job('webtoon_list').id
			logger.info('%s 스케줄러에 등록하였습니다.', test)
		except ConflictingIdError:
			test = scheduler.get_job('webtoon_list').id
			test2 = scheduler.modify_job('webtoon_list').id
			logger.info('%s가 %s 스케줄러로 수정되었습니다.', test,test2)
		return redirect(url_for('webtoon.index'))
	
@webtoon.route('webtoon_down', methods=['POST'])
def dozi_down():
	if session.get('logFlag') != True:
		return redirect(url_for('main.index'))
	else:
		gbun = request.form['gbun']
		alldown = 'True'
		title = None
		subtitle = None
		compress = request.form['compress']
		cbz = request.form['cbz']
		startname = request.form['startname']
		start_time = request.form['start_time']
		try:
			scheduler.add_job(down, trigger=CronTrigger.from_crontab(start_time), id=startname, args=[compress,cbz,alldown,title, subtitle,gbun] )
			test = scheduler.get_job(startname).id
			logger.info('%s 스케줄러에 등록하였습니다.', test)
		except ConflictingIdError:
			test = scheduler.get_job(startname).id
			test2 = scheduler.modify_job(startname).id
			logger.info('%s가 %s 스케줄러로 수정되었습니다.', test,test2)
		return redirect(url_for('webtoon.index'))
