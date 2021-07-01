#-*- coding: utf-8 -*-
import sys
try:
	reload(sys)
	sys.setdefaultencoding('utf-8')
except:
	pass
import requests
import os, io, re, zipfile, shutil, json, time, random, base64
import urllib.request as urllib2
try:
	import argparse
except ImportError:
	os.system('pip install argparse')
	import argparse	
try:
	from bs4 import BeautifulSoup as bs
except ImportError:
	os.system('pip install BeautifulSoup4')
	from bs4 import BeautifulSoup as bs
try:
	import telepot
except ImportError:
	os.system('pip install telepot')
	import telepot

try:
	import sqlite3
except ImportError:
	os.system('pip install sqlite3')
	import sqlite3
from flask import Blueprint
#여기서 필요한 모듈
import os
from datetime import datetime, timedelta
import requests
from flask import Flask, flash, redirect, render_template, request, session, abort, url_for
import os.path
from flask_ipblock import IPBlock
from flask_ipblock.documents import IPNetwork
import random
import bs4
import sqlite3
import threading
import telegram
import time
import subprocess
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.base import JobLookupError
from apscheduler.triggers.cron import CronTrigger

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

webtoon = Blueprint('webtoon', __name__, url_prefix='/webtoon')
scheduler = BackgroundScheduler()
scheduler.start()

@webtoon.route('/')
@webtoon.route('index')
def second():
	if not session.get('logFlag'):
		return redirect(url_for('main.index'))
	else:
		#t_main = request.form['t_main']
		return render_template('copytoon.html')

@webtoon.route('toonkor')
def second2():
	if not session.get('logFlag'):
		return redirect(url_for('main.index'))
	else:
		#t_main = request.form['t_main']
		return render_template('toonkor.html') 
		
def cleanText(readData):
	#텍스트에 포함되어 있는 특수 문자 제거
	#text = re.sub('[-=+,#/\?:^$.@*\"※~&%ㆍ!』\\‘|\(\)\[\]\<\>`\'…》]', '', readData)
	text = re.sub('[\/:*?"<>|]', '', readData)
	return text	

def url_to_image(subtitle, title, url, filename, dfolder):
	print("시작")
	session2 = requests.Session()
	header = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.101 Safari/537.36"}
	req = session2.get(url,headers=header)	
	time.sleep(random.uniform(2,5)) 
	parse = re.sub('[\/:*?"<>|]', '', title)
	parse2 = re.sub('[\/:*?"<>|]', '', subtitle)
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
			
def manazip(subtitle, title ,filename , dfolder, cbz):
	parse = re.sub('[\/:*?"<>|]', '', title)
	parse2 = re.sub('[\/:*?"<>|]', '', subtitle)
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

def exec_start(t_main, code, packege):
	print(packege)
	maintitle = []
	subtitle = []
	urltitle = []
	session2 = requests.Session()
	header = {"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5)\AppleWebKit 537.36 (KHTML, like Gecko) Chrome","Accept":"text/html,application/xhtml+xml,application/xml;\q=0.9,imgwebp,*/*;q=0.8"}
	if code == 'all':
		response = requests.get(t_main)
		html = response.text
		soup = bs(html, "html.parser").findAll("div",{"class":"section-item-title"})
		for tag in soup:
			url = tag.find('a')
			maintitle.append(url["href"])
	else:
		allcode = code.split('|')
		print(allcode)
		for i in allcode:
			#aa = '/'+ i
			#print(aa)
			t_maincode = t_main + i
			#print(t_maincode)
			maintitle.append(i)
			
	for mainurl in maintitle:
		#url = mainurl.strip()
		url = mainurl.lstrip()
		wkt = url
		wat = wkt.replace("/", "")
		title = wat.replace(".html", "")
		if code == 'all':
			all = t_main + url
		else:
			all = t_main + '/' + url
		#print(all)
		response1 = session2.get(all,headers=header)
		html = response1.text
		soup = bs(html, "html.parser")
		#print(all)
		mm = soup.find("div",{"class":"contents-list"})
		try:
			toonlist = mm.findAll('a')
			for post in toonlist:
				urltitle.append(post["href"])
				subtitle.append(title)
		except:
			pass
	#print(subtitle) #소제목
	#print(urltitle) #웹툰주소
	#print(maintitle) #대제목
	#대제목 소제목 다운로드url 주소를 DB에 저장한다.
	for a,c in zip(subtitle,urltitle):
		#subtitle 대제목으로 바뀌었다. a 대제목
		#urltitle 이곳에서 소제목을 뺀다. c url주소
		wkt = c #이곳부터 c url 주소에서 소제목을 만들다.
		wat = wkt.replace("/", "")
		b = wat.replace(".html", "") #소제목이다.
		d = "False" #처음에 등록할때 무조건 False 로 등록한다.
		#print(a, b , c ,d)
		con = sqlite3.connect("./webtoon.db")
		cur = con.cursor()
		sql = "select * from database where urltitle = ?"
		cur.execute(sql, (c,))
		row = cur.fetchone()
		if row != None:
			pass
		else:
			cur.execute("INSERT OR REPLACE INTO database (maintitle, subtitle, urltitle, complte) VALUES (?, ?, ?, ?)", (a,b,c,d))
			con.commit()
	con.close()

def exec_start2(t_main, code, packege):
	maintitle = []
	maintitle2 = [] #대제목 2번째 DB를 위한 작업공간
	subtitle = []
	urltitle = []
	session = requests.Session()
	header = {"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5)\AppleWebKit 537.36 (KHTML, like Gecko) Chrome","Accept":"text/html,application/xhtml+xml,application/xml;\q=0.9,imgwebp,*/*;q=0.8"}
	
	if code == 'all':
		response = requests.get(t_main)
		time.sleep(random.uniform(2,5)) 	
		html = response.text
		soup = bs(html, "html.parser").findAll("a",{"id":"title"})
		for tag in soup:
			latest = tag.text
			test1 = latest.lstrip()
			maintitle.append(test1)
			#print(test1)
	else:
		allcode = code.split('|')
		print(allcode)
		for i in allcode:
			print(i)
			t_maincode = t_main + i
			print(t_maincode)
			maintitle.append(i)
			
	for mainurl in maintitle:	
		test = mainurl
		all = t_main + '/' + test
		#print(all)
		response1 = session.get(all,headers=header)
		time.sleep(random.uniform(2,5)) 
		html = response1.text
		soup2 = bs(html, "html.parser").find("table",{"class":"web_list"})
		try:
			toonview_list = soup2.findAll("tr",{"class":"tborder"})
			for post in toonview_list:
				post = post.find("td",{"class":"content__title"})
				title = post.get_text().lstrip()
				url3 = post.attrs['data-role']
				wat = url3.replace("/", "")
				title = wat.replace(".html", "")
				urltitle.append(url3)
				subtitle.append(title)	
				maintitle2.append(mainurl)
				print(title)
				print(url3)
				print(mainurl)					
		except:
			pass
		
	#앞에서 크롤링한 정보를 DB에 저장한다.
	for a,b,c in zip(maintitle2,subtitle,urltitle):
		d = "False" #처음에 등록할때 무조건 False 로 등록한다.	
		print(a, b , c ,d)
		con = sqlite3.connect("./webtoon.db")
		cur = con.cursor()
		sql = "select * from database2 where urltitle = ?"
		cur.execute(sql, (c,))
		row = cur.fetchone()
		if row != None:
			pass
		else:
			cur.execute("INSERT OR REPLACE INTO database2 (maintitle, subtitle, urltitle, complte) VALUES (?, ?, ?, ?)", (a,b,c,d))
			con.commit()
	con.close()	

#공통 다운로드	
def godown(t_main, compress, cbz, packege):	
	#DB 목록을 받아와 다운로드를 진행한다.
	con = sqlite3.connect("./webtoon.db")
	cur = con.cursor()
	if packege == 'toonkor':
		sql = "select * from database2"
	else:
		sql = "select * from database"
	cur.execute(sql)
	row = cur.fetchall()
	
	session2 = requests.Session()
	header = {"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5)\AppleWebKit 537.36 (KHTML, like Gecko) Chrome","Accept":"text/html,application/xhtml+xml,application/xml;\q=0.9,imgwebp,*/*;q=0.8"}
	for i in row:
		title = i[0]
		subtitle = i[1]
		url = i[2]
		complte = i[3]
		wwwkt = t_main + url
		print(wwwkt)
		if complte == 'True':
			pass
		else:
			response1 = session2.get(wwwkt,headers=header)
			html = response1.text				
			print("{} 의 {} 을 시작합니다".format(title, subtitle))		
			soup = bs(html, "html.parser")
			if packege == 'toonkor':
				tt = re.search(r'var toon_img = (.*?);', html, re.S)
				json_string = tt.group(1)
				obj = str(base64.b64decode(json_string), encoding='utf-8')
				taglist = re.compile(r'src="(.*?)"').findall(obj)				
			else:
				obj = soup.find("div",{"id":"bo_v_con"})
				taglist = obj.findAll("img")
			urls = []
			print(taglist)	
			for img in taglist:
				if packege == 'toonkor':
					urls.append(img)
				else:
					if img["src"].endswith("jpg"):
						urls.append(str(img["src"]))
						#print(img["src"])

			jpeg_no = 00
				
			timestr = time.strftime("%Y%m%d-%H%M%S-")
			parse2 = re.sub('[-=.#/?:$}]', '', title)
			parse = cleanText(parse2)
			dfolder = os.path.dirname(os.path.abspath(__file__)) + '/' + packege
			for url in urls:
				#print(url)
				filename = str(jpeg_no+1).zfill(3) + ".jpg"
				if 'https://zerotoon.com/' in url:
					pass
				elif 'https://cloudflare.africa.com/' in url:
					url_to_image(subtitle,title, url, filename, dfolder)
				else:
					domain = t_main + url
					url_to_image(subtitle, title, domain, filename, dfolder)
				
				jpeg_no += 1
			try:
				if compress == '0':
					manazip(subtitle, title, filename, dfolder, cbz)
				else:
					pass
			except:
				pass
			#마지막 실행까지 작업안했던 결과물 저장
			con = sqlite3.connect("./webtoon.db")
			cur = con.cursor()
			if packege == 'toonkor':
				sql = "UPDATE database2 SET complte = ? WHERE subtitle = ?"
			else:
				sql = "UPDATE database SET complte = ? WHERE subtitle = ?"
			cur.execute(sql,('True',subtitle))
			con.commit()
				
		con.close()
	
@webtoon.route('copytoon_list', methods=['POST'])
def copytoon_list():
	if session.get('logFlag') != True:
		return redirect(url_for('main.index'))
	else:
		#데이타베이스 없으면 생성
		conn = sqlite3.connect('./webtoon.db')
		conn.execute('CREATE TABLE IF NOT EXISTS database (maintitle TEXT, subtitle TEXT, urltitle TEXT, complte TEXT)')
		conn.close()
		packege = 'copytoon'
		t_main = request.form['t_main']
		code = request.form['code']
		compress = request.form['compress']
		cbz = request.form['cbz']
		startname = request.form['startname']
		start_time = request.form['start_time']
		scheduler.add_job(exec_start, trigger=CronTrigger.from_crontab(start_time), id=startname, args=[t_main,code,packege] )
		print(t_main)
		print(compress)
		print(cbz)
		return redirect(url_for('main.index'))
		
@webtoon.route('copytoon_down', methods=['POST'])
def copytoon_down():
	if session.get('logFlag') != True:
		return redirect(url_for('main.index'))
	else:
		conn = sqlite3.connect('./webtoon.db')
		conn.execute('CREATE TABLE IF NOT EXISTS database (maintitle TEXT, subtitle TEXT, urltitle TEXT, complte TEXT)')
		conn.close()
		packege = 'copytoon'
		t_main = request.form['t_main']
		compress = request.form['compress']
		cbz = request.form['cbz']
		startname = request.form['startname']
		start_time = request.form['start_time']
		scheduler.add_job(godown, trigger=CronTrigger.from_crontab(start_time), id=startname, args=[t_main,compress,cbz,packege] )
		print(t_main)
		print(compress)
		print(cbz)
		return redirect(url_for('main.index'))

@webtoon.route('toonkor_list', methods=['POST'])
def toonkor_list():
	if session.get('logFlag') != True:
		return redirect(url_for('main.index'))
	else:
		#데이타베이스 없으면 생성
		conn = sqlite3.connect('./webtoon.db')
		conn.execute('CREATE TABLE IF NOT EXISTS database2 (maintitle TEXT, subtitle TEXT, urltitle TEXT, complte TEXT)')
		conn.close()
		packege = 'toonkor'
		t_main = request.form['t_main']
		code = request.form['code']
		compress = request.form['compress']
		cbz = request.form['cbz']
		startname = request.form['startname']
		start_time = request.form['start_time']
		scheduler.add_job(exec_start2, trigger=CronTrigger.from_crontab(start_time), id=startname, args=[t_main,code,packege] )
		print(t_main)
		print(compress)
		print(cbz)
		return redirect(url_for('main.index'))
		
@webtoon.route('toonkor_down', methods=['POST'])
def toonkor_down():
	if session.get('logFlag') != True:
		return redirect(url_for('main.index'))
	else:
		conn = sqlite3.connect('./webtoon.db')
		conn.execute('CREATE TABLE IF NOT EXISTS database2 (maintitle TEXT, subtitle TEXT, urltitle TEXT, complte TEXT)')
		conn.close()
		packege = 'toonkor'
		t_main = request.form['t_main']
		compress = request.form['compress']
		cbz = request.form['cbz']
		startname = request.form['startname']
		start_time = request.form['start_time']
		scheduler.add_job(godown, trigger=CronTrigger.from_crontab(start_time), id=startname, args=[t_main,compress,cbz,packege] )
		print(t_main)
		print(compress)
		print(cbz)
		return redirect(url_for('main.index'))
		
@webtoon.route('sch_del', methods=['POST'])
def sch_del():
	if not session.get('logFlag'):
		return redirect(url_for('main.index'))
	else:
		startname = request.form['startname']
		try:
			scheduler.remove_job(startname)
		except:
			pass
		return redirect(url_for('main.index'))