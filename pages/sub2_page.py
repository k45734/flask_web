#-*- coding: utf-8 -*-
import sys
try:
	reload(sys)
	sys.setdefaultencoding('utf-8')
except:
	pass
from flask import Flask, flash, redirect, render_template, request, session, abort, url_for, Blueprint
import os.path, json, os, re, time, logging, io, subprocess, platform, telegram, threading, sqlite3, random,urllib.request
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
from apscheduler.triggers.cron import CronTrigger

if platform.system() == 'Windows':
	at = os.path.splitdrive(os.getcwd())
	sub2db = at[0] + '/data'
else:
	sub2db = '/data'
	
bp2 = Blueprint('sub2', __name__, url_prefix='/sub2')
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

#텔레그램 에러 오류 해결??
#os.system('pip install urllib3==1.24.1')

def mydate():
	nowtime = time.localtime()
	mytime = "%04d-%02d-%02d" % (nowtime.tm_year, nowtime.tm_mon, nowtime.tm_mday)
	return mytime
	
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
	
#텔레그램 알림
def tel(telgm,telgm_alim,telgm_token,telgm_botid,text):
	if len(text) <= 4096:
		if telgm == 'True' :
			bot = telegram.Bot(token = telgm_token)
			if telgm_alim == 'True':
				try:
					bot.sendMessage(chat_id = telgm_botid, text=text, disable_notification=True)
				except ConnectTimeoutError:
					time.sleep(30)
					bot.sendMessage(chat_id = telgm_botid, text=text, disable_notification=True)
			else:
				try:
					bot.sendMessage(chat_id = telgm_botid, text=text, disable_notification=False)
				except ConnectTimeoutError:
					time.sleep(30)
					bot.sendMessage(chat_id = telgm_botid, text=text, disable_notification=False)
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
							bot.sendMessage(chat_id = telgm_botid, text=part, disable_notification=True)
						except ConnectTimeoutError:
							bot.sendMessage(chat_id = telgm_botid, text=part, disable_notification=True) 
					else :
						try:
							bot.sendMessage(chat_id = telgm_botid, text=part, disable_notification=False)
						except ConnectTimeoutError:
							time.sleep(30)
							bot.sendMessage(chat_id = telgm_botid, text=part, disable_notification=False)
					print(part)
				else:
					print(part)
			else: # 두번째 메시지부터 '(Continuing...)\n'을 앞에 붙여줍니다.
				if telgm == 'True' :
					bot = telegram.Bot(token = telgm_token)
					if telgm_alim == 'True':
						try:
							bot.sendMessage(chat_id = telgm_botid, text='(Continuing...)\n' + part, disable_notification=True)
						except ConnectTimeoutError:
							time.sleep(30)
							bot.sendMessage(chat_id = telgm_botid, text='(Continuing...)\n' + part, disable_notification=True) 
					else :
						try:
							bot.sendMessage(chat_id = telgm_botid, text='(Continuing...)\n' + part, disable_notification=False)
						except ConnectTimeoutError:
							time.sleep(30)
							bot.sendMessage(chat_id = telgm_botid, text='(Continuing...)\n' + part, disable_notification=False)
					print(part)
				else:
					print(part)
			#time.sleep(10)
			time.sleep(0.5)
	comp = '완료'
	return comp	

#텔레그램 알림
def tel_img(telgm,telgm_alim,telgm_token,telgm_botid,msg):
	if telgm == 'True' :
		bot = telegram.Bot(token = telgm_token)
		if telgm_alim == 'True':
			try:
				bot.send_photo(chat_id = telgm_botid, photo=open(msg,'rb'), disable_notification=True)
			except ConnectTimeoutError:
				time.sleep(30)
				bot.send_photo(chat_id = telgm_botid, photo=open(msg,'rb'), disable_notification=True)
		else:
			try:
				bot.send_photo(chat_id = telgm_botid, photo=open(msg,'rb'), disable_notification=False)
			except ConnectTimeoutError:
				time.sleep(30)
				bot.send_photo(chat_id = telgm_botid, photo=open(msg,'rb'), disable_notification=False)
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
	#con.execute("PRAGMA synchronous = OFF")
	#con.execute("PRAGMA journal_mode = MEMORY")
	con.execute("PRAGMA cache_size = 10000")
	#con.execute("PRAGMA locking_mode = EXCLUSIVE")
	con.execute("PRAGMA locking_mode = NORMAL")
	con.execute("PRAGMA temp_store = MEMORY")
	con.execute("PRAGMA auto_vacuum = 1")
	#con.execute("PRAGMA journal_mode=WAL")
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
			msg = {'시간':new_s,'상품위치':b,'현재상태':c, '상품상태':d}
			test.append(msg)				
		except:
			pass
	return test
	
#저장된 정보를 출력하여 나열하여 메모리에 저장한뒤 출력한다.
def ff(msg2, json_string,json_string2,json_string4,json_string5):
	msg = []
	for i in range(len(msg2)):
		a = msg2[i]['시간']
		b = msg2[i]['상품위치']
		c = msg2[i]['현재상태']
		d = msg2[i]['상품상태']
		#total = '{} {} {} {}'.format(a,b,c,d)
		total = '{}'.format(d)
		msg.append(total)
	return msg
#택배조회 확인
def track_url(url):
	try:
		request=urllib.request.Request(url,None) #The assembled request
		response = urllib.request.urlopen(request,timeout=3)		
	except:
		print('The server couldn\'t fulfill the request. %s'% url)     
	else:
		data = response.read()
		data = data.decode()     
		result = 0
		result = data.find('id')
		if result > 0:
			print ("Website is working fine %s "% url)
			return 9999
		return response.status
#택배조회 구동	
def tracking_start(telgm,telgm_alim,telgm_token,telgm_botid):
	logger.info('택배알림시작')
	url = []
	#SQLITE3 DB 없으면 만들다.
	con = sqlite3.connect(sub2db + '/delivery.db',timeout=60)
	con.execute('CREATE TABLE IF NOT EXISTS tracking (PARCEL TEXT, NUMBER TEXT, DATE TEXT,COMPLTE TEXT)')
	#con.execute("PRAGMA synchronous = OFF")
	#con.execute("PRAGMA journal_mode = MEMORY")
	con.execute("PRAGMA cache_size = 10000")
	#con.execute("PRAGMA locking_mode = EXCLUSIVE")
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
	for row in rows:
		carrier_id = row['PARCEL']
		track_id = row['NUMBER']	
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
				"USPS":"us.usps"
				}
		carrier = code[f'{carrier_id}']
		url_list = ["http://192.168.0.2:8085/carriers", "https://apis.tracker.delivery/carriers" ]
		for url2 in url_list:
			result = track_url(url2)
			if result == 9999:	
				#ttt = url2 + '/' +  carrier + '/tracks/' + track_id
				keys = ['url','carrier','track_id','carrier_id']
				values = [url2,carrier,track_id,carrier_id]
				dt = dict(zip(keys, values))
				url.append(dt)
				break
	h = {"Cache-Control": "no-cache",   "Pragma": "no-cache"}
	#with requests.Session() as s:
	for a in url:
		main_url = a['url']
		carrier = a['carrier']
		track_id = a['track_id']
		carrier_id = a['carrier_id']
		aa = main_url + '/' +  carrier + '/tracks/' + track_id
		url = requests.get(aa, headers=h)
		resp = url.json()
		print(resp)
		check = resp.get('from', None)
		
		if check == None:
			msg = '{} {} 송장번호가 없는거 같습니다.\n'.format(carrier_id,track_id)
			tel(telgm,telgm_alim,telgm_token,telgm_botid,msg)
		else:
			json_string = check.get("name", None) #누가 보냈냐			
			json_string2 = resp.get("to").get("name") #누가 받냐
			json_string3 = resp.get("state").get("text") #배송현재상태
			#json_string4 = resp.get("carrier").get("name") #택배사이름
			#json_string5 = resp.get("carrier").get("id") #택배사송장번호
			
			json_string_m = resp.get("progresses") #배송상황
			msg2 = flfl(json_string_m)
			gg = ff(msg2,json_string,json_string2,carrier_id,track_id)
			ms = '\n'.join(gg)
			msga = '================================\n보내는 사람 : {}\n받는 사람 : {}\n택배사 : {} {}\n{}\n================================'.format(json_string,json_string2,carrier_id,track_id,ms)
			if '배송완료' in msga :
				tracking_del_new(carrier_id,track_id)
			elif '배달 완료' in msga :
				tracking_del_new(carrier_id,track_id)
			elif '배달완료' in msga :
				tracking_del_new(carrier_id,track_id)
			else:
				pass
			tel(telgm,telgm_alim,telgm_token,telgm_botid,msga)
	logger.info('택배 알림완료')
	try:
		con = sqlite3.connect(sub2db + '/delivery.db',timeout=60)		
		con.execute('VACUUM')
		con.commit()
		logger.info('DB최적화를 진행하였습니다.')
	except:
		con.rollback()	
	finally:	
		con.close()	
	comp = '완료'
	return comp
	
@bp2.route('tracking')
def tracking():
	#데이타베이스 없으면 생성
	con = sqlite3.connect(sub2db + '/telegram.db',timeout=60)
	con.execute('CREATE TABLE IF NOT EXISTS tracking (telgm_token TEXT, telgm_botid TEXT, start_time TEXT, telgm TEXT, telgm_alim TEXT)')
	#con.execute("PRAGMA synchronous = OFF")
	#con.execute("PRAGMA journal_mode = MEMORY")
	con.execute("PRAGMA cache_size = 10000")
	#con.execute("PRAGMA locking_mode = EXCLUSIVE")
	con.execute("PRAGMA locking_mode = NORMAL")
	con.execute("PRAGMA temp_store = MEMORY")
	con.execute("PRAGMA auto_vacuum = 1")
	con.execute("PRAGMA journal_mode=WAL")
	con.execute("PRAGMA synchronous=NORMAL")
	con.close()
	#SQLITE3 DB 없으면 만들다.
	con = sqlite3.connect(sub2db + '/delivery.db',timeout=60)
	con.execute('CREATE TABLE IF NOT EXISTS tracking (PARCEL TEXT, NUMBER TEXT, DATE TEXT,COMPLTE TEXT)')
	#con.execute("PRAGMA synchronous = OFF")
	#con.execute("PRAGMA journal_mode = MEMORY")
	con.execute("PRAGMA cache_size = 10000")
	#con.execute("PRAGMA locking_mode = EXCLUSIVE")
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
		#con.execute("PRAGMA synchronous = OFF")
		#con.execute("PRAGMA journal_mode = MEMORY")
		con.execute("PRAGMA cache_size = 10000")
		#con.execute("PRAGMA locking_mode = EXCLUSIVE")
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
		else:
			telgm_token='입력하세요'
			telgm_botid='입력하세요'
			start_time = '*/1 * * * *'
			telgm = 'False'
			telgm_alim = 'False'
		view = []
		#알림
		con = sqlite3.connect(sub2db + '/delivery.db',timeout=60)
		#con.execute("PRAGMA synchronous = OFF")
		#con.execute("PRAGMA journal_mode = MEMORY")
		con.execute("PRAGMA cache_size = 10000")
		#con.execute("PRAGMA locking_mode = EXCLUSIVE")
		con.execute("PRAGMA locking_mode = NORMAL")
		con.execute("PRAGMA temp_store = MEMORY")
		con.execute("PRAGMA auto_vacuum = 1")
		con.execute("PRAGMA journal_mode=WAL")
		con.execute("PRAGMA synchronous=NORMAL")
		con.row_factory = sqlite3.Row
		cur = con.cursor()
		sql = "select * from tracking where COMPLTE = ?"
		cur.execute(sql, ('False',))
		rows = cur.fetchall()
		for row in rows:
			carrier_id = row['PARCEL']
			track_id = row['NUMBER']
			COMPETE = row['COMPLTE']
			if COMPETE == 'True':
				wow = '배송완료'
			else:
				wow = '배송중'
			keys = ['PARCEL','NUMBER','COMPLETE']
			values = [carrier_id, track_id, wow]
			dt = dict(zip(keys, values))
			view.append(dt)
		return render_template('tracking.html',view = view, telgm_token = telgm_token, telgm_botid = telgm_botid, start_time = start_time, telgm = telgm, telgm_alim = telgm_alim)

@bp2.route('tracking_add', methods=['POST'])
def tracking_add():
	mytime = mydate()
	#SQLITE3 DB 없으면 만들다.
	con = sqlite3.connect(sub2db + '/delivery.db',timeout=60)
	con.execute('CREATE TABLE IF NOT EXISTS tracking (PARCEL TEXT, NUMBER TEXT, DATE TEXT,COMPLTE TEXT)')
	#con.execute("PRAGMA synchronous = OFF")
	#con.execute("PRAGMA journal_mode = MEMORY")
	con.execute("PRAGMA cache_size = 10000")
	#con.execute("PRAGMA locking_mode = EXCLUSIVE")
	con.execute("PRAGMA locking_mode = NORMAL")
	con.execute("PRAGMA temp_store = MEMORY")
	con.execute("PRAGMA auto_vacuum = 1")
	con.execute("PRAGMA journal_mode=WAL")
	con.execute("PRAGMA synchronous=NORMAL")
	con.close()
	if not session.get('logFlag'):
		return redirect(url_for('main.index'))
	else:
		try:
			carrier_id = request.form['carrier_id']
			track_id = request.form['track_id']
			con = sqlite3.connect(sub2db + '/delivery.db',timeout=60)
			#con.execute("PRAGMA synchronous = OFF")
			#con.execute("PRAGMA journal_mode = MEMORY")
			con.execute("PRAGMA cache_size = 10000")
			#con.execute("PRAGMA locking_mode = EXCLUSIVE")
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
					INSERT OR REPLACE INTO tracking (PARCEL, NUMBER, DATE, COMPLTE) VALUES (?,?,?,?)
				"""
			cursor.execute(sql, (carrier_id, track_id,mytime,'False'))
			con.commit()
			cursor.close()
			con.close()
			msg = '택배사 {} 송장번호 {} 등록 완료'.format(carrier_id,track_id)
		except:
			pass
	return redirect(url_for('sub2.tracking'))

@bp2.route('tracking_one/<carrier_id>/<track_id>', methods=["GET"])
def tracking_one(carrier_id,track_id):
	#SQLITE3 DB 없으면 만들다.
	con = sqlite3.connect(sub2db + '/delivery.db',timeout=60)
	con.execute('CREATE TABLE IF NOT EXISTS tracking (PARCEL TEXT, NUMBER TEXT, DATE TEXT,COMPLTE TEXT)')
	#con.execute("PRAGMA synchronous = OFF")
	#con.execute("PRAGMA journal_mode = MEMORY")
	con.execute("PRAGMA cache_size = 10000")
	#con.execute("PRAGMA locking_mode = EXCLUSIVE")
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
		sql = "select * from tracking"
		cur.execute(sql,)
		rows = cur.fetchall()
		for i in rows:
			telgm_token = i['telgm_token']
			telgm_botid = i['telgm_botid']
			telgm = i['telgm']
			telgm_alim = i['telgm_alim']
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
				"USPS":"us.usps"
				}
		carrier = code[f'{carrier_id}']
		url_list = ["http://192.168.0.2:8085/carriers", "https://apis.tracker.delivery/carriers" ]
		for url2 in url_list:
			result = track_url(url2)
			if result == 9999:	
				#ttt = url2 + '/' +  carrier + '/tracks/' + track_id
				keys = ['url','carrier','track_id','carrier_id']
				values = [url2,carrier,track_id,carrier_id]
				dt = dict(zip(keys, values))
				url.append(dt)
				break
	h = {"Cache-Control": "no-cache",   "Pragma": "no-cache"}
	#with requests.Session() as s:
	for a in url:
		main_url = a['url']
		carrier = a['carrier']
		track_id = a['track_id']
		carrier_id = a['carrier_id']
		aa = main_url + '/' +  carrier + '/tracks/' + track_id
		url = requests.get(aa, headers=h)
		resp = url.json()
		print(resp)
		check = resp.get('from', None)
		
		if check == None:
			msg = '{} {} 송장번호가 없는거 같습니다.\n'.format(carrier_id,track_id)
			tel(telgm,telgm_alim,telgm_token,telgm_botid,msg)
		else:
			json_string = check.get("name", None) #누가 보냈냐			
			json_string2 = resp.get("to").get("name") #누가 받냐
			json_string3 = resp.get("state").get("text") #배송현재상태
			#json_string4 = resp.get("carrier").get("name") #택배사이름
			#json_string5 = resp.get("carrier").get("id") #택배사송장번호
			
			json_string_m = resp.get("progresses") #배송상황
			msg2 = flfl(json_string_m)
			gg = ff(msg2,json_string,json_string2,carrier_id,track_id)
			ms = '\n'.join(gg)
			msga = '================================\n보내는 사람 : {}\n받는 사람 : {}\n택배사 : {} {}\n{}\n================================'.format(json_string,json_string2,carrier_id,track_id,ms)
			if '배송완료' in msga :
				tracking_del_new(carrier_id,track_id)
			elif '배달 완료' in msga :
				tracking_del_new(carrier_id,track_id)
			elif '배달완료' in msga :
				tracking_del_new(carrier_id,track_id)
			else:
				pass
			tel(telgm,telgm_alim,telgm_token,telgm_botid,msga)
	logger.info('택배 알림완료')
	comp = '완료'
	return comp	
	
@bp2.route('tracking_del/<carrier_id>/<track_id>', methods=["GET"])
def tracking_del(carrier_id,track_id):
	#SQLITE3 DB 없으면 만들다.
	con = sqlite3.connect(sub2db + '/delivery.db',timeout=60)
	con.execute('CREATE TABLE IF NOT EXISTS tracking (PARCEL TEXT, NUMBER TEXT, DATE TEXT,COMPLTE TEXT)')
	#con.execute("PRAGMA synchronous = OFF")
	#con.execute("PRAGMA journal_mode = MEMORY")
	con.execute("PRAGMA cache_size = 10000")
	#con.execute("PRAGMA locking_mode = EXCLUSIVE")
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
		#con.execute("PRAGMA synchronous = OFF")
		#con.execute("PRAGMA journal_mode = MEMORY")
		con.execute("PRAGMA cache_size = 10000")
		#con.execute("PRAGMA locking_mode = EXCLUSIVE")
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

@bp2.route("track_api/<carrier_id>/<track_id>", methods=["GET"])
def track_api(carrier_id, track_id):
	print(carrier_id, track_id)
	mytime = mydate()
	try:
		#SQLITE3 DB 없으면 만들다.
		con = sqlite3.connect(sub2db + '/delivery.db',timeout=60)
		con.execute('CREATE TABLE IF NOT EXISTS tracking (PARCEL TEXT, NUMBER TEXT, DATE TEXT,COMPLTE TEXT)')
		#con.execute("PRAGMA synchronous = OFF")
		#con.execute("PRAGMA journal_mode = MEMORY")
		con.execute("PRAGMA cache_size = 10000")
		#con.execute("PRAGMA locking_mode = EXCLUSIVE")
		con.execute("PRAGMA locking_mode = NORMAL")
		con.execute("PRAGMA temp_store = MEMORY")
		con.execute("PRAGMA auto_vacuum = 1")
		con.execute("PRAGMA journal_mode=WAL")
		con.execute("PRAGMA synchronous=NORMAL")
		con.close()
		#carrier_id = request.form['carrier_id']
		#track_id = request.form['track_id']
		con = sqlite3.connect(sub2db + '/delivery.db',timeout=60)
		#con.execute("PRAGMA synchronous = OFF")
		#con.execute("PRAGMA journal_mode = MEMORY")
		con.execute("PRAGMA cache_size = 10000")
		#con.execute("PRAGMA locking_mode = EXCLUSIVE")
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
				INSERT OR REPLACE INTO tracking (PARCEL, NUMBER, DATE, COMPLTE) VALUES (?,?,?,?)
			"""
		cursor.execute(sql, (carrier_id, track_id,mytime,'False'))
		con.commit()
		cursor.close()
		con.close()
		msg = '택배사 {} 송장번호 {} 등록 완료'.format(carrier_id,track_id)
	except:
		msg = '택배사 {} 송장번호 {} 등록 실패'.format(carrier_id,track_id)
	
	return 	msg
	
@bp2.route('tracking_ok', methods=['POST'])
def tracking_ok():
	if not session.get('logFlag'):
		return redirect(url_for('main.index'))
	else:
		start_time = request.form['start_time']
		startname = request.form['startname']
		carrier_id = request.form['carrier_id']
		track_id = request.form['track_id']
		telgm = request.form['telgm']
		telgm_alim = request.form['telgm_alim']
		telgm_token = request.form['telgm_token']
		telgm_botid = request.form['telgm_botid']
		now = request.form['now']
		con = sqlite3.connect(sub2db + '/telegram.db',timeout=60)
		#con.execute("PRAGMA synchronous = OFF")
		#con.execute("PRAGMA journal_mode = MEMORY")
		con.execute("PRAGMA cache_size = 10000")
		#con.execute("PRAGMA locking_mode = EXCLUSIVE")
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
			"""
		else:
			sql = """
				INSERT INTO tracking 
				(telgm_token, telgm_botid, start_time, telgm, telgm_alim) VALUES (?, ?, ?, ?, ?)
			"""
		
		cursor.execute(sql, (telgm_token, telgm_botid, start_time, telgm, telgm_alim))
		con.commit()
		cursor.close()
		con.close()
		try:
			if now == 'True':
				scheduler.add_job(tracking_start, trigger=CronTrigger.from_crontab(start_time), id=startname, args=[telgm,telgm_alim,telgm_token,telgm_botid])
				test = scheduler.get_job(startname).id
			else:
				tracking_start(telgm,telgm_alim,telgm_token,telgm_botid)
			logger.info('%s 를 스케줄러에 추가하였습니다.', test)
		except:
			pass
		return redirect(url_for('sub2.tracking'))
	
#실동작	
def Typhoon():
	nowtime = time.localtime()
	newdate = "%04d-%02d-%02d_%02d시%02d분%02d초" % (nowtime.tm_year, nowtime.tm_mon, nowtime.tm_mday, nowtime.tm_hour, nowtime.tm_min, nowtime.tm_sec)
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
			filename = name.text + ".jpg"
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
	return [last,fifi,name]
		
def weather_start(location,telgm,telgm_alim,telgm_token,telgm_botid):
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
	big_region = resp['warn'][0]['region']
	big_efftsatus = resp['warn'][0]['efftsatus']
	big_efftsatus_pre = resp['warn'][0]['efftsatus_pre']
	msg2 = '{} {}\n\n* 해당 구역\n\n{}\n\n* 내용\n\n{}\n\n* 예비특보\n\n{}'.format(big_date,big_title,big_region,big_efftsatus,big_efftsatus_pre)
	try:
		msg4,filename,name = Typhoon()
		msg3 = " ".join(msg4)
		msg = '{}\n\n{}\n\n태풍 정보 ({})\n{}'.format(msg1,msg2,name.text,msg3)		
	except:
		msg = '{}\n\n{}'.format(msg1,msg2)
	tel(telgm,telgm_alim,telgm_token,telgm_botid,msg)
	try:
		tel_img(telgm,telgm_alim,telgm_token,telgm_botid,filename)
	except:
		pass
	logger.info('날씨 알림완료')
	comp = '완료'
	return comp	
	
@bp2.route('weather')
def weather():
	#데이타베이스 없으면 생성
	con = sqlite3.connect(sub2db + '/telegram.db',timeout=60)
	con.execute('CREATE TABLE IF NOT EXISTS weather (telgm_token TEXT, telgm_botid TEXT, start_time TEXT, telgm TEXT, telgm_alim TEXT)')
	#con.execute("PRAGMA synchronous = OFF")
	#con.execute("PRAGMA journal_mode = MEMORY")
	con.execute("PRAGMA cache_size = 10000")
	#con.execute("PRAGMA locking_mode = EXCLUSIVE")
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
		cur.execute("select * from weather")
		rows = cur.fetchone()
		if rows:
			telgm_token = rows['telgm_token']
			telgm_botid = rows['telgm_botid']
			start_time = rows['start_time']
			telgm = rows['telgm']
			telgm_alim = rows['telgm_alim']
		else:
			telgm_token='입력하세요'
			telgm_botid='입력하세요'
			start_time = '*/1 * * * *'
			telgm = 'False'
			telgm_alim = 'False'
		return render_template('weather.html', telgm_token = telgm_token, telgm_botid = telgm_botid, start_time = start_time, telgm = telgm, telgm_alim = telgm_alim)

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
		now = request.form['now']
		con = sqlite3.connect(sub2db + '/telegram.db',timeout=60)
		#con.execute("PRAGMA synchronous = OFF")
		#con.execute("PRAGMA journal_mode = MEMORY")
		con.execute("PRAGMA cache_size = 10000")
		#con.execute("PRAGMA locking_mode = EXCLUSIVE")
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
			"""
		else:
			sql = """
				INSERT INTO weather 
				(telgm_token, telgm_botid, start_time, telgm, telgm_alim) VALUES (?, ?, ?, ?, ?)
			"""
		
		cursor.execute(sql, (telgm_token, telgm_botid, start_time, telgm, telgm_alim))
		con.commit()
		cursor.close()
		con.close()
		try:
			if now == 'True':
				scheduler.add_job(weather_start, trigger=CronTrigger.from_crontab(start_time), id=startname, args=[location,telgm,telgm_alim,telgm_token,telgm_botid])
				test = scheduler.get_job(startname).id
			else:
				weather_start(location,telgm,telgm_alim,telgm_token,telgm_botid)
			logger.info('%s 를 스케줄러에 추가하였습니다.', test)
		except:
			pass
		return redirect(url_for('sub2.weather'))

#운세알리미
#운세알리미 DB
def add_unse(lastdate, zodiac, zodiac2, list, complte):
	try:
		con = sqlite3.connect(sub2db + '/unse.db',timeout=60)
		#con.execute("PRAGMA synchronous = OFF")
		#con.execute("PRAGMA journal_mode = MEMORY")
		con.execute("PRAGMA cache_size = 10000")
		#con.execute("PRAGMA locking_mode = EXCLUSIVE")
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
def add_unse_d(a, b, c, d, e):
	try:
		#마지막 실행까지 작업안했던 결과물 저장
		con = sqlite3.connect(sub2db + '/unse.db',timeout=60)
		#con.execute("PRAGMA synchronous = OFF")
		#con.execute("PRAGMA journal_mode = MEMORY")
		con.execute("PRAGMA cache_size = 10000")
		#con.execute("PRAGMA locking_mode = EXCLUSIVE")
		con.execute("PRAGMA locking_mode = NORMAL")
		con.execute("PRAGMA temp_store = MEMORY")
		con.execute("PRAGMA auto_vacuum = 1")
		con.execute("PRAGMA journal_mode=WAL")
		con.execute("PRAGMA synchronous=NORMAL")
		cur = con.cursor()
		sql = "select * from unse where DATE = ? AND ZODIAC2 = ? AND MEMO = ?"
		cur.execute(sql, (a, c, d))
		row = cur.fetchone()
		if row == None:
			print("해당 내용은 DB에 없습니다.")
		else:
			sql = "UPDATE unse SET COMPLTE = ? WHERE DATE = ? AND ZODIAC2 = ? AND MEMO = ?"	
			cur.execute(sql,('True', a, c, d))
			con.commit()
	except:
		con.rollback()	
	finally:	
		con.close()	
	comp = '완료'
	return comp	
def unse_start(telgm,telgm_alim,telgm_token,telgm_botid):
	try:
		logger.info('운세알림시작')
		#SQLITE3 DB 없으면 만들다.
		con = sqlite3.connect(sub2db + '/unse.db',timeout=60)
		con.execute('CREATE TABLE IF NOT EXISTS unse (DATE TEXT, ZODIAC TEXT, ZODIAC2 TEXT, MEMO TEXT, COMPLTE TEXT)')
		#con.execute("PRAGMA synchronous = OFF")
		#con.execute("PRAGMA journal_mode = MEMORY")
		con.execute("PRAGMA cache_size = 10000")
		#con.execute("PRAGMA locking_mode = EXCLUSIVE")
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
		count = 0
		for row in rows:
			timestr = time.strftime("%Y%m%d")
			a = row['DATE'] #생성날짜
			b = row['ZODIAC'] #띠
			c = row['ZODIAC2'] #띠별운세
			d = row['MEMO'] #띠별상세운세
			e = row['COMPLTE'] #완료여부
			msg = b + ' (' + c + ')\n' + d
			tel(telgm,telgm_alim,telgm_token,telgm_botid,msg)
			add_unse_d(a, b, c, d, e)
		logger.info('운세 알림완료')	
	except:
		pass
	try:
		con = sqlite3.connect(sub2db + '/unse.db',timeout=60)
		con.execute('VACUUM')
		con.commit()
		logger.info('DB최적화를 진행하였습니다.')
	except:
		con.rollback()	
	finally:	
		con.close()			
	comp = '완료'
	return comp
@bp2.route('unse')
def unse():
	#데이타베이스 없으면 생성
	con = sqlite3.connect(sub2db + '/telegram.db',timeout=60)
	con.execute('CREATE TABLE IF NOT EXISTS unse (telgm_token TEXT, telgm_botid TEXT, start_time TEXT, telgm TEXT, telgm_alim TEXT)')
	#con.execute("PRAGMA synchronous = OFF")
	#con.execute("PRAGMA journal_mode = MEMORY")
	con.execute("PRAGMA cache_size = 10000")
	#con.execute("PRAGMA locking_mode = EXCLUSIVE")
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
		cur.execute("select * from unse")
		rows = cur.fetchone()
		if rows:
			telgm_token = rows['telgm_token']
			telgm_botid = rows['telgm_botid']
			start_time = rows['start_time']
			telgm = rows['telgm']
			telgm_alim = rows['telgm_alim']
		else:
			telgm_token='입력하세요'
			telgm_botid='입력하세요'
			start_time = '*/1 * * * *'
			telgm = 'False'
			telgm_alim = 'False'
		return render_template('unse.html', telgm_token = telgm_token, telgm_botid = telgm_botid, start_time = start_time, telgm = telgm, telgm_alim = telgm_alim)


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
			"""
		else:
			sql = """
				INSERT INTO unse 
				(telgm_token, telgm_botid, start_time, telgm, telgm_alim) VALUES (?, ?, ?, ?, ?)
			"""
		
		cursor.execute(sql, (telgm_token, telgm_botid, start_time, telgm, telgm_alim))
		conn.commit()
		cursor.close()
		conn.close()
		try:
			if now == 'True':
				scheduler.add_job(unse_start, trigger=CronTrigger.from_crontab(start_time), id=startname, args=[telgm,telgm_alim,telgm_token,telgm_botid])
				test = scheduler.get_job(startname).id
			else:
				unse_start(telgm,telgm_alim,telgm_token,telgm_botid)
			logger.info('%s 를 스케줄러에 추가하였습니다.', test)
		except:
			pass
		return redirect(url_for('sub2.unse'))
	
#퀴즈정답알림
#DB 알리미
def quiz_add_go(title, memo_s, URL):
	try: #URL TEXT, SEL TEXT, SELNUM TEXT
		con = sqlite3.connect(sub2db + '/quiz.db',timeout=60)
		con.row_factory = sqlite3.Row
		cur = con.cursor()
		sql = "select * from quiz where URL = ? "
		cur.execute(sql, (URL,))
		row = cur.fetchone()
		if row != None:
			MEMO = row['MEMO']
			old_title = row['TITLE']
			if memo_s == MEMO and title == old_title:
				pass
			else:
				cur.execute("update quiz set MEMO = ?, COMPLTE = ?, TITLE = ? where URL = ? ",(memo_s,'False',title,URL))
				con.commit()
				logger.info('해당 내용은 DB에 있어서 %s %s -> %s %s 수정합니다.', old_title, MEMO, title, memo_s)
				#print("해당 내용은 DB에 있어서 {} {} -> {} {} 수정합니다.".format(old_title, MEMO, title, memo_s))
		else:
			cur.execute("INSERT OR REPLACE INTO quiz (TITLE, URL, MEMO, COMPLTE) VALUES (?,?,?,?)", (title, URL, memo_s, 'False'))
			con.commit()
	except:
		con.rollback()	
	finally:
		con.close()
	comp = '완료'
	return comp
#알리미 완료
def quiz_add_go_d(MEMO, URL):
	try:
		#마지막 실행까지 작업안했던 결과물 저장
		con = sqlite3.connect(sub2db + '/quiz.db',timeout=60)
		cur = con.cursor()
		sql = "select * from quiz where MEMO = ? and URL = ?"
		cur.execute(sql, (MEMO,URL))
		row = cur.fetchone()
		if row == None:
			pass
		else:
			sql = "UPDATE quiz SET COMPLTE = ? WHERE MEMO = ? and URL = ?"	
			cur.execute(sql,('True', MEMO,URL))
			con.commit()
	except:
		con.rollback()	
	finally:	
		con.close()
	comp = '완료'
	return comp	
def quiz_start(telgm,telgm_alim,telgm_token,telgm_botid):
	try:
		logger.info('퀴즈정답알림 시작')
		#퀴즈정답 시작후 10초후 작동시작
		time.sleep(10)
		#SQLITE3 DB 없으면 만들다.
		con = sqlite3.connect(sub2db + '/quiz.db',timeout=60)
		con.execute('CREATE TABLE IF NOT EXISTS quiz (TITLE TEXT, URL TEXT, MEMO TEXT, COMPLTE TEXT)')
		#con.execute("PRAGMA synchronous = OFF")
		#con.execute("PRAGMA journal_mode = MEMORY")
		con.execute("PRAGMA cache_size = 10000")
		con.execute("PRAGMA locking_mode = EXCLUSIVE")
		con.execute("PRAGMA temp_store = MEMORY")
		con.execute("PRAGMA auto_vacuum = 1")
		con.execute("PRAGMA journal_mode=WAL")
		con.execute("PRAGMA synchronous=NORMAL")
		con.close()
		list = []
		last = []
		URL = 'https://quizbang.tistory.com/m/entries.json?size=50'
		req = requests.get(URL).json()
		check = req['code']
		if check == 200:
			for p in range(0,1):
				URL = 'https://quizbang.tistory.com/m/entries.json?size=50&page=' + str(p)
				req = requests.get(URL).json()
				page = req['result']['nextPage']
				list_r = req['result']['items']
				if page == None:
					break
				else:
					for i in list_r:
						title_n = i['title']
						#all_text = i['summary']
						url = i['path']
						keys = ['TITLE','URL']
						values = [title_n, url]
						dt = dict(zip(keys, values))
						list.append(dt)
		else:
			print('종료')
			pass
		for i in list:
			list_url = i['URL']
			title = i['TITLE']
			with requests.Session() as s:
				header = {"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5)\AppleWebKit 537.36 (KHTML, like Gecko) Chrome","Accept":"text/html,application/xhtml+xml,application/xml;\q=0.9,imgwebp,*/*;q=0.8"}				
				URL = 'https://quizbang.tistory.com' + list_url
				req = urllib.request.urlopen(URL).read()
				soup = bs(req, 'html.parser')
				all_text2 = soup.text
				all_text = soup.find('div',{'class':'blogview_content useless_p_margin editor_ke'}).text
				result_remove_all = re.sub(r"\s", " ", all_text)
				if '오퀴즈' in title:
					p = re.compile('Liiv Mate 앱내에서도 잠금화면\/보 고쌓기\(안드(.*?)\[')
				elif '캐시워크' in title:
					p = re.compile('Liiv Mate 앱내에서도 잠금화면\/보 (.*?)\[')
				elif '홈플러스' in title:
					p = re.compile('Lii14v Mate 앱내에서도 잠금화면(.*?)\[')
				elif '신한' in title:
					p = re.compile('Liiv Mate 앱내에서도 잠금화면\/보 고쌓기\(안드로이(.*?)\[')
				elif '리브메이트' in title:
					p1 = re.compile('Liiv Mate 앱내에서도 잠금화면\/보고쌓기\(안드로이 (.*?)\[')
					check = p1.findall(result_remove_all)
					if len(check) == 0:
						#print(result_remove_all)
						p = re.compile('●(.*?)\[')
					else:
						p = re.compile('Liiv Mate 앱내에서도 잠금화면\/보고쌓기\(안드로이 (.*?)\[')
				elif '토스' in title:
					p = re.compile('퀴즈가 안보이면 업데이트 해주세요.\)   로 (.*?) \[')
				elif '우리WON멤버스' in title:
					p1 = re.compile('Liiv Mate 앱내에서도 잠금화면\/보고쌓기\(안드로이 퀴즈\)(.*?)\[')
					check = p1.findall(result_remove_all)
					if len(check) == 0:
						p = re.compile('Liiv Mate 앱내에서도 잠금화면\/보고쌓기\(안드로이 (.*?)\[')
					else:
						p = re.compile('Liiv Mate 앱내에서도 잠금화면\/보고쌓기\(안드로이 퀴즈\)(.*?)\[')
				else:	
					p = re.compile('정답 :(.*?)\[')
				memo = p.findall(result_remove_all)
				memo_check = ''.join(memo).lstrip()
				if 'Liiv Mate' in memo_check:
					memo_s = memo_check.replace('는 지속적으로 확대할 예정입니다. - Liiv Mate 앱내에서도 잠금화면/보 고쌓기(안드로이 ', '')
				else:
					memo_s = ''.join(memo).lstrip()
				if '됩니다.' in memo_s :
					pass
				elif len(memo_s) == 0 :
					pass
				else:
					keys = ['TITLE','MEMO', 'URL']
					values = [title, memo_s, URL]
					dt = dict(zip(keys, values))
					last.append(dt)
					
		for ii in last:
			title = ii['TITLE']
			memo_s = ii['MEMO']
			URL = ii['URL']
			quiz_add_go(title, memo_s, URL)		
		lllast = []		
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
				msg = '{}\n정답 : {}'.format(TITLE,MEMO)
				tel(telgm,telgm_alim,telgm_token,telgm_botid,msg)
				quiz_add_go_d(MEMO, URL)
			logger.info('퀴즈정답 완료했습니다.')
		else:
			logger.info('퀴즈정답 신규내용이 없습니다.')
			pass
		con.close()
	except:	
		pass
	
	comp = '완료'
	return comp		
@bp2.route('quiz')
def quiz():
	#데이타베이스 없으면 생성
	con = sqlite3.connect(sub2db + '/telegram.db',timeout=60)
	con.execute('CREATE TABLE IF NOT EXISTS quiz (telgm_token TEXT, telgm_botid TEXT, start_time TEXT, telgm TEXT, telgm_alim TEXT)')
	#con.execute("PRAGMA synchronous = OFF")
	#con.execute("PRAGMA journal_mode = MEMORY")
	con.execute("PRAGMA cache_size = 10000")
	#con.execute("PRAGMA locking_mode = EXCLUSIVE")
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
		cur.execute("select * from quiz")
		rows = cur.fetchone()
		if rows:
			telgm_token = rows['telgm_token']
			telgm_botid = rows['telgm_botid']
			start_time = rows['start_time']
			telgm = rows['telgm']
			telgm_alim = rows['telgm_alim']
		else:
			telgm_token='입력하세요'
			telgm_botid='입력하세요'
			start_time = '*/1 * * * *'
			telgm = 'False'
			telgm_alim = 'False'
		return render_template('quiz.html', telgm_token = telgm_token, telgm_botid = telgm_botid, start_time = start_time, telgm = telgm, telgm_alim = telgm_alim)


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
			"""
		else:
			sql = """
				INSERT INTO quiz 
				(telgm_token, telgm_botid, start_time, telgm, telgm_alim) VALUES (?, ?, ?, ?, ?)
			"""
		
		cursor.execute(sql, (telgm_token, telgm_botid, start_time, telgm, telgm_alim))
		conn.commit()
		cursor.close()
		conn.close()
		try:
			if now == 'True':
				scheduler.add_job(quiz_start, trigger=CronTrigger.from_crontab(start_time), id=startname, args=[telgm,telgm_alim,telgm_token,telgm_botid])
				test = scheduler.get_job(startname).id
			else:
				quiz_start(telgm,telgm_alim,telgm_token,telgm_botid)
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
	#con.execute("PRAGMA synchronous = OFF")
	#con.execute("PRAGMA journal_mode = MEMORY")
	con.execute("PRAGMA cache_size = 10000")
	#con.execute("PRAGMA locking_mode = EXCLUSIVE")
	con.execute("PRAGMA locking_mode = NORMAL")
	con.execute("PRAGMA temp_store = MEMORY")
	con.execute("PRAGMA auto_vacuum = 1")
	con.execute("PRAGMA journal_mode=WAL")
	con.execute("PRAGMA synchronous=NORMAL")
	con.close()
	list = []
	last = []	
	URL = 'https://funmom.tistory.com/m/entries.json?size=50'
	req = requests.get(URL).json()
	check = req['code']
	if check == 200:
		#page = req['result']['nextPage'] #?page=0&size=10
		for p in range(0,100000):
			URL = 'https://funmom.tistory.com/m/entries.json?size=50&page=' + str(p)
			req = requests.get(URL).json()
			page = req['result']['nextPage']
			list_r = req['result']['items']
			if page == None:
				break
			else:
				for i in list_r:
					title_n = i['title']
					#all_text = i['summary']
					url = i['path']
					keys = ['TITLE','URL']
					values = [title_n, url]
					dt = dict(zip(keys, values))
					list.append(dt)
	else:
		print('종료')
		pass
	for i in list:
		list_url = i['URL']
		title = i['TITLE']
		URL = 'https://funmom.tistory.com' + list_url
		req = urllib.request.urlopen(URL).read()
		soup = bs(req, 'html.parser')
		menu = soup.find(attrs={'class' :'inner_g'}).text #카테고리 이름 div class="list_tag"
		last_c = menu.split('/')
		category = last_c[0]
		category2 = last_c[1]
		thisdata = cleanText(title)
		ex_id_divs = soup.find_all(attrs={'class' : ["imageblock alignCenter","imageblock"]})
		urls = []
		for img in ex_id_divs:
			img_url = img.find("img")
			url1 = str(img_url["src"])
			url2 = str(img_url["srcset"])
			dt = [url1, url2]
			urls.append(dt)
		
		jpeg_no = 00
		for url in urls:
			last_url = ' '.join(url)
			filename=thisdata + "-" + str(jpeg_no+1).zfill(3) + ".jpg"
			add_c(title, category, category2, list_url, last_url, filename)
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
	#con.execute("PRAGMA synchronous = OFF")
	#con.execute("PRAGMA journal_mode = MEMORY")
	con.execute("PRAGMA cache_size = 10000")
	#con.execute("PRAGMA locking_mode = EXCLUSIVE")
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
def addnews(CAST, TITLE, URL, MEMO, newdate, COMPLETE):
	try:
		#SQLITE3 DB 없으면 만들다.
		con = sqlite3.connect(sub2db + '/news.db',timeout=60)
		con.execute('CREATE TABLE IF NOT EXISTS ' + CAST + ' (CAST TEXT, TITLE TEXT, URL TEXT, MEMO TEXT, DATE TEXT, COMPLETE TEXT)')	
		#con.execute("PRAGMA synchronous = OFF")
		#con.execute("PRAGMA journal_mode = MEMORY")
		con.execute("PRAGMA cache_size = 10000")
		#con.execute("PRAGMA locking_mode = EXCLUSIVE")
		con.execute("PRAGMA locking_mode = NORMAL")
		con.execute("PRAGMA temp_store = MEMORY")
		con.execute("PRAGMA auto_vacuum = 1")
		con.execute("PRAGMA journal_mode=WAL")
		con.execute("PRAGMA synchronous=NORMAL")
		con.close()	
		time.sleep(2)
		con = sqlite3.connect(sub2db + '/news.db',timeout=60)
		#con.execute("PRAGMA synchronous = OFF")
		#con.execute("PRAGMA journal_mode = MEMORY")
		con.execute("PRAGMA cache_size = 10000")
		#con.execute("PRAGMA locking_mode = EXCLUSIVE")
		con.execute("PRAGMA locking_mode = NORMAL")
		con.execute("PRAGMA temp_store = MEMORY")
		con.execute("PRAGMA auto_vacuum = 1")
		con.execute("PRAGMA journal_mode=WAL")
		con.execute("PRAGMA synchronous=NORMAL")
		cur = con.cursor()
		sql = 'select * from ' + CAST + ' where TITLE = ? and URL = ?'
		cur.execute(sql, (TITLE,URL))
		row = cur.fetchone()
		if row != None:
			pass
		else:
			cur.execute('INSERT OR REPLACE INTO ' + CAST + ' (CAST, TITLE, URL, MEMO, DATE,COMPLETE) VALUES (?,?,?,?,?,?)', (CAST, TITLE, URL, MEMO, newdate, COMPLETE))
			con.commit()
	except:
		con.rollback()
	finally:
		con.close()	
	comp = '완료'
	return comp
		
def addnews_d(CAST,TITLE,URL):
	try:
		#마지막 실행까지 작업안했던 결과물 저장
		time.sleep(2)
		con = sqlite3.connect(sub2db + '/news.db',timeout=60)
		#con.execute("PRAGMA synchronous = OFF")
		#con.execute("PRAGMA journal_mode = MEMORY")
		con.execute("PRAGMA cache_size = 10000")
		#con.execute("PRAGMA locking_mode = EXCLUSIVE")
		con.execute("PRAGMA locking_mode = NORMAL")
		con.execute("PRAGMA temp_store = MEMORY")
		con.execute("PRAGMA auto_vacuum = 1")
		con.execute("PRAGMA journal_mode=WAL")
		con.execute("PRAGMA synchronous=NORMAL")
		cur = con.cursor()
		sql = 'UPDATE ' + CAST + ' SET COMPLETE = ? WHERE TITLE = ? AND URL = ?'
		cur.execute(sql,('True',TITLE, URL))
		con.commit()
	except:
		con.rollback()
	finally:	
		con.close()	
	comp = '완료'
	return comp

def vietnews(newdate):
	header = {"User-Agent":"Mozilla/5.0 (Linux; Android 8.0.0; SM-G955U Build/R16NW) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Mobile Safari/537.36","Accept":"text/html,application/xhtml+xml,application/xml;\q=0.9,imgwebp,*/*;q=0.8"}
	URL = 'https://www.vinatimes.net/news'
	req = requests.get(URL,headers=header)	
	bs0bj = bs(req.content.decode('utf-8','replace'),'html.parser')
	posts = bs0bj.findAll("div",{"class":"list_title"})
	for test in posts:
		if 'https://www.vinatimes.net/notice/461808' in test.a['href']:
			pass
		elif 'https://www.vinatimes.net/notice/456598' in test.a['href']:
			pass 
		elif 'https://www.vinatimes.net/notice/454369' in test.a['href']:
			pass
		else:
			URL = test.a['href']
			req = requests.get(URL,headers=header)
			bs0bj = bs(req.content.decode('utf-8','replace'),'html.parser')
			ttitle = bs0bj.find("h1")
			posts = bs0bj.find('div',{'class':'xe_content'})
			MEMO2 = posts.text.strip()
			MEMO3 = MEMO2.replace('  ','\n')
			MEMO = MEMO3.replace("\n", "")
			TITLE = ttitle.text.strip()
			CAST = "VIET"
			COMPLETE = 'False'
			addnews(CAST, TITLE, URL, MEMO, newdate, COMPLETE)	

	logger.info('VIET 목록완료')
	return CAST
		
def ytnsnews(newdate):
	with requests.Session() as s:
		header = {"User-Agent":"Mozilla/5.0 (Linux; Android 8.0.0; SM-G955U Build/R16NW) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Mobile Safari/537.36","Accept":"text/html,application/xhtml+xml,application/xml;\q=0.9,imgwebp,*/*;q=0.8"}
		MAIN = 'https://m.ytn.co.kr/newslist/news_list.php?s_mcd=9999'
		req = s.get(MAIN,headers=header)
		bs0bj = bs(req.content.decode('utf-8','replace'),'html.parser')
		posts = bs0bj.findAll("a",{"class":"news_list"})	
		for i in posts:
			URL = i['href']
			req = s.get(URL,headers=header)
			bs0bj = bs(req.content.decode('utf-8','replace'),'html.parser')
			ttitle = bs0bj.find("h1",{"id":"h1"})
			post = bs0bj.find('div',{'id':'article_content_text'})	
			movie = bs0bj.findAll('iframe',{'id':'zumFrame'})
			TITLE = ttitle.text.strip()
			MEMO = post.text.strip()
			CAST = "YTN"
			COMPLETE = 'False'
			addnews(CAST, TITLE, URL, MEMO, newdate, COMPLETE)
	logger.info('YTN 목록완료')
	return CAST
		
def esbsnews(newdate):
	with requests.Session() as s:
		header = {"User-Agent":"Mozilla/5.0 (Linux; Android 8.0.0; SM-G955U Build/R16NW) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Mobile Safari/537.36","Accept":"text/html,application/xhtml+xml,application/xml;\q=0.9,imgwebp,*/*;q=0.8"}
		URL = 'https://mnews.sbs.co.kr/news/newsMain.do'
		req = s.get(URL,headers=header)
		bs0bj = bs(req.content.decode('utf-8','replace'),'html.parser')
		lists = bs0bj.select('ul > li > a')
		for i in lists:
			check = i.attrs['href']
			print(check)
			if 'endPage.do' not in check:
				pass
			else:
				URL = 'https://mnews.sbs.co.kr/news/' + i.attrs['href']
				req = s.get(URL,headers=header)
				bs0bj = bs(req.content.decode('utf-8','replace'),'html.parser')
				ttitle = bs0bj.select('#subTitleText')
				posts = bs0bj.select('#contentText')
				TITLE = ttitle[0].text.strip()
				MEMO = posts[0].text.strip()
				CAST = "SBS"
				COMPLETE = 'False'
				addnews(CAST, TITLE, URL, MEMO, newdate, COMPLETE)
	logger.info('SBS 목록완료')
	return CAST
	
def ekbsnews(newdate):
	with requests.Session() as s:
		header = {"User-Agent":"Mozilla/5.0 (Linux; Android 8.0.0; SM-G955U Build/R16NW) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Mobile Safari/537.36","Accept":"text/html,application/xhtml+xml,application/xml;\q=0.9,imgwebp,*/*;q=0.8"}
		URL = 'https://news.kbs.co.kr/mobile/main.html'
		req = s.get(URL,headers=header)
		bs0bj = bs(req.content.decode('utf-8','replace'),'html.parser')
		lists = bs0bj.select("ul > li > a")
		for i in lists:
			check = i.attrs['href']
			if '/mobile/news/view.do' not in check:
				pass
			else:
				URL = 'https://news.kbs.co.kr' + i.attrs['href']
				req = s.get(URL,headers=header)
				bs0bj = bs(req.content.decode('utf-8','replace'),'html.parser')
				ttitle = bs0bj.select('h2 > strong')
				posts = bs0bj.select('#cont_newstext')
				MEMO = posts[0].text.strip()
				TITLE = ttitle[0].text.strip()
				CAST = "KBS"
				COMPLETE = 'False'
				addnews(CAST, TITLE, URL, MEMO, newdate, COMPLETE)
	logger.info('KBS 목록완료')
	return CAST
		
def daumnews(newdate):
	with requests.Session() as s:
		header = {"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5)\AppleWebKit 537.36 (KHTML, like Gecko) Chrome","Accept":"text/html,application/xhtml+xml,application/xml;\q=0.9,imgwebp,*/*;q=0.8"}
		URL = 'https://news.daum.net/?nil_top=mobile'
		req = s.get(URL,headers=header)
		bs0bj = bs(req.content.decode('utf-8','replace'),'html.parser')
		lists = bs0bj.select("main > section > div > div > div > ul > li > div > div") #body > div.container-doc > main > section > div > div.content-article > div.box_g.box_news_issue > ul > li:nth-child(1) > div > div
		for i in lists:	
			try:
				link = i.select('strong > a')
				URL = link[0]['href'] + '/?nil_top=mobile'
				req = s.get(URL,headers=header)
				bs0bj = bs(req.content.decode('utf-8','replace'),'html.parser')
				ttitle = bs0bj.select('h3.tit_view')
				posts = bs0bj.select('div.article_view')
				MEME = []
				for i in posts[0].findAll('p'):
					MEME.append(i.text)
				TITLE = ttitle[0].text.strip()
				MEMO = ' '.join(MEME)
				CAST = "DAUM"
				COMPLETE = 'False'
				addnews(CAST, TITLE, URL, MEMO, newdate, COMPLETE)
			except:
				continue
	logger.info('DAUM 목록완료')
	return CAST


def newsalim_start(telgm,telgm_alim,telgm_token,telgm_botid,broadcaster):
	logger.info('뉴스알림시작')
	news = broadcaster
	print(news)
	#오늘날짜
	nowtime1 = datetime.now()
	newdate = "%04d-%02d-%02d" % (nowtime1.year, nowtime1.month, nowtime1.day)
	time_old = "%02dH%02dM" % (nowtime1.hour, nowtime1.minute)
	CAST = []
	if news == 'YTN':
		a = ytnsnews(newdate)
		CAST.append(a)
	elif news == 'SBS':
		b = esbsnews(newdate)
		CAST.append(b)
	elif news == 'KBS':
		c = ekbsnews(newdate)
		CAST.append(c)
	elif news == 'VIET':
		d = vietnews(newdate)
		CAST.append(d)
	elif news == 'DAUM':
		e = daumnews(newdate)
		CAST.append(e)
	else:
		a = ytnsnews(newdate)
		CAST.append(a)
		time.sleep(1)
		b = esbsnews(newdate)
		CAST.append(b)
		time.sleep(1)
		c = ekbsnews(newdate)
		CAST.append(c)
		time.sleep(1)
		d = vietnews(newdate)
		CAST.append(d)
		time.sleep(1)
		e = daumnews(newdate)
		CAST.append(e)
		time.sleep(1)
	coco = []	
	for i in CAST:
		logger.info('%s 알림 시작',i)
		con = sqlite3.connect(sub2db + '/news.db',timeout=60)
		con.execute("PRAGMA cache_size = 10000")
		con.execute("PRAGMA locking_mode = NORMAL")
		con.execute("PRAGMA temp_store = MEMORY")
		con.execute("PRAGMA auto_vacuum = 1")
		con.execute("PRAGMA journal_mode=WAL")
		con.execute("PRAGMA synchronous=NORMAL")
		con.row_factory = sqlite3.Row
		cur = con.cursor()	
		sql = 'select * from ' + i + ' where COMPLETE = ?'
		cur.execute(sql, ('False', ))
		rows = cur.fetchall()
		count = 1
		#DB의 정보를 읽어옵니다.
		for row in rows: 
			CAST = row['CAST']
			TITLE = row['TITLE']
			URL = row['URL']
			MEMO = row['MEMO']
			COMPLETE = row['COMPLETE']
			msg = '{}\n{}\n{}'.format(CAST,TITLE,MEMO)
			tel(telgm,telgm_alim,telgm_token,telgm_botid,msg)
			addnews_d(CAST,TITLE,URL)
			#if count % 5 == 0:
				#time.sleep(10)
			count += 1
		con.close()	
		logger.info('%s 알림 종료',i)
	logger.info('뉴스 알림완료')	
	comp = '완료'
	return comp

	
@bp2.route('news')
def news():
	#데이타베이스 없으면 생성
	con = sqlite3.connect(sub2db + '/telegram.db',timeout=60)
	con.execute('CREATE TABLE IF NOT EXISTS news (start_time TEXT)')
	#con.execute("PRAGMA synchronous = OFF")
	#con.execute("PRAGMA journal_mode = MEMORY")
	con.execute("PRAGMA cache_size = 10000")
	#con.execute("PRAGMA locking_mode = EXCLUSIVE")
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
		cur.execute("select * from news")
		rows = cur.fetchone()
		if rows:
			telgm_token = rows['telgm_token']
			telgm_botid = rows['telgm_botid']
			start_time = rows['start_time']
			telgm = rows['telgm']
			telgm_alim = rows['telgm_alim']
		else:
			telgm_token='입력하세요'
			telgm_botid='입력하세요'
			start_time = '*/1 * * * *'
			telgm = 'False'
			telgm_alim = 'False'
		return render_template('news.html', telgm_token = telgm_token, telgm_botid = telgm_botid, start_time = start_time, telgm = telgm, telgm_alim = telgm_alim)


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
		now = request.form['now']
		broadcaster = request.form['broadcaster']
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
			"""
		else:
			sql = """
				INSERT INTO news 
				(telgm_token, telgm_botid, start_time, telgm, telgm_alim) VALUES (?, ?, ?, ?, ?)
			"""
		
		cursor.execute(sql, (telgm_token, telgm_botid, start_time, telgm, telgm_alim))
		conn.commit()
		cursor.close()
		conn.close()
		try:
			if now == 'True':
				scheduler.add_job(newsalim_start, trigger=CronTrigger.from_crontab(start_time), id=startname, args=[telgm,telgm_alim,telgm_token,telgm_botid,broadcaster])
				test = scheduler.get_job(startname).id
			else:
				newsalim_start(telgm,telgm_alim,telgm_token,telgm_botid,broadcaster)
			logger.info('%s 를 스케줄러에 추가하였습니다.', test)
		except:
			pass
		return redirect(url_for('sub2.news'))
