from flask import Blueprint
#-*- coding: utf-8 -*-
import sys
try:
	reload(sys)
	sys.setdefaultencoding('utf-8')
except:
	pass
import os, io, re, zipfile, shutil, json, time, random, base64, urllib.request, platform, logging, requests, os.path, threading, time, subprocess
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

#여기서 필요한 모듈
from datetime import datetime, timedelta
from flask import Flask, flash, redirect, render_template, request, session, abort, url_for
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.jobstores.base import BaseJobStore, JobLookupError, ConflictingIdError
from apscheduler.triggers.cron import CronTrigger

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
nowDatetime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
webtoon = Blueprint('webtoon', __name__, url_prefix='/webtoon')
job_defaults = { 'max_instances': 1 }
schedulerc = BackgroundScheduler(job_defaults=job_defaults)
f = open('./log/flask.log','a', encoding='utf-8')
rfh = logging.handlers.RotatingFileHandler(filename='./log/flask.log', mode='a', maxBytes=5*1024*1024, backupCount=2, encoding=None, delay=0)
logging.basicConfig(level=logging.INFO,format="[%(filename)s:%(lineno)d %(levelname)s] - %(message)s",handlers=[rfh])
logger = logging.getLogger()
schedulerc.start()

try:
	#DB 변경
	conn = sqlite3.connect('./webtoon.db',timeout=60)
	#카피툰
	cptoon = conn.cursor()
	cptoon_sql = "SELECT COUNT(*) AS CNTREC FROM pragma_table_info('database')"
	cptoon.execute(cptoon_sql)
	#툰코
	tnk = conn.cursor()
	tnk_sql = "SELECT COUNT(*) AS CNTREC FROM pragma_table_info('database2')"
	tnk.execute(tnk_sql)
	#뉴토끼
	ntoki = conn.cursor()
	ntoki_sql = "SELECT COUNT(*) AS CNTREC FROM pragma_table_info('database3')"
	ntoki.execute(ntoki_sql)
	#네이버
	nver = conn.cursor()
	nver_sql = "SELECT COUNT(*) AS CNTREC FROM pragma_table_info('database4')"
	nver.execute(nver_sql)

	#다음
	dum = conn.cursor()
	dum_sql = "SELECT COUNT(*) AS CNTREC FROM pragma_table_info('database5')"
	dum.execute(dum_sql)
	row = cptoon.fetchone()
	row2 = tnk.fetchone()
	row3 = ntoki.fetchone()
	row4 = nver.fetchone()
	row5 = dum.fetchone()
	if row[0] != 0:
		#print('테이블이 있다')
		conn.execute("ALTER TABLE database RENAME TO copytoon")
	else:
		print('테이블이 없다.')
	if row2[0] != 0:
		#print('테이블이 있다')
		conn.execute("ALTER TABLE database2 RENAME TO toonkor")
	else:
		print('테이블이 없다.')
	if row3[0] != 0:
		#print('테이블이 있다')
		conn.execute("ALTER TABLE database3 RENAME TO newtoki")
	else:
		print('테이블이 없다.')
	if row4[0] != 0:
		#print('테이블이 있다')
		conn.execute("ALTER TABLE database4 RENAME TO naver")
	else:
		print('테이블이 없다.')

	if row5[0] != 0:
		#print('테이블이 있다')
		conn.execute("DROP TABLE database5")
	else:
		print('테이블이 없다.')	

	#DB컬럼 추가
	conn = sqlite3.connect('./webtoon.db',timeout=60)
	cur = conn.cursor()
	cur2 = conn.cursor()
	sql = "SELECT COUNT(*) AS CNTREC FROM pragma_table_info('copytoon') WHERE name='toon'"
	cur.execute(sql)
	row = cur.fetchone()
	if row[0] == 0:
		conn.execute("ALTER TABLE copytoon ADD COLUMN toon TEXT")
		conn.execute("UPDATE copytoon SET toon = 'copytoon'")
	else:
		conn.execute("UPDATE copytoon SET toon = 'copytoon'")
		print('컬럼이 있습니다.')
	conn.close()

	conn = sqlite3.connect('./webtoon.db',timeout=60)
	cur = conn.cursor()
	cur2 = conn.cursor()
	sql = "SELECT COUNT(*) AS CNTREC FROM pragma_table_info('toonkor') WHERE name='toon'"
	cur.execute(sql)
	row = cur.fetchone()
	if row[0] == 0:
		conn.execute("ALTER TABLE toonkor ADD COLUMN toon TEXT")
		conn.execute("UPDATE toonkor SET toon = 'toonkor'")
	else:
		conn.execute("UPDATE toonkor SET toon = 'toonkor'")
		print('컬럼이 있습니다.')
	conn.close()

	conn = sqlite3.connect('./webtoon.db',timeout=60)
	cur = conn.cursor()
	cur2 = conn.cursor()
	sql = "SELECT COUNT(*) AS CNTREC FROM pragma_table_info('newtoki') WHERE name='toon'"
	cur.execute(sql)
	row = cur.fetchone()
	if row[0] == 0:
		conn.execute("ALTER TABLE newtoki ADD COLUMN toon TEXT")
		conn.execute("UPDATE newtoki SET toon = 'newtoki'")
	else:
		conn.execute("UPDATE newtoki SET toon = 'newtoki'")
		print('컬럼이 있습니다.')
	conn.close()

	conn = sqlite3.connect('./webtoon.db',timeout=60)
	cur = conn.cursor()
	cur2 = conn.cursor()
	sql = "SELECT COUNT(*) AS CNTREC FROM pragma_table_info('naver') WHERE name='toon'"
	cur.execute(sql)
	row = cur.fetchone()
	if row[0] == 0:
		conn.execute("ALTER TABLE naver ADD COLUMN toon TEXT")
		conn.execute("UPDATE naver SET toon = 'naver'")
	else:
		conn.execute("UPDATE naver SET toon = 'naver'")
		print('컬럼이 있습니다.')
	conn.close()
except:
	pass


@webtoon.route('/')
@webtoon.route('index')
def index():
	if not session.get('logFlag'):
		return redirect(url_for('main.index'))
	else:
		tltl = []
		test2 = schedulerc.get_jobs()
		for i in test2:
			aa = i.id
			tltl.append(aa)
		#t_main = request.form['t_main']
		return render_template('webtoon_index.html', tltl = tltl)

@webtoon.route('copytoon')
def second():
	if not session.get('logFlag'):
		return redirect(url_for('main.index'))
	else:
		rows = []
		con = sqlite3.connect("./webtoon.db")
		con.row_factory = sqlite3.Row
		cur = con.cursor()
		try:
			cur.execute("select * from copytoon where complte = 'False'")
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
			cur.execute("select * from copytoon where complte = 'PASS'")
			rows2 = cur.fetchall()
			for i2 in rows2:
				i2 = count2
				count2 += 1
			rows.append(i2)
		except:	
			i2 = '0'	
			rows.append(i2)
		try:
			count3 = 1
			cur.execute("select * from copytoon where complte = 'True'")
			rows3 = cur.fetchall()
			for i3 in rows3:
				i3 = count3
				count3 += 1
			rows.append(i3)
		except:	
			i3 = '0'
			rows.append(i3)
		return render_template('copytoon.html', rows = rows)

@webtoon.route('toonkor')
def second2():
	if not session.get('logFlag'):
		return redirect(url_for('main.index'))
	else:
		rows = []
		con = sqlite3.connect("./webtoon.db")
		con.row_factory = sqlite3.Row
		cur = con.cursor()
		try:
			cur.execute("select * from toonkor where complte = 'False'")
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
			cur.execute("select * from toonkor where complte = 'PASS'")
			rows2 = cur.fetchall()
			for i2 in rows2:
				i2 = count2
				count2 += 1
			rows.append(i2)
		except:	
			i2 = '0'	
			rows.append(i2)
		try:
			count3 = 1
			cur.execute("select * from toonkor where complte = 'True'")
			rows3 = cur.fetchall()
			for i3 in rows3:
				i3 = count3
				count3 += 1
			rows.append(i3)
		except:	
			i3 = '0'
			rows.append(i3)

		return render_template('toonkor.html', rows = rows) 

@webtoon.route('newtoki')
def second3():
	if not session.get('logFlag'):
		return redirect(url_for('main.index'))
	else:
		rows = []
		con = sqlite3.connect("./webtoon.db")
		con.row_factory = sqlite3.Row
		cur = con.cursor()
		try:
			cur.execute("select * from newtoki where complte = 'False'")
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
			cur.execute("select * from newtoki where complte = 'PASS'")
			rows2 = cur.fetchall()
			for i2 in rows2:
				i2 = count2
				count2 += 1
			rows.append(i2)
		except:	
			i2 = '0'	
			rows.append(i2)
		try:
			count3 = 1
			cur.execute("select * from newtoki where complte = 'True'")
			rows3 = cur.fetchall()
			for i3 in rows3:
				i3 = count3
				count3 += 1
			rows.append(i3)
		except:	
			i3 = '0'
			rows.append(i3)

		return render_template('newtoki.html', rows = rows)

@webtoon.route('naver')
def second4():
	if not session.get('logFlag'):
		return redirect(url_for('main.index'))
	else:
		rows = []
		con = sqlite3.connect("./webtoon.db")
		con.row_factory = sqlite3.Row
		cur = con.cursor()
		try:
			cur.execute("select * from naver where complte = 'False'")
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
			cur.execute("select * from naver where complte = 'PASS'")
			rows2 = cur.fetchall()
			for i2 in rows2:
				i2 = count2
				count2 += 1
			rows.append(i2)
		except:	
			i2 = '0'	
			rows.append(i2)
		try:
			count3 = 1
			cur.execute("select * from naver where complte = 'True'")
			rows3 = cur.fetchall()
			for i3 in rows3:
				i3 = count3
				count3 += 1
			rows.append(i3)
		except:	
			i3 = '0'
			rows.append(i3)

		return render_template('naver.html', rows = rows)

@webtoon.route('dozi')
def second5():
	if not session.get('logFlag'):
		return redirect(url_for('main.index'))
	else:
		rows = []
		con = sqlite3.connect("./webtoon.db")
		con.row_factory = sqlite3.Row
		cur = con.cursor()
		try:
			cur.execute("select * from dozi where complte = 'False'")
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
			cur.execute("select * from dozi where complte = 'PASS'")
			rows2 = cur.fetchall()
			for i2 in rows2:
				i2 = count2
				count2 += 1
			rows.append(i2)
		except:	
			i2 = '0'	
			rows.append(i2)
		try:
			count3 = 1
			cur.execute("select * from dozi where complte = 'True'")
			rows3 = cur.fetchall()
			for i3 in rows3:
				i3 = count3
				count3 += 1
			rows.append(i3)
		except:	
			i3 = '0'
			rows.append(i3)

		return render_template('dozi.html', rows = rows)	
		
def cleanText(readData):
	#텍스트에 포함되어 있는 특수 문자 제거
	text = readData.replace('/', '')
	text = re.sub('[-\\/:*?\"<>|]', '', text).strip()
	text = re.sub("\s{2,}", ' ', text)
	return text	

def url_to_image(subtitle, title, url, filename, dfolder):
	header = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.101 Safari/537.36"}
	with requests.Session() as s:
		try:
			time.sleep(random.uniform(2,5)) 
			req = s.get(url,headers=header)	
		except:
			time.sleep(random.uniform(2,5)) 
			req = s.get(url,headers=header)	
	
	title2 = title.strip()
	subtitle2 = subtitle.strip()
	parse = cleanText(title2)
	parse2 = cleanText(subtitle2)
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
			
def manazip(subtitle, title, filename, dfolder, cbz, packege):
	title2 = title.strip()
	subtitle2 = subtitle.strip()
	parse = cleanText(title2)
	parse2 = cleanText(subtitle2)
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
	shutil.rmtree(dfolder + '/{}/{}'.format(parse,parse2))
	print('{}  압축 완료'.format(parse))				
	logger.info('%s / %s / %s  압축 완료', packege, parse, parse2)
	
@webtoon.route('db_reset', methods=['POST'])
def db_reset():
	if not session.get('logFlag'):
		return redirect(url_for('main.index'))
	else:
		packege = request.form['packege']
		try:
			time.sleep(random.uniform(2,10)) 
			con = sqlite3.connect('./webtoon.db')
			cur = con.cursor()
			cur.execute("delete from "+ packege)
			con.commit()
		except:
			con.rollback()
		finally:		
			con.close()

		return redirect(url_for('main.index'))

@webtoon.route('db_redown', methods=['POST'])
def db_redown():
	if not session.get('logFlag'):
		return redirect(url_for('main.index'))
	else:
		packege = request.form['packege']
		try:
			time.sleep(random.uniform(2,10)) 
			con = sqlite3.connect('./webtoon.db')
			cur = con.cursor()
			sql = "UPDATE " + packege + " SET complte = ?"
			cur.execute(sql,('False',))
			con.commit()
		except:
			con.rollback()
		finally:		
			con.close()
		return redirect(url_for('main.index'))

@webtoon.route('db_repass', methods=['POST'])
def db_repass():
	if not session.get('logFlag'):
		return redirect(url_for('main.index'))
	else:
		packege = request.form['packege']
		try:
			time.sleep(random.uniform(2,10)) 
			con = sqlite3.connect('./webtoon.db',timeout=60)
			cur = con.cursor()
			sql = "UPDATE " + packege + " SET complte = ? WHERE complte = ?"
			cur.execute(sql,('False','PASS'))
			con.commit()
		except:
			con.rollback()
		finally:		
			con.close()
		return redirect(url_for('main.index'))
		
def add_c(packege, a, b, c, d, atat):
	print(packege, a, b , c ,d, atat)
	try:
		#데이타베이스 없으면 생성
		conn = sqlite3.connect('./webtoon.db',timeout=60)
		sql = "CREATE TABLE IF NOT EXISTS " + packege + " (maintitle TEXT, subtitle TEXT, urltitle TEXT, complte TEXT, toon TEXT)"
		conn.execute(sql)
		conn.close()
		time.sleep(random.uniform(2,10)) 
		print(packege, a, b , c ,d, atat)
		con = sqlite3.connect('./webtoon.db')
		cur = con.cursor()
		sql = "select * from " + packege + " where urltitle = ?"
		cur.execute(sql, (c,))
		row = cur.fetchone()
		if row != None:
			pass
		else:
			cur.execute("INSERT OR REPLACE INTO " + packege + " (maintitle, subtitle, urltitle, complte, toon) VALUES (?, ?, ?, ?, ?)", (a,b,c,d,atat))
			con.commit()
	except:
		con.rollback()
	finally:		
		con.close()

def add_d(packege, subtitle, title):
	try:
		#데이타베이스 없으면 생성
		conn = sqlite3.connect('./webtoon.db',timeout=60)
		sql = "CREATE TABLE IF NOT EXISTS " + packege + " (maintitle TEXT, subtitle TEXT, urltitle TEXT, complte TEXT, toon TEXT)"
		conn.execute(sql)
		conn.close()
		time.sleep(random.uniform(2,10)) 
		#마지막 실행까지 작업안했던 결과물 저장
		con = sqlite3.connect('./webtoon.db')
		cur = con.cursor()
		sql = "UPDATE " + packege + " SET complte = ? WHERE subtitle = ? AND maintitle = ?"
		cur.execute(sql,('True',subtitle, title))
		con.commit()
	except:
		con.rollback()
	finally:	
		con.close()	
		
def add_pass(packege, subtitle, title):
	try:
		#데이타베이스 없으면 생성
		conn = sqlite3.connect('./webtoon.db',timeout=60)
		sql = "CREATE TABLE IF NOT EXISTS " + packege + " (maintitle TEXT, subtitle TEXT, urltitle TEXT, complte TEXT, toon TEXT)"
		conn.execute(sql)
		conn.close()
		time.sleep(random.uniform(2,10)) 
		#마지막 실행까지 작업안했던 결과물 저장
		con = sqlite3.connect('./webtoon.db')
		cur = con.cursor()
		sql = "UPDATE " + packege + " SET complte = ? WHERE subtitle = ? AND maintitle = ?"
		cur.execute(sql,('PASS',subtitle, title))
		con.commit()
	except:
		con.rollback()
	finally:	
		con.close()			
def checkURL(url2):
	user_agent = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.7) Gecko/2009021910 Firefox/3.0.7'
	headers={'User-Agent':user_agent,} 
	try:
		 request=urllib.request.Request(url2,None,headers) #The assembled request
		 response = urllib.request.urlopen(request,timeout=3)
	except:
		print('The server couldn\'t fulfill the request. %s'% url2)     
	else:
		data = response.read()
		#print(html)
		data = data.decode()     
		result = 0
		result = data.find(url2)     
		if result > 0:
			print ("Website is working fine %s "% url2)
			return 9999       
		return response.status		
		
def exec_start(t_main, code, packege,startname):
	print("카피툰시작")
	logger.info('카피툰시작')
	newURL = t_main
	maintitle = []
	maintitle2 = []
	subtitle = []
	urltitle = []
	header = {"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5)\AppleWebKit 537.36 (KHTML, like Gecko) Chrome","Accept":"text/html,application/xhtml+xml,application/xml;\q=0.9,imgwebp,*/*;q=0.8"}
	for i in range(245,500):
		url2 = ("https://copytoon%s.com" % (i))
		time.sleep(2)
		result = checkURL(url2)
		text_file_path = os.getcwd() + '/templates/copytoon.html'
		new_text_content = ''
		target_word = t_main
		if result == 9999:
			with open(text_file_path,'r',encoding='utf-8') as f:
				lines = f.readlines()
				for i, l in enumerate(lines):
					new_string = l.strip().replace(target_word,url2)
					if new_string:
						new_text_content += new_string + '\n'
					else:
						new_text_content += '\n'
			with open(text_file_path,'w',encoding='utf-8') as f:
				f.write(new_text_content)
			break	
	with requests.Session() as s:
		t_main = url2
		print(url2)
		if code == 'all':
			response = s.get(t_main,headers=header)
			html = response.text
			soup = bs(html, "html.parser").findAll("div",{"class":"section-item-title"})
			for tag in soup:
				url = tag.find('a')
				maintitle.append(url["href"])
		else:
			allcode = code.split('|')
			for i in allcode:
				t_maincode = t_main + i
				maintitle.append(i)
				
		for mainurl in maintitle:
			url = mainurl.lstrip()
			wkt = url
			wat = wkt.replace("/", "")
			title = wat.replace(".html", "")
			if code == 'all':
				all = t_main + url
			else:
				all = t_main + '/' + url
			print('{} 의 {} 을 찾았습니다. {}'.format(packege, all, nowDatetime))
			logger.info('%s 의 %s 을 찾았습니다. %s', packege, all, nowDatetime)
			response1 = s.get(all,headers=header)
			html = response1.text
			soup = bs(html, "html.parser")
			mm = soup.find("div",{"class":"contents-list"})
			try:
				toonlist = mm.findAll('a')
				count = []
				for post in toonlist:
					count.append(post["href"])
				test22 = len(count)
				cc = int(test22)
				for post in toonlist:
					urltitle.append(post["href"])
					sub = '{}화'.format(cc)
					maintitle2.append(title)
					subtitle.append(sub)
					cc -= 1
			except:
				pass
		#print(subtitle) #소제목
		#print(urltitle) #웹툰주소
		#print(maintitle) #대제목
		#대제목 소제목 다운로드url 주소를 DB에 저장한다.
		for a,b,c in zip(maintitle2,subtitle,urltitle):
			d = "False" #처음에 등록할때 무조건 False 로 등록한다.
			atat = packege
			add_c(packege, a,b,c,d, atat)
			logger.info('%s 의 %s 의 %s 를 등록하였습니다.', packege, a, b)
		try:
			test = schedulerc.get_job(startname).id
			logger.info('%s가 스케줄러에 있습니다.', test)
		except Exception as e:
			test = None
		if test == None:
			logger.info('%s의 스케줄러가 종료가 되지 않았습니다.', startname)
		else:
			schedulerc.remove_job(startname)
			schedulerc.start()
			logger.info('%s 스케줄러를 삭제하였습니다.', test)
			test2 = schedulerc.get_jobs()
			for i in test2:
				aa = i.id
				logger.info('%s 가 스케줄러가 있습니다.', aa)
			
def exec_start2(t_main, code, packege,startname):
	print("툰코시작")
	logger.info('툰코시작')
	maintitle = []
	maintitle2 = [] #대제목 2번째 DB를 위한 작업공간
	subtitle = []
	urltitle = []
	header = {"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5)\AppleWebKit 537.36 (KHTML, like Gecko) Chrome","Accept":"text/html,application/xhtml+xml,application/xml;\q=0.9,imgwebp,*/*;q=0.8"}
	with requests.Session() as s:		
		url2 = 'https://t.me/s/new_toonkor'
		req = s.get(url2)
		html = req.text
		ttt = re.compile(r'<a href="(.*?)"').findall(html)
		n = len(ttt)
		if ttt[n-2] == 'https://t.me/new_toonkor':
			tta = ttt[n-1]
		else:
			tta = ttt[n-2]
		final_str = tta
		logger.info(final_str)
		text_file_path = os.getcwd() + '/templates/toonkor.html'
		new_text_content = ''
		target_word = t_main
		with open(text_file_path,'r',encoding='utf-8') as f:
			lines = f.readlines()
			for i, l in enumerate(lines):
				new_string = l.strip().replace(target_word,final_str)
				if new_string:
					new_text_content += new_string + '\n'
				else:
					new_text_content += '\n'
		with open(text_file_path,'w',encoding='utf-8') as f:
			f.write(new_text_content)
		t_main = final_str
		print(t_main)
		if code == 'all':
			response = s.get(t_main,headers=header)
			time.sleep(random.uniform(2,5)) 	
			html = response.text
			soup = bs(html, "html.parser").findAll("a",{"id":"title"})
			for tag in soup:
				latest = tag['href']
				aa = latest.replace("/", "")
				maintitle.append(aa)
		else:
			allcode = code.split('|')
			for i in allcode:
				t_maincode = t_main + i
				maintitle.append(i)
				
		for mainurl in maintitle:
			test = mainurl
			all = t_main + '/' + test
			print('{} 의 {} 을 찾았습니다. {}'.format(packege, all, nowDatetime))
			logger.info('%s 의 %s 을 찾았습니다. %s', packege, all, nowDatetime)
			response1 = s.get(all,headers=header)
			time.sleep(random.uniform(2,5)) 
			html = response1.text
			soup2 = bs(html, "html.parser").find("table",{"class":"web_list"})
			try:
				toonview_list = soup2.findAll("tr",{"class":"tborder"})
				count = []
				for post in toonview_list:
					post = post.find("td",{"class":"content__title"})
					url3 = post.attrs['data-role']
					count.append(url3)
				test22 = len(count)
				cc = int(test22)
				for post in toonview_list:
					post = post.find("td",{"class":"content__title"})
					title = post.get_text().lstrip()
					url3 = post.attrs['data-role']
					title = '{}화'.format(cc)
					urltitle.append(url3)
					subtitle.append(title)	
					maintitle2.append(mainurl)
					cc -= 1					
			except:
				pass
		
		#앞에서 크롤링한 정보를 DB에 저장한다.
		for a,b,c in zip(maintitle2,subtitle,urltitle):
			d = "False" #처음에 등록할때 무조건 False 로 등록한다.	
			atat = packege
			add_c(packege, a,b,c,d, atat)
			logger.info('%s 의 %s 의 %s 를 등록하였습니다.', packege, a, b)
		try:
			test = schedulerc.get_job(startname).id
			logger.info('%s가 스케줄러에 있습니다.', test)
		except Exception as e:
			test = None
		if test == None:
			logger.info('%s의 스케줄러가 종료가 되지 않았습니다.', startname)
		else:
			schedulerc.remove_job(startname)
			schedulerc.start()
			logger.info('%s 스케줄러를 삭제하였습니다.', test)
			test2 = schedulerc.get_jobs()
			for i in test2:
				aa = i.id
				logger.info('%s 가 스케줄러가 있습니다.', aa)
			
def exec_start3(t_main,code,packege,genre,startname):
	print("뉴토끼시작")
	logger.info('뉴토끼시작')
	packege = 'newtoki'
	main_list = [] #url 주소를 만든다.
	maintitle = [] #대제목이 저장된다
	maintitle2 = [] #대제목 2번째 DB를 위한 작업공간
	subtitle = [] #소제목이 저장된다.
	urltitle = []
	header = {"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5)\AppleWebKit 537.36 (KHTML, like Gecko) Chrome","Accept":"text/html,application/xhtml+xml,application/xml;\q=0.9,imgwebp,*/*;q=0.8"}
	for i in range(116,500):
		url2 = ("https://newtoki%s.com" % (i))
		time.sleep(2)
		result = checkURL(url2)
		text_file_path = os.getcwd() + '/templates/newtoki.html'
		new_text_content = ''
		target_word = t_main
		if result == 9999:
			with open(text_file_path,'r',encoding='utf-8') as f:
				lines = f.readlines()
				for i, l in enumerate(lines):
					new_string = l.strip().replace(target_word,url2)
					if new_string:
						new_text_content += new_string + '\n'
					else:
						new_text_content += '\n'
			with open(text_file_path,'w',encoding='utf-8') as f:
				f.write(new_text_content)
			break
	with requests.Session() as s:
		if code == 'all':
			for page in range(1,11): 
				main_url = t_main + '/webtoon/p' + str(page) + '?toon=' + genre
				time.sleep(random.uniform(30,60)) 
				req = s.get(main_url)	
				html = req.text
				gogo = bs(html, "html.parser")
				posts = gogo.find_all(attrs = {'class':'img-item'})
				posts_list = gogo.find(attrs = {'class':'img-item'})
				if posts_list is None: 
					pass
				else:	
					for i in posts:
						a_link = i('a')
						a_href = a_link[1]['href'].split('webtoon/')[1].split('/')[0]
						main_url = t_main + '/webtoon/' + a_href
						main_list.append(main_url)
		else:	
			allcode = code.split('|')
			for i in allcode:
				main_url = t_main + '/webtoon/' + i	
				main_list.append(main_url)
		
		for a in main_list :
			print('{} 의 {} 을 찾았습니다. {}'.format(packege, a, nowDatetime))
			logger.info('%s 의 %s 을 찾았습니다. %s', packege, a, nowDatetime)
			time.sleep(random.uniform(30,60))
			try:
				req = s.get(a,headers=header)
			except:
				print("캡챠있다.")
				logger.info('캡챠있다')
				continue
			html = req.text
			gogo = bs(html, "html.parser")
			title = gogo.find(attrs={'class':'page-desc'})
			cacha = gogo.find("div",{"class":"form-header"})
			data_tmp = title.text.lstrip() #대제목	
			posts_list = gogo.find_all(attrs = {'class':'item-subject'})
			count = []
				
			if cacha:
				print("캡챠있다.")
				continue
			else:
				for b in posts_list:
					a_link = b['href']
					count.append(a_link)
				test22 = len(count)
				cc = int(test22)
				for b in posts_list:
					aa = b.find('b')
					a_link = b['href']
					a_link2 = a_link.replace(t_main,'')
					aa_tmp = '{}화'.format(cc)
					maintitle.append(data_tmp) #대제목이다.
					subtitle.append(aa_tmp) #소제목이다.
					urltitle.append(a_link2) #URL 주소가 저장된다.
					cc -= 1
				
		#앞에서 크롤링한 정보를 DB에 저장한다.
		for a,b,c in zip(maintitle,subtitle,urltitle):
			d = "False" #처음에 등록할때 무조건 False 로 등록한다.
			atat = packege
			add_c(packege, a,b,c,d, atat)
			logger.info('%s 의 %s 의 %s 를 등록하였습니다.', packege, a, b)
		try:
			test = schedulerc.get_job(startname).id
			logger.info('%s가 스케줄러에 있습니다.', test)
		except Exception as e:
			test = None
		if test == None:
			logger.info('%s의 스케줄러가 종료가 되지 않았습니다.', startname)
		else:
			schedulerc.remove_job(startname)
			schedulerc.start()
			logger.info('%s 스케줄러를 삭제하였습니다.', test)
			test2 = schedulerc.get_jobs()
			for i in test2:
				aa = i.id
				logger.info('%s 가 스케줄러가 있습니다.', aa)
		
def exec_start4(code,packege,startname):
	print("네이버웹툰시작")
	logger.info('네이버웹툰시작')
	packege = 'naver'
	maintitle = []
	subtitle = []
	urltitle = []
	titleid = []
	header = {"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5)\AppleWebKit 537.36 (KHTML, like Gecko) Chrome","Accept":"text/html,application/xhtml+xml,application/xml;\q=0.9,imgwebp,*/*;q=0.8"}
	with requests.Session() as s:
		url = 'https://comic.naver.com/webtoon/weekday.nhn'
		response = s.get(url,headers=header)
		html = response.text
		soup = bs(html, "html.parser")
		tags = soup.findAll("div",{"class":"thumb"})
		if code == 'all':
			#전체 웹툰코드를 받아온다. 
			for tag in tags:		
				href = tag.find('a')['href']
				title_id = href.split('titleId=')[1].split('&')[0].strip()
				titleid.append(title_id)
		else:
			allcode = code.split('|')
			for i in allcode:
				t_maincode = i
				titleid.append(i)			

		for i in titleid:
			print('{} 의 {} 을 찾았습니다. {}'.format(packege, i, nowDatetime))
			logger.info('%s 의 %s 을 찾았습니다. %s', packege, i, nowDatetime)
			suburl = 'https://comic.naver.com/webtoon/list.nhn?titleId=' + i
			response = s.get(suburl,headers=header)
			html = response.text
			soup = bs(html, "html.parser")
			#대제목을 가져온다.
			tags = soup.find("div",{"class":"detail"})
			tt2 = tags.find('span',{'class':'title'}).text
					
			for p in range(1, 1001):
				pageurl = 'https://comic.naver.com/webtoon/list.nhn?titleId=' + i + '&page=' + str(p)
				response = s.get(pageurl,headers=header)
				html = response.text
				soup = bs(html, "html.parser")
				sublist = soup.findAll("td",{"class":"title"})
				pageend = soup.find("a",{"class":"next"})		
				
				if pageend:
					for ii in sublist:
						test = ii.find('a')['href']
						cc = test.split('no=')[1].split('&')[0].strip()
						test2 = '{}화'.format(cc)
						maintitle.append(tt2)
						subtitle.append(test2)
						urltitle.append(test)
						#cc -= 1
				else:
					for ii in sublist:
						test = ii.find('a')['href']
						cc = test.split('no=')[1].split('&')[0].strip()
						test2 = '{}화'.format(cc)
						maintitle.append(tt2)
						subtitle.append(test2)
						urltitle.append(test)
						#cc -= 1	
					break				
				
		#앞에서 크롤링한 정보를 DB에 저장한다.
		for a,b,c in zip(maintitle,subtitle,urltitle):
			d = "False" #처음에 등록할때 무조건 False 로 등록한다.	
			atat = packege
			add_c(packege, a,b,c,d, atat)
			logger.info('%s 의 %s 의 %s 를 등록하였습니다.', packege, a, b)
		try:
			test = schedulerc.get_job(startname).id
			logger.info('%s가 스케줄러에 있습니다.', test)
		except Exception as e:
			test = None
		if test == None:
			logger.info('%s의 스케줄러가 종료가 되지 않았습니다.', startname)
		else:
			schedulerc.remove_job(startname)
			schedulerc.start()
			logger.info('%s 스케줄러를 삭제하였습니다.', test)
			test2 = schedulerc.get_jobs()
			for i in test2:
				aa = i.id
				logger.info('%s 가 스케줄러가 있습니다.', aa)

#도지코믹스
def exec_start5(t_main, packege,startname):
	header = {"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5)\AppleWebKit 537.36 (KHTML, like Gecko) Chrome","Accept":"text/html,application/xhtml+xml,application/xml;\q=0.9,imgwebp,*/*;q=0.8"}
	for i in range(30,500):
		str_zoro = str(i).zfill(3)
		url2 = ("https://dozi%s.com" % (str_zoro))		
		time.sleep(2)
		result = checkURL(url2)
		text_file_path = os.getcwd() + '/templates/dozi.html'
		new_text_content = ''
		target_word = t_main
		if result == 9999:
			with open(text_file_path,'r',encoding='utf-8') as f:
				lines = f.readlines()
				for i, l in enumerate(lines):
					new_string = l.strip().replace(target_word,url2)
					if new_string:
						new_text_content += new_string + '\n'
					else:
						new_text_content += '\n'
			with open(text_file_path,'w',encoding='utf-8') as f:
				f.write(new_text_content)
			break
	with requests.Session() as s:
		t_main = url2 + '/%EC%97%85%EB%8D%B0%EC%9D%B4%ED%8A%B8'		
		response = s.get(t_main,headers=header)
		html = response.text
		soup = bs(html, "html.parser").findAll("div",{"class":"section-item-inner"})
		for tag in soup:
			#웹툰 소스
			toon = tag.find('div',{'class':'toon-company'})
			try:
				mytoon = toon.find('img')['title']
			except:
				mytoon = '기타'
				#URL 주소
			urlfind = tag.find('a') 
			url = urlfind['href']#메인 URL주소
			title = urlfind['alt'] #대제목
			#회차목록과 주소를 가져온다.
			response1 = s.get(url,headers=header)
			html = response1.text
			soup = bs(html, "html.parser")
			mm = soup.findAll("td",{"name":"view_list"})
			sublist = len(mm)
			cc = int(sublist)
			for ii in mm:
				test = ii['data-role'] #url subtitle
				test2 = ii['alt'] #subtitle name
				atat = mytoon
				a = title
				b = cc
				c = test
				d = 'False'
				print('{} {} {}\n{}'.format(atat, a, b, c))
				add_c(packege, atat, a, b, c, d)
				cc -= 1
	try:
		test = schedulerc.get_job(startname).id
		logger.info('%s가 스케줄러에 있습니다.', test)
	except Exception as e:
		test = None
	if test == None:
		logger.info('%s의 스케줄러가 종료가 되지 않았습니다.', startname)
	else:
		schedulerc.remove_job(startname)
		schedulerc.start()
		logger.info('%s 스케줄러를 삭제하였습니다.', test)
		test2 = schedulerc.get_jobs()
		for i in test2:
			aa = i.id
			logger.info('%s 가 스케줄러가 있습니다.', aa)

#새주소 받아오기
def new_url(packege, t_main):
	if packege == 'copytoon':
		for i in range(245,500):
			url2 = ("https://copytoon%s.com" % (i))
			time.sleep(2)
			result = checkURL(url2)			
			text_file_path = os.getcwd() + '/templates/copytoon.html'
			new_text_content = ''
			target_word = t_main		
			if result == 9999:				
				print("new down url : " + url2)
				print(text_file_path)
				with open(text_file_path,'r',encoding='utf-8') as f:
					lines = f.readlines()
					for i, l in enumerate(lines):
						new_string = l.strip().replace(target_word,url2)
						if new_string:
							new_text_content += new_string + '\n'
						else:
							new_text_content += '\n'
				with open(text_file_path,'w',encoding='utf-8') as f:
					f.write(new_text_content)
				break
		newurl = url2
	elif packege == 'naver':
		newurl = 'https://comic.naver.com'
	elif packege == 'dozi':	
		for i in range(30,500):
			str_zoro = str(i).zfill(3)
			url2 = ("https://dozi%s.com" % (str_zoro))		
			time.sleep(2)
			result = checkURL(url2)
			text_file_path = os.getcwd() + '/templates/dozi.html'
			new_text_content = ''
			target_word = t_main
			if result == 9999:
				with open(text_file_path,'r',encoding='utf-8') as f:
					lines = f.readlines()
					for i, l in enumerate(lines):
						new_string = l.strip().replace(target_word,url2)
						if new_string:
							new_text_content += new_string + '\n'
						else:
							new_text_content += '\n'
				with open(text_file_path,'w',encoding='utf-8') as f:
					f.write(new_text_content)
				break
		newurl = url2
	elif packege == 'newtoki':	
		for i in range(116,500):
			url2 = ("https://newtoki%s.com" % (i))
			time.sleep(2)
			result = checkURL(url2)			
			text_file_path = os.getcwd() + '/templates/newtoki.html'
			new_text_content = ''
			target_word = t_main	
			if result == 9999:			
				print("new url : " + url2)
				print(text_file_path)
				with open(text_file_path,'r',encoding='utf-8') as f:
					lines = f.readlines()
					for i, l in enumerate(lines):
						new_string = l.strip().replace(target_word,url2)
						if new_string:
							new_text_content += new_string + '\n'
						else:
							new_text_content += '\n'
				with open(text_file_path,'w',encoding='utf-8') as f:
					f.write(new_text_content)
				break
		newurl = url2
	elif packege == 'toonkor':
		with requests.Session() as s:
			url2 = 'https://t.me/s/new_toonkor'
			req = s.get(url2)
			html = req.text
			ttt = re.compile(r'<a href="(.*?)"').findall(html)
			n = len(ttt)
			if ttt[n-2] == 'https://t.me/new_toonkor':
				tta = ttt[n-1]
			else:
				tta = ttt[n-2]
			final_str = tta[:-1]
			text_file_path = os.getcwd() + '/templates/toonkor.html'
			new_text_content = ''
			target_word = t_main
			
			with open(text_file_path,'r',encoding='utf-8') as f:
				lines = f.readlines()
				for i, l in enumerate(lines):
					new_string = l.strip().replace(target_word,final_str)
					if new_string:
						new_text_content += new_string + '\n'
					else:
						new_text_content += '\n'
			with open(text_file_path,'w',encoding='utf-8') as f:
				f.write(new_text_content)	
			newurl = final_str	
	return newurl
	
#공통 다운로드	
def godown(t_main, compress, cbz, packege , startname):	
	#데이타베이스 없으면 생성
	conn = sqlite3.connect('./webtoon.db',timeout=60)
	sql = "CREATE TABLE IF NOT EXISTS " + packege + " (maintitle TEXT, subtitle TEXT, urltitle TEXT, complte TEXT, toon TEXT)"
	conn.execute(sql)
	conn.close()
	#DB 목록을 받아와 다운로드를 진행한다.
	con = sqlite3.connect('./webtoon.db',timeout=60)
	cur = con.cursor()
	sql = "select * from " + packege + " where complte = 'False'"
	cur.execute(sql)
	row = cur.fetchall()
	session2 = requests.Session()
	header = {"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5)\AppleWebKit 537.36 (KHTML, like Gecko) Chrome","Accept":"text/html,application/xhtml+xml,application/xml;\q=0.9,imgwebp,*/*;q=0.8"}	
	for i in row:
		title_old = i[0]
		title = "".join(title_old.split())
		title_old = i[1]
		subtitle = "".join(title_old.split())
		url = i[2]
		complte = i[3]
		newurl = new_url(packege, t_main)
		wwwkt = newurl + url
		logger.info('%s', wwwkt)
		try:
			response1 = session2.get(wwwkt,headers=header)
			html = response1.text
			st = response1.status_code
			logger.info('%s 의 상태는 %s', packege, st)
			soup = bs(html, "html.parser")
			print("{}에서 {} 의 {} 을 시작합니다".format(packege,title, subtitle))
			logger.info('%s에서 %s 의 %s 을 시작합니다', packege,title, subtitle)
			if packege == 'toonkor':
				tt = re.search(r'var toon_img = (.*?);', html, re.S)
				json_string = tt.group(1)
				obj = str(base64.b64decode(json_string), encoding='utf-8')
				taglist = re.compile(r'src="(.*?)"').findall(obj)
				logger.info('%s', taglist)
			elif packege == 'newtoki':
				time.sleep(random.uniform(30,60))
				tmp = ''.join(re.compile(r'html_data\+\=\'(.*?)\'\;').findall(html))
				html = ''.join([chr(int(x, 16)) for x in tmp.rstrip('.').split('.')])
				taglist = re.compile(r'src="/img/loading-image.gif"\sdata\-\w{11}="(.*?)"').findall(html)
			elif packege == 'naver':
				obj = soup.find("div",{"class":"wt_viewer"})
				taglist = obj.findAll("img")
			elif packege == 'dozi':
				tt = re.search(r'var tnimg = (.*?);', html, re.S) #툰코와 비슷함 이부분만 다름
				json_string = tt.group(1)
				obj = str(base64.b64decode(json_string), encoding='utf-8')
				taglist = re.compile(r'src="(.*?)"').findall(obj)
			elif packege == 'copytoon':
				obj = soup.find("div",{"id":"bo_v_con"})
				taglist = obj.findAll("img")
			else:
				logger.info('%s',t_main)
				continue

			urls = []
			
			for img in taglist:
				if packege == 'toonkor' or packege == 'newtoki':
					urls.append(img)
				else:
					urls.append(img['src'])
			jpeg_no = 00
			
			if platform.system() == 'Windows':
				at = os.path.splitdrive(os.getcwd())
				root = at[0] + '/data'
			else:
				root = '/data'
			
			dfolder = root + '/' + packege
			for url in urls:
				filename = str(jpeg_no+1).zfill(3) + ".jpg"
				if 'https://' in url:
					url_to_image(subtitle, title, url, filename, dfolder)
				elif 'http://' in url:
					url_to_image(subtitle, title, url, filename, dfolder)
				elif 'https://zerotoon.com/' in url:
					pass
				else:
					domain = t_main + url
					url_to_image(subtitle, title, domain, filename, dfolder)
				
				jpeg_no += 1

			if compress == '0':
				manazip(subtitle, title, filename, dfolder, cbz, packege)
			else:
				pass
		except:
			add_pass(packege, subtitle, title)
			logger.info('%s에서 %s 의 %s 을 링크가 없으므로 다음부터 실행하지 않습니다.', packege,title, subtitle)
		else:
			add_d(packege, subtitle, title)
			logger.info('%s 의 %s 의 %s 를 등록하였습니다.', packege, title, subtitle)
		
@webtoon.route('naver_list', methods=['POST'])
def naver_list():
	if session.get('logFlag') != True:
		return redirect(url_for('main.index'))
	else:
		packege = request.form['packege']
		code = request.form['code']
		compress = request.form['compress']
		cbz = request.form['cbz']
		startname = request.form['startname']
		start_time = request.form['start_time']
		try:
			schedulerc.add_job(exec_start4, trigger=CronTrigger.from_crontab(start_time), id=startname, args=[code,packege,startname] )
			test = schedulerc.get_job(startname).id
			logger.info('%s 스케줄러에 등록하였습니다.', test)
		except ConflictingIdError:
			test = schedulerc.get_job(startname).id
			test2 = schedulerc.modify_job(startname).id
			logger.info('%s가 %s 스케줄러로 수정되었습니다.', test,test2)
		return redirect(url_for('webtoon.index'))
		
@webtoon.route('naver_down', methods=['POST'])
def naver_down():
	if session.get('logFlag') != True:
		return redirect(url_for('main.index'))
	else:
		packege = request.form['packege']
		t_main = request.form['t_main']
		compress = request.form['compress']
		cbz = request.form['cbz']
		startname = request.form['startname']
		start_time = request.form['start_time']
		try:
			schedulerc.add_job(godown, trigger=CronTrigger.from_crontab(start_time), id=startname, args=[t_main,compress,cbz,packege,startname] )
			test = schedulerc.get_job(startname).id
			logger.info('%s 스케줄러에 등록하였습니다.', test)
		except ConflictingIdError:	
			test = schedulerc.get_job(startname).id
			test2 = schedulerc.modify_job(startname).id
			logger.info('%s가 %s 스케줄러로 수정되었습니다.', test,test2)
		return redirect(url_for('webtoon.index'))
		
@webtoon.route('newtoki_list', methods=['POST'])
def newtoki_list():
	if session.get('logFlag') != True:
		return redirect(url_for('main.index'))
	else:
		packege = request.form['packege']
		t_main = request.form['t_main']
		genre = request.form['genre']
		code = request.form['code']
		compress = request.form['compress']
		cbz = request.form['cbz']
		startname = request.form['startname']
		start_time = request.form['start_time']
		try:
			schedulerc.add_job(exec_start3, trigger=CronTrigger.from_crontab(start_time), id=startname, args=[t_main,code,packege,genre,startname] )
			test = schedulerc.get_job(startname).id
			logger.info('%s 스케줄러에 등록하였습니다.', test)
		except ConflictingIdError:	
			test = schedulerc.get_job(startname).id
			test2 = schedulerc.modify_job(startname).id
			logger.info('%s가 %s 스케줄러로 수정되었습니다.', test,test2)
		return redirect(url_for('webtoon.index'))
		
@webtoon.route('newtoki_down', methods=['POST'])
def newtoki_down():
	if session.get('logFlag') != True:
		return redirect(url_for('main.index'))
	else:
		packege = request.form['packege']
		t_main = request.form['t_main']
		genre = request.form['genre']
		compress = request.form['compress']
		cbz = request.form['cbz']
		startname = request.form['startname']
		start_time = request.form['start_time']
		try:
			schedulerc.add_job(godown, trigger=CronTrigger.from_crontab(start_time), id=startname, args=[t_main,compress,cbz,packege,startname] )
			test = schedulerc.get_job(startname).id
			logger.info('%s 스케줄러에 등록하였습니다.', test)
		except ConflictingIdError:	
			test = schedulerc.get_job(startname).id
			test2 = schedulerc.modify_job(startname).id
			logger.info('%s가 %s 스케줄러로 수정되었습니다.', test,test2)
		return redirect(url_for('webtoon.index'))
		
@webtoon.route('copytoon_list', methods=['POST'])
def copytoon_list():
	if session.get('logFlag') != True:
		return redirect(url_for('main.index'))
	else:
		packege = request.form['packege']
		t_main = request.form['t_main']
		code = request.form['code']
		compress = request.form['compress']
		cbz = request.form['cbz']
		startname = request.form['startname']
		start_time = request.form['start_time']
		try:
			schedulerc.add_job(exec_start, trigger=CronTrigger.from_crontab(start_time), id=startname, args=[t_main,code,packege,startname] )
			test = schedulerc.get_job(startname).id
			logger.info('%s 스케줄러에 등록하였습니다.', test)
		except ConflictingIdError:	
			test = schedulerc.get_job(startname).id
			test2 = schedulerc.modify_job(startname).id
			logger.info('%s가 %s 스케줄러로 수정되었습니다.', test,test2)
		return redirect(url_for('webtoon.index'))
		
@webtoon.route('copytoon_down', methods=['POST'])
def copytoon_down():
	if session.get('logFlag') != True:
		return redirect(url_for('main.index'))
	else:
		packege = request.form['packege']
		t_main = request.form['t_main']
		compress = request.form['compress']
		cbz = request.form['cbz']
		startname = request.form['startname']
		start_time = request.form['start_time']
		try:
			schedulerc.add_job(godown, trigger=CronTrigger.from_crontab(start_time), id=startname, args=[t_main,compress,cbz,packege,startname] )
			test = schedulerc.get_job(startname).id
			logger.info('%s 스케줄러에 등록하였습니다.', test)
		except ConflictingIdError:	
			test = schedulerc.get_job(startname).id
			test2 = schedulerc.modify_job(startname).id
			logger.info('%s가 %s 스케줄러로 수정되었습니다.', test,test2)
		return redirect(url_for('webtoon.index'))

@webtoon.route('toonkor_list', methods=['POST'])
def toonkor_list():
	if session.get('logFlag') != True:
		return redirect(url_for('main.index'))
	else:
		packege = request.form['packege']
		t_main = request.form['t_main']
		code = request.form['code']
		compress = request.form['compress']
		cbz = request.form['cbz']
		startname = request.form['startname']
		start_time = request.form['start_time']
		try:
			schedulerc.add_job(exec_start2, trigger=CronTrigger.from_crontab(start_time), id=startname, args=[t_main,code,packege,startname] )
			test = schedulerc.get_job(startname).id
			logger.info('%s 스케줄러에 등록하였습니다.', test)
		except ConflictingIdError:
			test = schedulerc.get_job(startname).id
			test2 = schedulerc.modify_job(startname).id
			logger.info('%s가 %s 스케줄러로 수정되었습니다.', test,test2)
		return redirect(url_for('webtoon.index'))
		
@webtoon.route('toonkor_down', methods=['POST'])
def toonkor_down():
	if session.get('logFlag') != True:
		return redirect(url_for('main.index'))
	else:
		packege = request.form['packege']
		t_main = request.form['t_main']
		compress = request.form['compress']
		cbz = request.form['cbz']
		startname = request.form['startname']
		start_time = request.form['start_time']
		try:
			schedulerc.add_job(godown, trigger=CronTrigger.from_crontab(start_time), id=startname, args=[t_main,compress,cbz,packege,startname] )
			test = schedulerc.get_job(startname).id
			logger.info('%s 스케줄러에 등록하였습니다.', test)
		except ConflictingIdError:
			test = schedulerc.get_job(startname).id
			test2 = schedulerc.modify_job(startname).id
			logger.info('%s가 %s 스케줄러로 수정되었습니다.', test,test2)
		return redirect(url_for('webtoon.index'))
		
@webtoon.route('sch_del', methods=['POST'])
def sch_del():
	if not session.get('logFlag'):
		return redirect(url_for('main.index'))
	else:
		startname = request.form['startname']
		try:
			test = schedulerc.get_job(startname).id
			logger.info('%s가 스케줄러에 있습니다.', test)
		except Exception as e:
			test = None
		if test == None:
			logger.info('%s의 스케줄러가 종료가 되지 않았습니다.', startname)
		else:
			schedulerc.remove_job(startname)
			logger.info('%s 스케줄러를 삭제하였습니다.', test)
			test2 = schedulerc.get_jobs()
			for i in test2:
				aa = i.id
				logger.info('%s 가 스케줄러가 있습니다.', aa)
		
		return redirect(url_for('webtoon.index'))
		
#추가
@webtoon.route('dozi_list', methods=['POST'])
def dozi_list():
	if session.get('logFlag') != True:
		return redirect(url_for('main.index'))
	else:
		packege = request.form['packege']
		t_main = request.form['t_main']
		code = request.form['code']
		compress = request.form['compress']
		cbz = request.form['cbz']
		startname = request.form['startname']
		start_time = request.form['start_time']
		try:
			schedulerc.add_job(exec_start5, trigger=CronTrigger.from_crontab(start_time), id=startname, args=[t_main,packege,startname] )
			test = schedulerc.get_job(startname).id
			logger.info('%s 스케줄러에 등록하였습니다.', test)
		except ConflictingIdError:
			test = schedulerc.get_job(startname).id
			test2 = schedulerc.modify_job(startname).id
			logger.info('%s가 %s 스케줄러로 수정되었습니다.', test,test2)
		return redirect(url_for('webtoon.index'))	
		
@webtoon.route('dozi_down', methods=['POST'])
def dozi_down():
	if session.get('logFlag') != True:
		return redirect(url_for('main.index'))
	else:
		packege = request.form['packege']
		t_main = request.form['t_main']
		compress = request.form['compress']
		cbz = request.form['cbz']
		startname = request.form['startname']
		start_time = request.form['start_time']
		try:
			schedulerc.add_job(godown, trigger=CronTrigger.from_crontab(start_time), id=startname, args=[t_main,compress,cbz,packege,startname] )
			test = schedulerc.get_job(startname).id
			logger.info('%s 스케줄러에 등록하였습니다.', test)
		except ConflictingIdError:
			test = schedulerc.get_job(startname).id
			test2 = schedulerc.modify_job(startname).id
			logger.info('%s가 %s 스케줄러로 수정되었습니다.', test,test2)
		return redirect(url_for('webtoon.index'))
