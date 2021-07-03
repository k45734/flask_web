﻿#-*- coding: utf-8 -*-
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
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.jobstores.base import BaseJobStore, JobLookupError, ConflictingIdError
from apscheduler.triggers.cron import CronTrigger

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

webtoon = Blueprint('webtoon', __name__, url_prefix='/webtoon')
job_defaults = { 'max_instances': 1 }
scheduler = BackgroundScheduler(job_defaults=job_defaults)
#scheduler = BackgroundScheduler()
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

@webtoon.route('newtoki')
def second3():
	if not session.get('logFlag'):
		return redirect(url_for('main.index'))
	else:
		#t_main = request.form['t_main']
		return render_template('newtoki.html')

@webtoon.route('naver')
def second4():
	if not session.get('logFlag'):
		return redirect(url_for('main.index'))
	else:
		#t_main = request.form['t_main']
		return render_template('naver.html')

@webtoon.route('daum')
def second5():
	if not session.get('logFlag'):
		return redirect(url_for('main.index'))
	else:
		#t_main = request.form['t_main']
		return render_template('daum.html')
		
def cleanText(readData):
	#텍스트에 포함되어 있는 특수 문자 제거
	#text = re.sub('[-=+,#/\?:^$.@*\"※~&%ㆍ!』\\‘|\(\)\[\]\<\>`\'…》]', '', readData)
	#text = re.sub('[-_\/:*?"<>|]', '', readData)
	text = readData.replace('/', '')
	text = re.sub('[\\/:*?\"<>|]', '', text).strip()
	text = re.sub("\s{2,}", ' ', text)
	return text	

def url_to_image(subtitle, title, url, filename, dfolder):
	#print(url)
	session2 = requests.Session()
	header = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.101 Safari/537.36"}
	time.sleep(random.uniform(2,5)) 
	try:
		req = session2.get(url,headers=header)	
	except:
		req = session2.get(url,headers=header)	
	title2 = title.strip()
	subtitle2 = subtitle.strip()
	#parse = re.sub('[-_\/:*?"<>|]', '', title2)
	#parse2 = re.sub('[-_\/:*?"<>|]', '', subtitle2)
	parse = cleanText(title2)
	parse2 = cleanText(subtitle2)
	fifi = dfolder + '/' + parse + '/' + parse2 + '/' + filename
	#print(fifi)
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
	title2 = title.strip()
	subtitle2 = subtitle.strip()
	#parse = re.sub('[\/:*?"<>|]', '', title2)
	#parse2 = re.sub('[\/:*?"<>|]', '', subtitle2)
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

def exec_start(t_main, code, packege):
	#print(packege)
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
		#print(allcode)
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
		#print(allcode)
		for i in allcode:
			#print(i)
			t_maincode = t_main + i
			#print(t_maincode)
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
				#print(title)
				#print(url3)
				#print(mainurl)					
		except:
			pass
		
	#앞에서 크롤링한 정보를 DB에 저장한다.
	for a,b,c in zip(maintitle2,subtitle,urltitle):
		d = "False" #처음에 등록할때 무조건 False 로 등록한다.	
		#print(a, b , c ,d)
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
	
def exec_start3(t_main,code,packege,genre):
	print(genre)
	with requests.Session() as s:
		main_list = [] #url 주소를 만든다.
		maintitle = [] #대제목이 저장된다
		maintitle2 = [] #대제목 2번째 DB를 위한 작업공간
		subtitle = [] #소제목이 저장된다.
		urltitle = []		
		
		if code == 'all':
			for page in range(1,11): 
				main_url = t_main + '/webtoon/p' + str(page) + '?toon=' + genre
				time.sleep(random.uniform(2,5)) 
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
						a_href = a_link[1]['href']
						main_list.append(a_href)
						#print(a_href)

		else:	
			allcode = code.split('|')
			#print(allcode)
			for i in allcode:
				main_url = t_main + '/webtoon/' + i	
				main_list.append(main_url)
				#print(i)
				#t_maincode = t_main + i
				#print(t_maincode)
				#maintitle.append(i)
				
		#print(main_url)	
			
		for a in main_list :
			time.sleep(random.uniform(2,5)) 
			req = s.get(a)
			html = req.text
			gogo = bs(html, "html.parser")
			title = gogo.find(attrs={'class':'page-desc'})
			data_tmp = title.text.lstrip() #대제목	
			posts_list = gogo.find_all(attrs = {'class':'item-subject'})
			for b in posts_list:
				aa = b.find('b')
				a_link = b['href']
				a_text = b.text
				sub = a_text.strip()
				pattern = re.compile(r'\s\s+')
				aa_tmp = re.sub(pattern, ' ', sub)			
				maintitle.append(data_tmp) #대제목이다.
				subtitle.append(aa_tmp) #소제목이다.
				urltitle.append(a_link) #URL 주소가 저장된다.
				#print('{} | {} | {}'.format(data_tmp,aa_tmp,a_link)) #대제목 , 소제목

		#앞에서 크롤링한 정보를 DB에 저장한다.
		for a,b,c in zip(maintitle,subtitle,urltitle):
			d = "False" #처음에 등록할때 무조건 False 로 등록한다.	
			#print(a, b , c ,d)
			con = sqlite3.connect("./webtoon.db")
			cur = con.cursor()
			sql = "select * from database3 where urltitle = ?"
			cur.execute(sql, (c,))
			row = cur.fetchone()
			if row != None:
				pass
			else:
				cur.execute("INSERT OR REPLACE INTO database3 (maintitle, subtitle, urltitle, complte) VALUES (?, ?, ?, ?)", (a,b,c,d))
				con.commit()
		con.close()	
		
def exec_start4(code,packege):
	packege = 'naver'
	maintitle = []
	subtitle = []
	urltitle = []
	titleid = []

	with requests.Session() as s:
		url = 'https://comic.naver.com/webtoon/weekday.nhn'
		response = s.get(url)
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
			#print(allcode)
			for i in allcode:
				#print(i)
				t_maincode = i
				#print(t_maincode)
				titleid.append(i)			

		for i in titleid:
			#print(i)
			suburl = 'https://comic.naver.com/webtoon/list.nhn?titleId=' + i
			response = s.get(suburl)
			html = response.text
			soup = bs(html, "html.parser")
			#대제목을 가져온다.
			tags = soup.find("div",{"class":"detail"})
			#for i in tags:
				#대제목을 찾는다.
			test = tags('h2')
			tt = re.sub('<span.*?>.*?</h2>', '', str(test), 0, re.I|re.S)
			tt2 = re.sub('<h2>', '', str(tt), 0, re.I|re.S)
			pattern = re.compile(r'\s+')
			tt2 = re.sub(pattern, '', tt2)
			tt2 = tt2.replace("[", "")
			tt2 = tt2.replace("]", "")
			for p in range(1, 1001):
				pageurl = 'https://comic.naver.com/webtoon/list.nhn?titleId=' + i + '&page=' + str(p)
				response = s.get(pageurl)
				html = response.text
				soup = bs(html, "html.parser")
				sublist = soup.findAll("td",{"class":"title"})
				pageend = soup.find("a",{"class":"next"})
	
				if pageend:
					for ii in sublist:
						test = ii.find('a')['href']
						tests = ii.text
						test2 = tests.strip()
						maintitle.append(tt2)
						subtitle.append(test2)
						urltitle.append(test)
						#print('{} {} {}'.format(tt2,test2,test))
				else:
					for ii in sublist:
						test = ii.find('a')['href']
						tests = ii.text
						test2 = tests.strip()
						maintitle.append(tt2)
						subtitle.append(test2)
						urltitle.append(test)
						#print('{} {} {}'.format(tt2,test2,test))
					break
				
	#앞에서 크롤링한 정보를 DB에 저장한다.
	for a,b,c in zip(maintitle,subtitle,urltitle):
		d = "False" #처음에 등록할때 무조건 False 로 등록한다.	
		#print(a, b , c ,d)
		con = sqlite3.connect("./webtoon.db")
		cur = con.cursor()
		sql = "select * from database4 where urltitle = ?"
		cur.execute(sql, (c,))
		row = cur.fetchone()
		if row != None:
			pass
		else:
			cur.execute("INSERT OR REPLACE INTO database4 (maintitle, subtitle, urltitle, complte) VALUES (?, ?, ?, ?)", (a,b,c,d))
			con.commit()
	con.close()	
	
def exec_start5(code,packege):
	packege = 'daum'
	maintitle = []
	subtitle = []
	urltitle = []
	titleid = []
	episode_id = []
	headers = {
				'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36',
				'Accept' : 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
				'Accept-Language' : 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
				'Referer' : ''
				} 

	with requests.Session() as s:
		url = 'http://webtoon.daum.net/data/pc/webtoon/list_serialized/%s' % datetime.now().strftime('%A').lower()[0:3]
		data = requests.get(url,headers=headers).json()
		status = data['result']['status']
		ass = data['result']['message']
		#print(ass)
		#전체 웹툰코드를 받아온다. 
		if code == 'all':				
			if ass != 'you are not login':
				for item in data['data']:
					nickname = item['nickname']
					titleid.append(nickname)
			else:
				print("test")
				pass
		else:
			allcode = code.split('|')
			for i in allcode:
				titleid.append(i)
				
		for i in titleid:
			time.sleep(random.uniform(2,10)) 
			url = 'http://webtoon.daum.net/data/pc/webtoon/view/%s' % (i)
			data = requests.get(url,headers=headers).json()
			status = data['result']['status']
			ass = data['result']['message']
			#print(ass)
			if ass != 'you are not login':
				test = data['data']['webtoon']['title']
				for epi in data['data']['webtoon']['webtoonEpisodes']:
					tt = epi['id']
					sub = epi['title']
					maintitle.append(test)
					subtitle.append(sub)
					urltitle.append(tt)
					#print('{} 의 {}'.format(test,sub))
			else:
				print("test1")
				pass
				
		#앞에서 크롤링한 정보를 DB에 저장한다.
		for a,b,c in zip(maintitle,subtitle,urltitle):
			d = "False" #처음에 등록할때 무조건 False 로 등록한다.	
			#print(a, b , c)
			con = sqlite3.connect("./webtoon.db")
			cur = con.cursor()
			sql = "select * from database4 where urltitle = ?"
			cur.execute(sql, (c,))
			row = cur.fetchone()
			if row != None:
				pass
			else:
				cur.execute("INSERT OR REPLACE INTO database5 (maintitle, subtitle, urltitle, complte) VALUES (?, ?, ?, ?)", (a,b,c,d))
				con.commit()
		con.close()		
		
#공통 다운로드	
def godown(t_main, compress, cbz, packege):	
	#DB 목록을 받아와 다운로드를 진행한다.
	con = sqlite3.connect("./webtoon.db")
	cur = con.cursor()
	if packege == 'toonkor':
		sql = "select * from database2"
	elif packege == 'newtoki':
		sql = "select * from database3"
	elif packege == 'naver':
		sql = "select * from database4"
	elif packege == 'daum':
		sql = "select * from database5"
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
		if packege == 'naver':
			wwwkt = 'https://comic.naver.com' + url
		elif packege == 'daum':
			time.sleep(random.uniform(2,10)) 
			wwwkt = 'http://webtoon.daum.net/data/pc/webtoon/viewer_images/%s' % (url)
		else:
			wwwkt = t_main + url
		if complte == 'True':
			continue
		else:
			if packege != 'daum':
				response1 = session2.get(wwwkt,headers=header)
				html = response1.text
				soup = bs(html, "html.parser")					
			else:
				try:
					data = requests.get(wwwkt,headers=header).json()
					ass = data['result']['message']
					status = data['result']['status']
				except:
					data = requests.get(wwwkt,headers=header).json()
					ass = data['result']['message']
					status = data['result']['status']				
			print("{} 의 {} 을 시작합니다".format(title, subtitle))
			if packege == 'toonkor':
				tt = re.search(r'var toon_img = (.*?);', html, re.S)
				json_string = tt.group(1)
				obj = str(base64.b64decode(json_string), encoding='utf-8')
				taglist = re.compile(r'src="(.*?)"').findall(obj)
			elif packege == 'newtoki':
				tmp = ''.join(re.compile(r'html_data\+\=\'(.*?)\'\;').findall(data))
				html = ''.join([chr(int(x, 16)) for x in tmp.rstrip('.').split('.')])
				#image_list = re.compile(r'img\ssrc="/img/loading-image.gif"\sdata\-\w{11}="(.*?)"').findall(html)
				taglist = re.compile(r'src="/img/loading-image.gif"\sdata\-\w{11}="(.*?)"').findall(html)
			elif packege == 'naver':
				obj = soup.find("div",{"class":"wt_viewer"})
				taglist = obj.findAll("img")
			elif packege == 'daum':
				pass
			else:
				obj = soup.find("div",{"id":"bo_v_con"})
				taglist = obj.findAll("img")
			urls = []
			if packege != 'daum':	
				#print(taglist)
				for img in taglist:
					if packege == 'toonkor':
						urls.append(img)
					elif packege == 'newtoki':
						urls.append(img)
					else:
						if img["src"].endswith("jpg"):
							urls.append(str(img["src"]))
							#print(img["src"])
				
			else:
				if ass != 'you are not login':
					for w in data['data']:
						img = w['url']
						#print(img)
						urls.append(img)
				else:
					print("유료")
					continue
			jpeg_no = 00
				
			timestr = time.strftime("%Y%m%d-%H%M%S-")
			parse2 = re.sub('[-=.#/?:$}]', '', title)
			parse = cleanText(parse2)
			dfolder = os.path.dirname(os.path.abspath(__file__)) + '/' + packege
			for url in urls:
				#print(url)
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
			try:
				if compress == '0':
					manazip(subtitle, title, filename, dfolder, cbz)
				else:
					pass
			except:
				print("종료")
			else:
				#마지막 실행까지 작업안했던 결과물 저장
				con = sqlite3.connect("./webtoon.db")
				cur = con.cursor()
				if packege == 'toonkor':
					sql = "UPDATE database2 SET complte = ? WHERE subtitle = ?"
				elif packege == 'newtoki':
					sql = "UPDATE database3 SET complte = ? WHERE subtitle = ?"
				elif packege == 'naver':
					sql = "UPDATE database4 SET complte = ? WHERE subtitle = ?"
				elif packege == 'daum':
					sql = "UPDATE database5 SET complte = ? WHERE subtitle = ?"
				else:
					sql = "UPDATE database SET complte = ? WHERE subtitle = ?"
				cur.execute(sql,('True',subtitle))
				con.commit()
					
			con.close()

@webtoon.route('daum_list', methods=['POST'])
def daum_list():
	if session.get('logFlag') != True:
		return redirect(url_for('main.index'))
	else:
		#데이타베이스 없으면 생성
		conn = sqlite3.connect('./webtoon.db')
		conn.execute('CREATE TABLE IF NOT EXISTS database5 (maintitle TEXT, subtitle TEXT, urltitle TEXT, complte TEXT)')
		conn.close()
		packege = 'daum'
		code = request.form['code']
		compress = request.form['compress']
		cbz = request.form['cbz']
		startname = request.form['startname']
		start_time = request.form['start_time']
		try:
			scheduler.add_job(exec_start5, trigger=CronTrigger.from_crontab(start_time), id=startname, args=[code,packege] )
		except ConflictingIdError:
			scheduler.modify_job(startname)
		return redirect(url_for('main.index'))
		
@webtoon.route('daum_down', methods=['POST'])
def daum_down():
	if session.get('logFlag') != True:
		return redirect(url_for('main.index'))
	else:
		conn = sqlite3.connect('./webtoon.db')
		conn.execute('CREATE TABLE IF NOT EXISTS database5 (maintitle TEXT, subtitle TEXT, urltitle TEXT, complte TEXT)')
		conn.close()
		packege = 'daum'
		t_main = request.form['t_main']
		compress = request.form['compress']
		cbz = request.form['cbz']
		startname = request.form['startname']
		start_time = request.form['start_time']
		try:
			scheduler.add_job(godown, trigger=CronTrigger.from_crontab(start_time), id=startname, args=[t_main,compress,cbz,packege] )
		except ConflictingIdError:
			scheduler.modify_job(startname)
		return redirect(url_for('main.index'))
		
@webtoon.route('naver_list', methods=['POST'])
def naver_list():
	if session.get('logFlag') != True:
		return redirect(url_for('main.index'))
	else:
		#데이타베이스 없으면 생성
		conn = sqlite3.connect('./webtoon.db')
		conn.execute('CREATE TABLE IF NOT EXISTS database4 (maintitle TEXT, subtitle TEXT, urltitle TEXT, complte TEXT)')
		conn.close()
		packege = 'naver'
		code = request.form['code']
		compress = request.form['compress']
		cbz = request.form['cbz']
		startname = request.form['startname']
		start_time = request.form['start_time']
		try:
			scheduler.add_job(exec_start4, trigger=CronTrigger.from_crontab(start_time), id=startname, args=[code,packege] )
		except ConflictingIdError:
			scheduler.modify_job(startname)
		return redirect(url_for('main.index'))
		
@webtoon.route('naver_down', methods=['POST'])
def naver_down():
	if session.get('logFlag') != True:
		return redirect(url_for('main.index'))
	else:
		conn = sqlite3.connect('./webtoon.db')
		conn.execute('CREATE TABLE IF NOT EXISTS database4 (maintitle TEXT, subtitle TEXT, urltitle TEXT, complte TEXT)')
		conn.close()
		packege = 'naver'
		t_main = request.form['t_main']
		compress = request.form['compress']
		cbz = request.form['cbz']
		startname = request.form['startname']
		start_time = request.form['start_time']
		try:
			scheduler.add_job(godown, trigger=CronTrigger.from_crontab(start_time), id=startname, args=[t_main,compress,cbz,packege] )
		except ConflictingIdError:	
			scheduler.modify_job(startname)
		return redirect(url_for('main.index'))
		
@webtoon.route('newtoki_list', methods=['POST'])
def newtoki_list():
	if session.get('logFlag') != True:
		return redirect(url_for('main.index'))
	else:
		#데이타베이스 없으면 생성
		conn = sqlite3.connect('./webtoon.db')
		conn.execute('CREATE TABLE IF NOT EXISTS database3 (maintitle TEXT, subtitle TEXT, urltitle TEXT, complte TEXT)')
		conn.close()
		packege = 'newtoki'
		t_main = request.form['t_main']
		genre = request.form['genre']
		code = request.form['code']
		compress = request.form['compress']
		cbz = request.form['cbz']
		startname = request.form['startname']
		start_time = request.form['start_time']
		try:
			scheduler.add_job(exec_start3, trigger=CronTrigger.from_crontab(start_time), id=startname, args=[t_main,code,packege,genre] )
		except ConflictingIdError:	
			scheduler.modify_job(startname)
		return redirect(url_for('main.index'))
		
@webtoon.route('newtoki_down', methods=['POST'])
def newtoki_down():
	if session.get('logFlag') != True:
		return redirect(url_for('main.index'))
	else:
		conn = sqlite3.connect('./webtoon.db')
		conn.execute('CREATE TABLE IF NOT EXISTS database3 (maintitle TEXT, subtitle TEXT, urltitle TEXT, complte TEXT)')
		conn.close()
		packege = 'newtoki'
		t_main = request.form['t_main']
		genre = request.form['genre']
		compress = request.form['compress']
		cbz = request.form['cbz']
		startname = request.form['startname']
		start_time = request.form['start_time']
		try:
			scheduler.add_job(godown, trigger=CronTrigger.from_crontab(start_time), id=startname, args=[t_main,compress,cbz,packege] )
		except ConflictingIdError:	
			scheduler.modify_job(startname)
		return redirect(url_for('main.index'))
		
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
		try:
			scheduler.add_job(exec_start, trigger=CronTrigger.from_crontab(start_time), id=startname, args=[t_main,code,packege] )
		except ConflictingIdError:	
			scheduler.modify_job(startname)
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
		try:
			scheduler.add_job(godown, trigger=CronTrigger.from_crontab(start_time), id=startname, args=[t_main,compress,cbz,packege] )
		except ConflictingIdError:	
			scheduler.modify_job(startname)
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
		try:
			scheduler.add_job(exec_start2, trigger=CronTrigger.from_crontab(start_time), id=startname, args=[t_main,code,packege] )
		except ConflictingIdError:
			scheduler.modify_job(startname)
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
		try:
			scheduler.add_job(godown, trigger=CronTrigger.from_crontab(start_time), id=startname, args=[t_main,compress,cbz,packege] )
		except ConflictingIdError:
			scheduler.modify_job(startname)
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