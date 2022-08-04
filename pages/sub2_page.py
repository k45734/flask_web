#-*- coding: utf-8 -*-
import sys
try:
	reload(sys)
	sys.setdefaultencoding('utf-8')
except:
	pass
from flask import Blueprint
import os.path, json, os, re, time, logging, io, subprocess, platform, telegram, threading, sqlite3, random
from datetime import datetime

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
try: #python3
	from urllib.request import urlopen
except: #python2
	from urllib2 import urlopen
	#from urllib.request import urlopen 
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

#여기서 필요한 모듈
from pytz import utc
from datetime import datetime, timedelta
from flask import Flask, flash, redirect, render_template, request, session, abort, url_for
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.jobstores.base import JobLookupError
from apscheduler.triggers.cron import CronTrigger
from apscheduler.executors.pool import ThreadPoolExecutor, ProcessPoolExecutor
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
if platform.system() == 'Windows':
	at = os.path.splitdrive(os.getcwd())
	sub2db = at[0] + '/data'
	logdata = at[0] + '/data/log'
else:
	sub2db = '/data'
	logdata = '/data/log'
	
bp2 = Blueprint('sub2', __name__, url_prefix='/sub2')
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
jobstores = {
    'default': SQLAlchemyJobStore(url='sqlite:////data/jobs.sqlite', tablename='sub2')
}
executors = {
    'default': ThreadPoolExecutor(20),
    'processpool': ProcessPoolExecutor(5)
}
job_defaults = {
    'coalesce': False,
    'max_instances': 1
}
scheduler2 = BackgroundScheduler(jobstores=jobstores,job_defaults=job_defaults,executors=executors,timezone='Asia/Seoul')
f = open(logdata + '/flask.log','a', encoding='utf-8')
rfh = logging.handlers.RotatingFileHandler(filename=logdata + '/flask.log', mode='a', maxBytes=5*1024*1024, backupCount=2, encoding=None, delay=0)
logging.basicConfig(level=logging.INFO,format="[%(filename)s:%(lineno)d %(levelname)s] - %(message)s",handlers=[rfh])
logger = logging.getLogger()
scheduler2.start()

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
		test2 = scheduler2.get_jobs()
		for i in test2:
			aa = i.id
			tltl.append(aa)
		#t_main = request.form['t_main']
		return render_template('sub2_index.html', tltl = tltl)

def url_to_image(url, dfolder, category, category2, filename):
	header = {"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5)\AppleWebKit 537.36 (KHTML, like Gecko) Chrome","Accept":"text/html,application/xhtml+xml,application/xml;\q=0.9,imgwebp,*/*;q=0.8"}
	#req = requests.get(url,headers=header)
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
			
#텔레그램 알림
def tel(telgm,telgm_alim,telgm_token,telgm_botid,msg):
	if telgm == 'True' :
		bot = telegram.Bot(token = telgm_token)
		if telgm_alim == 'True':
			bot.sendMessage(chat_id = telgm_botid, text=msg, disable_notification=True)
		else :
			bot.sendMessage(chat_id = telgm_botid, text=msg, disable_notification=False)
		print(msg)
	else:
		print(msg)
				
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
			test = scheduler2.get_job(startname).id
			logger.info('%s가 스케줄러에 있습니다.', test)
		except Exception as e:
			test = None
		if test == None:
			logger.info('%s의 스케줄러가 종료가 되지 않았습니다.', startname)
		else:
			#remove_job
			scheduler2.remove_job(startname)
			#scheduler2.shutdown()
			logger.info('%s 스케줄러를 삭제하였습니다.', test)
			test2 = scheduler2.get_jobs()
			for i in test2:
				aa = i.id
				logger.info('%s 가 스케줄러가 있습니다.', aa)
		return redirect(url_for('sub2.index'))
		
#택배조회서비스
#알리미 완료
def tracking_del_new(carrier_id, track_id):
	#마지막 실행까지 작업안했던 결과물 저장
	con = sqlite3.connect(sub2db + '/delivery.db',timeout=60)
	
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
		
#서버에서 조회를 하여 메모리에 저장
def flfl(json_string_m):
	test = []
	for list in json_string_m:
		a = list.get("time")
		at = a[0:16]
		new_s = at.replace('T',' ')
		b = list.get("location").get('name')
		c = list.get("status").get('text')
		d = list.get("description")
		msg = {'시간':new_s,'상품위치':b,'현재상태':c, '상품상태':d}
		test.append(msg)				
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
#택배조회 구동	
def tracking_start(telgm,telgm_alim,telgm_token,telgm_botid):
	url = []
	#SQLITE3 DB 없으면 만들다.
	conn = sqlite3.connect(sub2db + '/delivery.db',timeout=60)
	conn.execute('CREATE TABLE IF NOT EXISTS tracking (PARCEL TEXT, NUMBER TEXT, DATE TEXT,COMPLTE TEXT)')
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
		ttt = 'https://apis.tracker.delivery/carriers/' +  carrier + '/tracks/' + track_id
		url.append(ttt)
	h = {"Cache-Control": "no-cache",   "Pragma": "no-cache"}
	with requests.Session() as s:
		for a in url:
			url = s.get(a, headers=h)
			resp = url.json()
			check = resp.get('from', None)
			if check == None:
				msg = '송장번호가 없는거 같습니다.\n'
				tel(telgm,telgm_alim,telgm_token,telgm_botid,msg)
			else:
				json_string = check.get("name", None) #누가 보냈냐			
				json_string2 = resp.get("to").get("name") #누가 받냐
				json_string3 = resp.get("state").get("text") #배송현재상태
				json_string4 = resp.get("carrier").get("name") #택배사이름
				json_string5 = resp.get("carrier").get("id") #택배사송장번호
				json_string_m = resp.get("progresses") #배송상황
				msg2 = flfl(json_string_m)
				gg = ff(msg2,json_string,json_string2,json_string4,json_string5)
				ms = '\n'.join(gg)
				msga = '==========================================\n보내는 사람 : {}\n받는 사람 : {}\n택배사 : {} {}\n{}\n=========================================='.format(json_string,json_string2,json_string4,json_string5,ms)
				if '완료' in msga :
					tracking_del_new(json_string4, json_string5)
				else:
					pass
				tel(telgm,telgm_alim,telgm_token,telgm_botid,msga)
				
@bp2.route('tracking')
def tracking():
	#데이타베이스 없으면 생성
	conn = sqlite3.connect(sub2db + '/telegram.db',timeout=60)
	conn.execute('CREATE TABLE IF NOT EXISTS tracking (telgm_token TEXT, telgm_botid TEXT, start_time TEXT, telgm TEXT, telgm_alim TEXT)')
	conn.close()
	#SQLITE3 DB 없으면 만들다.
	conn = sqlite3.connect(sub2db + '/delivery.db',timeout=60)
	conn.execute('CREATE TABLE IF NOT EXISTS tracking (PARCEL TEXT, NUMBER TEXT, DATE TEXT,COMPLTE TEXT)')
	conn.close()
	if not session.get('logFlag'):
		return redirect(url_for('main.index'))
	else:
		telgm_token = request.args.get('telgm_token')
		telgm_botid = request.args.get('telgm_botid')
		con = sqlite3.connect(sub2db + '/telegram.db',timeout=60)
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
		view1 = []
		view2 = []
		#알림
		con = sqlite3.connect(sub2db + '/delivery.db',timeout=60)
		con.row_factory = sqlite3.Row
		cur = con.cursor()
		sql = "select * from tracking"
		cur.execute(sql,)
		rows = cur.fetchall()
		for row in rows:
			carrier_id = row['PARCEL']
			track_id = row['NUMBER']
			view1.append(carrier_id)
			view2.append(track_id)
		return render_template('tracking.html',zip=zip, view1 = view1, view2 = view2, telgm_token = telgm_token, telgm_botid = telgm_botid, start_time = start_time, telgm = telgm, telgm_alim = telgm_alim)

@bp2.route('tracking_add', methods=['POST'])
def tracking_add():
	mytime = mydate()
	#SQLITE3 DB 없으면 만들다.
	conn = sqlite3.connect(sub2db + '/delivery.db',timeout=60)
	conn.execute('CREATE TABLE IF NOT EXISTS tracking (PARCEL TEXT, NUMBER TEXT, DATE TEXT,COMPLTE TEXT)')
	conn.close()
	if not session.get('logFlag'):
		return redirect(url_for('main.index'))
	else:
		carrier_id = request.form['carrier_id']
		track_id = request.form['track_id']
		conn = sqlite3.connect(sub2db + '/delivery.db',timeout=60)
		cursor = conn.cursor()
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
		conn.commit()
		cursor.close()
		conn.close()
	return redirect(url_for('sub2.tracking'))

@bp2.route('tracking_del/<carrier_id>/<track_id>', methods=["GET"])
def tracking_del(carrier_id,track_id):
	#SQLITE3 DB 없으면 만들다.
	conn = sqlite3.connect(sub2db + '/delivery.db',timeout=60)
	conn.execute('CREATE TABLE IF NOT EXISTS tracking (PARCEL TEXT, NUMBER TEXT, DATE TEXT,COMPLTE TEXT)')
	conn.close()
	if not session.get('logFlag'):
		return redirect(url_for('main.index'))
	else:
		conn = sqlite3.connect(sub2db + '/delivery.db',timeout=60)
		cursor = conn.cursor()
		sql = "DELETE FROM tracking WHERE PARCEL = ? AND NUMBER = ?"
		cursor.execute(sql, (carrier_id, track_id))
		conn.commit()
		cursor.close()
		conn.close()
	return redirect(url_for('sub2.tracking'))	
	
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
		conn = sqlite3.connect(sub2db + '/telegram.db',timeout=60)
		cursor = conn.cursor()
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
		conn.commit()
		cursor.close()
		conn.close()
		try:
			scheduler2.add_job(tracking_start, trigger=CronTrigger.from_crontab(start_time), id=startname, args=[telgm,telgm_alim,telgm_token,telgm_botid])
			test = scheduler2.get_job(startname).id
			logger.info('%s 를 스케줄러에 추가하였습니다.', test)
		except:
			pass
		return redirect(url_for('sub2.index'))
		
def weather_start(location,telgm,telgm_alim,telgm_token,telgm_botid):
	#기상청 날씨누리 현재시간기준
	natotal = []
	with requests.Session() as s:
		#지역명을 찾는다.
		GEO = {'query': location, 
				'start': '1',
				'src': 'A4'}
		url = 'https://www.weather.go.kr/w/renew2021/rest/main/place-search.do' 
		resp = s.get(url,data=GEO).json()
		geo_code = resp[0]['dongCode']
		#지역명으로 날씨검색을 한다.
		weather = {'code': geo_code,
				'unit': 'm/s',
				'aws': 'N'}
		url = 'https://www.weather.go.kr/w/wnuri-fct2021/main/current-weather.do'
		html = s.get(url,data=weather).text
		gogo = bs(html, "html.parser")	
		
		for i in gogo.findAll('span'):
			natotal.append(i.text)
		#특보예보
		fact = gogo.find("div",{"class":"cmp-impact-fct"}).text
		natotal.append(fact)
		#현재온도
		temp = natotal[4]
		#특보
		fact_a = natotal[-1]
		fact_ok = ''.join(fact_a.split())
		#현재날짜
		msg = '{}\n온도 {} / 체감온도 {} / 습도 {} / 바람 {} / 1시간강수량 {}\n{}'.format(natotal[0],temp[0:5],natotal[10],natotal[12],natotal[14],natotal[16],fact_ok)
		tel(telgm,telgm_alim,telgm_token,telgm_botid,msg)
@bp2.route('weather')
def weather():
	#데이타베이스 없으면 생성
	conn = sqlite3.connect(sub2db + '/telegram.db',timeout=60)
	conn.execute('CREATE TABLE IF NOT EXISTS weather (telgm_token TEXT, telgm_botid TEXT, start_time TEXT, telgm TEXT, telgm_alim TEXT)')
	conn.close()
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
		conn = sqlite3.connect(sub2db + '/telegram.db',timeout=60)
		cursor = conn.cursor()
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
		conn.commit()
		cursor.close()
		conn.close()
		try:
			scheduler2.add_job(weather_start, trigger=CronTrigger.from_crontab(start_time), id=startname, args=[location,telgm,telgm_alim,telgm_token,telgm_botid])
			test = scheduler2.get_job(startname).id
			logger.info('%s 를 스케줄러에 추가하였습니다.', test)
		except:
			pass
		return redirect(url_for('sub2.index'))
		
#뉴스알림		
def addnews(a,b,c,d,e):
	con = sqlite3.connect(sub2db + '/news.db',timeout=60)
	cur = con.cursor()
	sql = "select * from news where TITLE = ? and URL = ?"
	cur.execute(sql, (b,c))
	row = cur.fetchone()
	if row != None:
		pass
	else:
		cur.execute("INSERT OR REPLACE INTO news (CAST, TITLE, URL, COMPLETE, DATE) VALUES (?,?,?,?,?)", (a,b,c,d,e))
		con.commit()
	
		#con.rollback()
	con.close()
	
def addnews_d(a, b, c, d, e):
	try:
		#마지막 실행까지 작업안했던 결과물 저장
		con = sqlite3.connect(sub2db + '/news.db',timeout=60)
		cur = con.cursor()
		sql = "UPDATE news SET COMPLETE = ? WHERE TITLE = ? AND URL = ?"
		cur.execute(sql,('True',b, c))
		con.commit()
	except:
		con.rollback()
	finally:	
		con.close()		

def vietnews(newdate):
	session = requests.Session()
	header = {"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5)\AppleWebKit 537.36 (KHTML, like Gecko) Chrome","Accept":"text/html,application/xhtml+xml,application/xml;\q=0.9,imgwebp,*/*;q=0.8"}
	URL = 'https://www.vinatimes.net/news'
	req = session.get(URL,headers=header)
	bs0bj = bs(req.content.decode('utf-8','replace'),'html.parser')
	posts = bs0bj.findAll("div",{"class":"list_title"})
	vietnews = []
	for test in posts:
		title = test.text
		a2 = "".join(title.split())
		a3 = test.a['href']
		a5 = "VIET"
		keys = ['CAST','TITLE','URL','DATE']
		values = [a5, a2, a3, newdate]
		dt = dict(zip(keys, values))
		vietnews.append(dt)
	return vietnews	
		
def esbsnews(newdate):
	session = requests.Session()
	header = {"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5)\AppleWebKit 537.36 (KHTML, like Gecko) Chrome","Accept":"text/html,application/xhtml+xml,application/xml;\q=0.9,imgwebp,*/*;q=0.8"}
	URL = 'https://news.sbs.co.kr/news/newsMain.do?div=pc_news'
	req = session.get(URL,headers=header)
	bs0bj = bs(req.content.decode('utf-8','replace'),'html.parser')
	posts = bs0bj.find("div",{"class":"w_news_list"})
	lists = posts.findAll("a")
	sbsnews = []
	for i in lists:
		a1 = i.attrs['href']
		a5 = i.text
		a2 = "".join(a5.split())
		a3 = 'https://news.sbs.co.kr' + a1
		a4 = "{} \n{}\n".format(a2, a3)
		a5 = "SBS"
		keys = ['CAST','TITLE','URL','DATE']
		values = [a5, a2, a3, newdate]
		dt = dict(zip(keys, values))
		sbsnews.append(dt)
	return sbsnews		

def ekbsnews(newdate):
	session = requests.Session()
	header = {"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5)\AppleWebKit 537.36 (KHTML, like Gecko) Chrome","Accept":"text/html,application/xhtml+xml,application/xml;\q=0.9,imgwebp,*/*;q=0.8"}
	URL = 'http://news.kbs.co.kr/common/main.html'
	req = session.get(URL,headers=header)
	bs0bj = bs(req.content.decode('utf-8','replace'),'html.parser')
	posts = bs0bj.find("div",{"class":"fl col-box col-recent"})
	lists = posts.findAll("a")
	kbsnews = []
	for i in lists:
		a1 = i.attrs['href']
		a2 = i.text
		a3 = 'http://news.kbs.co.kr' + a1
		a4 = "{} \n{}\n".format(a2, a3)
		a5 = "KBS"
		keys = ['CAST','TITLE','URL', 'DATE']
		values = [a5, a2, a3, newdate]
		dt = dict(zip(keys, values))
		kbsnews.append(dt)
	return kbsnews		
	
def ytnsnews(newdate):
	session = requests.Session()
	header = {"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5)\AppleWebKit 537.36 (KHTML, like Gecko) Chrome","Accept":"text/html,application/xhtml+xml,application/xml;\q=0.9,imgwebp,*/*;q=0.8"}
	URL = 'https://www.yna.co.kr/news?site=navi_latest_depth01'
	req = session.get(URL,headers=header)
	bs0bj = bs(req.content.decode('utf-8','replace'),'html.parser')
	list = bs0bj.find("div",{"class":"section01"})	
	posts = list.findAll("div",{"class":"news-con"})	
	ytnnews = []
	for i in posts:
		a1 = i.text
		a2 = " ".join(a1.split())
		a3 = 'https:' + i.find('a')['href']
		a4 = "YTN"
		keys = ['CAST','TITLE','URL', 'DATE']
		values = [a4, a2, a3, newdate]
		dt = dict(zip(keys, values))
		ytnnews.append(dt)
	return ytnnews	
	
def news_start(telgm,telgm_alim,telgm_token,telgm_botid):	
	#오늘날짜
	nowtime1 = datetime.now()
	newdate = "%04d-%02d-%02d" % (nowtime1.year, nowtime1.month, nowtime1.day)
	#7일이전
	nowtime2 = nowtime1 - timedelta(days=7)
	olddate = "%04d-%02d-%02d" % (nowtime2.year, nowtime2.month, nowtime2.day)
	#SQLITE3 DB 없으면 만들다.
	#SQLITE3 DB 없으면 만들다.
	conn = sqlite3.connect(sub2db + '/news.db',timeout=60)
	conn.execute('CREATE TABLE IF NOT EXISTS news (CAST TEXT, TITLE TEXT, URL TEXT, COMPLETE TEXT, DATE TEXT)')	
	conn.close()

	sbs = esbsnews(newdate)
	kbs = ekbsnews(newdate)
	viet = vietnews(newdate)
	ytn = ytnsnews(newdate)
	for i in sbs:
		a = i['CAST']
		b = i['TITLE']
		c = i['URL']
		d = 'False'
		e = newdate
		addnews(a,b,c,d,e)
	for i in kbs:
		a = i['CAST']
		b = i['TITLE']
		c = i['URL']
		d = 'False'
		e = newdate
		addnews(a,b,c,d,e)
	for i in viet:
		a = i['CAST']
		b = i['TITLE']
		c = i['URL']
		d = 'False'
		e = newdate
		addnews(a,b,c,d,e)
	for i in ytn:
		a = i['CAST']
		b = i['TITLE']
		c = i['URL']
		d = 'False'
		e = newdate
		addnews(a,b,c,d,e)
	#최신 기사
	con = sqlite3.connect(sub2db + '/news.db',timeout=60)
	con.row_factory = sqlite3.Row
	cur = con.cursor()	
	sql = "select * from news where COMPLETE = ?"
	cur.execute(sql, ('False', ))
	rows = cur.fetchall()		
	#DB의 정보를 읽어옵니다.
	for row in rows:
		a = row['CAST']
		b = row['TITLE']
		c = row['URL']
		d = row['COMPLETE']
		e = row['DATE']
		msg = '{}\n{}\n{}'.format(a,b,c)
		tel(telgm,telgm_alim,telgm_token,telgm_botid,msg)
		time.sleep(10)
		#중복 알림에거
		addnews_d(a,b,c,d,e)
		
	#오래된 기사 삭제	
	con = sqlite3.connect(sub2db + '/news.db',timeout=60)
	cur = con.cursor()	
	sql = "select * from news where DATE not between ? and ?"
	cur.execute(sql, (olddate, newdate))
	rows = cur.fetchall()
	for row in rows:
		a = row[1]
		print(a)
		cur.execute("DELETE FROM news WHERE TITLE = ?", (a,))
		con.commit()

@bp2.route('news')
def news():
	#데이타베이스 없으면 생성
	conn = sqlite3.connect(sub2db + '/telegram.db',timeout=60)
	conn.execute('CREATE TABLE IF NOT EXISTS news (telgm_token TEXT, telgm_botid TEXT, start_time TEXT, telgm TEXT, telgm_alim TEXT)')
	conn.close()
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
			print(telgm_alim, telgm)
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
			scheduler2.add_job(news_start, trigger=CronTrigger.from_crontab(start_time), id=startname, args=[telgm,telgm_alim,telgm_token,telgm_botid])
			test = scheduler2.get_job(startname).id
			logger.info('%s 를 스케줄러에 추가하였습니다.', test)
		except:
			pass
		return redirect(url_for('sub2.index'))

#운세알리미
#운세알리미 DB
def add_unse(lastdate, zodiac, zodiac2, list, complte):
	try:
		con = sqlite3.connect(sub2db + '/unse.db',timeout=60)
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
		
def add_unse_d(a, b, c, d, e):
	try:
		#마지막 실행까지 작업안했던 결과물 저장
		con = sqlite3.connect(sub2db + '/unse.db',timeout=60)
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
		
def unse_start(telgm,telgm_alim,telgm_token,telgm_botid):
	#SQLITE3 DB 없으면 만들다.
	conn = sqlite3.connect(sub2db + '/unse.db',timeout=60)
	conn.execute('CREATE TABLE IF NOT EXISTS unse (DATE TEXT, ZODIAC TEXT, ZODIAC2 TEXT, MEMO TEXT, COMPLTE TEXT)')
	conn.close()
	session = requests.Session()
	header = {"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5)\AppleWebKit 537.36 (KHTML, like Gecko) Chrome","Accept":"text/html,application/xhtml+xml,application/xml;\q=0.9,imgwebp,*/*;q=0.8"}

	auth = 'https://www.unsin.co.kr/unse/free/todayline/form?linenum=9'
	rs = requests.get(auth,headers=header,verify=False)
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
		
@bp2.route('unse')
def unse():
	#데이타베이스 없으면 생성
	conn = sqlite3.connect(sub2db + '/telegram.db',timeout=60)
	conn.execute('CREATE TABLE IF NOT EXISTS unse (telgm_token TEXT, telgm_botid TEXT, start_time TEXT, telgm TEXT, telgm_alim TEXT)')
	conn.close()
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
			scheduler2.add_job(unse_start, trigger=CronTrigger.from_crontab(start_time), id=startname, args=[telgm,telgm_alim,telgm_token,telgm_botid])
			test = scheduler2.get_job(startname).id
			logger.info('%s 를 스케줄러에 추가하였습니다.', test)
		except:
			pass
		return redirect(url_for('sub2.index'))


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
		
def quiz_start(telgm,telgm_alim,telgm_token,telgm_botid):
	logger.info('퀴즈정답알림 시작')
	#SQLITE3 DB 없으면 만들다.
	conn = sqlite3.connect(sub2db + '/quiz.db',timeout=60)
	conn.execute('CREATE TABLE IF NOT EXISTS quiz (TITLE TEXT, URL TEXT, MEMO TEXT, COMPLTE TEXT)')
	conn.close()
	list = []
	last = []
	#u = {'https://quizbang.tistory.com/category/%ED%80%B4%EC%A6%88%20%EC%A0%95%EB%8B%B5/%EC%98%A4%ED%80%B4%EC%A6%88',
	#	'https://quizbang.tistory.com/category/%ED%80%B4%EC%A6%88%20%EC%A0%95%EB%8B%B5/%EC%BA%90%EC%8B%9C%EC%9B%8C%ED%81%AC',
	#	}
	with requests.Session() as s:
		header = {"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5)\AppleWebKit 537.36 (KHTML, like Gecko) Chrome","Accept":"text/html,application/xhtml+xml,application/xml;\q=0.9,imgwebp,*/*;q=0.8"}				
		#for page in u:
		for page in range(1,11):
			URL = 'https://quizbang.tistory.com/category/?page=' + str(page)
			#URL = page
			req = s.get(URL,headers=header)
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
		with requests.Session() as s:
			header = {"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5)\AppleWebKit 537.36 (KHTML, like Gecko) Chrome","Accept":"text/html,application/xhtml+xml,application/xml;\q=0.9,imgwebp,*/*;q=0.8"}				
			URL = 'https://quizbang.tistory.com' + list_url
			req = s.get(URL,headers=header)
			html = req.text
			gogo = bs(html, "html.parser")
			posts = gogo.find('h2').text
			p = re.compile('(?<=\:)(.*)')
			memo = p.findall(posts)
			memo_s = ''.join(memo)
			#if '됩니다.' in memo_s :
			#	pass
			#elif len(memo_s) == 0 :
			#	pass
			#else:
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
		#msg = '퀴즈정답 신규내용이 없습니다'
		#tel(telgm,telgm_alim,telgm_token,telgm_botid,msg)
		logger.info('퀴즈정답 신규내용이 없습니다.')
		
@bp2.route('quiz')
def quiz():
	#데이타베이스 없으면 생성
	conn = sqlite3.connect(sub2db + '/telegram.db',timeout=60)
	conn.execute('CREATE TABLE IF NOT EXISTS quiz (telgm_token TEXT, telgm_botid TEXT, start_time TEXT, telgm TEXT, telgm_alim TEXT)')
	conn.close()
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
			scheduler2.add_job(quiz_start, trigger=CronTrigger.from_crontab(start_time), id=startname, args=[telgm,telgm_alim,telgm_token,telgm_botid])
			test = scheduler2.get_job(startname).id
			logger.info('%s 를 스케줄러에 추가하였습니다.', test)
		except:
			pass
		return redirect(url_for('sub2.index'))
		
#펀맘 서비스
#펀맘 DB		
def add_d(id, go, complte):
	try:
		#print(a,b)
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
def funmom_start(startname):
	logger.info('펀맘알림 시작')
	conn = sqlite3.connect(sub2db + '/funmom.db',timeout=60)
	conn.execute('CREATE TABLE IF NOT EXISTS funmom (ID TEXT, title TEXT, urltitle TEXT, complte TEXT)')
	conn.close()
	with requests.Session() as s:
		header = {"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5)\AppleWebKit 537.36 (KHTML, like Gecko) Chrome","Accept":"text/html,application/xhtml+xml,application/xml;\q=0.9,imgwebp,*/*;q=0.8"}
		gogo = 1
		a = 1
		while True:
			dd = "https://funmom.tistory.com/category/?page=" + str(gogo)
			login = s.get(dd,headers=header)
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
				login2 = s.get(dd2,headers=header)
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
				
@bp2.route('funmom')
def funmom():
	#데이타베이스 없으면 생성
	conn = sqlite3.connect(sub2db + '/telegram.db',timeout=60)
	conn.execute('CREATE TABLE IF NOT EXISTS funmom (start_time TEXT)')
	conn.close()
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
		#ID TEXT, title TEXT, urltitle TEXT, complte TEXT
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
			scheduler2.add_job(funmom_start, trigger=CronTrigger.from_crontab(start_time), id=startname, args=[startname])
			test = scheduler2.get_job(startname).id
			logger.info('%s 를 스케줄러에 추가하였습니다.', test)
		except:
			pass
		
		return redirect(url_for('sub2.index'))