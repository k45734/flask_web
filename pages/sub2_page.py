#-*- coding: utf-8 -*-
import sys
try:
	reload(sys)
	sys.setdefaultencoding('utf-8')
except:
	pass
from flask import Flask, flash, redirect, render_template, request, session, abort, url_for, Blueprint
import os.path, json, os, re, time, logging, io, subprocess, platform, telegram, threading, sqlite3, random,urllib.request, asyncio
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

from pages.main_page import scheduler
from pages.main_page import logger
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.base import JobLookupError, ConflictingIdError
from apscheduler.triggers.cron import CronTrigger
from apscheduler.executors.pool import ThreadPoolExecutor, ProcessPoolExecutor
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
#페이지 기능
try:
	from flask_paginate import Pagination, get_page_args
except ImportError:
	os.system('pip install flask_paginate')
	from flask_paginate import Pagination, get_page_args
#RSS 모듈
try:
	import feedparser
except ImportError:
	os.system('pip install feedparser')
	import feedparser
from html import unescape	
if platform.system() == 'Windows':
	at = os.path.splitdrive(os.getcwd())
	sub2db = at[0] + '/data/db'
else:
	sub2db = '/data/db'

connect_timeout = 10
read_timeout = 10
bp2 = Blueprint('sub2', __name__, url_prefix='/sub2')
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

py_ver = int(f"{sys.version_info.major}{sys.version_info.minor}")
if py_ver > 37 and sys.platform.startswith('win'):
	asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
#텔레그램 에러 오류 해결??
#os.system('pip install urllib3==1.24.1')

def mydate():
	nowtime = time.localtime()
	mytime = "%04d-%02d-%02d" % (nowtime.tm_year, nowtime.tm_mon, nowtime.tm_mday)
	return mytime
	
def mytime():
	nowtime = time.localtime()
	mytime = "%02d" % (nowtime.tm_hour)
	return mytime	

def remove_html(sentence) :
	sentence = re.sub('(<([^>]+)>)', '', sentence)
	return sentence

def symbol_re(text):	
	sy_re = text.replace("&amp;", ' &')
	sy_re = text.replace("&quot;", ' "')
	return sy_re
	
@bp2.route('/')
@bp2.route('index')
def index():
	if not session.get('logFlag'):
		return redirect(url_for('main.index'))
	else:
		tltl = []
		test2 = scheduler.get_jobs()
		for i in test2:
			aa = i.id
			tltl.append(aa)
		return render_template('sub2_index.html', tltl = tltl)

def url_to_image(url, dfolder, category, category2, filename):
	list_url = url.split()
	for l in list_url:
		header = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36"}
		with requests.Session() as s:
			try:
				req = s.get(l,headers=header)
			except:
				continue
			fifi = dfolder + '/' + category + '/' + category2 + '/' + filename
			print(fifi)
			if not os.path.exists('{}'.format(dfolder)):
				os.makedirs('{}'.format(dfolder))
			if not os.path.exists('{}/{}'.format(dfolder,category)):
				os.makedirs('{}/{}'.format(dfolder,category))
			if not os.path.exists('{}/{}/{}'.format(dfolder,category,category2)):
				os.makedirs('{}/{}/{}'.format(dfolder,category,category2))
			with open(fifi, 'wb') as code:
				code.write(req.content)
		break
		
	comp = '완료'
	return comp
	
def url_to_image2(url, dfolder, filename):
	header = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.101 Safari/537.36"}
	req = requests.get(url,headers=header)
	category = 'weather'
	fifi = dfolder + '/' + category + '/' + filename
	if not os.path.exists('{}'.format(dfolder)):
		os.makedirs('{}'.format(dfolder))
	if not os.path.exists('{}/{}'.format(dfolder,category)):
		os.makedirs('{}/{}'.format(dfolder,category))
	with open(fifi, 'wb') as code:
		code.write(req.content)
	comp = '완료'
	return comp	

#텔레그램 특정시간 조용하게
def tel_mute(start_time2,end_time,telgm_botid,text,bot,telgm_alim):
	alim_start_end = []
	alim_start_end2 = []
	mynow = mytime()
	time_start = start_time2.zfill(2)
	time_end = end_time.zfill(2)
	
	if int(time_start) == int(time_end):
		print('시작시간과 종료시간 같음')
		logger.info('시작시간과 종료시간 같음')
		if telgm_alim == 'True':
			asyncio.run(bot.send_message(chat_id = telgm_botid, text=text, disable_notification=True))
		else:
			asyncio.run(bot.send_message(chat_id = telgm_botid, text=text, disable_notification=False))
	
	else:
		for i in range(0 , int(time_end)+1):
			a = str(i).zfill(2)
			alim_start_end.append(a)
			
		for i in range(int(time_start) , 25):
			a = str(i).zfill(2)
			alim_start_end2.append(a)
		
		list = alim_start_end + alim_start_end2
		if mynow not in list:
			if telgm_alim == 'True':
				asyncio.run(bot.send_message(chat_id = telgm_botid, text=text, disable_notification=True))
				logger.info('일반알림 무음')
			else:
				asyncio.run(bot.send_message(chat_id = telgm_botid, text=text, disable_notification=False))
				logger.info('일반알림 시끄럽게')
			
		#미포함
		else:
			if telgm_alim == 'True':
				asyncio.run(bot.send_message(chat_id = telgm_botid, text=text, disable_notification=True))
				print('무음')
				logger.info('일반알림 무음')
			else:
				asyncio.run(bot.send_message(chat_id = telgm_botid, text=text, disable_notification=False))
				logger.info('일반알림 시끄럽게')

#텔레그램 특정시간 조용하게
def tel_mute2(start_time2,end_time,telgm_botid,text,bot,telgm_alim):
	alim_start_end = []
	alim_start_end2 = []
	mynow = mytime()
	time_start = start_time2.zfill(2)
	time_end = end_time.zfill(2)
	
	if int(time_start) == int(time_end):
		print('시작시간과 종료시간 같음')
		logger.info('시작시간과 종료시간 같음')
		if telgm_alim == 'True':
			asyncio.run(bot.send_photo(chat_id = telgm_botid, photo=open(text,'rb'), disable_notification=True))
		else:
			asyncio.run(bot.send_photo(chat_id = telgm_botid, photo=open(text,'rb'), disable_notification=False))
	
	else:
		for i in range(0 , int(time_end)+1):
			a = str(i).zfill(2)
			alim_start_end.append(a)
			
		for i in range(int(time_start) , 25):
			a = str(i).zfill(2)
			alim_start_end2.append(a)
		
		list = alim_start_end + alim_start_end2
		if mynow not in list:
			if telgm_alim == 'True':
				asyncio.run(bot.send_photo(chat_id = telgm_botid, photo=open(text,'rb'), disable_notification=True))
				print('무음')
				logger.info('포토알림 무음')
			else:
				asyncio.run(bot.send_photo(chat_id = telgm_botid, photo=open(text,'rb'), disable_notification=False))
				print('시끄럽게')
				logger.info('포토알림 시끄럽게')
			
		#미포함
		else:
			if telgm_alim == 'True':
				asyncio.run(bot.send_photo(chat_id = telgm_botid, photo=open(text,'rb'), disable_notification=True))
				print('무음')
				logger.info('포토알림 무음')
			else:
				asyncio.run(bot.send_photo(chat_id = telgm_botid, photo=open(text,'rb'), disable_notification=False))
				print('시끄럽게')
				logger.info('포토알림 시끄럽게')
#텔레그램 알림
def tel(telgm,telgm_alim,telgm_token,telgm_botid,text,start_time2,end_time):	
	if len(text) <= 4096:
		if telgm == 'True' :
			bot = telegram.Bot(token = telgm_token)
			if telgm_alim == 'True':
				try:
					tel_mute(start_time2,end_time,telgm_botid,text,bot,telgm_alim)
				except Exception as e:
					logger.error(e)
					time.sleep(30)
					tel_mute(start_time2,end_time,telgm_botid,text,bot,telgm_alim)
			else:
				try:
					tel_mute(start_time2,end_time,telgm_botid,text,bot,telgm_alim)
				except Exception as e:
					logger.error(e)
					time.sleep(30)
					tel_mute(start_time2,end_time,telgm_botid,text,bot,telgm_alim)
		else:
			print(text)
		#time.sleep(10)	
	else:
		parts = []
		while len(text) > 0:
			if len(text) > 4080: # '(Continuing...)\n'이 16자임을 고려하여 4096-16=4080을 했습니다.
				part = text[:4080]
				first_lnbr = part.rfind('\n')
				if first_lnbr != -1: # 가능하면 개행문자를 기준으로 자릅니다.
					parts.append(part[:first_lnbr])
					text = text[(first_lnbr+1):]
				else:
					parts.append(part)
					text = text[4080:]
			else:
				parts.append(text)
				break
		for idx, part in enumerate(parts):
			if idx == 0:
				if telgm == 'True' :
					bot = telegram.Bot(token = telgm_token)
					if telgm_alim == 'True':
						try:
							tel_mute(start_time2,end_time,telgm_botid,part,bot,telgm_alim)
						except Exception as e:
							logger.error(e)
							time.sleep(30)
							tel_mute(start_time2,end_time,telgm_botid,part,bot,telgm_alim) 
					else :
						try:
							tel_mute(start_time2,end_time,telgm_botid,part,bot,telgm_alim)
						except Exception as e:
							logger.error(e)
							time.sleep(30)
							tel_mute(start_time2,end_time,telgm_botid,part,bot,telgm_alim)
					print(part)
				else:
					print(part)
			else: # 두번째 메시지부터 '(Continuing...)\n'을 앞에 붙여줍니다.
				if telgm == 'True' :
					bot = telegram.Bot(token = telgm_token)
					if telgm_alim == 'True':
						try:
							tel_mute(start_time2,end_time,telgm_botid,part,bot,telgm_alim)
						except Exception as e:
							logger.error(e)
							time.sleep(30)
							tel_mute(start_time2,end_time,telgm_botid,part,bot,telgm_alim)
					else :
						try:
							tel_mute(start_time2,end_time,telgm_botid,part,bot,telgm_alim)
						except Exception as e:
							logger.error(e)
							time.sleep(30)
							tel_mute(start_time2,end_time,telgm_botid,part,bot,telgm_alim)
					print(part)
				else:
					print(part)
			#time.sleep(10)
			time.sleep(0.5)
	comp = '완료'
	return comp

#텔레그램 알림
def tel_img(telgm,telgm_alim,telgm_token,telgm_botid,msg,start_time2,end_time):
	if telgm == 'True' :
		bot = telegram.Bot(token = telgm_token)
		if telgm_alim == 'True':
			try:
				tel_mute2(start_time2,end_time,telgm_botid,msg,bot,telgm_alim)
			except Exception as e:
				logger.error(e)
				time.sleep(30)
				tel_mute2(start_time2,end_time,telgm_botid,msg,bot,telgm_alim)
		else:
			try:
				tel_mute2(start_time2,end_time,telgm_botid,msg,bot,telgm_alim)
			except Exception as e:
				logger.error(e)
				time.sleep(30)
				tel_mute2(start_time2,end_time,telgm_botid,msg,bot,telgm_alim)
	else:
		print(msg)	
	comp = '완료'
	return comp	
	
def cleanText(readData):
	#텍스트에 포함되어 있는 특수 문자 제거
	text = re.sub('[-=+,#/\?:^$.@*\"※~&%ㆍ!』\\‘|\(\)\[\]\<\>`\'…》]', '', readData)
	return text				

@bp2.route('sch_del', methods=['POST'])
def sch_del():
	if not session.get('logFlag'):
		return redirect(url_for('main.index'))
	else:
		startname = request.form['startname']
		try:
			test = scheduler.get_job(startname).id
			logger.info('%s가 스케줄러에 있습니다.', test)
		except Exception as e:
			logger.error(e)
			test = None
		if test == None:
			logger.info('%s의 스케줄러가 종료가 되지 않았습니다.', startname)
		else:
			#remove_job
			scheduler.remove_job(startname)
			logger.info('%s 스케줄러를 삭제하였습니다.', test)
			test2 = scheduler.get_jobs()
			for i in test2:
				aa = i.id
				logger.info('%s 가 스케줄러가 있습니다.', aa)
		return redirect(url_for('main.index'))
	
#택배조회서비스
#알리미 완료
def tracking_del_new(carrier_id, track_id):
	#마지막 실행까지 작업안했던 결과물 저장
	con = sqlite3.connect(sub2db + '/delivery.db',timeout=60)
	con.execute("PRAGMA cache_size = 10000")
	con.execute("PRAGMA locking_mode = NORMAL")
	con.execute("PRAGMA temp_store = MEMORY")
	con.execute("PRAGMA auto_vacuum = 1")
	con.execute("PRAGMA synchronous=NORMAL")	
	cur = con.cursor()
	sql = "select * from tracking where NUMBER = ? and PARCEL = ?"
	cur.execute(sql, (track_id,carrier_id))
	row = cur.fetchone()
	if row == None:
		pass
	else:
		sql = "UPDATE tracking SET COMPLTE = ? WHERE NUMBER = ? and PARCEL = ?"	
		cur.execute(sql,('True', track_id, carrier_id))
		con.commit()			
		con.close()
	comp = '완료'
	return comp	
#서버에서 조회를 하여 메모리에 저장
def flfl(json_string_m):
	test = []
	for list in json_string_m:
		try:
			a = list.get("time")
			at = a[0:16]
			new_s = at.replace('T',' ')
			b = list.get("location").get('name')
			c = list.get("status").get('text')
			d = list.get("description")
			msg = {'시간':new_s,'상품위치':b,'현재상태':c, '상품상태':d.replace('\n\t\t\t\t\t\t\t\t\t\t', '')}
			test.append(msg)				
		except:
			pass
	return test
	
#저장된 정보를 출력하여 나열하여 메모리에 저장한뒤 출력한다.
def ff(msg2):
	msg = []
	for i in range(len(msg2)):
		a = msg2[i]['시간']
		b = msg2[i]['상태']
		c = msg2[i]['상세내용']
		total = '{} {} {}'.format(a,b,c)
		msg.append(total)
	return msg
#택배조회 확인
def track_url(url):
	response = requests.get(url)
	check = response.status_code
	if check != 500:
		print('ok %s' % url)
		return 9999
	else:
		print('no %s' % url)
		pass
	#try:
	#	request=urllib.request.Request(url,None) #The assembled request
	#	response = urllib.request.urlopen(request,timeout=3)		
	#except:
	#	print('The server couldn\'t fulfill the request. %s'% url)     
	#else:
	#	data = response.read()
	#	data = data.decode()     
	#	result = 0
	#	result = data.find('id')
	#	if result > 0:
	#		print ("Website is working fine %s "% url)
	#		return 9999
	#	return response.status
		
#택배구동
def tracking_pro(telgm,telgm_alim,telgm_token,telgm_botid,carrier_id,track_id,start_time2,end_time,box):
	url = []
	code = { "DHL":"de.dhl",
			"Sagawa":"jp.sagawa",
			"Kuroneko Yamato":"jp.yamato",
			"Japan Post":"jp.yuubin",
			"천일택배":"kr.chunilps",
			"CJ대한통운":"kr.cjlogistics",
			"CU 편의점택배":"kr.cupost",
			"GS Postbox 택배":"kr.cvsnet",
			"CWAY (Woori Express)":"kr.cway",
			"대신택배":"kr.daesin",
			"우체국 택배":"kr.epost",
			"우체국택배":"kr.epost",
			"한의사랑택배":"kr.hanips",
			"한진택배":"kr.hanjin",
			"합동택배":"kr.hdexp",
			"홈픽":"kr.homepick",
			"한서호남택배":"kr.honamlogis",
			"일양로지스":"kr.ilyanglogis",
			"경동택배":"kr.kdexp",
			"건영택배":"kr.kunyoung",
			"로젠택배":"kr.logen",
			"롯데택배":"kr.lotte",
			"SLX":"kr.slx",
			"성원글로벌카고":"kr.swgexp",
			"TNT":"nl.tnt",
			"EMS":"un.upu.ems",
			"Fedex":"us.fedex",
			"UPS":"us.ups",
			"USPS":"us.usps",
			"Cainiao": "cn.cainiao.global",
			"LTL":"kr.ltl",
			"롯데국제택배":"kr.lotte.global",
			"LX 판토스":"kr.epantos",
			"오늘의픽업":"kr.todaypickup",
			"우체국EMS":"kr.epost.ems"
			}
	carrier = code[f'{carrier_id}']
	logger.info(carrier)
	logger.info(carrier_id)
	url2 = "http://0.0.0.0:4000/graphql"
	keys = ['url','carrier','track_id','carrier_id','box']
	values = [url2,carrier,track_id,carrier_id,box]
	dt = dict(zip(keys, values))
	url.append(dt)
	
	with requests.Session() as s:
		for a in url:
			main_url = a['url']
			carrier = a['carrier']
			track_id = a['track_id']
			carrier_id = a['carrier_id']
			box = a['box']
			LOGIN_INFO = {"query": "query Track($carrierId: ID!,$trackingNumber: String!) {track(carrierId: $carrierId,trackingNumber: $trackingNumber) {lastEvent {time status {code name} description}events(last: 10) {edges {node {time status {code name} description}}}}}",
						"variables": {"carrierId": carrier,
									"trackingNumber": track_id
									},
						}
			headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.61 Safari/537.36',
						'Authorization': 'Bearer $YOUR_ACCESS_TOKEN',
						'Content-Type': 'application/json'}
			data = json.dumps(LOGIN_INFO)
			test = json.loads(data)
			try:
				url_s = s.post(main_url, data=data,headers=headers, timeout=(connect_timeout, read_timeout))
			except:	
				msg = '{} {} {} 택배 서버 접속 오류\n'.format(carrier_id,track_id,box)
				tel(telgm,telgm_alim,telgm_token,telgm_botid,msg,start_time2,end_time)
				continue
			resp = url_s.json()
			#print(resp)
			try:
				check = resp.get('data').get('track')
			except:
				check_list = resp.get('errors')
				for ii in check_list:
					check = ii.get('message')
			if check == None or 'Invalid or expired token' in check or 'Internal error' in check:
				msg = '{} {} {} 송장번호가 없는거 같습니다.\n'.format(carrier_id,track_id,box)
				tel(telgm,telgm_alim,telgm_token,telgm_botid,msg,start_time2,end_time)
			else:
				in_data = resp.get('data').get('track').get('events').get('edges')
				last_data = []
				for ii in in_data:
					json_string = ii.get('node').get('time') #시간
					if json_string == None:
						at = json_string
						new_s = at
					else:
						at = json_string[0:16]
						new_s = at.replace('T',' ')
					json_string2 = ii.get('node').get('status').get('name') #배송진행상태
					json_string3 = ii.get('node').get('description') #상세배송진행상태
					msg = {'시간':new_s, '상태':json_string2, '상세내용':json_string3}
					last_data.append(msg)
				gg = ff(last_data)
				ms = '\n'.join(gg)
				print(carrier_id,track_id,box)
				msga = '================================\n택배사 : {} {}\n물품명 : {}\n{}\n================================'.format(carrier_id,track_id,box,ms)
				print(msga)
				if '배송완료' in msga :
					tracking_del_new(carrier_id,track_id)
				elif '배달 완료' in msga :
					tracking_del_new(carrier_id,track_id)
				elif '배달완료' in msga :
					tracking_del_new(carrier_id,track_id)
				elif 'Delivered'in msga :
					tracking_del_new(carrier_id,track_id)
				else:
					pass
				#print(msga)
				tel(telgm,telgm_alim,telgm_token,telgm_botid,msga,start_time2,end_time)
		logger.info('택배 알림완료')
	
#택배조회 구동	
def tracking_start(telgm,telgm_alim,telgm_token,telgm_botid,start_time2,end_time):
	logger.info('택배알림시작')
	#SQLITE3 DB 없으면 만들다.
	con = sqlite3.connect(sub2db + '/delivery.db',timeout=60)
	con.execute('CREATE TABLE IF NOT EXISTS tracking (PARCEL TEXT, NUMBER TEXT, DATE TEXT, BOX TEXT,COMPLTE TEXT)')
	con.execute("PRAGMA cache_size = 10000")
	con.execute("PRAGMA locking_mode = NORMAL")
	con.execute("PRAGMA temp_store = MEMORY")
	con.execute("PRAGMA auto_vacuum = 1")
	con.execute("PRAGMA journal_mode=WAL")
	con.execute("PRAGMA synchronous=NORMAL")
	con.close()
	#데이터베이스 컬럼 추가하기
	conn = sqlite3.connect(sub2db + '/delivery.db',timeout=60)
	cur = conn.cursor()
	sql = "SELECT sql FROM sqlite_master WHERE name='tracking' AND sql LIKE '%DATE%'"
	cur.execute(sql)
	rows = cur.fetchall()
	if len(rows) == 0:
		sql = "alter table tracking add column DATE TEXT"
		cur.execute(sql)
	else:
		pass
	sql = "SELECT sql FROM sqlite_master WHERE name='tracking' AND sql LIKE '%PARCEL%'"
	cur.execute(sql)
	rows = cur.fetchall()
	if len(rows) == 0:
		sql = "alter table tracking add column PARCEL TEXT"
		cur.execute(sql)
	else:
		pass
	sql = "SELECT sql FROM sqlite_master WHERE name='tracking' AND sql LIKE '%COMPLTE%'"
	cur.execute(sql)
	rows = cur.fetchall()
	if len(rows) == 0:
		sql = "alter table tracking add column COMPLTE TEXT"
		cur.execute(sql)
	elif len(rows) == 1:
		sql = "update tracking set COMPLTE = 'False' where COMPLTE is null"
		cur.execute(sql)
	else:
		pass
	conn.commit()
	conn.close()
	#알림
	con = sqlite3.connect(sub2db + '/delivery.db',timeout=60)
	con.row_factory = sqlite3.Row
	cur = con.cursor()
	sql = "select * from tracking where COMPLTE = ?"
	cur.execute(sql, ('False',))
	rows = cur.fetchall()
	if len(rows) != 0 :
		for row in rows:
			carrier_id = row['PARCEL']
			track_id = row['NUMBER']
			box = row['box']
			print(carrier_id,track_id)
			comp = tracking_pro(telgm,telgm_alim,telgm_token,telgm_botid,carrier_id,track_id,start_time2,end_time,box)
	else:
		comp = '정보없음'
	logger.info('택배알림완료')
	return comp
	
@bp2.route('tracking')
def tracking():
	#데이타베이스 없으면 생성
	con = sqlite3.connect(sub2db + '/telegram.db',timeout=60)
	con.execute('CREATE TABLE IF NOT EXISTS tracking (telgm_token TEXT, telgm_botid TEXT, start_time TEXT, telgm TEXT, telgm_alim TEXT)')
	con.execute("PRAGMA cache_size = 10000")
	con.execute("PRAGMA locking_mode = NORMAL")
	con.execute("PRAGMA temp_store = MEMORY")
	con.execute("PRAGMA auto_vacuum = 1")
	con.execute("PRAGMA journal_mode=WAL")
	con.execute("PRAGMA synchronous=NORMAL")
	con.close()
	#SQLITE3 DB 없으면 만들다.
	con = sqlite3.connect(sub2db + '/delivery.db',timeout=60)
	con.execute('CREATE TABLE IF NOT EXISTS tracking (PARCEL TEXT, NUMBER TEXT, DATE TEXT, BOX TEXT,COMPLTE TEXT)')
	con.execute("PRAGMA cache_size = 10000")
	con.execute("PRAGMA locking_mode = NORMAL")
	con.execute("PRAGMA temp_store = MEMORY")
	con.execute("PRAGMA auto_vacuum = 1")
	con.execute("PRAGMA journal_mode=WAL")
	con.execute("PRAGMA synchronous=NORMAL")	
	con.close()
	#데이터베이스 컬럼 추가하기
	con = sqlite3.connect(sub2db + '/telegram.db',timeout=60)
	con.row_factory = sqlite3.Row
	cur = con.cursor()
	sql = "SELECT sql FROM sqlite_master WHERE name='tracking' AND sql LIKE '%start_time2%'"
	cur.execute(sql)
	rows = cur.fetchall()
	if len(rows) == 0:
		sql = "alter table tracking add column start_time2 TEXT"
		cur.execute(sql)
	else:
		pass
	con.close()
	con = sqlite3.connect(sub2db + '/telegram.db',timeout=60)
	con.row_factory = sqlite3.Row
	cur = con.cursor()
	sql = "SELECT sql FROM sqlite_master WHERE name='tracking' AND sql LIKE '%end_time%'"
	cur.execute(sql)
	rows = cur.fetchall()
	if len(rows) == 0:
		sql = "alter table tracking add column end_time TEXT"
		cur.execute(sql)
	else:
		pass
	con.close()
	con = sqlite3.connect(sub2db + '/delivery.db',timeout=60)
	cur = con.cursor()
	sql = "SELECT sql FROM sqlite_master WHERE name='tracking' AND sql LIKE '%BOX%'"
	cur.execute(sql)
	rows = cur.fetchall()
	if len(rows) == 0:
		sql = "alter table tracking add column BOX TEXT"
		cur.execute(sql)
	else:
		pass
	con.close()
	if not session.get('logFlag'):
		return redirect(url_for('main.index'))
	else:
		telgm_token = request.args.get('telgm_token')
		telgm_botid = request.args.get('telgm_botid')
		con = sqlite3.connect(sub2db + '/telegram.db',timeout=60)
		con.execute("PRAGMA cache_size = 10000")
		con.execute("PRAGMA locking_mode = NORMAL")
		con.execute("PRAGMA temp_store = MEMORY")
		con.execute("PRAGMA auto_vacuum = 1")
		con.execute("PRAGMA journal_mode=WAL")
		con.execute("PRAGMA synchronous=NORMAL")
		con.row_factory = sqlite3.Row
		cur = con.cursor()
		cur.execute("select * from tracking")
		rows = cur.fetchone()
		if rows:
			telgm_token = rows['telgm_token']
			telgm_botid = rows['telgm_botid']
			start_time = rows['start_time']
			telgm = rows['telgm']
			telgm_alim = rows['telgm_alim']
			start_time2 = rows['start_time2']
			end_time = rows['end_time']
		else:
			telgm_token='입력하세요'
			telgm_botid='입력하세요'
			start_time = '*/1 * * * *'
			telgm = 'False'
			telgm_alim = 'False'
			start_time2 = '10'
			end_time = '06'
		
		return render_template('tracking.html', telgm_token = telgm_token, telgm_botid = telgm_botid, start_time = start_time, telgm = telgm, telgm_alim = telgm_alim, start_time2 = start_time2, end_time = end_time)

@bp2.route('tracking_list', methods=["GET"])
def tracking_list():
	#데이타베이스 없으면 생성
	con = sqlite3.connect(sub2db + '/telegram.db',timeout=60)
	con.execute('CREATE TABLE IF NOT EXISTS tracking (telgm_token TEXT, telgm_botid TEXT, start_time TEXT, telgm TEXT, telgm_alim TEXT)')
	con.execute("PRAGMA cache_size = 10000")
	con.execute("PRAGMA locking_mode = NORMAL")
	con.execute("PRAGMA temp_store = MEMORY")
	con.execute("PRAGMA auto_vacuum = 1")
	con.execute("PRAGMA journal_mode=WAL")
	con.execute("PRAGMA synchronous=NORMAL")
	con.close()
	#SQLITE3 DB 없으면 만들다.
	con = sqlite3.connect(sub2db + '/delivery.db',timeout=60)
	con.execute('CREATE TABLE IF NOT EXISTS tracking (PARCEL TEXT, NUMBER TEXT, DATE TEXT, BOX TEXT,COMPLTE TEXT)')
	con.execute("PRAGMA cache_size = 10000")
	con.execute("PRAGMA locking_mode = NORMAL")
	con.execute("PRAGMA temp_store = MEMORY")
	con.execute("PRAGMA auto_vacuum = 1")
	con.execute("PRAGMA journal_mode=WAL")
	con.execute("PRAGMA synchronous=NORMAL")	
	con.close()
	if not session.get('logFlag'):
		return redirect(url_for('main.index'))
	else:
		telgm_token = request.args.get('telgm_token')
		telgm_botid = request.args.get('telgm_botid')
		telgm = request.args.get('telgm')
		telgm_alim = request.args.get('telgm_alim')
		per_page = 10
		page, _, offset = get_page_args(per_page=per_page)
		#알림
		con = sqlite3.connect(sub2db + '/delivery.db',timeout=60)
		con.execute("PRAGMA cache_size = 10000")
		con.execute("PRAGMA locking_mode = NORMAL")
		con.execute("PRAGMA temp_store = MEMORY")
		con.execute("PRAGMA auto_vacuum = 1")
		con.execute("PRAGMA journal_mode=WAL")
		con.execute("PRAGMA synchronous=NORMAL")
		con.row_factory = sqlite3.Row
		cur = con.cursor()
		cur.execute("SELECT COUNT(*) FROM tracking;")
		total = cur.fetchone()[0]
		cur.execute('SELECT * FROM tracking ORDER BY DATE DESC LIMIT ' + str(per_page) + ' OFFSET ' + str(offset))
		view = cur.fetchall()
		return render_template('tracking_list.html',view = view, telgm_token = telgm_token, telgm_botid = telgm_botid, telgm = telgm, telgm_alim = telgm_alim, pagination=Pagination(page=page, total=total, per_page=per_page))

@bp2.route('tracking/tracking_add', methods=['GET'])
def tracking_add():
	mytime = mydate()
	#SQLITE3 DB 없으면 만들다.
	con = sqlite3.connect(sub2db + '/delivery.db',timeout=60)
	con.execute('CREATE TABLE IF NOT EXISTS tracking (PARCEL TEXT, NUMBER TEXT, DATE TEXT, BOX TEXT, COMPLTE TEXT)')
	con.execute("PRAGMA cache_size = 10000")
	con.execute("PRAGMA locking_mode = NORMAL")
	con.execute("PRAGMA temp_store = MEMORY")
	con.execute("PRAGMA auto_vacuum = 1")
	con.execute("PRAGMA journal_mode=WAL")
	con.execute("PRAGMA synchronous=NORMAL")
	con.close()
	if not session.get('logFlag'):
		return redirect(url_for('main.index'))
	else:
		#try:
		carrier_id = request.args.get('carrier_id')
		track_id = request.args.get('track_id').strip()
		box_nun = request.args.get('box_nun')
		if len(track_id) == 0:
			pass
		else:
			print(carrier_id, track_id, mytime)
			con = sqlite3.connect(sub2db + '/delivery.db',timeout=60)
			con.execute("PRAGMA cache_size = 10000")
			con.execute("PRAGMA locking_mode = NORMAL")
			con.execute("PRAGMA temp_store = MEMORY")
			con.execute("PRAGMA auto_vacuum = 1")
			con.execute("PRAGMA journal_mode=WAL")
			con.execute("PRAGMA synchronous=NORMAL")
			cursor = con.cursor()
			sql = "select * from tracking where PARCEL = ? and NUMBER = ?"
			cursor.execute(sql, (carrier_id,track_id))
			rows = cursor.fetchone()
			if rows:
				pass
			else:
				sql = """
					INSERT OR REPLACE INTO tracking (PARCEL, NUMBER, DATE, BOX, COMPLTE) VALUES (?,?,?,?,?)
				"""
				cursor.execute(sql, (carrier_id, track_id,mytime,box_nun,'False'))
			con.commit()
			cursor.close()
			con.close()
			msg = '택배사 {} 송장번호 {} 등록 완료'.format(carrier_id,track_id)
			#else:
			#	msg = '송장번호가 없습니다.'
		return redirect(url_for('sub2.tracking'))

@bp2.route('<carrier_id>/<track_id>/tracking_complte', methods=["GET"])
def tracking_complte(carrier_id,track_id):
	if not session.get('logFlag'):
		return redirect(url_for('main.index'))
	else:
		tracking_del_new(carrier_id,track_id)
	return redirect(url_for('sub2.tracking'))	
	
@bp2.route('<carrier_id>/<track_id>/<telgm_token>/<telgm_botid>/<telgm>/<telgm_alim>/tracking_one', methods=["GET"])
def tracking_one(carrier_id,track_id,telgm,telgm_alim,telgm_token,telgm_botid):
	#SQLITE3 DB 없으면 만들다.
	con = sqlite3.connect(sub2db + '/delivery.db',timeout=60)
	con.execute('CREATE TABLE IF NOT EXISTS tracking (PARCEL TEXT, NUMBER TEXT, DATE TEXT, BOX TEXT,COMPLTE TEXT)')
	con.execute("PRAGMA cache_size = 10000")
	con.execute("PRAGMA locking_mode = NORMAL")
	con.execute("PRAGMA temp_store = MEMORY")
	con.execute("PRAGMA auto_vacuum = 1")
	con.execute("PRAGMA journal_mode=WAL")
	con.execute("PRAGMA synchronous=NORMAL")
	con.close()
	con = sqlite3.connect(sub2db + '/delivery.db',timeout=60)
	con.row_factory = sqlite3.Row
	cursor = con.cursor()
	sql = "select * from tracking where PARCEL = ? and NUMBER = ?"
	cursor.execute(sql, (carrier_id,track_id))
	rows = cursor.fetchone()
	box = rows['box']
	if not session.get('logFlag'):
		return redirect(url_for('main.index'))
	else:
		start_time2 = '23'
		end_time = '6'
		try:
			msga = tracking_pro(telgm,telgm_alim,telgm_token,telgm_botid,carrier_id,track_id, start_time2, end_time,box)
		except:
			pass

	return redirect(url_for('sub2.tracking'))	
	
@bp2.route('<carrier_id>/<track_id>/tracking_del', methods=["GET"])
def tracking_del(carrier_id,track_id):
	#SQLITE3 DB 없으면 만들다.
	con = sqlite3.connect(sub2db + '/delivery.db',timeout=60)
	con.execute('CREATE TABLE IF NOT EXISTS tracking (PARCEL TEXT, NUMBER TEXT, DATE TEXT, BOX TEXT,COMPLTE TEXT)')
	con.execute("PRAGMA cache_size = 10000")
	con.execute("PRAGMA locking_mode = NORMAL")
	con.execute("PRAGMA temp_store = MEMORY")
	con.execute("PRAGMA auto_vacuum = 1")
	con.execute("PRAGMA journal_mode=WAL")
	con.execute("PRAGMA synchronous=NORMAL")
	con.close()
	if not session.get('logFlag'):
		return redirect(url_for('main.index'))
	else:
		con = sqlite3.connect(sub2db + '/delivery.db',timeout=60)
		con.execute("PRAGMA cache_size = 10000")
		con.execute("PRAGMA locking_mode = NORMAL")
		con.execute("PRAGMA temp_store = MEMORY")
		con.execute("PRAGMA auto_vacuum = 1")
		con.execute("PRAGMA journal_mode=WAL")
		con.execute("PRAGMA synchronous=NORMAL")
		cursor = con.cursor()
		sql = "DELETE FROM tracking WHERE PARCEL = ? AND NUMBER = ?"
		cursor.execute(sql, (carrier_id, track_id))
		con.commit()
		cursor.close()
		con.close()
	return redirect(url_for('sub2.tracking'))	

@bp2.route("track_api/<carrier_id>/<track_id>/<box_nun>", methods=["GET"])
def track_api(carrier_id, track_id, box_nun):
	if len(track_id) == 0:
		msg = '택배사 {} 송장번호 {} 등록 실패'.format(carrier_id,track_id)
	else:
		print(carrier_id, track_id)
		mytime = mydate()
		#SQLITE3 DB 없으면 만들다.
		con = sqlite3.connect(sub2db + '/delivery.db',timeout=60)
		con.execute('CREATE TABLE IF NOT EXISTS tracking (PARCEL TEXT, NUMBER TEXT, DATE TEXT, BOX TEXT, COMPLTE TEXT)')
		con.execute("PRAGMA cache_size = 10000")
		con.execute("PRAGMA locking_mode = NORMAL")
		con.execute("PRAGMA temp_store = MEMORY")
		con.execute("PRAGMA auto_vacuum = 1")
		con.execute("PRAGMA journal_mode=WAL")
		con.execute("PRAGMA synchronous=NORMAL")
		con.close()
		con = sqlite3.connect(sub2db + '/delivery.db',timeout=60)
		con.execute("PRAGMA cache_size = 10000")
		con.execute("PRAGMA locking_mode = NORMAL")
		con.execute("PRAGMA temp_store = MEMORY")
		con.execute("PRAGMA auto_vacuum = 1")
		con.execute("PRAGMA journal_mode=WAL")
		con.execute("PRAGMA synchronous=NORMAL")
		cursor = con.cursor()
		sql = "select * from tracking where PARCEL = ? and NUMBER = ?"
		cursor.execute(sql, (carrier_id,track_id.strip()))
		rows = cursor.fetchone()
		if rows:
			pass
		else:
			sql = """
				INSERT OR REPLACE INTO tracking (PARCEL, NUMBER, DATE, BOX, COMPLTE) VALUES (?,?,?,?,?)
			"""
			cursor.execute(sql, (carrier_id, track_id,mytime,box_nun,'False'))
		con.commit()
		cursor.close()
		con.close()
		msg = '택배사 {} 송장번호 {} 등록 완료'.format(carrier_id,track_id)
		#else:
		#	msg = '송장번호가 없습니다.'
			
	return 	msg
	
@bp2.route('tracking/tracking_ok', methods=['GET'])
def tracking_ok():
	if not session.get('logFlag'):
		return redirect(url_for('main.index'))
	else:
		start_time = request.args.get('start_time')
		startname = request.args.get('startname')
		carrier_id = request.args.get('carrier_id')
		track_id = request.args.get('track_id')
		telgm = request.args.get('telgm')
		telgm_alim = request.args.get('telgm_alim')
		telgm_token = request.args.get('telgm_token')
		telgm_botid = request.args.get('telgm_botid')
		start_time2 = request.args.get('start_time2')
		end_time = request.args.get('end_time')
		now = request.args.get('now')
		con = sqlite3.connect(sub2db + '/telegram.db',timeout=60)
		con.execute("PRAGMA cache_size = 10000")
		con.execute("PRAGMA locking_mode = NORMAL")
		con.execute("PRAGMA temp_store = MEMORY")
		con.execute("PRAGMA auto_vacuum = 1")
		con.execute("PRAGMA journal_mode=WAL")
		con.execute("PRAGMA synchronous=NORMAL")
		cursor = con.cursor()
		cursor.execute("select * from tracking")
		rows = cursor.fetchone()
		if rows:
			sql = """
				update tracking
					set telgm_token = ?
					, telgm_botid = ?
					, start_time = ?
					, telgm = ?
					, telgm_alim = ?
					, start_time2 = ?
					, end_time = ?
			"""
		else:
			sql = """
				INSERT INTO tracking 
				(telgm_token, telgm_botid, start_time, telgm, telgm_alim, start_time2, end_time) VALUES (?, ?, ?, ?, ?, ?, ?)
			"""
		
		cursor.execute(sql, (telgm_token, telgm_botid, start_time, telgm, telgm_alim, start_time2, end_time))
		con.commit()
		cursor.close()
		con.close()
		try:
			if now == 'True':
				scheduler.add_job(tracking_start, trigger=CronTrigger.from_crontab(start_time), id=startname, args=[telgm,telgm_alim,telgm_token,telgm_botid, start_time2, end_time])
				test = scheduler.get_job(startname).id
			else:
				tracking_start(telgm,telgm_alim,telgm_token,telgm_botid, start_time2, end_time)
			logger.info('%s 를 스케줄러에 추가하였습니다.', test)
		except:
			pass
		return redirect(url_for('sub2.tracking'))
	
#실동작	
def Typhoon():
	nowtime = time.localtime()
	newdate = "%04d-%02d-%02d_%02d시%02d분%02d초" % (nowtime.tm_year, nowtime.tm_mon, nowtime.tm_mday, nowtime.tm_hour, nowtime.tm_min, nowtime.tm_sec)
	Typhoon_date = "%04d-%02d-%02d_%02d시%02d분" % (nowtime.tm_year, nowtime.tm_mon, nowtime.tm_mday, nowtime.tm_hour, nowtime.tm_min)
	no = []
	mydata = []
	last = []
	h = {"Cache-Control": "no-cache",   "Pragma": "no-cache"}
	a = 'https://search.daum.net/search?w=tot&DA=YZR&t__nil_searchbox=btn&sug=&sugo=&sq=&o=&q=%ED%83%9C%ED%92%8D'
	req = requests.get(a, headers=h)
	bs0bj = bs(req.content.decode('utf-8','replace'),'html.parser')
	#태풍 이름
	name = bs0bj.find("em",{"class":"f_etit ls_1"})
	
	#태풍 경로 텍스트 정보
	ttitle = bs0bj.find("table",{"class":"tbl"})
	if ttitle == None:
		pass
	else:
		#태풍 경로 이미지
		img_map = bs0bj.find("div",{"class":"inner_map"})
		urls = []
		for img in img_map("img"):
			tt = img.get('src')
			tt_aa = result = tt[-64:]
			cc = 'http://t1.daumcdn.net/contentshub/kweatherTyphoonReport/' + tt_aa
			urls.append(cc)
		for url in urls:
			if platform.system() == 'Windows':
				at = os.path.splitdrive(os.getcwd())
				root = at[0] + '/data'
			else:
				root = '/data'
			dfolder = root + '/'
			filename = Typhoon_date + '_' + name.text + ".jpg"
			category = 'weather'
			fifi = dfolder + '/' + category + '/' + filename
			url_to_image2(url, dfolder, filename)

		for i in ttitle.findAll('td'):
			a1 = i.text.strip()
			no.append(a1)
		
		for i in range(len(no)):
			try:
				dict = {'예상일시':no[i],'진행방향':no[i + 1],'진행속도(km/h)':no[i + 2],'최대풍속(m/s)':no[i + 3],'강풍반경(km)':no[i + 4],'강도':no[i + 5],'크기':no[i + 6]}
				if i % 7 == 0:
					mydata.append(dict)
			except:
				pass
		for ii in mydata:	
			a = ii['예상일시']
			b = ii['진행방향']
			c = ii['진행속도(km/h)']
			d = ii['최대풍속(m/s)']
			e = ii['강풍반경(km)']
			f = ii['강도']
			g = ii['크기']
			msg = '예상일시 : {} 진행방향 : {} 진행속도(km/h) : {} 최대풍속(m/s) : {} 강풍반경(km) : {} 강도 : {} 크기 : {}\n'.format(a,b,c,d,e,f,g)
			last.append(msg)
	time.sleep(1)
	return [last,fifi,name]
		
def weather_start(location,telgm,telgm_alim,telgm_token,telgm_botid,start_time2,end_time):
	logger.info('날씨알림시작')
	headers = {"User-Agent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36'}
	#with requests.Session() as s:
	mainurl = 'https://www.kr-weathernews.com/mv3/if/search.fcgi?query=' + location
	url = requests.get(mainurl, headers=headers)
	resp = url.json()
	list = resp['cities']
	for i in list:
		code = i['region_key']
	
	start = 'https://www.kr-weathernews.com/mv3/if/today.fcgi?region=' + code
	url = requests.get(start, headers=headers)
	resp = url.json()
	state = resp['state'] #주소1
	city = resp['city'] #주소2
	news = resp['news']['type']
	news2 = resp['news']['title']
	sunrise = resp['sunrise'] #일출
	sunset = resp['sunset'] #일몰
	date = resp['current']['date']
	time = resp['current']['time']
	temp = resp['current']['temp']
	feeltemp = resp['current']['feeltemp'] #어제보다 ... 높음
	rhum = resp['current']['rhum'] #습도
	press = resp['current']['press'] #기압
	wdir = resp['current']['wdir'] #바람 남...
	wspd = resp['current']['wspd'] #wdir + wspd
	pm10 = resp['current']['pm10'] #미세먼지
	pm25 = resp['current']['pm25'] #초미세먼지
	prec = resp['current']['prec'] #강수량 1시간
	msg1 = '{} {}기준 {} {}\n현재온도 {}℃ (체감온도 {}℃)\n미세먼지 : {}   초미세먼지 : {}\n강수량 : {}㎜   습도 : {}％\n기압 : {}hPa\n바람 : {} {}m/s\n일출 : {}   일몰 : {}\n{}'.format(date,time,state,city,temp,feeltemp,pm10,pm25,prec,rhum,press,wdir,wspd,sunrise,sunset,news2)	
	#msg1 = '{} {}기준 {} {}\n현재온도 {}℃ (체감온도 {}℃)\n미세먼지 : {}   초미세먼지 : {}\n습도 : {}％\n기압 : {}hPa\n바람 : {} {}m/s\n일출 : {}   일몰 : {}\n{} {}'.format(date,time,state,city,temp,feeltemp,pm10,pm25,rhum,press,wdir,wspd,sunrise,sunset,news,news2)	

	big = 'https://www.kr-weathernews.com/mv3/if/warn.fcgi?region=' + code
	url = requests.get(big, headers=headers)
	resp = url.json()
	big_date = resp['warn'][0]['announce_date']
	big_title = resp['warn'][0]['title']
	#해당구역
	s3_big_region = []
	s_big_region = resp['warn'][0]['region']
	s2_big_region = re.sub(r"(\(\d\) )",'  ',s_big_region)
	s4_big_region = s2_big_region.split('  ')
	for i in s4_big_region:
		if len(i) == 0:
			pass
		else:
			mm = 'o {}\n'.format(i)
			s3_big_region.append(mm)
	big_region = ''.join(s3_big_region)
	#내용
	s3_big_efftsatus = []
	s_big_efftsatus = resp['warn'][0]['efftsatus']
	s2_big_efftsatus = s_big_efftsatus.split('o ')
	for i in s2_big_efftsatus:
		if len(i) == 0:
			pass
		else:
			mm = 'o {}\n'.format(i)
			s3_big_efftsatus.append(mm)
	big_efftsatus = ''.join(s3_big_efftsatus)
	#예비특보
	s3_big_efftsatus_pre = []
	s_big_efftsatus_pre = resp['warn'][0]['efftsatus_pre']
	s2_big_efftsatus_pre = re.sub(r"(\(\d\) )",'  ',s_big_efftsatus_pre)
	s4_big_efftsatus_pre = s2_big_efftsatus_pre.split('  ')
	for i in s4_big_efftsatus_pre:
		if len(i) == 0:
			pass
		else:
			mm = 'o {}\n'.format(i)
			s3_big_efftsatus_pre.append(mm)
	re3_big_efftsatus_pre = []
	re2_big_efftsatus_pre = ''.join(s3_big_efftsatus_pre)
	re_big_efftsatus_pre2 = re2_big_efftsatus_pre.split('o ')
	for i in re_big_efftsatus_pre2:
		if len(i) == 0:
			pass
		else:
			mm = 'o {}\n'.format(i)
			re3_big_efftsatus_pre.append(mm)
	big_efftsatus_pre = ''.join(re3_big_efftsatus_pre)
	msg2 = '{} {}\n\n* 해당 구역\n\n{}\n\n* 내용\n\n{}\n\n* 예비특보\n\n{}'.format(big_date,big_title,big_region,big_efftsatus,big_efftsatus_pre)
	try:
		msg4,filename,name = Typhoon()
		msg3 = " ".join(msg4)
		msg = '{}\n\n{}\n\n태풍 정보 ({})\n{}'.format(msg1,msg2,name.text,msg3)		
	except:
		msg = '{}\n\n{}'.format(msg1,msg2)
	tel(telgm,telgm_alim,telgm_token,telgm_botid,msg,start_time2,end_time)
	try:
		tel_img(telgm,telgm_alim,telgm_token,telgm_botid,filename,start_time2,end_time)
	except:
		pass
	logger.info('날씨 알림완료')
	comp = '완료'
	return comp	
	
@bp2.route('weather')
def weather():
	#데이타베이스 없으면 생성
	con = sqlite3.connect(sub2db + '/telegram.db',timeout=60)
	con.execute('CREATE TABLE IF NOT EXISTS weather (telgm_token TEXT, telgm_botid TEXT, start_time TEXT, telgm TEXT, telgm_alim TEXT, start_time2 TEXT, end_time TEXT)')
	con.execute("PRAGMA cache_size = 10000")
	con.execute("PRAGMA locking_mode = NORMAL")
	con.execute("PRAGMA temp_store = MEMORY")
	con.execute("PRAGMA auto_vacuum = 1")
	con.execute("PRAGMA journal_mode=WAL")
	con.execute("PRAGMA synchronous=NORMAL")
	con.close()
	con = sqlite3.connect(sub2db + '/telegram.db',timeout=60)
	con.row_factory = sqlite3.Row
	cur = con.cursor()
	sql = "SELECT sql FROM sqlite_master WHERE name='weather' AND sql LIKE '%start_time2%'"
	cur.execute(sql)
	rows = cur.fetchall()
	if len(rows) == 0:
		sql = "alter table weather add column start_time2 TEXT"
		cur.execute(sql)
	else:
		pass
	con.close()
	con = sqlite3.connect(sub2db + '/telegram.db',timeout=60)
	con.row_factory = sqlite3.Row
	cur = con.cursor()
	sql = "SELECT sql FROM sqlite_master WHERE name='weather' AND sql LIKE '%end_time%'"
	cur.execute(sql)
	rows = cur.fetchall()
	if len(rows) == 0:
		sql = "alter table weather add column end_time TEXT"
		cur.execute(sql)
	else:
		pass
	con.close()
	con = sqlite3.connect(sub2db + '/telegram.db',timeout=60)
	con.row_factory = sqlite3.Row
	cur = con.cursor()
	sql = "SELECT sql FROM sqlite_master WHERE name='weather' AND sql LIKE '%location%'"
	cur.execute(sql)
	rows = cur.fetchall()
	if len(rows) == 0:
		sql = "alter table weather add column location TEXT"
		cur.execute(sql)
	else:
		pass
	con.close()
	if not session.get('logFlag'):
		return redirect(url_for('main.index'))
	else:	
		telgm_token = request.args.get('telgm_token')
		telgm_botid = request.args.get('telgm_botid')
		con = sqlite3.connect(sub2db + '/telegram.db',timeout=60)
		con.row_factory = sqlite3.Row
		cur = con.cursor()
		cur.execute("select * from weather")
		rows = cur.fetchone()
		if rows:
			telgm_token = rows['telgm_token']
			telgm_botid = rows['telgm_botid']
			start_time = rows['start_time']
			telgm = rows['telgm']
			telgm_alim = rows['telgm_alim']
			start_time2 = rows['start_time2']
			end_time = rows['end_time']
			location = rows['location']
		else:
			telgm_token='입력하세요'
			telgm_botid='입력하세요'
			start_time = '*/1 * * * *'
			telgm = 'False'
			telgm_alim = 'False'
			start_time2 = '10'
			end_time = '06'
			location = '서울'
		return render_template('weather.html', telgm_token = telgm_token, telgm_botid = telgm_botid, start_time = start_time, telgm = telgm, telgm_alim = telgm_alim, start_time2 = start_time2, end_time = end_time, location = location)

@bp2.route('weather_ok', methods=['POST'])
def weather_ok():
	if not session.get('logFlag'):
		return redirect(url_for('main.index'))
	else:
		start_time = request.form['start_time']
		startname = request.form['startname']
		location = request.form['location']
		telgm = request.form['telgm']
		telgm_alim = request.form['telgm_alim']
		telgm_token = request.form['telgm_token']
		telgm_botid = request.form['telgm_botid']
		start_time2 = request.form['start_time2']
		end_time = request.form['end_time']
		now = request.form['now']
		con = sqlite3.connect(sub2db + '/telegram.db',timeout=60)
		con.execute("PRAGMA cache_size = 10000")
		con.execute("PRAGMA locking_mode = NORMAL")
		con.execute("PRAGMA temp_store = MEMORY")
		con.execute("PRAGMA auto_vacuum = 1")
		con.execute("PRAGMA journal_mode=WAL")
		con.execute("PRAGMA synchronous=NORMAL")
		cursor = con.cursor()
		cursor.execute("select * from weather")
		rows = cursor.fetchone()
		if rows:
			sql = """
				update weather
					set telgm_token = ?
					, telgm_botid = ?
					, start_time = ?
					, telgm = ?
					, telgm_alim = ?
					, start_time2 = ?
					, end_time = ?
					, location =?
			"""
		else:
			sql = """
				INSERT INTO weather 
				(telgm_token, telgm_botid, start_time, telgm, telgm_alim, start_time2, end_time,location) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
			"""
		
		cursor.execute(sql, (telgm_token, telgm_botid, start_time, telgm, telgm_alim, start_time2, end_time, location))
		con.commit()
		cursor.close()
		con.close()
		try:
			if now == 'True':
				scheduler.add_job(weather_start, trigger=CronTrigger.from_crontab(start_time), id=startname, args=[location,telgm,telgm_alim,telgm_token,telgm_botid, start_time2, end_time])
				test = scheduler.get_job(startname).id
			else:
				weather_start(location,telgm,telgm_alim,telgm_token,telgm_botid, start_time2, end_time)
			logger.info('%s 를 스케줄러에 추가하였습니다.', test)
		except:
			pass
		return redirect(url_for('sub2.weather'))

#운세알리미
#운세알리미 DB
def add_unse(lastdate, zodiac, zodiac2, list, complte):
	try:
		con = sqlite3.connect(sub2db + '/unse.db',timeout=60)
		con.execute("PRAGMA cache_size = 10000")
		con.execute("PRAGMA locking_mode = NORMAL")
		con.execute("PRAGMA temp_store = MEMORY")
		con.execute("PRAGMA auto_vacuum = 1")
		con.execute("PRAGMA journal_mode=WAL")
		con.execute("PRAGMA synchronous=NORMAL")
		cur = con.cursor()
		sql = "select * from unse where DATE = ? AND ZODIAC2 = ? AND MEMO = ?"
		cur.execute(sql, (lastdate, zodiac2, list))
		row = cur.fetchone()
		if row != None:
			print("해당 내용은 DB에 있습니다.")
		else:
			cur.execute("INSERT OR REPLACE INTO unse (DATE, ZODIAC, ZODIAC2, MEMO, COMPLTE) VALUES (?,?,?,?,?)", (lastdate, zodiac, zodiac2, list, complte))
			con.commit()
	except:
		con.rollback()	
	finally:
		con.close()
	comp = '완료'
	return comp	
	
def add_unse_d(a):
	try:
		#마지막 실행까지 작업안했던 결과물 저장
		con = sqlite3.connect(sub2db + '/unse.db',timeout=60)
		con.execute("PRAGMA cache_size = 10000")
		con.execute("PRAGMA locking_mode = NORMAL")
		con.execute("PRAGMA temp_store = MEMORY")
		con.execute("PRAGMA auto_vacuum = 1")
		con.execute("PRAGMA journal_mode=WAL")
		con.execute("PRAGMA synchronous=NORMAL")
		cur = con.cursor()
		sql = "select * from unse where DATE = ?"
		cur.execute(sql, (a,))
		row = cur.fetchone()
		if row == None:
			print("해당 내용은 DB에 없습니다.")
		else:
			sql = "UPDATE unse SET COMPLTE = ? WHERE DATE = ?"	
			cur.execute(sql,('True', a))
			con.commit()
	except:
		con.rollback()	
	finally:	
		con.close()	
	comp = '완료'
	return comp	
	
def unse_start(telgm,telgm_alim,telgm_token,telgm_botid, start_time2 ,end_time):
	logger.info('운세알림시작')
	#SQLITE3 DB 없으면 만들다.
	con = sqlite3.connect(sub2db + '/unse.db',timeout=60)
	con.execute('CREATE TABLE IF NOT EXISTS unse (DATE TEXT, ZODIAC TEXT, ZODIAC2 TEXT, MEMO TEXT, COMPLTE TEXT)')
	con.execute("PRAGMA cache_size = 10000")
	con.execute("PRAGMA locking_mode = NORMAL")
	con.execute("PRAGMA temp_store = MEMORY")
	con.execute("PRAGMA auto_vacuum = 1")
	con.execute("PRAGMA journal_mode=WAL")
	con.execute("PRAGMA synchronous=NORMAL")
	con.close()
	session = requests.Session()
	header = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36"}

	auth = 'https://www.unsin.co.kr/unse/free/todayline/form?linenum=9'
	rs = requests.get(auth,headers=header)
	bs0bj = bs(rs.content.decode('utf-8','replace'),'html.parser')
	posts = bs0bj.findAll("div",{"class":"ani_result"})
	dates = bs0bj.find('span',{'class':'cal'}).text
	lastdate = " ".join(dates.split())
	for i in posts:
		a = i.text
		test = i.find('dd')
		title = test.text
		a2 = " ".join(title.split())
		aaa = a2.split(maxsplit=1)
		zodiac = aaa[0]
		zodiac2 = aaa[1]
		name = i.find('ul')
		li = name.text
		list = " ".join(li.split())
		#a4 = a2 + '\n' + list
		a4 = zodiac + '\n' + zodiac2 + '\n' + list
		complte = 'False'
		add_unse(lastdate, zodiac, zodiac2, list, complte)
		
	#중복 알림 방지
	con = sqlite3.connect(sub2db + '/unse.db',timeout=60)
	con.row_factory = sqlite3.Row
	cur = con.cursor()
	sql = "select * from unse where COMPLTE = ?"
	cur.execute(sql,('False',))
	rows = cur.fetchall()
	msg = []
	for row in rows:
		timestr = time.strftime("%Y%m%d")
		a = row['DATE'] #생성날짜
		b = row['ZODIAC'] #띠
		c = row['ZODIAC2'] #띠별운세
		d = row['MEMO'] #띠별상세운세
		e = row['COMPLTE'] #완료여부
		a4 = b + ' (' + c + ')\n' + d
		msg.append(a4)
		
	msg_all = "\n\n".join(msg)	
	tel(telgm,telgm_alim,telgm_token,telgm_botid,msg_all, start_time2, end_time)
	add_unse_d(a)
	logger.info('운세 알림완료')	

	
	comp = '완료'
	return comp
@bp2.route('unse')
def unse():
	#데이타베이스 없으면 생성
	con = sqlite3.connect(sub2db + '/telegram.db',timeout=60)
	con.execute('CREATE TABLE IF NOT EXISTS unse (telgm_token TEXT, telgm_botid TEXT, start_time TEXT, telgm TEXT, telgm_alim TEXT)')
	con.execute("PRAGMA cache_size = 10000")
	con.execute("PRAGMA locking_mode = NORMAL")
	con.execute("PRAGMA temp_store = MEMORY")
	con.execute("PRAGMA auto_vacuum = 1")
	con.execute("PRAGMA journal_mode=WAL")
	con.execute("PRAGMA synchronous=NORMAL")
	con.close()
	con = sqlite3.connect(sub2db + '/telegram.db',timeout=60)
	con.row_factory = sqlite3.Row
	cur = con.cursor()
	sql = "SELECT sql FROM sqlite_master WHERE name='unse' AND sql LIKE '%start_time2%'"
	cur.execute(sql)
	rows = cur.fetchall()
	if len(rows) == 0:
		sql = "alter table unse add column start_time2 TEXT"
		cur.execute(sql)
	else:
		pass
	con.close()
	con = sqlite3.connect(sub2db + '/telegram.db',timeout=60)
	con.row_factory = sqlite3.Row
	cur = con.cursor()
	sql = "SELECT sql FROM sqlite_master WHERE name='unse' AND sql LIKE '%end_time%'"
	cur.execute(sql)
	rows = cur.fetchall()
	if len(rows) == 0:
		sql = "alter table unse add column end_time TEXT"
		cur.execute(sql)
	else:
		pass
	con.close()
	if not session.get('logFlag'):
		return redirect(url_for('main.index'))
	else:
		telgm_token = request.args.get('telgm_token')
		telgm_botid = request.args.get('telgm_botid')
		con = sqlite3.connect(sub2db + '/telegram.db',timeout=60)
		con.row_factory = sqlite3.Row
		cur = con.cursor()
		cur.execute("select * from unse")
		rows = cur.fetchone()
		if rows:
			telgm_token = rows['telgm_token']
			telgm_botid = rows['telgm_botid']
			start_time = rows['start_time']
			telgm = rows['telgm']
			telgm_alim = rows['telgm_alim']
			start_time2 = rows['start_time2']
			end_time = rows['end_time']
		else:
			telgm_token='입력하세요'
			telgm_botid='입력하세요'
			start_time = '*/1 * * * *'
			telgm = 'False'
			telgm_alim = 'False'
			start_time2 = '10'
			end_time = '06'
		return render_template('unse.html', telgm_token = telgm_token, telgm_botid = telgm_botid, start_time = start_time, telgm = telgm, telgm_alim = telgm_alim, start_time2 = start_time2, end_time = end_time)


@bp2.route('unse_ok', methods=['POST'])
def unse_ok():
	if not session.get('logFlag'):
		return redirect(url_for('main.index'))
	else:
		start_time = request.form['start_time']
		startname = request.form['startname']
		telgm = request.form['telgm']
		telgm_alim = request.form['telgm_alim']
		telgm_token = request.form['telgm_token']
		telgm_botid = request.form['telgm_botid']
		start_time2 = request.form['start_time2']
		end_time = request.form['end_time']
		now = request.form['now']
		conn = sqlite3.connect(sub2db + '/telegram.db',timeout=60)
		cursor = conn.cursor()
		cursor.execute("select * from unse")
		rows = cursor.fetchone()
		if rows:
			sql = """
				update unse
					set telgm_token = ?
					, telgm_botid = ?
					, start_time = ?
					, telgm = ?
					, telgm_alim = ?
					, start_time2 = ?
					, end_time = ?
			"""
		else:
			sql = """
				INSERT INTO unse 
				(telgm_token, telgm_botid, start_time, telgm, telgm_alim, start_time2, end_time) VALUES (?, ?, ?, ?, ?, ?, ?)
			"""
		
		cursor.execute(sql, (telgm_token, telgm_botid, start_time, telgm, telgm_alim, start_time2, end_time))
		conn.commit()
		cursor.close()
		conn.close()
		try:
			if now == 'True':
				scheduler.add_job(unse_start, trigger=CronTrigger.from_crontab(start_time), id=startname, args=[telgm,telgm_alim,telgm_token,telgm_botid, start_time2, end_time])
				test = scheduler.get_job(startname).id
			else:
				unse_start(telgm,telgm_alim,telgm_token,telgm_botid, start_time2, end_time)
			logger.info('%s 를 스케줄러에 추가하였습니다.', test)
		except:
			pass
		return redirect(url_for('sub2.unse'))
	
#퀴즈정답알림

@bp2.route('quiz_list')
def quiz_list():
	#SQLITE3 DB 없으면 만들다.
	con = sqlite3.connect(sub2db + '/quiz.db',timeout=60)
	con.execute('CREATE TABLE IF NOT EXISTS quiz (TITLE TEXT, URL TEXT, MEMO TEXT, COMPLTE TEXT,SITE_NAME TEXT, DATE TEXT)')
	con.execute("PRAGMA cache_size = 10000")
	con.execute("PRAGMA locking_mode = NORMAL")
	con.execute("PRAGMA temp_store = MEMORY")
	con.execute("PRAGMA auto_vacuum = 1")
	con.execute("PRAGMA journal_mode=WAL")
	con.execute("PRAGMA synchronous=NORMAL")	
	con.close()
	if not session.get('logFlag'):
		return redirect(url_for('main.index'))
	else:
		per_page = 10
		page, _, offset = get_page_args(per_page=per_page)
		#알림
		con = sqlite3.connect(sub2db + '/quiz.db',timeout=60)
		con.execute("PRAGMA cache_size = 10000")
		con.execute("PRAGMA locking_mode = NORMAL")
		con.execute("PRAGMA temp_store = MEMORY")
		con.execute("PRAGMA auto_vacuum = 1")
		con.execute("PRAGMA journal_mode=WAL")
		con.execute("PRAGMA synchronous=NORMAL")
		con.row_factory = sqlite3.Row
		cur = con.cursor()
		cur.execute("SELECT COUNT(*) FROM quiz;")
		total = cur.fetchone()[0]
		cur.execute('SELECT * FROM quiz ORDER BY DATE DESC LIMIT ' + str(per_page) + ' OFFSET ' + str(offset))
		view = cur.fetchall()
		return render_template('quiz_list.html',view = view, pagination=Pagination(page=page, total=total, per_page=per_page))

def quiz_add_go(title, memo_s, URL,SITE_NAME, DATE):
	#SQLITE3 DB 없으면 만들다.
	con = sqlite3.connect(sub2db + '/quiz.db',timeout=60)
	con.execute('CREATE TABLE IF NOT EXISTS quiz (TITLE TEXT, URL TEXT, MEMO TEXT, COMPLTE TEXT,SITE_NAME TEXT, DATE TEXT)')
	con.execute("PRAGMA cache_size = 10000")
	con.execute("PRAGMA locking_mode = EXCLUSIVE")
	con.execute("PRAGMA temp_store = MEMORY")
	con.execute("PRAGMA auto_vacuum = 1")
	con.execute("PRAGMA journal_mode=WAL")
	con.execute("PRAGMA synchronous=NORMAL")
	con.close()
	#데이터베이스 컬럼 추가하기
	con = sqlite3.connect(sub2db + '/quiz.db',timeout=60)	
	cur = con.cursor()
	sql = "SELECT sql FROM sqlite_master WHERE name='quiz' AND sql LIKE '%SITE_NAME%'"
	cur.execute(sql)
	rows = cur.fetchall()
	if len(rows) == 0:
		sql = "alter table quiz add column SITE_NAME TEXT"
		cur.execute(sql)
	else:
		pass
	#데이터베이스 컬럼 추가하기
	con = sqlite3.connect(sub2db + '/quiz.db',timeout=60)	
	cur = con.cursor()
	sql = "SELECT sql FROM sqlite_master WHERE name='quiz' AND sql LIKE '%DATE%'"
	cur.execute(sql)
	rows = cur.fetchall()
	if len(rows) == 0:
		sql = "alter table quiz add column DATE TEXT"
		cur.execute(sql)
	else:
		pass
	try: #URL TEXT, SEL TEXT, SELNUM TEXT
		con = sqlite3.connect(sub2db + '/quiz.db',timeout=60)
		con.row_factory = sqlite3.Row
		cur = con.cursor()
		sql = "select * from quiz where URL = ? AND SITE_NAME = ?"
		cur.execute(sql, (URL,SITE_NAME))
		row = cur.fetchone()
		if row != None:
			MEMO = row['MEMO']
			old_title = row['TITLE']
			if memo_s == MEMO and title == old_title:
				pass
			else:
				cur.execute("update quiz set MEMO = ?, COMPLTE = ?, TITLE = ? where URL = ? AND SITE_NAME = ?",(memo_s,'False',title,URL,SITE_NAME))
				con.commit()
				#print("해당 내용은 DB에 있어서 {} {} -> {} {} 수정합니다.".format(old_title,MEMO, title,memo_s))
		else:
			cur.execute("INSERT OR REPLACE INTO quiz (TITLE, URL, MEMO, COMPLTE, SITE_NAME, DATE) VALUES (?,?,?,?,?,?)", (title, URL, memo_s, 'False',SITE_NAME,DATE))
			con.commit()
	except:
		con.rollback()	
	finally:
		con.close()
#알리미 완료
def quiz_add_go_d(MEMO, URL,SITE_NAME):
	try:
		#마지막 실행까지 작업안했던 결과물 저장
		con = sqlite3.connect(sub2db + '/quiz.db',timeout=60)
		cur = con.cursor()
		sql = "select * from quiz where MEMO = ? and URL = ? AND SITE_NAME = ?"
		cur.execute(sql, (MEMO,URL,SITE_NAME))
		row = cur.fetchone()
		if row == None:
			pass
		else:
			sql = "UPDATE quiz SET COMPLTE = ? WHERE MEMO = ? and URL = ? and SITE_NAME = ?"	
			cur.execute(sql,('True', MEMO,URL,SITE_NAME))
			con.commit()
	except:
		con.rollback()	
	finally:	
		con.close()
		
def quiz_start(telgm,telgm_alim,telgm_token,telgm_botid,myalim, start_time2, end_time):
	if platform.system() == 'Windows':
		at = os.path.splitdrive(os.getcwd())
		root = at[0] + '/data'
	else:
		root = '/data'
	dfolder = root + '/'
	logger.info('퀴즈정답알림 시작')
	#퀴즈정답 시작후 30초후 작동시작
	time.sleep(30)
	list = []
	last = []
	try:
		header = {"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5)\AppleWebKit 537.36 (KHTML, like Gecko) Chrome","Accept":"text/html,application/xhtml+xml,application/xml;\q=0.9,imgwebp,*/*;q=0.8"}
		url = 'https://quizbang.tistory.com/rss'
		parsed_data = get_data(url)

		count = len(parsed_data['entries'])

		answer = []
		for i in range(count):
			article = parsed_data['entries'][i]
			try:
				old_title = article['title']
				title = symbol_re(old_title)
				if title == 'ㅡ':
					print('내용없음')
					continue
			except:
				continue
			link = article['link']
			memo_list = article['description']
			#내용 파일로 저장한뒤 TEXT로 읽어옴
			html_file = open(dfolder + '/html_file.html', 'w', encoding="UTF-8")
			html_file.write(memo_list)
			html_file.close()
			page = open(dfolder + '/html_file.html', 'rt', encoding='utf-8').read()
			soup = bs(page, 'html.parser')
			all_text = soup.text
			new_str = all_text.replace(u"\xa0", u" ")
			p = re.compile('▶(.*?)\(퀴즈 방식이 변경되어')
			memo_re = p.findall(new_str)
			if len(memo_re) == 0:
				p = re.compile('▶(.*?)🎁')
				memo_re = p.findall(new_str)
				if len(memo_re) == 0:
					p = re.compile('▶(.*?\n.*\n.*)🎁')
					memo_re = p.findall(new_str)
					if len(memo_re) == 0:
						p = re.compile('▶(.*?)\n')
						memo_re = p.findall(new_str)
			else:
				pass
			memo_old_re = ''.join(memo_re).lstrip().strip()
			#정답 없으면 패스
			if memo_old_re == '':
				continue
			else:
				memo_re1 = memo_old_re.replace("<br>", ' ')
				memo_re = memo_re1.replace("<br />", ' ')
				html_memo = remove_html(memo_re)
				p2 = re.compile('(.*?)\[')
				html_memo_find = p2.findall(html_memo)
				if len(html_memo_find) == 0:
					memo = html_memo
				else:
					#memo = ''.join(html_memo_find).lstrip().strip()
					memo = html_memo_find[0]
			#정답 추가
			answer.append(memo)
			answer2_url = link
			req = requests.get(answer2_url,headers=header)
			html = req.text
			gogo = bs(html, "html.parser")
			try:
				posts = gogo.findAll("p",{"class":"comment-content"})			
				for i in posts:
					answer2 = i.text.strip()
					answer.append(answer2)
				result = []
				for value in answer:
					if value not in result:
						result.append(value)
			except:
				result = answer
			#print(result)
			answer = []
			memo = ' '.join(result).lstrip()
			keys = ['TITLE','MEMO', 'URL','SITE_NAME']
			values = [title, memo, link, 'https://quizbang.tistory.com']
			dt = dict(zip(keys, values))
			last.append(dt)
	except:
		logger.info('퀴즈방 에러')
		pass

	#기존 리스트 목록 삭제
	list.clear()
	try:
		with requests.Session() as s:
			header = {"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5)\AppleWebKit 537.36 (KHTML, like Gecko) Chrome","Accept":"text/html,application/xhtml+xml,application/xml;\q=0.9,imgwebp,*/*;q=0.8"}
			URL = 'https://www.ppomppu.co.kr/search_bbs.php?bbs_cate=2&keyword=%BF%C0%C4%FB%C1%EE&search_type=sub_memo&order_typedate'
			req = s.get(URL,headers=header)
			html = req.text
			gogo = bs(html, "html.parser")
			posts = gogo.findAll("div",{"class":"conts"})
                                
			for i in posts:
				title_old = i.find('span',{'class':'title'}).find_all(text = True)
				title = title_old[0] + title_old[1]
				#print(title)
				url = i.find('a')["href"]
				keys = ['TITLE','URL']
				values = [title, url]
				dt = dict(zip(keys, values))
				list.append(dt)
            
			for ii in list:
				title = ii['TITLE']
				url_c = ii['URL']
				if 'https' in url_c:
					continue
				else:
					sec = 'https://www.ppomppu.co.kr' + ii['URL']
					#logger.info(sec)
					try:
						req = s.get(sec,headers=header)
						req.raise_for_status()
					except requests.exceptions.RequestException as e:
						logger.info(e)
						continue
					html = req.text
					gogo = bs(html, "html.parser")
					memo_old = gogo.findAll("table",{"class":"pic_bg"})
					memo_new = memo_old[2].findAll('b')
					if len(memo_new) == 0:
						memo_new = memo_old[2].findAll('p')
					else:
						pass
					memo_list = []
					for af in memo_new:
						a = af.text
						f = a.replace(u'\xa0',u'')
						memo_list.append(f)
					memo = ' '.join(memo_list).lstrip()
					p = re.compile('(.*?)  ')
					memo_last = p.findall(memo)
					memos = '  '.join(memo_last).lstrip()
					if memos == '':
						continue
					else:
						print(memos)
					if len(memos) == 0:
						memos = memo
					else:
						pass
					keys = ['TITLE','MEMO', 'URL','SITE_NAME']
					values = [title, memos, sec,'https://www.ppomppu.co.kr']
					dt = dict(zip(keys, values))
					last.append(dt)
	except:
		logger.info('뽐뿌퀴즈 에러')
		pass
	try:
		#토실행운퀴즈
		header = {"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5)\AppleWebKit 537.36 (KHTML, like Gecko) Chrome","Accept":"text/html,application/xhtml+xml,application/xml;\q=0.9,imgwebp,*/*;q=0.8"}
		url = 'https://luckyquiz3.blogspot.com/feeds/posts/default?alt=rss'
		parsed_data = get_data(url)
		#print(parsed_data)
		#try:
		#	news_name = parsed_data['feed']['title']
		#except:
		#	pass
		count = len(parsed_data['entries'])
		answer = []
		for i in range(count):
			article = parsed_data['entries'][i]
			try:
				title = article['title']
			except:
				continue
			link = article['link']
			memo_list = article['description']
			#내용 파일로 저장한뒤 TEXT로 읽어옴
			html_file = open(dfolder + '/html_file.html', 'w', encoding="UTF-8")
			html_file.write(memo_list)
			html_file.close()
			page = open(dfolder + '/html_file.html', 'rt', encoding='utf-8').read()
			soup = bs(page, 'html.parser')
			all_text = soup.text
			#원코드
			#p = re.compile('정답은(.*?)\입니다.')
			#memo_re = p.findall(all_text)
			#memo = ''.join(memo_re).lstrip().strip()
			#수정코드
			p = re.compile('정답은(.*?)\입니다.')
			memo_re = p.findall(all_text)
			memo = ''.join(memo_re).lstrip().strip()
			memo_a = memo.split(' ')
			p2 = re.compile('다른정답  (.*?)    ㅡ')
			memo_re2 = p2.findall(all_text)
			memo2 = ''.join(memo_re2).lstrip().strip()
			memo2_a = memo2.split('   ')
			memo3 = ' '.join(memo2_a).lstrip().strip()
			memo3_a = memo3.split(' ')
			lt_memo = memo_a + memo3_a
			l_memo = ' '.join(lt_memo).lstrip().strip()
			#정답 추가
			answer.append(l_memo)
			answer2_url = link
			print(answer2_url)
			req = requests.get(answer2_url,headers=header)
			html = req.text
			gogo = bs(html, "html.parser")
			try:
				posts = gogo.findAll("p",{"class":"comment-content"})			
				for i in posts:
					answer2 = i.text.strip()
					answer.append(answer2)
				result = []
				for value in answer:
					if value not in result:
						result.append(value)
			except:
				result = answer
			print(result)
			answer = []
			memo = ' '.join(result).lstrip()
			keys = ['TITLE','MEMO', 'URL','SITE_NAME']
			values = [title, memo, link, 'https://luckyquiz3.blogspot.com']
			dt = dict(zip(keys, values))
			last.append(dt)
	except:	
		logger.info('토실행운퀴즈 에러')
		pass
	try:
		url = 'http://www.tipistip.com/bbs/rss.php?bo_table=quiz'
		parsed_data = get_data(url)

		count = len(parsed_data['entries'])
		last = []
		answer = []
		for i in range(count):
			article = parsed_data['entries'][i]
			try:
				old_title = article['title']
				title = symbol_re(old_title)
				#print(title)
				if title == 'ㅡ':
					print('내용없음')
					continue
			except:
				continue
			link = article['link']
			memo_list = article['description']
			title_old = re.compile('(.*?)문제는.*')
			p = re.compile('정답 : (.*)')
			title_new = title_old.findall(title)
			#print(len(title_new))
			if len(title_new) == 0:
				title = title
			else:
				title = ''.join(title_new).lstrip().strip()
			memo_re = p.findall(memo_list)
			memo = ''.join(memo_re).lstrip().strip()
			keys = ['TITLE','MEMO', 'URL','SITE_NAME']
			values = [title, memo, link, 'http://www.tipistip.com/bbs/rss.php?bo_table=quiz']
			dt = dict(zip(keys, values))
			last.append(dt)
	except:
		logger.info('퀴즈정답알림 에러')
		pass
		
	#마지막 DB 저장
	mytime = mydate()
	for ii in last:
		title = ii['TITLE']
		memo_s = ii['MEMO']
		URL = ii['URL']
		SITE_NAME = ii['SITE_NAME']
		DATE = mytime
		quiz_add_go(title, memo_s, URL,SITE_NAME, DATE)
		
	#알려준다.
	con = sqlite3.connect(sub2db + '/quiz.db',timeout=60)
	con.row_factory = sqlite3.Row
	cur = con.cursor()
	sql = "select * from quiz where COMPLTE = ?"
	cur.execute(sql, ('False',))
	rows = cur.fetchall()
	if len(rows) != 0:
		for row in rows:
			TITLE = row['TITLE']
			MEMO = row['MEMO']
			URL = row['URL']
			SITE_NAME = row['SITE_NAME']
			if '공유' in MEMO:
				pass
			else:	
				if 'ppomppu' in SITE_NAME :
					site = '뽐뿌'
				elif 'gaecheon' in SITE_NAME :
					site = '단델리온 더스트'
				elif 'luckyquiz' in SITE_NAME :
					site = '토실행운퀴즈'
				elif 'quizbang' in SITE_NAME :
					site = '퀴즈방'
				elif 'tipistip' in SITE_NAME :
					site = '퀴즈정답알림'
				msg = '|{}|{}\n정답 : ▶ {}'.format(site,TITLE,MEMO)
				check_len = myalim.split('|')
				check_alim = len(check_len)
				if check_alim == 0:
					pass
				elif check_alim > 0:
					for i in check_len:
						if i in msg:
							if '잠시 후 공개' in msg:
								pass
							else:
								tel(telgm,telgm_alim,telgm_token,telgm_botid,msg, start_time2, end_time)
								quiz_add_go_d(MEMO, URL,SITE_NAME)
					
		logger.info('퀴즈정답 완료했습니다.')
	else:
		logger.info('퀴즈정답 신규내용이 없습니다.')
		pass
	con.close()
	
@bp2.route('quiz')
def quiz():
	#데이타베이스 없으면 생성
	con = sqlite3.connect(sub2db + '/telegram.db',timeout=60)
	con.execute('CREATE TABLE IF NOT EXISTS quiz (telgm_token TEXT, telgm_botid TEXT, start_time TEXT, telgm TEXT, telgm_alim TEXT, myalim TEXT)')
	con.execute("PRAGMA cache_size = 10000")
	con.execute("PRAGMA locking_mode = NORMAL")
	con.execute("PRAGMA temp_store = MEMORY")
	con.execute("PRAGMA auto_vacuum = 1")
	con.execute("PRAGMA journal_mode=WAL")
	con.execute("PRAGMA synchronous=NORMAL")
	con.close()
	con = sqlite3.connect(sub2db + '/telegram.db',timeout=60)
	con.row_factory = sqlite3.Row
	cur = con.cursor()
	sql = "SELECT sql FROM sqlite_master WHERE name='quiz' AND sql LIKE '%myalim%'"
	cur.execute(sql)
	rows = cur.fetchall()
	if len(rows) == 0:
		sql = "alter table quiz add column myalim TEXT"
		cur.execute(sql)
	else:
		pass
	con.close()
	#데이터베이스 컬럼 추가하기
	con = sqlite3.connect(sub2db + '/quiz.db',timeout=60)	
	cur = con.cursor()
	sql = "SELECT sql FROM sqlite_master WHERE name='quiz' AND sql LIKE '%DATE%'"
	cur.execute(sql)
	rows = cur.fetchall()
	if len(rows) == 0:
		sql = "alter table quiz add column DATE TEXT"
		cur.execute(sql)
	else:
		pass
	con.close()
	con = sqlite3.connect(sub2db + '/telegram.db',timeout=60)
	con.row_factory = sqlite3.Row
	cur = con.cursor()
	sql = "SELECT sql FROM sqlite_master WHERE name='quiz' AND sql LIKE '%start_time2%'"
	cur.execute(sql)
	rows = cur.fetchall()
	if len(rows) == 0:
		sql = "alter table quiz add column start_time2 TEXT"
		cur.execute(sql)
	else:
		pass
	con.close()
	con = sqlite3.connect(sub2db + '/telegram.db',timeout=60)
	con.row_factory = sqlite3.Row
	cur = con.cursor()
	sql = "SELECT sql FROM sqlite_master WHERE name='quiz' AND sql LIKE '%end_time%'"
	cur.execute(sql)
	rows = cur.fetchall()
	if len(rows) == 0:
		sql = "alter table quiz add column end_time TEXT"
		cur.execute(sql)
	else:
		pass
	con.close()
	if not session.get('logFlag'):
		return redirect(url_for('main.index'))
	else:
		telgm_token = request.args.get('telgm_token')
		telgm_botid = request.args.get('telgm_botid')
		con = sqlite3.connect(sub2db + '/telegram.db',timeout=60)
		con.row_factory = sqlite3.Row
		cur = con.cursor()
		cur.execute("select * from quiz")
		rows = cur.fetchone()
		if rows:
			telgm_token = rows['telgm_token']
			telgm_botid = rows['telgm_botid']
			start_time = rows['start_time']
			telgm = rows['telgm']
			telgm_alim = rows['telgm_alim']
			myalim = rows['myalim']
			start_time2 = rows['start_time2']
			end_time = rows['end_time']
		else:
			telgm_token='입력하세요'
			telgm_botid='입력하세요'
			start_time = '*/1 * * * *'
			telgm = 'False'
			telgm_alim = 'False'
			myalim = '오퀴즈'
			start_time2 = '10'
			end_time = '06'
		return render_template('quiz.html', telgm_token = telgm_token, telgm_botid = telgm_botid, start_time = start_time, telgm = telgm, telgm_alim = telgm_alim, myalim = myalim, start_time2 = start_time2, end_time = end_time)


@bp2.route('quiz_ok', methods=['POST'])
def quiz_ok():
	if not session.get('logFlag'):
		return redirect(url_for('main.index'))
	else:
		start_time = request.form['start_time']
		startname = request.form['startname']
		telgm = request.form['telgm']
		telgm_alim = request.form['telgm_alim']
		telgm_token = request.form['telgm_token']
		telgm_botid = request.form['telgm_botid']
		start_time2 = request.form['start_time2']
		end_time = request.form['end_time']
		myalim = request.form['myalim']
		now = request.form['now']
		conn = sqlite3.connect(sub2db + '/telegram.db',timeout=60)
		cursor = conn.cursor()
		cursor.execute("select * from quiz")
		rows = cursor.fetchone()
		if rows:
			sql = """
				update quiz
					set telgm_token = ?
					, telgm_botid = ?
					, start_time = ?
					, telgm = ?
					, telgm_alim = ?
					, myalim = ?
					, start_time2 = ?
					, end_time = ?
			"""
		else:
			sql = """
				INSERT INTO quiz 
				(telgm_token, telgm_botid, start_time, telgm, telgm_alim, myalim, start_time2, end_time) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
			"""
		
		cursor.execute(sql, (telgm_token, telgm_botid, start_time, telgm, telgm_alim, myalim, start_time2, end_time))
		conn.commit()
		cursor.close()
		conn.close()
		try:
			if now == 'True':
				scheduler.add_job(quiz_start, trigger=CronTrigger.from_crontab(start_time), id=startname, args=[telgm,telgm_alim,telgm_token,telgm_botid,myalim, start_time2, end_time])
				test = scheduler.get_job(startname).id
			else:
				quiz_start(telgm,telgm_alim,telgm_token,telgm_botid,myalim, start_time2, end_time)
			logger.info('%s 를 스케줄러에 추가하였습니다.', test)
		except:
			pass
		return redirect(url_for('sub2.quiz'))
		
#펀맘 서비스
#펀맘 DB		
def add_d(id, go):
	try:
		#마지막 실행까지 작업안했던 결과물 저장
		con = sqlite3.connect(sub2db + '/funmom.db',timeout=60)
		cur = con.cursor()
		sql = "UPDATE funmom SET complte = ? WHERE image_url = ? AND ID = ?"
		cur.execute(sql,('True',go,id))
		con.commit()
	except:
		con.rollback()
	finally:	
		con.close()	
	comp = '완료'
	return comp
#펀맘 DB	
def add_c(title, category, category2, list_url, url, filename):
	try:
		con = sqlite3.connect(sub2db + '/funmom.db',timeout=60)
		cur = con.cursor()
		sql = "select * from funmom where image_url = ?"
		cur.execute(sql, (url,))
		row = cur.fetchone()
		if row != None:
			pass
		else:
			complte = 'False'
			cur.execute("INSERT OR REPLACE INTO funmom (title, category, category2, urltitle, image_url, image_file, complte) VALUES (?, ?, ?, ?, ?, ?, ?)", (title, category, category2, list_url, url, filename, complte))
			con.commit()
	except:
		con.rollback()
	finally:		
		con.close()	
	comp = '완료'
	return comp
	
def funmom_start(startname):
	if platform.system() == 'Windows':
		at = os.path.splitdrive(os.getcwd())
		root = at[0] + '/data'
	else:
		root = '/data'
	dfolder = root + '/'
	ccc = []
	con = sqlite3.connect(sub2db + '/funmom.db',timeout=60)
	con.row_factory = sqlite3.Row
	cur = con.cursor()
	sql = 'PRAGMA table_info(funmom)'
	cur.execute(sql)
	result = cur.fetchall()
	for i in result:
		checking = i['name']
		ccc.append(checking)
	con.close()	
	last_check = ' '.join(ccc)
	if 'category' in last_check:
		logger.info('테이블 존재 함')
	else:
		logger.info('테이블 없음 DB삭제후 재생성')
		file_path = sub2db + '/funmom.db'
		if os.path.exists(file_path):
			os.remove(file_path)
	logger.info('펀맘알림 시작')
	con = sqlite3.connect(sub2db + '/funmom.db',timeout=60)
	con.execute('CREATE TABLE IF NOT EXISTS funmom (ID integer primary key autoincrement, title TEXT, category TEXT, category2 TEXT, urltitle TEXT, image_url TEXT, image_file TEXT, complte TEXT)')
	con.execute("PRAGMA cache_size = 10000")
	con.execute("PRAGMA locking_mode = NORMAL")
	con.execute("PRAGMA temp_store = MEMORY")
	con.execute("PRAGMA auto_vacuum = 1")
	con.execute("PRAGMA journal_mode=WAL")
	con.execute("PRAGMA synchronous=NORMAL")
	con.close()
	list = []
	last = []	
	header = {"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5)\AppleWebKit 537.36 (KHTML, like Gecko) Chrome","Accept":"text/html,application/xhtml+xml,application/xml;\q=0.9,imgwebp,*/*;q=0.8"}
	url = 'https://funmom.tistory.com/rss'
	parsed_data = get_data(url)

	count = len(parsed_data['entries'])
	answer = []
	last = []
	urls = []
	for i in range(count):
		article = parsed_data['entries'][i]
		try:
			title = article['title']
		except:
			continue
		link = article['link']
		if 'notice' in link:
			pass
		else:
			memo_list = article['description']
			menu = article['category']
			last_c = menu.split('/')
			category = last_c[0]
			category2 = last_c[1]
			#내용 파일로 저장한뒤 TEXT로 읽어옴
			html_file = open(dfolder + '/html_file_funmom.html', 'w', encoding="UTF-8")
			html_file.write(memo_list)
			html_file.close()
			page = open(dfolder + '/html_file_funmom.html', 'rt', encoding='utf-8').read()
			soup = bs(page, 'html.parser')
			#all_text = soup.text
			ex_id_divs = soup.find_all("img")
			for img in ex_id_divs:
				urls.append(img)
			thisdata = cleanText(title)
			jpeg_no = 00
			for url in urls:
				last_url = url
				filename=thisdata + "-" + str(jpeg_no+1).zfill(3) + ".jpg"
				add_c(title, category, category2, link, last_url, filename)
				jpeg_no += 1
			
	con = sqlite3.connect(sub2db + '/funmom.db',timeout=60)
	con.row_factory = sqlite3.Row
	cur = con.cursor()
	sql = "select * from funmom where complte = ?"
	cur.execute(sql,('False',))
	row = cur.fetchall()	
	for i in row:
		id = i['ID']
		title = i['title']
		category = i['category']
		category2 = i['category2']
		urltitle = i['urltitle']
		image_url = i['image_url']
		image_file = i['image_file']
		complte = i['complte']
		if complte == 'True':
			continue
		else:
			if platform.system() == 'Windows':
				at = os.path.splitdrive(os.getcwd())
				root = at[0] + '/data'
			else:
				root = '/data'

			dfolder = root + '/funmom'
			url_to_image(image_url, dfolder, category, category2, image_file)
			add_d(id, image_url)
	logger.info('펀맘 알림완료')	
	try:
		con = sqlite3.connect(sub2db + '/funmom.db',timeout=60)
		con.execute('VACUUM')
		con.commit()
		logger.info('DB최적화를 진행하였습니다.')
	except:
		con.rollback()	
	finally:	
		con.close()	
	
	comp = '완료'
	return comp
	
@bp2.route('funmom')
def funmom():
	#데이타베이스 없으면 생성
	con = sqlite3.connect(sub2db + '/telegram.db',timeout=60)
	con.execute('CREATE TABLE IF NOT EXISTS funmom (start_time TEXT)')
	con.execute("PRAGMA cache_size = 10000")
	con.execute("PRAGMA locking_mode = NORMAL")
	con.execute("PRAGMA temp_store = MEMORY")
	con.execute("PRAGMA auto_vacuum = 1")
	con.execute("PRAGMA journal_mode=WAL")
	con.execute("PRAGMA synchronous=NORMAL")
	con.close()
	if not session.get('logFlag'):
		return redirect(url_for('main.index'))
	else:	
		con = sqlite3.connect(sub2db + '/telegram.db',timeout=60)
		con.row_factory = sqlite3.Row
		cur = con.cursor()
		cur.execute("select * from funmom")
		rows = cur.fetchone()
		if rows:
			start_time = rows['start_time']
		else:
			start_time = '*/1 * * * *'
		rows = []
		con = sqlite3.connect(sub2db + '/funmom.db',timeout=60)
		con.row_factory = sqlite3.Row
		cur = con.cursor()
		try:
			cur.execute("select * from funmom where complte = 'False'")
			rows1 = cur.fetchall()
			count = 1
			for i in rows1:
				i = count
				count += 1
			rows.append(i)
		except:
			i = '0'
			rows.append(i)
		try:
			count2 = 1
			cur.execute("select * from funmom where complte = 'True'")
			rows2 = cur.fetchall()
			for i2 in rows2:
				i2 = count2
				count2 += 1
			rows.append(i2)
		except:	
			i2 = '0'	
			rows.append(i2)
		return render_template('funmom.html', rows = rows, start_time = start_time)

@bp2.route('funmom_ok', methods=['POST'])
def funmom_ok():
	if not session.get('logFlag'):
		return redirect(url_for('main.index'))
	else:
		start_time = request.form['start_time']
		startname = request.form['startname']
		now = request.form['now']
		conn = sqlite3.connect(sub2db + '/telegram.db',timeout=60)
		cursor = conn.cursor()
		cursor.execute("select * from funmom")
		rows = cursor.fetchone()
		if rows:
			sql = """
				update funmom
					set start_time = ?
			"""
		else:
			sql = """
				INSERT INTO funmom 
				(start_time) VALUES (?)
			"""
		
		cursor.execute(sql, (start_time,))
		conn.commit()
		cursor.close()
		conn.close()
		try:
			if now == 'True':
				scheduler.add_job(funmom_start, trigger=CronTrigger.from_crontab(start_time), id=startname, args=[startname])
				test = scheduler.get_job(startname).id
			else:
				funmom_start(startname)
			logger.info('%s 를 스케줄러에 추가하였습니다.', test)
		except:
			pass
		
		return redirect(url_for('sub2.funmom'))


#뉴스알림		
def addnews(news_name, title, memo, link):
	#SQLITE3 DB 없으면 만들다.
	mytime = mydate()
	con = sqlite3.connect(sub2db + '/news_' + mytime + '.db',timeout=60)
	con.execute('CREATE TABLE IF NOT EXISTS news (NEWS_NAME TEXT, TITLE TEXT, MEMO TEXT, URL TEXT,COMPLETE TEXT)')
	con.execute("PRAGMA synchronous = OFF")
	con.execute("PRAGMA journal_mode = MEMORY")
	con.execute("PRAGMA cache_size = 10000")
	con.execute("PRAGMA locking_mode = EXCLUSIVE")
	con.execute("PRAGMA temp_store = MEMORY")
	con.execute("PRAGMA auto_vacuum = 1")
	con.close()	
	#데이터베이스 컬럼 추가하기
	con = sqlite3.connect(sub2db + '/news_' + mytime + '.db',timeout=60)
	cur = con.cursor()
	sql = "SELECT sql FROM sqlite_master WHERE name='news' AND sql LIKE '%NEWS_NAME%'"
	cur.execute(sql)
	rows = cur.fetchall()
	if len(rows) == 0:
		sql = "alter table news add column NEWS_NAME TEXT"
		cur.execute(sql)
	else:
		pass
	con = sqlite3.connect(sub2db + '/news_' + mytime + '.db',timeout=60)
	cur = con.cursor()
	sql = 'select * from news where TITLE = ? and MEMO = ? and NEWS_NAME = ?'
	cur.execute(sql, (title,memo,news_name))
	row = cur.fetchone()
	if row != None:
		pass
	else:
		try:
			COMPLETE = 'False'
			cur.execute('INSERT OR REPLACE INTO news (NEWS_NAME, TITLE, MEMO, URL, COMPLETE) VALUES (?,?,?,?,?)', (news_name, title, memo, link, COMPLETE))
			con.commit()	
		except:
			con.rollback()
		finally:
			con.close()		

def addnews_d(title, memo, news_name ):
	try:
		#마지막 실행까지 작업안했던 결과물 저장
		mytime = mydate()
		con = sqlite3.connect(sub2db + '/news_' + mytime + '.db',timeout=60)
		cur = con.cursor()
		sql = 'UPDATE news SET COMPLETE = ? WHERE TITLE = ? AND MEMO = ? AND NEWS_NAME = ?'
		cur.execute(sql,('True',title, memo,news_name))
		con.commit()
	except:
		con.rollback()
	finally:
		con.close()
		
def cleanText_uniti(readData):
	test = readData.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&').replace('&quot;', '“').replace('&#035;', '#').replace('&#039;', '‘').replace('&nbsp;', ' ').replace('&hellip;', '…').replace('&middot;', '·').replace('&lsquo;', '‘').replace('&rsquo;', '’')
	return test
	
def get_data(url):
    try:
        res = requests.get(url)
        html = res.text
        data = feedparser.parse(html)
        return data
    except:
        return None
		
def newsalim_start(telgm,telgm_alim,telgm_token,telgm_botid, start_time2, end_time):
	logger.info('뉴스알림시작')
	url = [
		'https://www.yonhapnewstv.co.kr/category/news/headline/feed/',
		'https://www.yonhapnewstv.co.kr/browse/feed/',
		'http://www.yonhapnewstv.co.kr/category/news/politics/feed/',
		'http://www.yonhapnewstv.co.kr/category/news/economy/feed/',
		'http://www.yonhapnewstv.co.kr/category/news/society/feed/',
		'http://www.yonhapnewstv.co.kr/category/news/local/feed/',
		'http://www.yonhapnewstv.co.kr/category/news/international/feed/',
		'http://www.yonhapnewstv.co.kr/category/news/culture/feed/',
		'http://www.yonhapnewstv.co.kr/category/news/sports/feed/',
		'http://www.yonhapnewstv.co.kr/category/news/weather/feed/',
		'http://www.khan.co.kr/rss/rssdata/total_news.xml',
		'http://rss.nocutnews.co.kr/nocutnews.xml',
		'http://rss.donga.com/total.xml',
		'http://rss.nocutnews.co.kr/nocutnews.xml',
		'http://www.mediatoday.co.kr/rss/allArticle.xml',
		'http://biz.heraldm.com/rss/010000000000.xml',
		'http://www.newsdaily.kr/rss/allArticle.xml',
		'https://news.sbs.co.kr/news/SectionRssFeed.do?sectionId=01&plink=RSSREADER',
		'https://news.sbs.co.kr/news/SectionRssFeed.do?sectionId=02&plink=RSSREADER',
		'https://news.sbs.co.kr/news/SectionRssFeed.do?sectionId=03&plink=RSSREADER',
		'https://news.sbs.co.kr/news/SectionRssFeed.do?sectionId=07&plink=RSSREADER',
		'https://news.sbs.co.kr/news/SectionRssFeed.do?sectionId=08&plink=RSSREADER',
		'https://news.sbs.co.kr/news/SectionRssFeed.do?sectionId=14&plink=RSSREADER',
		'https://news.sbs.co.kr/news/SectionRssFeed.do?sectionId=09&plink=RSSREADER',
		]
	for i in url:
		parsed_data = get_data(i)
		try:
			news_name = parsed_data['feed']['title']
		except:
			continue
		count = len(parsed_data['entries'])
		for i in range(count):
			article = parsed_data['entries'][i]
			try:
				title = article['title']
			except:
				continue
			link = article['link']
			if 'yonhapnewstv' in link:
				memo_list = article['content']
			else:
				memo_list = article['description']
			for i in memo_list:
				
				try:
					memo = i['value']
				except:
					memo = memo_list
			addnews(news_name, title, memo, link)
	#알림시작
	mytime = mydate()
	con = sqlite3.connect(sub2db + '/news_' + mytime + '.db',timeout=60)
	con.row_factory = sqlite3.Row
	cur = con.cursor()	
	sql = 'select * from news where COMPLETE = ?'
	cur.execute(sql, ('False', ))
	rows = cur.fetchall()
	
	#DB의 정보를 읽어옵니다.
	for row in rows:
		title = row['TITLE']
		memo = row['MEMO']
		text = re.sub('<.+?>', '', memo, 0, re.I|re.S)
		last_memo = unescape(text)
		news_name = row['NEWS_NAME']
		msg = '{}\n{}'.format(title,last_memo)
		tel(telgm,telgm_alim,telgm_token,telgm_botid,msg,start_time2,end_time)
		#중복 알림에거
		addnews_d(title, memo, news_name)
	con.close()	
	logger.info('뉴스 알림완료')	
	comp = '완료'
	return comp

	
@bp2.route('news')
def news():
	#데이타베이스 없으면 생성
	con = sqlite3.connect(sub2db + '/telegram.db',timeout=60)
	con.execute('CREATE TABLE IF NOT EXISTS news (telgm_token TEXT, telgm_botid TEXT, start_time TEXT, telgm TEXT, telgm_alim TEXT)')
	con.execute("PRAGMA cache_size = 10000")
	con.execute("PRAGMA locking_mode = NORMAL")
	con.execute("PRAGMA temp_store = MEMORY")
	con.execute("PRAGMA auto_vacuum = 1")
	con.execute("PRAGMA journal_mode=WAL")
	con.execute("PRAGMA synchronous=NORMAL")
	con.close()
	con = sqlite3.connect(sub2db + '/telegram.db',timeout=60)
	con.row_factory = sqlite3.Row
	cur = con.cursor()
	sql = "SELECT sql FROM sqlite_master WHERE name='news' AND sql LIKE '%start_time2%'"
	cur.execute(sql)
	rows = cur.fetchall()
	if len(rows) == 0:
		sql = "alter table news add column start_time2 TEXT"
		cur.execute(sql)
	else:
		pass
	con.close()
	con = sqlite3.connect(sub2db + '/telegram.db',timeout=60)
	con.row_factory = sqlite3.Row
	cur = con.cursor()
	sql = "SELECT sql FROM sqlite_master WHERE name='news' AND sql LIKE '%end_time%'"
	cur.execute(sql)
	rows = cur.fetchall()
	if len(rows) == 0:
		sql = "alter table news add column end_time TEXT"
		cur.execute(sql)
	else:
		pass
	con.close()
	if not session.get('logFlag'):
		return redirect(url_for('main.index'))
	else:
		telgm_token = request.args.get('telgm_token')
		telgm_botid = request.args.get('telgm_botid')
		con = sqlite3.connect(sub2db + '/telegram.db',timeout=60)
		con.row_factory = sqlite3.Row
		cur = con.cursor()
		cur.execute("select * from news")
		rows = cur.fetchone()
		if rows:
			telgm_token = rows['telgm_token']
			telgm_botid = rows['telgm_botid']
			start_time = rows['start_time']
			telgm = rows['telgm']
			telgm_alim = rows['telgm_alim']
			start_time2 = rows['start_time2']
			end_time = rows['end_time']
		else:
			telgm_token='입력하세요'
			telgm_botid='입력하세요'
			start_time = '*/1 * * * *'
			telgm = 'False'
			telgm_alim = 'False'
			start_time2 = '10'
			end_time = '06'
		return render_template('news.html', telgm_token = telgm_token, telgm_botid = telgm_botid, start_time = start_time, telgm = telgm, telgm_alim = telgm_alim, start_time2 = start_time2, end_time = end_time)


@bp2.route('news_ok', methods=['POST'])
def news_ok():
	if not session.get('logFlag'):
		return redirect(url_for('main.index'))
	else:
		start_time = request.form['start_time']
		startname = request.form['startname']
		telgm = request.form['telgm']
		telgm_alim = request.form['telgm_alim']
		telgm_token = request.form['telgm_token']
		telgm_botid = request.form['telgm_botid']
		start_time2 = request.form['start_time2']
		end_time = request.form['end_time']
		now = request.form['now']
		conn = sqlite3.connect(sub2db + '/telegram.db',timeout=60)
		cursor = conn.cursor()
		cursor.execute("select * from news")
		rows = cursor.fetchone()
		if rows:
			sql = """
				update news
					set telgm_token = ?
					, telgm_botid = ?
					, start_time = ?
					, telgm = ?
					, telgm_alim = ?
					, start_time2 = ?
					, end_time = ?
			"""
		else:
			sql = """
				INSERT INTO news 
				(telgm_token, telgm_botid, start_time, telgm, telgm_alim, start_time2, end_time) VALUES (?, ?, ?, ?, ?, ?, ?)
			"""
		
		cursor.execute(sql, (telgm_token, telgm_botid, start_time, telgm, telgm_alim, start_time2, end_time))
		conn.commit()
		cursor.close()
		conn.close()
		try:
			if now == 'True':
				scheduler.add_job(newsalim_start, trigger=CronTrigger.from_crontab(start_time), id=startname, args=[telgm,telgm_alim,telgm_token,telgm_botid, start_time2, end_time])
				test = scheduler.get_job(startname).id
			else:
				newsalim_start(telgm,telgm_alim,telgm_token,telgm_botid, start_time2, end_time)
			logger.info('%s 를 스케줄러에 추가하였습니다.', test)
		except:
			pass
		return redirect(url_for('sub2.news'))
		
#뽐뿌알림
#DB 알리미
def hotdeal_add_go(title, memo_list, link):
	#SQLITE3 DB 없으면 만들다.
	con = sqlite3.connect(sub2db + '/hotdeal.db',timeout=60)
	con.execute('CREATE TABLE IF NOT EXISTS hotdeal (TITLE TEXT, URL TEXT, MEMO TEXT, COMPLTE TEXT)')
	con.execute("PRAGMA cache_size = 10000")
	con.execute("PRAGMA locking_mode = EXCLUSIVE")
	con.execute("PRAGMA temp_store = MEMORY")
	con.execute("PRAGMA auto_vacuum = 1")
	con.execute("PRAGMA journal_mode=WAL")
	con.execute("PRAGMA synchronous=NORMAL")
	con.close()
	
	try: #URL TEXT, SEL TEXT, SELNUM TEXT
		con = sqlite3.connect(sub2db + '/hotdeal.db',timeout=60)
		con.row_factory = sqlite3.Row
		cur = con.cursor()
		sql = "select * from hotdeal where TITLE = ? AND URL = ?"
		cur.execute(sql, (title,link))
		row = cur.fetchone()
		if row != None:
			pass
		else:
			cur.execute("INSERT OR REPLACE INTO hotdeal (TITLE, URL, MEMO, COMPLTE) VALUES (?,?,?,?)", (title , link, memo_list, 'False'))
			con.commit()
	except:
		con.rollback()	
	finally:
		con.close()
		
def hotdeal_add_go_d(title, memo_list, link):
	try:
		#마지막 실행까지 작업안했던 결과물 저장
		con = sqlite3.connect(sub2db + '/hotdeal.db',timeout=60)
		cur = con.cursor()
		sql = "select * from hotdeal where MEMO = ? and URL = ? AND TITLE = ?"
		cur.execute(sql, (memo_list,link,title))
		row = cur.fetchone()
		if row == None:
			pass
		else:
			sql = "UPDATE hotdeal SET COMPLTE = ? WHERE MEMO = ? and URL = ? and TITLE = ?"	
			cur.execute(sql,('True', memo_list,link,title))
			con.commit()
	except:
		con.rollback()	
	finally:	
		con.close()

def hotdeal_start(telgm,telgm_alim,telgm_token,telgm_botid,myalim, start_time2, end_time):
	url = [
		'http://www.ppomppu.co.kr/rss.php?id=ppomppu',
		'https://www.ppomppu.co.kr/rss.php?id=pmarket',
		'http://www.ppomppu.co.kr/rss.php?id=ppomppu4',
		]
	for i in url:
		parsed_data = get_data(i)
		try:
			news_name = parsed_data['feed']['title']
		except:
			continue
		count = len(parsed_data['entries'])
		for i in range(count):
			article = parsed_data['entries'][i]
			try:
				title = article['title']
			except:
				continue
			link = article['link']
			memo_list = article['description']
			hotdeal_add_go(title, memo_list, link)
			
	#알림
	con = sqlite3.connect(sub2db + '/hotdeal.db',timeout=60)
	con.row_factory = sqlite3.Row
	cur = con.cursor()
	sql = "select * from hotdeal where COMPLTE = ?"
	cur.execute(sql, ('False',))
	rows = cur.fetchall()
	if len(rows) != 0:
		for row in rows:
			TITLE = row['TITLE']
			MEMO = row['MEMO']
			URL = row['URL']
			check_len = myalim.split('|')
			check_alim = len(check_len)
			msg = '{}\n{}'.format(TITLE,URL)
			if check_alim == 0:
				pass
			elif check_alim > 0:
				for i in check_len:
					if i in msg:
						tel(telgm,telgm_alim,telgm_token,telgm_botid,msg, start_time2, end_time)
					hotdeal_add_go_d(TITLE, MEMO, URL)


@bp2.route('hotdeal')
def hotdeal():
	#데이타베이스 없으면 생성
	con = sqlite3.connect(sub2db + '/telegram.db',timeout=60)
	con.execute('CREATE TABLE IF NOT EXISTS hotdeal (telgm_token TEXT, telgm_botid TEXT, start_time TEXT, telgm TEXT, telgm_alim TEXT, myalim TEXT, start_time2 TEXT, end_time TEXT)')
	con.execute("PRAGMA cache_size = 10000")
	con.execute("PRAGMA locking_mode = NORMAL")
	con.execute("PRAGMA temp_store = MEMORY")
	con.execute("PRAGMA auto_vacuum = 1")
	con.execute("PRAGMA journal_mode=WAL")
	con.execute("PRAGMA synchronous=NORMAL")
	con.close()
	if not session.get('logFlag'):
		return redirect(url_for('main.index'))
	else:
		telgm_token = request.args.get('telgm_token')
		telgm_botid = request.args.get('telgm_botid')
		con = sqlite3.connect(sub2db + '/telegram.db',timeout=60)
		con.row_factory = sqlite3.Row
		cur = con.cursor()
		cur.execute("select * from hotdeal")
		rows = cur.fetchone()
		if rows:
			telgm_token = rows['telgm_token']
			telgm_botid = rows['telgm_botid']
			start_time = rows['start_time']
			telgm = rows['telgm']
			telgm_alim = rows['telgm_alim']
			myalim = rows['myalim']
			start_time2 = rows['start_time2']
			end_time = rows['end_time']
		else:
			telgm_token='입력하세요'
			telgm_botid='입력하세요'
			start_time = '*/1 * * * *'
			telgm = 'False'
			telgm_alim = 'False'
			myalim = '11번가,옥션'
			start_time2 = '10'
			end_time = '06'
		return render_template('hotdeal.html', telgm_token = telgm_token, telgm_botid = telgm_botid, start_time = start_time, telgm = telgm, telgm_alim = telgm_alim, myalim = myalim, start_time2 = start_time2, end_time = end_time)


@bp2.route('hotdeal_ok', methods=['POST'])
def hotdeal_ok():
	if not session.get('logFlag'):
		return redirect(url_for('main.index'))
	else:
		start_time = request.form['start_time']
		startname = request.form['startname']
		telgm = request.form['telgm']
		telgm_alim = request.form['telgm_alim']
		telgm_token = request.form['telgm_token']
		telgm_botid = request.form['telgm_botid']
		start_time2 = request.form['start_time2']
		end_time = request.form['end_time']
		myalim = request.form['myalim']
		now = request.form['now']
		conn = sqlite3.connect(sub2db + '/telegram.db',timeout=60)
		cursor = conn.cursor()
		cursor.execute("select * from hotdeal")
		rows = cursor.fetchone()
		if rows:
			sql = """
				update hotdeal
					set telgm_token = ?
					, telgm_botid = ?
					, start_time = ?
					, telgm = ?
					, telgm_alim = ?
					, myalim = ?
					, start_time2 = ?
					, end_time = ?
			"""
		else:
			sql = """
				INSERT INTO hotdeal 
				(telgm_token, telgm_botid, start_time, telgm, telgm_alim, myalim, start_time2, end_time) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
			"""
		
		cursor.execute(sql, (telgm_token, telgm_botid, start_time, telgm, telgm_alim, myalim, start_time2, end_time))
		conn.commit()
		cursor.close()
		conn.close()
		try:
			if now == 'True':
				scheduler.add_job(hotdeal_start, trigger=CronTrigger.from_crontab(start_time), id=startname, args=[telgm,telgm_alim,telgm_token,telgm_botid,myalim, start_time2, end_time])
				test = scheduler.get_job(startname).id
			else:
				hotdeal_start(telgm,telgm_alim,telgm_token,telgm_botid,myalim, start_time2, end_time)
			logger.info('%s 를 스케줄러에 추가하였습니다.', test)
		except:
			pass
		return redirect(url_for('sub2.hotdeal'))
