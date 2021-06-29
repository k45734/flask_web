#-*- coding: utf-8 -*-
import sys
try:
	reload(sys)
	sys.setdefaultencoding('utf-8')
except:
	pass
import json, os
import re
import time
from datetime import datetime
import io
try:
	import requests
except ImportError:
	os.system('pip install requests')
	import requests
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
try: #python3
	from urllib.request import urlopen
except: #python2
	from urllib2 import urlopen
#from urllib.request import urlopen 
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from flask import Blueprint
#여기서 필요한 모듈
from datetime import datetime, timedelta
import requests
from flask import Flask, flash, redirect, render_template, request, session, abort, url_for
import os.path
from flask_ipblock import IPBlock
from flask_ipblock.documents import IPNetwork
import random
import sqlite3
import threading
import telegram
import time
import subprocess
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.base import JobLookupError

bp2 = Blueprint('sub2', __name__, url_prefix='/sub2')
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
scheduler = BackgroundScheduler()
scheduler.start()

@bp2.route('/')
@bp2.route('index')
def second():
	if not session.get('logFlag'):
		return redirect(url_for('main.index'))
	else:
		#t_main = request.form['t_main']
		return render_template('board.html')
	
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

def url_to_image(s, thisdata, url, dfolder2, filename):
	#time.sleep(60) #배포용 기능 제한
	header = {"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5)\AppleWebKit 537.36 (KHTML, like Gecko) Chrome","Accept":"text/html,application/xhtml+xml,application/xml;\q=0.9,imgwebp,*/*;q=0.8"}
	#req = requests.get(url, timeout=sleep)
	req = s.get(url,headers=header)
	fifi = dfolder2 + '/' + thisdata + '/' + filename
	print(fifi)
	if not os.path.exists('{}'.format(dfolder2)):
		os.makedirs('{}'.format(dfolder2))
	if not os.path.exists('{}/{}'.format(dfolder2,thisdata)):
		os.makedirs('{}/{}'.format(dfolder2,thisdata))
	with open(fifi, 'wb') as code:
		code.write(req.content)
		
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
				if telgm == '0' :
					bot = telepot.Bot(token = telgm_token)
					if telgm_alim == '0' :
						bot.sendMessage(chat_id = telgm_botid, text=msg_on, disable_notification=True)
					else:
						bot.sendMessage(chat_id = telgm_botid, text=msg_on, disable_notification=False)
				print(msg_on)
			else:
				print(msg_off)

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
					if telgm == '0' :
						bot = telepot.Bot(token = telgm_token)
						if telgm_alim == '0' :
							bot.sendMessage(chat_id = telgm_botid, text=message, disable_notification=True)
						else:
							bot.sendMessage(chat_id = telgm_botid, text=message, disable_notification=False)
					else:
						print(message)
			with io.open(file, 'w+' ,-1, "utf-8") as f_write:
				f_write.write(message)
				f_write.close()
				
def exec_start3():
	with requests.Session() as s:
		gogo = 1
		timestr = time.strftime("%Y%m%d-%H%M%S-")
		timestr2 = time.strftime("%Y%m%d-%H%M%S")
		header = {"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5)\AppleWebKit 537.36 (KHTML, like Gecko) Chrome","Accept":"text/html,application/xhtml+xml,application/xml;\q=0.9,imgwebp,*/*;q=0.8"}
		while True:
			print("{} 페이지가 시작되었습니다.".format(gogo))
			dd = "https://funmom.tistory.com/category/?page=" + str(gogo)
			#login = s.get(dd, timeout=sleep)
			login = s.get(dd,headers=header)
			#time.sleep(60) #배포용 기능 제한		
			html = login.text
			soup = bs(html, 'html.parser')
			list_test = soup.find(attrs={'class' :'jb-index-title jb-index-title-front'}) #목록이 있나 없나 확인
			list = soup.find_all(attrs={'class' :'jb-index-title jb-index-title-front'})
			#print(list)
			#print(list_test)
			if list_test == None:
				print("마지막 페이지입니다.\n종료합니다.")
				break
			
			hrefs = []
			for href in list:
				t = href.find("a")["href"]
				hrefs.append(str(t))
				#print(t)
				
			for go in hrefs:
				dd = 'https://funmom.tistory.com' + go
				#login = s.get(dd, timeout=sleep)
				#print(dd)
				login = s.get(dd,headers=header)
				#time.sleep(60) #배포용 기능 제한
				html = login.text
				soup = bs(html, 'html.parser')
				menu = soup.find(attrs={'class' :'another_category another_category_color_gray'}) #카테고리 이름
				test = menu.find('h4')
				#print(test)
				ttt = test('a')
				category = ttt[0].text
				category2 = ttt[1].text
				dfolder2 = os.path.dirname(os.path.abspath(__file__)) + '/funmom/' + category + '/' + category2
				title = soup.find('title')	
				thisdata = cleanText(title.text)
				ex_id_divs = soup.find_all(attrs={'class' : ["imageblock alignCenter","imageblock"]})
				urls = []

				for img in ex_id_divs:
					img_url = img.find("img")
					urls.append(str(img_url["src"]))		
				jpeg_no = 00
				for url in urls:
					#print(url)
					filename="funmom-" + str(jpeg_no) + ".jpg"
					url_to_image(s, thisdata, url, dfolder2, filename="funmom-" + str(jpeg_no) + ".jpg")
					jpeg_no += 1
			print("{} 페이지가 완료되었습니다.".format(gogo))
			gogo += 1

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
		if telgm == '0' :
			bot = telepot.Bot(token = telgm_token)
			if telgm_alim == '0' :
				bot.sendMessage(chat_id = telgm_botid, text=msg, disable_notification=True)
			else:
				bot.sendMessage(chat_id = telgm_botid, text=msg, disable_notification=False)	
		print(msg)

@bp2.route('tracking')
def tracking():
	if not session.get('logFlag'):
		return redirect(url_for('main.index'))
	else:	
		return render_template('tracking.html')

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
		try:
			scheduler.add_job(exec_start4, trigger='interval', seconds=int(start_time), id=startname, args=[carrier_id,track_id,telgm,telgm_alim,telgm_token,telgm_botid])
		except:
				pass
		return render_template('tracking.html')
		
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
			scheduler.add_job(exec_start3, trigger='interval', seconds=int(start_time), id=startname)
		except:
				pass
		return render_template('funmom.html')

		
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
				scheduler.add_job(exec_start, trigger='interval', seconds=int(start_time), id=startname, args=[t_main, sel, selnum, telgm, telgm_alim, telgm_token, telgm_botid] )
			except:
				pass
		if choice == 'b':
			try:
				scheduler.add_job(exec_start2, trigger='interval', seconds=int(start_time), id=startname, args=[cafenum, cafe, num, cafemenu, cafeboard, boardpath, telgm, telgm_alim, telgm_token, telgm_botid] )
			except:
				pass
		return redirect(url_for('main.index'))