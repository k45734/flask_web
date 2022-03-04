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
from datetime import datetime, timedelta
from flask import Flask, flash, redirect, render_template, request, session, abort, url_for
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.jobstores.base import JobLookupError
from apscheduler.triggers.cron import CronTrigger
if platform.system() == 'Windows':
	at = os.path.splitdrive(os.getcwd())
	sub2db = at[0] + '/data'
	logdata = at[0] + '/data/log'
else:
	sub2db = '/data'
	logdata = '/data/log'
	
bp2 = Blueprint('sub2', __name__, url_prefix='/sub2')
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
job_defaults = { 'max_instances': 1 }
scheduler2 = BackgroundScheduler(job_defaults=job_defaults)
#scheduler = BackgroundScheduler()
f = open(logdata + '/flask.log','a', encoding='utf-8')
rfh = logging.handlers.RotatingFileHandler(filename=logdata + '/flask.log', mode='a', maxBytes=5*1024*1024, backupCount=2, encoding=None, delay=0)
logging.basicConfig(level=logging.INFO,format="[%(filename)s:%(lineno)d %(levelname)s] - %(message)s",handlers=[rfh])
logger = logging.getLogger()
scheduler2.start()

#오늘날짜
nowtime1 = datetime.now()
newdate = "%04d-%02d-%02d" % (nowtime1.year, nowtime1.month, nowtime1.day)
#7일이전
nowtime2 = nowtime1 - timedelta(days=7)
olddate = "%04d-%02d-%02d" % (nowtime2.year, nowtime2.month, nowtime2.day)
try:
	con = sqlite3.connect(sub2db + '/telegram.db',timeout=60)
	con.row_factory = sqlite3.Row
	cur = con.cursor()
	cur.execute("SELECT * FROM sqlite_master WHERE type='table'")
	tableser = cur.fetchall()
	rows = []
	for tt in tableser:	
		#DB컬럼 이 있으면 삭제합니다.
		conn = sqlite3.connect(sub2db + '/telegram.db',timeout=60)
		cur = conn.cursor()
		cur2 = conn.cursor()
		sql = "SELECT COUNT(*) AS CNTREC FROM pragma_table_info('" + tt[1] + "') WHERE name='program'"
		cur.execute(sql)
		row = cur.fetchone()
		if row[0] == 0:
			print('컬럼이 있어서 초기화합니다.')
		else:
			conn.execute("DROP TABLE  " + tt[1])
		#DB컬럼 추가
		conn = sqlite3.connect(sub2db + '/telegram.db',timeout=60)
		cur = conn.cursor()
		cur2 = conn.cursor()
		sql = "SELECT COUNT(*) AS CNTREC FROM pragma_table_info('" + tt[1] + "') WHERE name='start_time'"
		cur.execute(sql)
		row = cur.fetchone()
		if row[0] == 0:
			conn.execute("ALTER TABLE " + tt[1] + " ADD COLUMN start_time TEXT")
		else:
			print('컬럼이 있습니다.')
		
		#DB컬럼 추가
		conn = sqlite3.connect(sub2db + '/telegram.db',timeout=60)
		cur = conn.cursor()
		cur2 = conn.cursor()
		sql = "SELECT COUNT(*) AS CNTREC FROM pragma_table_info('" + tt[1] + "') WHERE name='telgm'"
		cur.execute(sql)
		row = cur.fetchone()
		if row[0] == 0:
			conn.execute("ALTER TABLE " + tt[1] + " ADD COLUMN telgm TEXT")
		else:
			print('컬럼이 있습니다.')
		#DB컬럼 추가
		conn = sqlite3.connect(sub2db + '/telegram.db',timeout=60)
		cur = conn.cursor()
		cur2 = conn.cursor()
		sql = "SELECT COUNT(*) AS CNTREC FROM pragma_table_info('" + tt[1] + "') WHERE name='telgm_alim'"
		cur.execute(sql)
		row = cur.fetchone()
		if row[0] == 0:
			conn.execute("ALTER TABLE " + tt[1] + " ADD COLUMN telgm_alim TEXT")
		else:
			print('컬럼이 있습니다.')
		conn.close()
except:
	pass

try:
	#DB컬럼 추가
	conn = sqlite3.connect(sub2db + '/news.db',timeout=60)
	cur = conn.cursor()
	cur2 = conn.cursor()
	sql = "SELECT COUNT(*) AS CNTREC FROM pragma_table_info('news') WHERE name='DATE'"
	cur.execute(sql)
	row = cur.fetchone()
	if row[0] == 0:
		conn.execute("ALTER TABLE news ADD COLUMN DATE TEXT")
	else:
		print('컬럼이 있습니다.')
	conn.close()
except:
	pass
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

@bp2.route("second")		
def second():
	#데이타베이스 없으면 생성
	conn = sqlite3.connect(sub2db + '/telegram.db',timeout=60)
	conn.execute('CREATE TABLE IF NOT EXISTS board (telgm_token TEXT, telgm_botid TEXT)')
	conn.close()
	if not session.get('logFlag'):
		return redirect(url_for('main.index'))
	else:
		telgm_token = request.args.get('telgm_token')
		telgm_botid = request.args.get('telgm_botid')
		con = sqlite3.connect(sub2db + '/telegram.db',timeout=60)
		con.row_factory = sqlite3.Row
		cur = con.cursor()
		cur.execute("select * from board")
		rows = cur.fetchone()
		if rows:
			telgm_token = rows[0]
			telgm_botid = rows[1]
		else:
			telgm_token='입력하세요'
			telgm_botid='입력하세요'	
		return render_template('board.html', telgm_token = telgm_token, telgm_botid = telgm_botid)

@bp2.route("lotto")
def lotto():
	num_range = range(1,46)
	result=random.sample(num_range,6) 
	final_result=sorted(result)
	return render_template('start.html', testDataHtml=final_result)

@bp2.route("menu")
def menu():
	menu=["라면", "자장면", "짬뽕", "돈가스", "김치찌개", "부대찌게", "삼겹살", "오뎅국", "칼국수"]
	choice = random.choice(menu)
	return render_template('start.html', testDataHtml=choice)

# 3. /kospi 현재 네이버 기준
@bp2.route("kospi")
def kospi():
	url="https://finance.naver.com/sise/"
	pathway=requests.get(url).text
	soup = bs(pathway, 'html.parser')
	#bs4_trans=bs4.BeautifulSoup(pathway,"html.parser")
	result=soup.select_one("#KOSPI_now").text
	return render_template('start.html', testDataHtml=result)

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
	if telgm == '0' :
		bot = telegram.Bot(token = telgm_token)
		if telgm_alim == '0':
			bot.sendMessage(chat_id = telgm_botid, text=msg, disable_notification=True)
		else :
			bot.sendMessage(chat_id = telgm_botid, text=msg, disable_notification=False)
		print(msg)
	else:
		print(msg)
		
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
		cur.execute(sql, (a,))
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
#운세알리미 DB		
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
		
def cleanText(readData):
	#텍스트에 포함되어 있는 특수 문자 제거
	text = re.sub('[-=+,#/\?:^$.@*\"※~&%ㆍ!』\\‘|\(\)\[\]\<\>`\'…》]', '', readData)
	return text	

#일반게시판의 새로운 글 알림
def exec_start(t_main,sel,selnum,telgm,telgm_alim,telgm_token,telgm_botid):
	with requests.Session() as s:
		header = {"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5)\AppleWebKit 537.36 (KHTML, like Gecko) Chrome","Accept":"text/html,application/xhtml+xml,application/xml;\q=0.9,imgwebp,*/*;q=0.8"}
		url = t_main
		req = s.get(url,headers=header)
		html = req.text
		gogo = bs(html, "html.parser")
		posts = gogo.select(sel)
		#print(posts)
		st = posts[int(selnum)]
		a = st.text
		msg_on = '{}\n새 글이 있어요'.format(a)
		msg_off = '{}\n새 글이 없어요'.format(a)
		#파일이 없으면 만든다
		file = BASE_DIR + '/okcash.txt'
		if not os.path.isfile(file):
			f = io.open(file,'a', encoding='utf-8')

		with io.open(file, 'r+' ,-1, "utf-8") as f_read:
			before = f_read.readline()
			if before != a:			
				tel(telgm,telgm_alim,telgm_token,telgm_botid,msg)
			else:
				tel(telgm,telgm_alim,telgm_token,telgm_botid,msg)

		with io.open(file, 'w+',-1, "utf-8") as f_write:
			f_write.write(a)
			f_write.close()

#네이버 카페 게시판 글알림
def exec_start2(cafenum,cafe,num,cafemenu,cafeboard,boardpath,telgm,telgm_alim,telgm_token,telgm_botid):
	try:
		sys.stdout = io.TextIOWrapper(sys.stdout.detach(), encoding = 'utf-8')
		sys.stderr = io.TextIOWrapper(sys.stderr.detach(), encoding = 'utf-8')
	except:
		pass
	headers = {'cache-control' : 'no-cache',
				'content-encoding' : 'gzip',
				'content-type' : 'text/html;charset=MS949',
				'set-cookie' : 'JSESSIONID=932E6AC193B3DBB55088BCE5A66A49F0; Path=/; HttpOnly',
				'vary' : 'Accept-Encoding,User-Agent',
				'x-xss-protection' : '1; mode=block',
				'user-agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36'
				} 


	adapter = HTTPAdapter(max_retries=10)
	with requests.Session() as s:
		#클럽아이디와 메뉴번호를 받아온다
		print(boardpath)
		main_url = 'https://cafe.naver.com/' + cafe
		s.mount(main_url, adapter)
		login = s.get(main_url)
		html = login.text
		soup = bs(html, 'html.parser')
		club = soup.find(attrs={'class':'cafe-menu-list'})
		menu = soup.find_all(attrs={'class':'cafe-menu-list'})
		clubid = club.find('a')['href']
		clubidst = clubid[31:]
		clubidts = clubidst[:8]
		print("클럽아이디 {}".format( clubidts))
		#print(cafemenu)
		menuid = menu[int(cafemenu)].find_all('a')
		#menuid = menu[1].find_all('a')
		#print(menuid)
		a = menuid[int(cafeboard)]['href']
		#a = menuid[2]['href']
		#test = menu
		#print(a)
		menuidst = a[54:]
		menuidts = menuidst[:2]
		print("메뉴번호 {}".format(menuidts))
		#게시물번호와 게시물의 링크를 가져온다
		m_url = main_url + '/ArticleList.nhn?search.clubid=' + clubidts + '&search.menuid=' + menuidts + '&search.boardtype=L'
		s.mount(m_url, adapter)
		login = s.get(m_url)
		html = login.text
		soup = bs(html, 'html.parser')
		
		board_l = soup.find_all(attrs={'class':'td_article'})
		#print(board_l)
		board_f = board_l[int(cafenum)] #10]
		print(board_f)
		board_num = board_f.find(attrs={'class':['inner_number','inner']})
		
		#print(board_num)
		board_num_t = board_num.text
		print("게시물번호 {}".format(board_num_t))
		board_ff = board_f.find('a')['href']
		#print(board_ff)

		#게시물의 내용을 가져온다
		mb_url = main_url + board_ff
		ll = {'clubid':clubidts,
			'page':'1',
			'menuid':menuidts,
			'boardtype':'L',
			'articleid':board_num_t,
			'referrerAllArticles':'true'
			}
		s.mount(mb_url, adapter)
		asdasd = s.get(mb_url)
		html = asdasd.text
		soup = bs(html, 'html.parser')
		board_n = soup.select(boardpath)
		#board_n = soup.select_one(boardpath)
		#print(board_n)
		for i in board_n:
			ttt = i.text
			ttp = ttt.strip()
			file = BASE_DIR + '/url_' + num +'.txt'
			if not os.path.isfile(file):
				f = io.open(file,'a', encoding='utf-8')
			
			with io.open(file, 'r+' ,-1, "utf-8") as f_read:
				before = f_read.readline()
				message = ttp
				if before != message:
					tel(telgm,telgm_alim,telgm_token,telgm_botid,msg)
				else:
					tel(telgm,telgm_alim,telgm_token,telgm_botid,msg)
			with io.open(file, 'w+' ,-1, "utf-8") as f_write:
				f_write.write(message)
				f_write.close()
			
def exec_start3(startname):
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
					filename="funmom-" + str(jpeg_no) + ".jpg"
					url_to_image(url, dfolder, category, category2, filename)
					jpeg_no += 1
				add_d(id, go, complte)
				

def exec_start4(carrier_id,track_id,telgm,telgm_alim,telgm_token,telgm_botid):
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
	with requests.Session() as s:
		url = 'https://apis.tracker.delivery/carriers/' +  carrier + '/tracks/' + track_id #기본 URL
		#print(url)
		resp = s.get(url)
		html = resp.text
		jsonObject = json.loads(html)
		try:
			json_string = jsonObject.get("from").get("name") #누가 보냈냐			
			json_string2 = jsonObject.get("to").get("name") #누가 받냐
			json_string3 = jsonObject.get("state").get("text") #배송현재상태
			#json_string_m = jsonObject.get("progresses") #배송상황
			#for list in json_string_m:
			#	print(list.get("description"))
			json_string4 = jsonObject.get("carrier").get("name") #택배사
			msg = '{} 님이 {} 으로 보내신 {} 님의 현재 배송상태는 {} 입니다.'.format(json_string,json_string4,json_string2,json_string3)
		except:
			msg = '송장번호가 없는거 같습니다.'
		
		#json_string6 = json_string4.get("description")
		
		#print(jsonObject) 
		tel(telgm,telgm_alim,telgm_token,telgm_botid,msg)
		
def exec_start5(location,telgm,telgm_alim,telgm_token,telgm_botid):
	Finallocation = location + '날씨' 
	URL = 'https://www.google.com/search?client=opera&hs=iaa&ei=FHvcX9HDAtWC-QaY95HYBA&q=' + Finallocation

	headers = {
		"User-Agent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36 OPR/67.0.3575.115'}

	page = requests.get(URL, headers=headers)
	soup = bs(page.content, 'html.parser', from_encoding="utf8")
	data = soup.find("div", {"id": "wob_wc"})
	refine = data.findAll("span")

	data_list = []

	for x in refine:
		data_list.append(x.get_text())

	msg = Finallocation + ' ' + data_list[13] + '\n현재온도는 ' + data_list[0] + '\n강수확률은 ' + data_list[7] + '\n습도 : ' + data_list[8] + '\n풍속 : ' + data_list[10]
	tel(telgm,telgm_alim,telgm_token,telgm_botid,msg)

#운세알리미
def exec_start6(telgm,telgm_alim,telgm_token,telgm_botid):
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

def vietnews():
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
		
def esbsnews():
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

def ekbsnews():
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
	
def ytnsnews():
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
	
def exec_start7(telgm,telgm_alim,telgm_token,telgm_botid):	
	#SQLITE3 DB 없으면 만들다.
	#SQLITE3 DB 없으면 만들다.
	conn = sqlite3.connect(sub2db + '/news.db',timeout=60)
	conn.execute('CREATE TABLE IF NOT EXISTS news (CAST TEXT, TITLE TEXT, URL TEXT, COMPLETE TEXT, DATE TEXT)')	
	conn.close()

	sbs = esbsnews()
	kbs = ekbsnews()
	viet = vietnews()
	ytn = ytnsnews()
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
			telgm = '1'
			telgm_alim = '1'
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
			scheduler2.add_job(exec_start7, trigger=CronTrigger.from_crontab(start_time), id=startname, args=[telgm,telgm_alim,telgm_token,telgm_botid])
			test = scheduler2.get_job(startname).id
			logger.info('%s 를 스케줄러에 추가하였습니다.', test)
		except:
			pass
		return redirect(url_for('sub2.index'))
		
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
			telgm = '1'
			telgm_alim = '1'
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
			scheduler2.add_job(exec_start6, trigger=CronTrigger.from_crontab(start_time), id=startname, args=[telgm,telgm_alim,telgm_token,telgm_botid])
			test = scheduler2.get_job(startname).id
			logger.info('%s 를 스케줄러에 추가하였습니다.', test)
		except:
			pass
		return redirect(url_for('sub2.index'))
		
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
			telgm = '1'
			telgm_alim = '1'
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
			scheduler2.add_job(exec_start5, trigger=CronTrigger.from_crontab(start_time), id=startname, args=[location,telgm,telgm_alim,telgm_token,telgm_botid])
			test = scheduler2.get_job(startname).id
			logger.info('%s 를 스케줄러에 추가하였습니다.', test)
		except:
			pass
		return redirect(url_for('sub2.index'))
		
@bp2.route('tracking')
def tracking():
	#데이타베이스 없으면 생성
	conn = sqlite3.connect(sub2db + '/telegram.db',timeout=60)
	conn.execute('CREATE TABLE IF NOT EXISTS tracking (telgm_token TEXT, telgm_botid TEXT, start_time TEXT, telgm TEXT, telgm_alim TEXT)')
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
			telgm = '1'
			telgm_alim = '1'
		return render_template('tracking.html', telgm_token = telgm_token, telgm_botid = telgm_botid, start_time = start_time, telgm = telgm, telgm_alim = telgm_alim)

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
			scheduler2.add_job(exec_start4, trigger=CronTrigger.from_crontab(start_time), id=startname, args=[carrier_id,track_id,telgm,telgm_alim,telgm_token,telgm_botid])
			test = scheduler2.get_job(startname).id
			logger.info('%s 를 스케줄러에 추가하였습니다.', test)
		except:
			pass
		return redirect(url_for('sub2.index'))
		
@bp2.route('funmom')
def funmom():
	if not session.get('logFlag'):
		return redirect(url_for('main.index'))
	else:	
		return render_template('funmom.html')

@bp2.route('funmom_ok', methods=['POST'])
def funmom_ok():
	if not session.get('logFlag'):
		return redirect(url_for('main.index'))
	else:
		start_time = request.form['start_time']
		startname = request.form['startname']
		try:
			scheduler2.add_job(exec_start3, trigger=CronTrigger.from_crontab(start_time), id=startname, args=[startname])
			test = scheduler2.get_job(startname).id
			logger.info('%s 를 스케줄러에 추가하였습니다.', test)
		except:
			pass
		
		return redirect(url_for('sub2.index'))

		
@bp2.route('board', methods=['POST'])
def board():
	if session.get('logFlag') != True:
		return redirect(url_for('main.index'))
	else:

		#공통
		telgm = request.form['telgm']
		telgm_alim = request.form['telgm_alim']
		telgm_token = request.form['telgm_token']
		telgm_botid = request.form['telgm_botid']
		start_time = request.form['start_time']
		startname = request.form['startname']
		choice = request.form['choice']
		
		#네이버게시판 
		cafenum = request.form['cafenum']
		cafe = request.form['cafe']
		num = request.form['num']
		cafemenu = request.form['cafemenu']
		cafeboard = request.form['cafeboard']
		boardpath = request.form['boardpath']
		
		#게시판알림
		t_main = request.form['t_main']
		sel = request.form['sel']
		selnum = request.form['selnum']
		conn = sqlite3.connect(sub2db + '/telegram.db',timeout=60)
		cursor = conn.cursor()
		cur.execute("select * from board")
		rows = cursor.fetchone()
		if rows:
			sql = """
				update board
					set telgm_token = ?
					, telgm_botid = ?
				"""
		else:
			sql = """
				INSERT INTO board 
				(telgm_token, telgm_botid) VALUES (?, ?)
				"""
				
		cursor.execute(sql, (telgm_token, telgm_botid))
		conn.commit()
		cursor.close()
		conn.close()
		try:
			print(cafenum, cafe, num, cafemenu, cafeboard, boardpath)
		except:
			pass
		try:
			print(t_main, sel, selnum)
		except:
			pass

		try:
			print(telgm, telgm_alim, telgm_token, telgm_botid, start_time, startname) 
		except:
			pass
		if choice == 'a':
			try:
				scheduler2.add_job(exec_start, trigger=CronTrigger.from_crontab(start_time), id=startname, args=[t_main, sel, selnum, telgm, telgm_alim, telgm_token, telgm_botid] )
				test = scheduler2.get_job(startname).id
				logger.info('%s 를 스케줄러에 추가하였습니다.', test)
			except:
				pass
		if choice == 'b':
			try:
				scheduler2.add_job(exec_start2, trigger=CronTrigger.from_crontab(start_time), id=startname, args=[cafenum, cafe, num, cafemenu, cafeboard, boardpath, telgm, telgm_alim, telgm_token, telgm_botid] )
				test = scheduler2.get_job(startname).id
				logger.info('%s 를 스케줄러에 추가하였습니다.', test)
			except:
				pass
		#return render_template('board.html')
		return redirect(url_for('sub2.index'))