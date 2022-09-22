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
	header = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36"}
	with requests.Session() as s:
		req = s.get(url,headers=header)
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
	comp = '완료'
	return comp
	
def url_to_image2(url, filename):
	header = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.101 Safari/537.36"}
	req = requests.get(url,headers=header)	

	if not os.path.isfile(filename):
		with open(filename, 'wb') as code:
			code.write(req.content)
	comp = '완료'
	return comp		
	
#특수문자제거
def cleanText(readData):
	#텍스트에 포함되어 있는 특수 문자 제거
	text = re.sub('[-=+,#/\?:^$.@*\"※~&%ㆍ!』\\‘|\(\)\[\]\<\>`\'…》]', '', readData)
	#text = re.sub('[\/:*?"<>|]', '', readData)
	return text		
#텔레그램 알림
def tel(telgm,telgm_alim,telgm_token,telgm_botid,text):
	if len(text) <= 4096:
		if telgm == 'True' :
			bot = telegram.Bot(token = telgm_token)
			if telgm_alim == 'True':
				bot.sendMessage(chat_id = telgm_botid, text=text, disable_notification=True)    
			else:
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
					text = text[first_lnbr:]
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
						bot.sendMessage(chat_id = telgm_botid, text=part, disable_notification=True)    
					else :
						bot.sendMessage(chat_id = telgm_botid, text=part, disable_notification=False)
					print(part)
				else:
					print(part)
			else: # 두번째 메시지부터 '(Continuing...)\n'을 앞에 붙여줍니다.
				if telgm == 'True' :
					bot = telegram.Bot(token = telgm_token)
					if telgm_alim == 'True':
						bot.sendMessage(chat_id = telgm_botid, text=part, disable_notification=True)    
					else :
						bot.sendMessage(chat_id = telgm_botid, text=part, disable_notification=False)
					print(part)
				else:
					print(part)
			#time.sleep(10)
			#time.sleep(0.5)
	comp = '완료'
	return comp	

#텔레그램 알림
def tel_img(telgm,telgm_alim,telgm_token,telgm_botid,msg):
	if telgm == 'True' :
		bot = telegram.Bot(token = telgm_token)
		if telgm_alim == 'True':
			bot.send_photo(chat_id = telgm_botid, photo=open(msg,'rb'), disable_notification=True)   
		else:
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
		url_list = ["http://192.168.0.97:8085/carriers", "https://apis.tracker.delivery/carriers" ]
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
		sql = "select * from tracking"
		cur.execute(sql,)
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
			filename = dfolder + '/' + name.text + '_' + str(newdate) + ".jpg"
			url_to_image2(url, filename)

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
	return [last,filename]
		
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
		msg4,filename = Typhoon()
		msg3 = " ".join(msg4)
		msg = '{}\n\n{}\n\n태풍 정보\n{}'.format(msg1,msg2,msg3)	
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
def quiz_add_go_d(MEMO, COMPLTE):
	try:
		#마지막 실행까지 작업안했던 결과물 저장
		con = sqlite3.connect(sub2db + '/quiz.db',timeout=60)
		cur = con.cursor()
		sql = "select * from quiz where MEMO = ? and COMPLTE = ?"
		cur.execute(sql, (MEMO,COMPLTE))
		row = cur.fetchone()
		if row == None:
			print("해당 내용은 DB에 없습니다.")
		else:
			sql = "UPDATE quiz SET COMPLTE = ? WHERE MEMO = ?"	
			cur.execute(sql,('True', MEMO))
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
		#SQLITE3 DB 없으면 만들다.
		con = sqlite3.connect(sub2db + '/quiz.db',timeout=60)
		con.execute('CREATE TABLE IF NOT EXISTS quiz (TITLE TEXT, URL TEXT, MEMO TEXT, COMPLTE TEXT)')
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
		#with requests.Session() as s:
		header = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36"}				
		#for page in u:
		for page in range(1,11):
			URL = 'https://quizbang.tistory.com/category/?page=' + str(page)
			req = requests.get(URL,headers=header)
			html = req.text
			gogo = bs(html, "html.parser")
			posts = gogo.findAll("div",{"class":"post-item"})
		
			for i in posts:
				title = i.find('span',{'class':'title'}).text
				url = i.find('a')["href"]
				keys = ['TITLE','URL']
				values = [title, url]
				dt = dict(zip(keys, values))
				list.append(dt)
		
		for i in list:
			list_url = i['URL']
			title = i['TITLE']
			#with requests.Session() as s:
			header = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36"}				
			URL = 'https://quizbang.tistory.com' + list_url
			req = requests.get(URL,headers=header)
			html = req.text
			gogo = bs(html, "html.parser")
			#posts = gogo.find('h2').text
			#p = re.compile('(?<=\:)(.*)')
			#memo = p.findall(posts)
			all_text = gogo.text
			result_remove_all = re.sub(r"\s", "", all_text)
			p = re.compile('정답:(.*?)\[')
			memo = p.findall(result_remove_all)
			memo_s = ''.join(memo)
			keys = ['TITLE','MEMO', 'URL']
			values = [title, memo_s, URL]
			dt = dict(zip(keys, values))
			last.append(dt)
					
		for ii in last:
			title = ii['TITLE']
			memo_s = ii['MEMO']
			URL = ii['URL']
			quiz_add_go(title, memo_s, URL)
		
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
				COMPLTE = row['COMPLTE']
				msg = '{}\n정답 : {}'.format(TITLE,MEMO)
				tel(telgm,telgm_alim,telgm_token,telgm_botid,msg)
				quiz_add_go_d(MEMO, COMPLTE)
		else:
			logger.info('퀴즈정답 신규내용이 없습니다.')
	except:	
		pass
	try:
		con = sqlite3.connect(sub2db + '/quiz.db',timeout=60)
		con.execute('VACUUM')
		con.commit()
		logger.info('DB최적화를 진행하였습니다.')
	except:
		con.rollback()	
	finally:	
		con.close()	
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
def add_d(id, go, complte):
	try:
		#마지막 실행까지 작업안했던 결과물 저장
		con = sqlite3.connect(sub2db + '/funmom.db',timeout=60)
		cur = con.cursor()
		sql = "UPDATE funmom SET complte = ? WHERE urltitle = ? AND ID = ?"
		cur.execute(sql,('True',go,id))
		con.commit()
	except:
		con.rollback()
	finally:	
		con.close()	
	comp = '완료'
	return comp
#펀맘 DB	
def add_c(a,b,c,d):
	try:
		con = sqlite3.connect(sub2db + '/funmom.db',timeout=60)
		cur = con.cursor()
		sql = "select * from funmom where urltitle = ?"
		cur.execute(sql, (c,))
		row = cur.fetchone()
		if row != None:
			pass
		else:
			cur.execute("INSERT OR REPLACE INTO funmom (ID, title, urltitle, complte) VALUES (?, ?, ?, ?)", (a,b,c,d))
			con.commit()
	except:
		con.rollback()
	finally:		
		con.close()	
	comp = '완료'
	return comp
	
def funmom_start(startname):
	logger.info('펀맘알림 시작')
	con = sqlite3.connect(sub2db + '/funmom.db',timeout=60)
	con.execute('CREATE TABLE IF NOT EXISTS funmom (ID TEXT, title TEXT, urltitle TEXT, complte TEXT)')
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
	#with requests.Session() as s:
	header = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36"}
	gogo = 1
	a = 1
	while True:
		dd = "https://funmom.tistory.com/category/?page=" + str(gogo)
		login = requests.get(dd,headers=header)
		html = login.text
		soup = bs(html, 'html.parser')
		list = soup.find_all(attrs={'class' :'jb-index-title jb-index-title-front'})
		if len(list) == 0:
			print("마지막 페이지입니다.\n종료합니다.")
			break
		
		hrefs = []
		title = []
		for href in list:
			t = href.find("a")["href"]
			hrefs.append(str(t))
			title.append(href.text)
			
		tt = 0
		for c,b in zip(hrefs,title):
			d = "False" #처음에 등록할때 무조건 False 로 등록한다.
			add_c(a,b,c,d)
			a += 1
		gogo += 1
	print('목록을 전부 만들었습니다.')		
	logger.info('목록을 전부 만들었습니다.')
	con = sqlite3.connect(sub2db + '/funmom.db',timeout=60)
	cur = con.cursor()
	sql = "select * from funmom where complte = ?"
	cur.execute(sql,('False',))
	row = cur.fetchall()	
	for i in row:			
		id = i[0] #숫자
		ti = i[1] #제목
		go = i[2] #url
		complte = i[3] #완료여부
		if complte == 'True':
			continue
		else:
			dd2 = 'https://funmom.tistory.com' + go
			login2 = requests.get(dd2,headers=header)
			html = login2.text
			soup = bs(html, 'html.parser')
			menu = soup.find(attrs={'class' :'another_category another_category_color_gray'}) #카테고리 이름
			test = menu.find('h4')
			ttt = test('a')
			category = ttt[0].text
			category2 = ttt[1].text
			if platform.system() == 'Windows':
				at = os.path.splitdrive(os.getcwd())
				root = at[0] + '/data'
			else:
				root = '/data'

			dfolder = root + '/funmom'# + category + '/' + category2
			title = soup.find('title')	
			thisdata = cleanText(title.text)
			ex_id_divs = soup.find_all(attrs={'class' : ["imageblock alignCenter","imageblock"]})
			urls = []
			for img in ex_id_divs:
				img_url = img.find("img")
				urls.append(str(img_url["src"]))		
			jpeg_no = 00
			for url in urls:
				filename=thisdata + "-" + str(jpeg_no+1).zfill(3) + ".jpg"
				url_to_image(url, dfolder, category, category2, filename)
				jpeg_no += 1
			add_d(id, go, complte)
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
