#-*- coding: utf-8 -*-
import sys
try:
	reload(sys)
	sys.setdefaultencoding('utf-8')
except:
	pass
import requests
import os, io, re, zipfile, shutil, json, time, random, base64, urllib.request
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
nowDatetime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
#now = datetime.now()#.time()
webtoon = Blueprint('webtoon', __name__, url_prefix='/webtoon')
job_defaults = { 'max_instances': 1 }
schedulerc = BackgroundScheduler(job_defaults=job_defaults)
#scheduler = BackgroundScheduler()
schedulerc.start()

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
			if packege == 'copytoon':
				cur.execute("delete from database")
			elif packege == 'toonkor':
				cur.execute("delete from database2")
			elif packege == 'newtoki':
				cur.execute("delete from database3")
			elif packege == 'naver':
				cur.execute("delete from database4")
			elif packege == 'daum':
				cur.execute("delete from database5")
			else:
				print("데이터가 넘어오지 않았습니다")
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
			if packege == 'toonkor':
				sql = "UPDATE database2 SET complte = ?"
			elif packege == 'newtoki':
				sql = "UPDATE database3 SET complte = ?"
			elif packege == 'naver':
				sql = "UPDATE database4 SET complte = ?"
			elif packege == 'daum':
				sql = "UPDATE database5 SET complte = ?"
			elif packege == 'copytoon':
				sql = "UPDATE database SET complte = ?"
			else:
				print("정보가 없습니다.")			
			cur.execute(sql,('False',))
			con.commit()
		except:
			con.rollback()
		finally:		
			con.close()

		return redirect(url_for('main.index'))

def add_c(packege, a, b, c, d):
	try:
		time.sleep(random.uniform(2,10)) 
		print(packege, a, b , c ,d)
		con = sqlite3.connect('./webtoon.db')
		cur = con.cursor()
		if packege == 'copytoon':
			sql = "select * from database where urltitle = ?"
		elif packege == 'toonkor':
			sql = "select * from database2 where urltitle = ?"
		elif packege == 'newtoki':
			sql = "select * from database3 where urltitle = ?"
		elif packege == 'naver':
			sql = "select * from database4 where urltitle = ?"
		elif packege == 'daum':
			sql = "select * from database5 where urltitle = ?"
		else:
			print("데이터가 넘어오지 않았습니다")
		cur.execute(sql, (c,))
		row = cur.fetchone()
		if row != None:
			pass
		else:
			if packege == 'copytoon':
				cur.execute("INSERT OR REPLACE INTO database (maintitle, subtitle, urltitle, complte) VALUES (?, ?, ?, ?)", (a,b,c,d))
			elif packege == 'toonkor':
				cur.execute("INSERT OR REPLACE INTO database2 (maintitle, subtitle, urltitle, complte) VALUES (?, ?, ?, ?)", (a,b,c,d))
			elif packege == 'newtoki':
				cur.execute("INSERT OR REPLACE INTO database3 (maintitle, subtitle, urltitle, complte) VALUES (?, ?, ?, ?)", (a,b,c,d))
			elif packege == 'naver':
				cur.execute("INSERT OR REPLACE INTO database4 (maintitle, subtitle, urltitle, complte) VALUES (?, ?, ?, ?)", (a,b,c,d))
			elif packege == 'daum':
				cur.execute("INSERT OR REPLACE INTO database5 (maintitle, subtitle, urltitle, complte) VALUES (?, ?, ?, ?)", (a,b,c,d))
			else:
				print("데이터가 넘어오지 않았습니다")
			con.commit()
	except:
		con.rollback()
	finally:		
		con.close()

def add_d(packege, subtitle, title):
	try:
		time.sleep(random.uniform(2,10)) 
		print(packege, subtitle)
		#마지막 실행까지 작업안했던 결과물 저장
		con = sqlite3.connect('./webtoon.db')
		cur = con.cursor()
		if packege == 'toonkor':
			sql = "UPDATE database2 SET complte = ? WHERE subtitle = ? AND maintitle = ?"
		elif packege == 'newtoki':
			sql = "UPDATE database3 SET complte = ? WHERE subtitle = ? AND maintitle = ?"
		elif packege == 'naver':
			sql = "UPDATE database4 SET complte = ? WHERE subtitle = ? AND maintitle = ?"
		elif packege == 'daum':
			sql = "UPDATE database5 SET complte = ? WHERE subtitle = ? AND maintitle = ?"
		elif packege == 'copytoon':
			sql = "UPDATE database SET complte = ? WHERE subtitle = ? AND maintitle = ?"
		else:
			print("정보가 없습니다.")			
		cur.execute(sql,('True',subtitle, title))
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
		result = data.find("카피툰")     
		if result > 0:
			print ("Website is working fine %s "% url2)
			return 9999       
		return response.status		
		
def exec_start(t_main, code, packege):
	print("카피툰시작")
	newURL = t_main
	maintitle = []
	maintitle2 = []
	subtitle = []
	urltitle = []
	header = {"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5)\AppleWebKit 537.36 (KHTML, like Gecko) Chrome","Accept":"text/html,application/xhtml+xml,application/xml;\q=0.9,imgwebp,*/*;q=0.8"}
	for i in range(221,300):
		url2 = ("https://copytoon%s.com" % (i))
		time.sleep(2)
		result = checkURL(url2)
		if result == 9999:
			newURL = url2
			print("new url : " + url2)
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
			print('{} 의 {} 을 찾았습니다. {}'.format(packege, all, nowDatetime))
			response1 = s.get(all,headers=header)
			html = response1.text
			soup = bs(html, "html.parser")
			#print(all)
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
		#for a,c in zip(subtitle,urltitle):
		for a,b,c in zip(maintitle2,subtitle,urltitle):
			d = "False" #처음에 등록할때 무조건 False 로 등록한다.
			add_c(packege, a,b,c,d)

def exec_start2(t_main, code, packege):
	print("툰코시작")
	maintitle = []
	maintitle2 = [] #대제목 2번째 DB를 위한 작업공간
	subtitle = []
	urltitle = []
	header = {"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5)\AppleWebKit 537.36 (KHTML, like Gecko) Chrome","Accept":"text/html,application/xhtml+xml,application/xml;\q=0.9,imgwebp,*/*;q=0.8"}
	with requests.Session() as s:
		if code == 'all':
			response = s.get(t_main,headers=header)
			time.sleep(random.uniform(2,5)) 	
			html = response.text
			soup = bs(html, "html.parser").findAll("a",{"id":"title"})
			for tag in soup:
				#latest = tag.text
				latest = tag['href']
				aa = latest.replace("/", "")
				#test1 = latest.lstrip()
				maintitle.append(aa)
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
			print('{} 의 {} 을 찾았습니다. {}'.format(packege, all, nowDatetime))
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
					#print(title)
					#print(url3)
					#print(mainurl)					
			except:
				pass
		
		#앞에서 크롤링한 정보를 DB에 저장한다.
		for a,b,c in zip(maintitle2,subtitle,urltitle):
			d = "False" #처음에 등록할때 무조건 False 로 등록한다.	
			add_c(packege, a,b,c,d)
		
def exec_start3(t_main,code,packege,genre):
	print("뉴토끼시작")
	packege = 'newtoki'
	main_list = [] #url 주소를 만든다.
	maintitle = [] #대제목이 저장된다
	maintitle2 = [] #대제목 2번째 DB를 위한 작업공간
	subtitle = [] #소제목이 저장된다.
	urltitle = []
	header = {"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5)\AppleWebKit 537.36 (KHTML, like Gecko) Chrome","Accept":"text/html,application/xhtml+xml,application/xml;\q=0.9,imgwebp,*/*;q=0.8"}
	with requests.Session() as s:
		if code == 'all':
			for page in range(1,11): 
				main_url = t_main + '/webtoon/p' + str(page) + '?toon=' + genre
				time.sleep(random.uniform(2,10)) 
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
						#print(a_href)

		else:	
			allcode = code.split('|')
			#print(allcode)
			for i in allcode:
				main_url = t_main + '/webtoon/' + i	
				main_list.append(main_url)
		
		for a in main_list :
			print('{} 의 {} 을 찾았습니다. {}'.format(packege, a, nowDatetime))
			time.sleep(random.uniform(2,10)) 
			try:
				req = s.get(a,headers=header)
			except:
				print("캡챠있다.")
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
					#print('{} | {} | {}'.format(data_tmp,aa_tmp,a_link)) #대제목 , 소제목
				
		#앞에서 크롤링한 정보를 DB에 저장한다.
		for a,b,c in zip(maintitle,subtitle,urltitle):
			d = "False" #처음에 등록할때 무조건 False 로 등록한다.
			add_c(packege, a,b,c,d)
		
def exec_start4(code,packege):
	print("네이버웹툰시작")
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
			#print(allcode)
			for i in allcode:
				#print(i)
				t_maincode = i
				#print(t_maincode)
				titleid.append(i)			

		for i in titleid:
			print('{} 의 {} 을 찾았습니다. {}'.format(packege, i, nowDatetime))
			suburl = 'https://comic.naver.com/webtoon/list.nhn?titleId=' + i
			response = s.get(suburl,headers=header)
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
			#count = []
			#for p in range(1, 1001):
			#	pageurl = 'https://comic.naver.com/webtoon/list.nhn?titleId=' + i + '&page=' + str(p)
			#	response = s.get(pageurl,headers=header)
			#	html = response.text
			#	soup = bs(html, "html.parser")
			#	sublist = soup.findAll("td",{"class":"title"})
			#	pageend = soup.find("a",{"class":"next"})
				
			#	if pageend:
			#		for ii in sublist:
			#			test = ii.find('a')['href']
			#			count.append(test)
			#	else:
			#		for ii in sublist:
			#			test = ii.find('a')['href']
			#			count.append(test)
			#		break
					
			for p in range(1, 1001):
				pageurl = 'https://comic.naver.com/webtoon/list.nhn?titleId=' + i + '&page=' + str(p)
				response = s.get(pageurl,headers=header)
				html = response.text
				soup = bs(html, "html.parser")
				sublist = soup.findAll("td",{"class":"title"})
				pageend = soup.find("a",{"class":"next"})		
				
				if pageend:
					#test22 = len(count)
					#cc = int(test22)
					for ii in sublist:
						test = ii.find('a')['href']
						cc = test.split('no=')[1].split('&')[0].strip()
						test2 = '{}화'.format(cc)
						maintitle.append(tt2)
						subtitle.append(test2)
						urltitle.append(test)
						#cc -= 1
				else:
					#test22 = len(count)
					#cc = int(test22)
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
			add_c(packege, a,b,c,d)
	
def exec_start5(code,packege):
	print("다음웹툰시작")
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
			print('{} 의 {} 을 찾았습니다. {}'.format(packege, i, nowDatetime))
			time.sleep(random.uniform(2,10)) 
			url = 'http://webtoon.daum.net/data/pc/webtoon/view/%s' % (i)
			try:
				data = requests.get(url,headers=headers).json()
			except:
				data = requests.get(url,headers=headers).json()
			status = data['result']['status']
			ass = data['result']['message']
			if ass != 'you are not login':
				count = []
				test = data['data']['webtoon']['title']
				for epi in data['data']['webtoon']['webtoonEpisodes']:
					tt = epi['id']
					sub = epi['title']
					count.append(sub)
				test22 = len(count)
				cc = int(test22)
				for epi in data['data']['webtoon']['webtoonEpisodes']:
					tt = epi['id']
					sub = '{}화'.format(cc)
					maintitle.append(test)
					subtitle.append(sub)
					urltitle.append(tt)
					cc -= 1
			else:
				print("유료다")
				continue
				
		#앞에서 크롤링한 정보를 DB에 저장한다.
		for a,b,c in zip(maintitle,subtitle,urltitle):
			d = "False" #처음에 등록할때 무조건 False 로 등록한다.
			add_c(packege, a,b,c,d)		
		
#공통 다운로드	
def godown(t_main, compress, cbz, packege):	
	#DB 목록을 받아와 다운로드를 진행한다.
	con = sqlite3.connect('./webtoon.db',timeout=60)
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
	
	if packege == 'copytoon':
		for i in range(221,300):
			url2 = ("https://copytoon%s.com" % (i))
			time.sleep(2)
			result = checkURL(url2)
			if result == 9999:
				newURL = url2
				print("new url : " + url2)
				break
		t_main = url2
		print(t_main)
	else:
		print(t_main)
		pass
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
			try:
				test = url.replace(t_main,'')
				wwwkt = t_main + test
			except:
				wwwkt = t_main + url
		if complte == 'True':
			continue
		else:
			print(wwwkt)
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
				try:
					tt = re.search(r'var toon_img = (.*?);', html, re.S)
					json_string = tt.group(1)
					obj = str(base64.b64decode(json_string), encoding='utf-8')
					taglist = re.compile(r'src="(.*?)"').findall(obj)
				except:
					continue
			elif packege == 'newtoki':
				try:
					tmp = ''.join(re.compile(r'html_data\+\=\'(.*?)\'\;').findall(html))
					html = ''.join([chr(int(x, 16)) for x in tmp.rstrip('.').split('.')])
					#image_list = re.compile(r'img\ssrc="/img/loading-image.gif"\sdata\-\w{11}="(.*?)"').findall(html)
					taglist = re.compile(r'src="/img/loading-image.gif"\sdata\-\w{11}="(.*?)"').findall(html)
				except:
					continue
			elif packege == 'naver':
				try:
					obj = soup.find("div",{"class":"wt_viewer"})
					taglist = obj.findAll("img")
				except:
					continue
				#print(taglist)
			elif packege == 'daum':
				pass
			else:
				try:
					obj = soup.find("div",{"id":"bo_v_con"})
					taglist = obj.findAll("img")
				except:
					continue
			urls = []
			if packege != 'daum':	
				#print(taglist)
				for img in taglist:
					#print(taglist)
					if packege == 'toonkor':
						urls.append(img)
					elif packege == 'newtoki':
						urls.append(img)
					elif packege == 'naver':
						#print(img['src'])
						urls.append(img['src'])
					elif packege == 'copytoon':
						urls.append(img['src'])
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
				add_d(packege, subtitle, title)

@webtoon.route('daum_list', methods=['POST'])
def daum_list():
	if session.get('logFlag') != True:
		return redirect(url_for('main.index'))
	else:
		#데이타베이스 없으면 생성
		conn = sqlite3.connect('./webtoon.db',timeout=60)
		conn.execute('CREATE TABLE IF NOT EXISTS database5 (maintitle TEXT, subtitle TEXT, urltitle TEXT, complte TEXT)')
		conn.close()
		packege = request.form['packege']
		#packege = 'daum'
		code = request.form['code']
		compress = request.form['compress']
		cbz = request.form['cbz']
		startname = request.form['startname']
		start_time = request.form['start_time']
		try:
			schedulerc.add_job(exec_start5, trigger=CronTrigger.from_crontab(start_time), id=startname, args=[code,packege] )
		except ConflictingIdError:
			schedulerc.modify_job(startname)
		return redirect(url_for('main.index'))
		
@webtoon.route('daum_down', methods=['POST'])
def daum_down():
	if session.get('logFlag') != True:
		return redirect(url_for('main.index'))
	else:
		conn = sqlite3.connect('./webtoon.db',timeout=60)
		conn.execute('CREATE TABLE IF NOT EXISTS database5 (maintitle TEXT, subtitle TEXT, urltitle TEXT, complte TEXT)')
		conn.close()
		packege = request.form['packege']
		#packege = 'daum'
		t_main = request.form['t_main']
		compress = request.form['compress']
		cbz = request.form['cbz']
		startname = request.form['startname']
		start_time = request.form['start_time']
		try:
			schedulerc.add_job(godown, trigger=CronTrigger.from_crontab(start_time), id=startname, args=[t_main,compress,cbz,packege] )
		except ConflictingIdError:
			schedulerc.modify_job(startname)
		return redirect(url_for('main.index'))
		
@webtoon.route('naver_list', methods=['POST'])
def naver_list():
	if session.get('logFlag') != True:
		return redirect(url_for('main.index'))
	else:
		#데이타베이스 없으면 생성
		conn = sqlite3.connect('./webtoon.db',timeout=60)
		conn.execute('CREATE TABLE IF NOT EXISTS database4 (maintitle TEXT, subtitle TEXT, urltitle TEXT, complte TEXT)')
		conn.close()
		packege = request.form['packege']
		#packege = 'naver'
		code = request.form['code']
		compress = request.form['compress']
		cbz = request.form['cbz']
		startname = request.form['startname']
		start_time = request.form['start_time']
		try:
			schedulerc.add_job(exec_start4, trigger=CronTrigger.from_crontab(start_time), id=startname, args=[code,packege] )
		except ConflictingIdError:
			schedulerc.modify_job(startname)
		return redirect(url_for('main.index'))
		
@webtoon.route('naver_down', methods=['POST'])
def naver_down():
	if session.get('logFlag') != True:
		return redirect(url_for('main.index'))
	else:
		conn = sqlite3.connect('./webtoon.db',timeout=60)
		conn.execute('CREATE TABLE IF NOT EXISTS database4 (maintitle TEXT, subtitle TEXT, urltitle TEXT, complte TEXT)')
		conn.close()
		packege = request.form['packege']
		#packege = 'naver'
		t_main = request.form['t_main']
		compress = request.form['compress']
		cbz = request.form['cbz']
		startname = request.form['startname']
		start_time = request.form['start_time']
		try:
			schedulerc.add_job(godown, trigger=CronTrigger.from_crontab(start_time), id=startname, args=[t_main,compress,cbz,packege] )
		except ConflictingIdError:	
			schedulerc.modify_job(startname)
		return redirect(url_for('main.index'))
		
@webtoon.route('newtoki_list', methods=['POST'])
def newtoki_list():
	if session.get('logFlag') != True:
		return redirect(url_for('main.index'))
	else:
		#데이타베이스 없으면 생성
		conn = sqlite3.connect('./webtoon.db',timeout=60)
		conn.execute('CREATE TABLE IF NOT EXISTS database3 (maintitle TEXT, subtitle TEXT, urltitle TEXT, complte TEXT)')
		conn.close()
		packege = request.form['packege']
		#packege = 'newtoki'
		t_main = request.form['t_main']
		genre = request.form['genre']
		code = request.form['code']
		compress = request.form['compress']
		cbz = request.form['cbz']
		startname = request.form['startname']
		start_time = request.form['start_time']
		try:
			schedulerc.add_job(exec_start3, trigger=CronTrigger.from_crontab(start_time), id=startname, args=[t_main,code,packege,genre] )
		except ConflictingIdError:	
			schedulerc.modify_job(startname)
		return redirect(url_for('main.index'))
		
@webtoon.route('newtoki_down', methods=['POST'])
def newtoki_down():
	if session.get('logFlag') != True:
		return redirect(url_for('main.index'))
	else:
		conn = sqlite3.connect('./webtoon.db',timeout=60)
		conn.execute('CREATE TABLE IF NOT EXISTS database3 (maintitle TEXT, subtitle TEXT, urltitle TEXT, complte TEXT)')
		conn.close()
		packege = request.form['packege']
		#packege = 'newtoki'
		t_main = request.form['t_main']
		genre = request.form['genre']
		compress = request.form['compress']
		cbz = request.form['cbz']
		startname = request.form['startname']
		start_time = request.form['start_time']
		try:
			schedulerc.add_job(godown, trigger=CronTrigger.from_crontab(start_time), id=startname, args=[t_main,compress,cbz,packege] )
		except ConflictingIdError:	
			schedulerc.modify_job(startname)
		return redirect(url_for('main.index'))
		
@webtoon.route('copytoon_list', methods=['POST'])
def copytoon_list():
	if session.get('logFlag') != True:
		return redirect(url_for('main.index'))
	else:
		#데이타베이스 없으면 생성
		conn = sqlite3.connect('./webtoon.db',timeout=60)
		conn.execute('CREATE TABLE IF NOT EXISTS database (maintitle TEXT, subtitle TEXT, urltitle TEXT, complte TEXT)')
		conn.close()
		packege = request.form['packege']
		#packege = 'copytoon'
		t_main = request.form['t_main']
		code = request.form['code']
		compress = request.form['compress']
		cbz = request.form['cbz']
		startname = request.form['startname']
		start_time = request.form['start_time']
		try:
			schedulerc.add_job(exec_start, trigger=CronTrigger.from_crontab(start_time), id=startname, args=[t_main,code,packege] )
		except ConflictingIdError:	
			schedulerc.modify_job(startname)
		return redirect(url_for('main.index'))
		
@webtoon.route('copytoon_down', methods=['POST'])
def copytoon_down():
	if session.get('logFlag') != True:
		return redirect(url_for('main.index'))
	else:
		conn = sqlite3.connect('./webtoon.db',timeout=60)
		conn.execute('CREATE TABLE IF NOT EXISTS database (maintitle TEXT, subtitle TEXT, urltitle TEXT, complte TEXT)')
		conn.close()
		packege = request.form['packege']
		#packege = 'copytoon'
		t_main = request.form['t_main']
		compress = request.form['compress']
		cbz = request.form['cbz']
		startname = request.form['startname']
		start_time = request.form['start_time']
		try:
			schedulerc.add_job(godown, trigger=CronTrigger.from_crontab(start_time), id=startname, args=[t_main,compress,cbz,packege] )
		except ConflictingIdError:	
			schedulerc.modify_job(startname)
		return redirect(url_for('main.index'))

@webtoon.route('toonkor_list', methods=['POST'])
def toonkor_list():
	if session.get('logFlag') != True:
		return redirect(url_for('main.index'))
	else:
		#데이타베이스 없으면 생성
		conn = sqlite3.connect('./webtoon.db',timeout=60)
		conn.execute('CREATE TABLE IF NOT EXISTS database2 (maintitle TEXT, subtitle TEXT, urltitle TEXT, complte TEXT)')
		conn.close()
		packege = request.form['packege']
		#packege = 'toonkor'
		t_main = request.form['t_main']
		code = request.form['code']
		compress = request.form['compress']
		cbz = request.form['cbz']
		startname = request.form['startname']
		start_time = request.form['start_time']
		try:
			schedulerc.add_job(exec_start2, trigger=CronTrigger.from_crontab(start_time), id=startname, args=[t_main,code,packege] )
		except ConflictingIdError:
			schedulerc.modify_job(startname)
		return redirect(url_for('main.index'))
		
@webtoon.route('toonkor_down', methods=['POST'])
def toonkor_down():
	if session.get('logFlag') != True:
		return redirect(url_for('main.index'))
	else:
		conn = sqlite3.connect('./webtoon.db',timeout=60)
		conn.execute('CREATE TABLE IF NOT EXISTS database2 (maintitle TEXT, subtitle TEXT, urltitle TEXT, complte TEXT)')
		conn.close()
		packege = request.form['packege']
		#packege = 'toonkor'
		t_main = request.form['t_main']
		compress = request.form['compress']
		cbz = request.form['cbz']
		startname = request.form['startname']
		start_time = request.form['start_time']
		try:
			schedulerc.add_job(godown, trigger=CronTrigger.from_crontab(start_time), id=startname, args=[t_main,compress,cbz,packege] )
		except ConflictingIdError:
			schedulerc.modify_job(startname)
		return redirect(url_for('main.index'))
		
@webtoon.route('sch_del', methods=['POST'])
def sch_del():
	if not session.get('logFlag'):
		return redirect(url_for('main.index'))
	else:
		startname = request.form['startname']
		try:
			schedulerc.remove_job(startname)
		except:
			pass
		return redirect(url_for('main.index'))