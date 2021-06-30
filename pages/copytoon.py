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
#데이타베이스 없으면 생성
conn = sqlite3.connect('./webtoon.db')
conn.execute('CREATE TABLE IF NOT EXISTS database (maintitle TEXT, subtitle TEXT, urltitle TEXT, complte TEXT)')
conn.close()
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
		
def cleanText(readData):
	#텍스트에 포함되어 있는 특수 문자 제거
	#text = re.sub('[-=+,#/\?:^$.@*\"※~&%ㆍ!』\\‘|\(\)\[\]\<\>`\'…》]', '', readData)
	text = re.sub('[=+,#/\?:^$.@*\"※~&%ㆍ!』\\‘|\(\)\[\]\<\>`\'…》]', '', readData)
	return text	

def url_to_image(subtitle, title, url, filename, dfolder):
	print("시작")
	session2 = requests.Session()
	header = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.101 Safari/537.36"}
	req = session2.get(url,headers=header)	
	time.sleep(random.uniform(2,5)) 
	parse = re.sub('[-=.#/?:$}]', '', title)
	fifi = dfolder + '/' + parse + '/' + subtitle + '/' + filename
	#폴더 없으면 만들다
	if not os.path.exists('{}/{}/{}'.format(dfolder,parse,subtitle)):
		os.makedirs('{}/{}/{}'.format(dfolder,parse,subtitle))
	if not os.path.exists('{}/{}'.format(dfolder,parse)):
		os.makedirs('{}/{}'.format(dfolder,parse))
	if not os.path.exists('{}'.format(dfolder)):
		os.makedirs('{}'.format(dfolder))
	if not os.path.isfile(fifi):
		with open(fifi, 'wb') as code:
			code.write(req.content)
			
def manazip(subtitle, title ,filename , dfolder, cbz):
	parse = re.sub('[-=.#/?:$}]', '', title)
	if os.path.isdir(dfolder + '/{}/{}'.format(parse,subtitle)):
		if cbz == '0':
			fantasy_zip = zipfile.ZipFile(dfolder + '/{}/{}.cbz'.format(parse,subtitle), 'w')   
		else:
			fantasy_zip = zipfile.ZipFile(dfolder + '/{}/{}.zip'.format(parse,subtitle), 'w')   
		for folder, subfolders, files in os.walk(dfolder + '/{}/{}'.format(parse,subtitle)):                     
			for file in files:
				if file.endswith('.jpg'):
					fantasy_zip.write(os.path.join(folder, file), os.path.relpath(os.path.join(folder,file), dfolder + '/{}/{}'.format(parse,subtitle)), compress_type = zipfile.ZIP_DEFLATED)                     
		fantasy_zip.close()
	shutil.rmtree(dfolder + '/{}/{}'.format(parse,subtitle))
	print('{}  압축 완료'.format(parse))				

def exec_start(t_main, compress, cbz):
	#print(t_main)
	#print(compress)
	maintitle = []
	subtitle = []
	urltitle = []
	session2 = requests.Session()
	header = {"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5)\AppleWebKit 537.36 (KHTML, like Gecko) Chrome","Accept":"text/html,application/xhtml+xml,application/xml;\q=0.9,imgwebp,*/*;q=0.8"}
	response = requests.get(t_main)
	html = response.text
	soup = bs(html, "html.parser").findAll("div",{"class":"section-item-title"})
	for tag in soup:
		url = tag.find('a')
		maintitle.append(url["href"])
		
	for mainurl in maintitle:
		url = mainurl.strip()
		wkt = url
		wat = wkt.replace("/", "")
		title = wat.replace(".html", "")
		all = t_main + url
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
	
def exec_start2(t_main, compress, cbz):	
	#DB 목록을 받아와 다운로드를 진행한다.
	con = sqlite3.connect("./webtoon.db")
	cur = con.cursor()
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
		if complte == 'True':
			pass
		else:
			response1 = session2.get(wwwkt,headers=header)
			html = response1.text				
			print("{} 의 {} 을 시작합니다".format(title, subtitle))		
			soup = bs(html, "html.parser")
			obj = soup.find("div",{"id":"bo_v_con"})
			taglist = obj.findAll("img")
			urls = []
				
			for img in taglist:
				if img["src"].endswith("jpg"):
					urls.append(str(img["src"]))
					#print(img["src"])

			jpeg_no = 00
				
			timestr = time.strftime("%Y%m%d-%H%M%S-")
			parse2 = re.sub('[-=.#/?:$}]', '', title)
			parse = cleanText(parse2)
			dfolder = os.path.dirname(os.path.abspath(__file__)) + '/copytoon'
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
			sql = "UPDATE database SET complte = ? WHERE subtitle = ?"
			cur.execute(sql,('True',subtitle))
			con.commit()
				
		con.close()
	
@webtoon.route('copytoon_list', methods=['POST'])
def copytoon_list():
	if session.get('logFlag') != True:
		return redirect(url_for('main.index'))
	else:
		t_main = request.form['t_main']
		compress = request.form['compress']
		cbz = request.form['cbz']
		startname = request.form['startname']
		start_time = request.form['start_time']
		scheduler.add_job(exec_start, trigger=CronTrigger.from_crontab(start_time), id=startname, args=[t_main,compress,cbz] )
		print(t_main)
		print(compress)
		print(cbz)
		return redirect(url_for('main.index'))

@webtoon.route('copytoon_down', methods=['POST'])
def copytoon_down():
	if session.get('logFlag') != True:
		return redirect(url_for('main.index'))
	else:
		t_main = request.form['t_main']
		compress = request.form['compress']
		cbz = request.form['cbz']
		startname = request.form['startname']
		start_time = request.form['start_time']
		scheduler.add_job(exec_start2, trigger=CronTrigger.from_crontab(start_time), id=startname, args=[t_main,compress,cbz] )
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