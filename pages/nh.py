from flask import Blueprint
#-*- coding: utf-8 -*-
import sys
try:
	reload(sys)
	sys.setdefaultencoding('utf-8')
except:
	pass
from flask import Flask, flash, redirect, render_template, request, session, abort, url_for, Blueprint, jsonify
import os, io, re, zipfile, shutil, json, time, random, base64, urllib.request, platform, logging, requests, os.path, threading, time, subprocess, datetime
import urllib.request as urllib2
try:
	from openpyxl import Workbook
except ImportError:
	os.system('pip install openpyxl')
	from openpyxl import Workbook
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

try:
	import telegram
except ImportError:
	os.system('pip install python-telegram-bot')
	import telegram
from datetime import datetime, timedelta
from pages.main_page import scheduler
from pages.main_page import logger
from apscheduler.triggers.cron import CronTrigger
#페이지 기능
try:
	from flask_paginate import Pagination, get_page_args
except ImportError:
	os.system('pip install flask_paginate')
	from flask_paginate import Pagination, get_page_args
		
if platform.system() == 'Windows':
	at = os.path.splitdrive(os.getcwd())
	sub2db = at[0] + '/data/db'	
	mydir = at[0] + '/data'
else:
	sub2db = '/data/db'
	mydir = '/data'
		
nh = Blueprint('nh', __name__, url_prefix='/nh')
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def mydate():
	now = datetime.now()
	num = now.strftime('%y%m%d')
	myday = now.strftime('%Y-%m-%d')
	nowtime = time.localtime()
	mytime = "%04d%02d%02d" % (nowtime.tm_year, nowtime.tm_mon, nowtime.tm_mday)
	return [now,num,myday,nowtime,mytime]


def cleanText(readData):
	#텍스트에 포함되어 있는 특수 문자 제거
	text = re.sub('[-=+,#/\?:^$.@*\"※~&%ㆍ!』\\‘|\(\)\[\]\<\>`\'…》]', '', readData)
	return text	

#농협택배 예약을 위한 사전 DB	
def add(a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,r,s,t,u,v,w):
	#try:
	con = sqlite3.connect(mydir + '/db/nh.db',timeout=60)
	con.execute("PRAGMA cache_size = 10000")
	con.execute("PRAGMA locking_mode = NORMAL")
	con.execute("PRAGMA temp_store = MEMORY")
	con.execute("PRAGMA auto_vacuum = 1")
	con.execute("PRAGMA journal_mode=WAL")
	con.execute("PRAGMA synchronous=NORMAL")
	cur = con.cursor()
	sql = "select * from nh where rcvNm = ? and date = ? and prodNm = ? and amount = ?"
	cur.execute(sql, (a,t,r,u))
	row = cur.fetchone()
	print(row)
	if row == None:
		cur.execute("INSERT OR REPLACE INTO nh (rcvNm, rcvTelno, rcvHpno, rcvPostno, rcvAddr, rcvAddrDtl, prodTypeNm, prodAmt, priceTypeNm, rmk, sndNm, sndTelno, sndHpno, sndPostno, sndAddr, sndAddrDtl, boxQ, prodNm, surcharge, date, amount, rsvNo, rcpNo) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,r,s,t,u,v,w))
		con.commit()
		con.close()
		return True
	else:
		pass
		return False
	
	return
	
#농협택배 회원아이디와 기본보내는 사람의 정보DB	
def add_data(a,b,c,d,e,f,g):
	try:
		con = sqlite3.connect(mydir + '/db/nh.db',timeout=60)
		con.execute("PRAGMA cache_size = 10000")
		con.execute("PRAGMA locking_mode = NORMAL")
		con.execute("PRAGMA temp_store = MEMORY")
		con.execute("PRAGMA auto_vacuum = 1")
		con.execute("PRAGMA journal_mode=WAL")
		con.execute("PRAGMA synchronous=NORMAL")
		cur = con.cursor()
		sql = "select * from mydata where NHID = ?"
		cur.execute(sql, (a,))
		row = cur.fetchone()
		if row != None:
			pass
		else:
			cur.execute("INSERT OR REPLACE INTO mydata (NHID, NHPASSWD, NAME, HP, ZIP, ADDR, ADDR2) VALUES (?,?,?,?,?,?,?)", (a,b,c,d,e,f,g))
			con.commit()
	except:
		con.rollback()
	finally:		
		con.execute('VACUUM')
		con.close()	
	comp = '완료'
	return comp
	
#주소제한지역안내
def addr_not(d):
	headers = {"User-Agent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36'}
	with requests.Session() as s:
		GEO = {'postNo': d}
		mainurl = 'https://ex.nhlogis.co.kr/noMem/checkSndDenyArea.json'
		url = s.post(mainurl, headers=headers, data=GEO)
		resp = url.json()
		msg = resp['data']['procMsg']
	return msg
	
#주소검색을 한뒤 자동 입력하기		
def addr(ein):
	header = {"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5)\AppleWebKit 537.36 (KHTML, like Gecko) Chrome","Accept":"text/html,application/xhtml+xml,application/xml;\q=0.9,imgwebp,*/*;q=0.8"}
	with requests.Session() as s:
		url2 = 'https://www.juso.go.kr/support/AddressMainSearch.do?searchKeyword=' + ein
		req = s.get(url2)
		html = req.text
		gogo = bs(html, "html.parser")	
		test = gogo.find("div",{"class":"addr_cont"})
		#for i in test:
		#우편번호를 찾는다.
		zipcode = test.find('input',{'id':'bsiZonNo1'})
		new_addr = test.find('input', {'id':'rnAddr1'})
		old_addr = test.find('input', {'id':'lndnAddr1'})
		d = zipcode['value']
		e = new_addr['value']				
		return [d,e]
		
#택배조회 확인
def checkURL(url2):
	header = {"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5)\AppleWebKit 537.36 (KHTML, like Gecko) Chrome","Accept":"text/html,application/xhtml+xml,application/xml;\q=0.9,imgwebp,*/*;q=0.8"}
	try:
		request = requests.get(url2,headers=header,timeout=3)
		response = request.status_code
	except:
		print('%s 실패하였습니다.'% url2)
	else:
		if response == 200:
			print ("%s 성공하였습니다."% url2)
			return True      
		return False
		
#업무용 택배조회 알림
def trdb(track_number,track_date):
	with requests.Session() as s:
		headers = {"Cache-Control": "no-cache",   "Pragma": "no-cache",'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36'}
		main_url = 'http://kdtc.iptime.org:19998'
		url = s.get(main_url, headers=headers)
		check = url.status_code
		if check == 200:
			main = main_url + '/sub2/track_api/한진택배/' + track_number	
			url = s.get(main, headers=headers)
			print(url)

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
			msg = {'시간':new_s,'상품위치':b,'현재상태':c, '상품상태':d.replace('\n\t\t\t\t\t\t\t\t\t\t', '')}
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
		if '연락처' in d:
			total = '{} {} {}'.format(a, c, d)
		else:
			total = '{} {} {}'.format(a, b, d)
		msg.append(total)
	return msg
	
#택배사에서 직접조회
def tracking_ok(track_number):
	with requests.Session() as s:
		headers = {"Cache-Control": "no-cache",   "Pragma": "no-cache",'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36'}
		url_list = ["http://192.168.0.2:8085/carriers", "https://apis.tracker.delivery/carriers" ]
		for url2 in url_list:
			result = checkURL(url2)
			if result == True:
				main = url2 + '/kr.hanjin/tracks/' + track_number #기본 URL
				break
	
		url = s.get(main, headers=headers)
		resp = url.json()
		check = resp.get('from', None)
		if check == None:
			msga = '송장번호가 없는거 같습니다.\n'
		else:
			json_string = check.get("name", None) #누가 보냈냐			
			json_string2 = resp.get("to").get("name") #누가 받냐
			json_string3 = resp.get("state").get("text") #배송현재상태
			json_string4 = resp.get("carrier").get("name")
			json_string_m = resp.get("progresses") #배송상황
			msg2 = flfl(json_string_m)
			gg = ff(msg2,json_string,json_string2,json_string4,track_number)
			ms = '\n'.join(gg)
			msga = '================================\n보내는 사람 : {}\n받는 사람 : {}\n택배사 : {} {}\n{}\n================================'.format(json_string,json_string2,json_string4,track_number,ms)
			
	return msga	
	
def box_check(rsv_number):
	con = sqlite3.connect(mydir + '/db/nh.db',timeout=60)
	con.row_factory = sqlite3.Row
	cur = con.cursor()
	sql = "select * from nh where rsvNo = ?"
	cur.execute(sql, (rsv_number,))
	rows = cur.fetchone()
	msg = rows['prodNm']
	
	print(msg)
	logger.info(msg)
	return msg
	
def r_delivery(now,test,myday):
	datelink = now.strptime(test, "%y%m%d").strftime("%Y-%m-%d")
	con = sqlite3.connect(mydir + '/db/nh.db',timeout=60)
	con.row_factory = sqlite3.Row
	cur = con.cursor()
	sql = "select * from mydata"
	cur.execute(sql)
	rows = cur.fetchall()
	msg = []
	for row in rows:
		id = row['NHID']
		pw = row['NHPASSWD']
	LOGIN_INFO = {'userId': id,
				'pwd': pw,
				'rurl': '/main.do'
				}
	LIST_INFO = {'telNo':'', 
		'payType': '00',
		'searchOption': '2',
		'searchText': '' ,
		'orderType': '0',
		'orderYn': 'A',
		'startDt': datelink,
		'endDt': datelink,
		'paging': 'true',
		'page': '1',
		'rowCnt': '10'
		}
	header = {"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5)\AppleWebKit 537.36 (KHTML, like Gecko) Chrome","Accept":"text/html,application/xhtml+xml,application/xml;\q=0.9,imgwebp,*/*;q=0.8"}
	with requests.Session() as s:
		url = 'https://ex.nhlogis.co.kr/user/login/doLogin.json'
		url2 = 'https://ex.nhlogis.co.kr/resrv/inq/list.do'
		req = s.post(url, data=LOGIN_INFO)
		
		req1 = s.get(url2)
		html = req1.text
		gogo = bs(html, "html.parser")
		loginok = gogo.find('div', {'class':'util-box'})
		if loginok == None:
			print("로그인이 않되었습니다.")
		else:
			list = 'https://ex.nhlogis.co.kr/resrv/inq/selectList.json'
			req_list = s.post(list, data=LIST_INFO).json()
			ass = req_list['data']['list']
			
			for i in ass:
				aa = i['totCnt']
			LIST_INFO_S = {'telNo':'', 
						'payType': '00',
						'searchOption': '2',
						'searchText': '' ,
						'orderType': '0',
						'orderYn': 'A',
						'startDt': datelink,
						'endDt': datelink,
						'paging': 'true',
						'page': '1',
						'rowCnt': aa
						}
			list_s = 'https://ex.nhlogis.co.kr/resrv/inq/selectList.json'
			req_list_s = s.post(list_s, data=LIST_INFO_S).json()
			ass_a = req_list_s['data']['list']
			count = 1
			for it in ass_a:
				numdate = it['rsvDt']
				numbers = re.sub(r'[^0-9]', '', numdate)[2:]
				TK_INFO = {'invNo':it['invNo']}
				tk_a = 'https://ex.nhlogis.co.kr/dlvy/dlvy/select.json'
				req_tk = s.post(tk_a, data=TK_INFO).json()
				ass_at = req_tk['data']['list']
				track_number = it.get('invNo', None)#it['invNo']
				rsv_number = it.get('rsvNo',None)
				track_date = it.get('rsvDt', None)#it['rsvDt']
				print(track_number, track_date, rsv_number)
				if len(ass_at) != 0:
					for aai in ass_at:
						pass
					if numdate in datelink:
						if track_number != None and track_date != None:
							trdb(track_number,track_date)
						else:
							pass
						tr_all = tracking_ok(track_number)
						box_nun = box_check(rsv_number)
						print(box_nun)
						logger.info(box_nun)
						tracking = '실시간 배송확인\n' + 'http://smile.hanjin.co.kr:9080/eksys/smartinfo/map_web.html?wbl=' + it['invNo']
						all = '{}. {} {}\n{} 님 {} 되었습니다.\n배송원 {} 연락처 {}\n{}\n{}'.format(count, it['rsvDt'],it['invNo'],it['rcvNm'],it['scanNm'],aai['empNm'],aai['empTel'],tr_all,tracking)
						msg.append(all)
						count += 1
					else:
						pass
				else:
					if numdate in datelink:
						if track_number != None and track_date != None:
							trdb(track_number,track_date)
						else:
							pass
						all = '{} {}\n{} 님 {} 되었습니다.\n배송원이 아직 배정되지 않았습니다.'.format(it['rsvDt'],it['invNo'],it['rcvNm'],it['scanNm'])
						msg.append(all)
						count += 1
			
			if len(msg) == 0:
				all = '{} 정보가 없습니다.'.format(datelink)
				msg.append(all)
			else:
				pass					
	return msg
	
#엑셀파일과 실제 예약을 하기 위한 작업입니다.
def execelfile(numt):
	#workbook 생성하기(1개의 시트가 생성된 상태)
	workbook = Workbook()
	#현재 workbook의 활성화 된 Sheet 가져오기
	sheet = workbook.active
	sheet.title = "nh" #해당 sheet의 sheet명 변경하기
	# cell에 직접 데이터 입력하기
	sheet['A1'] = "받는분"
	sheet['B1'] = "휴대폰번호"
	sheet['C1'] = "일반전화번호"
	sheet['D1'] = "받는분우편번호"
	sheet['E1'] = "받는분주소"
	sheet['F1'] = "받는분상세주소"
	sheet['G1'] = "품목"
	sheet['H1'] = "물품금액(만원)"
	sheet['I1'] = "지불방법"
	sheet['J1'] = "비고"
	sheet['K1'] = "보내는분"
	sheet['L1'] = "휴대폰번호"
	sheet['M1'] = "일반전화번호"
	sheet['N1'] = "보내는분우편번호"
	sheet['O1'] = "보내는분주소"
	sheet['P1'] = "보내는분상세주소"
	sheet['Q1'] = "박스수량"
	sheet['R1'] = "물품명"
	sheet['S1'] = "추가운임"
	sheet['T1'] = "예약날짜"
	sheet['U1'] = "물품갯수"
	sheet['V1'] = "예약번호"
	con = sqlite3.connect(mydir + '/db/nh.db',timeout=60)
	con.row_factory = sqlite3.Row
	cur = con.cursor()
	if numt == 'all':
		sql = 'select * from nh'
		cur.execute(sql,)
	else:
		sql = "select * from nh where date = ?"
		cur.execute(sql, (numt,))
	rows = cur.fetchall()
	nh_data = []
	
	#DB의 정보를 읽어옵니다.
	for row in rows:
		a = row['rcvNm']
		b = row['rcvTelno']
		c = row['rcvHpno']
		d = row['rcvPostno']
		e = row['rcvAddr']
		f = row['rcvAddrDtl']
		g = row['prodTypeNm']
		h = row['prodAmt']
		i = row['priceTypeNm']
		j = row['rmk']
		k = row['sndNm']
		l = row['sndTelno']
		m = row['sndHpno']
		n = row['sndPostno']
		o = row['sndAddr']
		p = row['sndAddrDtl']
		q = row['boxQ']
		r = row['prodNm']
		s = row['surcharge']
		t = row['date']
		u = row['amount']
		v = row['rsvNo']
		nh_data.extend([[a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,r,s,t,u,v]])	
	con.execute('VACUUM')
	con.close()	
	for i in nh_data:
		sheet.append(i)
	# 파일 저장하기
	workbook.save(mydir + '/nh.xlsx')
	comp = '완료'
	return comp
	
#엑셀파일과 실제 예약을 하기 위한 작업입니다.
def jsonfile(numt, a, r, u, v, w):
	con = sqlite3.connect(mydir + '/db/nh.db',timeout=60)
	con.row_factory = sqlite3.Row
	cur = con.cursor()
	sql = "select * from nh where date = ? and rcvNm = ? and prodNm = ? and amount = ? and rsvNo = ? and rcpNo = ?"
	cur.execute(sql, (numt, a, r, u, v, w))
	row = cur.fetchone()
	if row == None:
		st_json = None
		pass
	else:
		mydata = []
		#DB의 정보를 읽어옵니다.
		#for row in rows:
		a = row['rcvNm']
		b = row['rcvTelno']
		c = row['rcvHpno']
		d = row['rcvPostno']
		e = row['rcvAddr']
		f = row['rcvAddrDtl']
		g = row['prodTypeNm']
		h = row['prodAmt']
		i = row['priceTypeNm']
		j = row['rmk']
		k = row['sndNm']
		l = row['sndTelno']
		m = row['sndHpno']
		n = row['sndPostno']
		o = row['sndAddr']
		p = row['sndAddrDtl']
		q = row['boxQ']
		r = row['prodNm']
		s = row['surcharge']
		t = row['date']
		u = row['amount']
		v = row['rsvNo']
		w = row['rcpNo']
		if '착불' in i:
			priceType = '02'
		else:
			priceType = '01'
		keys = ['ordNm','ordTelno','sndNm','sndTelno','sndHpno','sndPostno','sndAddr','sndAddrDtl','rcvNm','rcvTelno','rcvHpno','rcvPostno','rcvAddr','rcvAddrDtl','rmk','prodTypeNm','priceTypeNm','prodAmt','prodNm','boxQ','rcpNo','prodType','priceType','addrSeq','maYn']
		values = [k,l,k,m,l,n,o, p,a, c, b, d, e, f, j, g, i, h, r, q, w, '07', priceType, '', '']
		dt = dict(zip(keys, values))
		mydata.append(dt)	
		st_json = json.dumps(mydata, indent=4, ensure_ascii = False)
		comp = '완료'
	return st_json
	
#실제 예약을 합니다.
def rezcomp(st_json):
	now,num,myday,nowtime,mytime = mydate()
	con = sqlite3.connect(mydir + '/db/nh.db',timeout=60)
	con.execute("PRAGMA cache_size = 10000")
	con.execute("PRAGMA locking_mode = NORMAL")
	con.execute("PRAGMA temp_store = MEMORY")
	con.execute("PRAGMA auto_vacuum = 1")
	con.execute("PRAGMA journal_mode=WAL")
	con.execute("PRAGMA synchronous=NORMAL")
	con.row_factory = sqlite3.Row
	cur = con.cursor()
	sql = "select * from mydata"
	cur.execute(sql)
	rows = cur.fetchall()
	
	for row in rows:
		id = row['NHID']
		pw = row['NHPASSWD']
	LOGIN_INFO = {'userId': id,
				'pwd': pw,
				'rurl': '/main.do'
				}
	LIST_INFO = {'telNo':'', 
				'payType': '00',
				'searchOption': '2',
				'searchText': '' ,
				'orderType': '0',
				'orderYn': 'A',
				'startDt': '2010-01-01',
				'endDt': myday,
				'paging': 'true',
				'page': '1',
				'rowCnt': '10'
				}

	header = {"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5)\AppleWebKit 537.36 (KHTML, like Gecko) Chrome","Accept":"text/html,application/xhtml+xml,application/xml;\q=0.9,imgwebp,*/*;q=0.8"}
	with requests.Session() as s:
		url = 'https://ex.nhlogis.co.kr/user/login/doLogin.json'
		url2 = 'https://ex.nhlogis.co.kr/resrv/inq/list.do'
		req = s.post(url, data=LOGIN_INFO)
		req1 = s.get(url2)
		html = req1.text
		gogo = bs(html, "html.parser")
		loginok = gogo.find('div', {'class':'util-box'})
		if loginok == None:
			print("로그인이 않되었습니다.")
		else:
			print("로그인이 되었습니다.")
			rezcomp_data = []
			data2 = json.loads(st_json)
			if data2[0]['rcpNo'] == 'NULL':
				add_go = 'https://ex.nhlogis.co.kr/resrv/reg/save.json'
				add_list = s.post(add_go, data=data2[0]).json()
				print(add_list)
				print(add_list['data'])
				
				ck = add_list['result'] #성공여부
				if ck == True:
					aa = '성공'
				else:
					aa = '실패'
				ck1 = data2[0]['rcvNm'] #받는분
				ck2 = data2[0]['rcvAddr'] #받는분주소
				ck3 = data2[0]['rcvAddrDtl'] #받는분상세주소
				ck4 = data2[0]['rcvHpno'] #받는분전화번호
				ck6 = data2[0]['priceTypeNm'] #선불/착불
				ck5 = add_list['data']['rsvNo'] #농협택배 예약번호
				ck7 = data2[0]['rcvPostno'] #우편번호
				ck8 = add_list['data']['rcpNo'] #농협택배 접수번호
				keys = ['rcvNm','rcvAddr','rcvAddrDtl','rcvHpno','priceTypeNm','complte','rsvNo','rcvPostno','rcpNo']
				values = [ck1,ck4,ck2,ck3,ck6,aa,ck5,ck7,ck8]
				dt = dict(zip(keys, values))
				rezcomp_data.append(dt)
				con.execute('VACUUM')
				con.close()
			else:
				pass
			return rezcomp_data
	
#서버의 DB를 삭제합니다.
def delete_top2(a,t,rsvno):
	con = sqlite3.connect(mydir + '/db/nh.db',timeout=60)
	cur = con.cursor()
	sql2 = 'SELECT * from nh where rcvNm = ? and date = ? and rsvNo = ?'
	cur.execute(sql2, (a,t,rsvno))
	row = cur.fetchone()
	
	if row == None:
		a = '없음'
		t = '없음'
	else:
		sql = "delete from nh where rcvNm = ? and date = ? and rsvNo = ?"
		cur.execute(sql, (a,t,rsvno))
		con.commit()
		con.execute('VACUUM')
		con.close()
	return [a,t]
		
#서버에 DB를 저장합니다.
def adduse(context):
	now,num,myday,nowtime,mytime = mydate()
	#SQLITE3 DB 없으면 만들다.
	con = sqlite3.connect(mydir + '/db/nh.db',timeout=60)
	con.execute('CREATE TABLE IF NOT EXISTS nh (rcvNm TEXT, rcvTelno TEXT,rcvHpno TEXT,rcvPostno TEXT,rcvAddr TEXT,rcvAddrDtl TEXT,prodTypeNm TEXT,prodAmt TEXT,priceTypeNm TEXT,rmk TEXT,sndNm TEXT,sndTelno TEXT,sndHpno TEXT,sndPostno TEXT,sndAddr TEXT,sndAddrDtl TEXT,boxQ TEXT,prodNm TEXT,surcharge TEXT,date TEXT,amount TEXT,rsvNo TEXT, rcpNo TEXT)')	
	con.execute("PRAGMA cache_size = 10000")
	con.execute("PRAGMA locking_mode = NORMAL")
	con.execute("PRAGMA temp_store = MEMORY")
	con.execute("PRAGMA auto_vacuum = 1")
	con.execute("PRAGMA journal_mode=WAL")
	con.execute("PRAGMA synchronous=NORMAL")
	con.close()
	#데이터베이스 컬럼 추가하기
	con = sqlite3.connect(mydir + '/db/nh.db',timeout=60)
	con.row_factory = sqlite3.Row
	cur = con.cursor()
	sql = "SELECT sql FROM sqlite_master WHERE name='nh' AND sql LIKE '%rcpNo%'"
	cur.execute(sql)
	rows = cur.fetchall()
	if len(rows) == 0:
		sql = "alter table nh add column rcpNo TEXT"
		cur.execute(sql)
	else:
		pass
	con.close()
	con = sqlite3.connect(mydir + '/db/nh.db',timeout=60)
	con.row_factory = sqlite3.Row
	cur = con.cursor()
	sql = "select * from mydata"
	cur.execute(sql)
	rows = cur.fetchall()
	for row in rows:
		k = row['NAME']
		l = row['HP']
		m = l
		n = row['ZIP']
		o = row['ADDR']
		p = row['ADDR2']
	a = context[0]
	b = context[1]
	if '-' in b:
		b = cleanText(b)
	c = b
	ein = context[2]
	d,e = addr(ein)
	f = context[3]
	g = '일반식품'
	h = '10'
	#선불/착불
	if len(context) != 7:
		i = '선불'
	else:
		if '선불' in context[6]:
			i = '선불'
		else:
			i = '착불'	
	j = '빠른배송부탁드립니다.'		
	q = '1'
	if context[4] != None:
		r = context[4]
	else:
		r = '일반'
	s = '없음'
	t = num
	if context[5] != None:
		u = context[5]
	else:
		u = '일반'
	v = 'NULL'
	w = 'NULL'
	add(a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,r,s,t,u,v,w)
	all = '{}\n{}\n{} {}\n{} {}'.format(a,b,e,f,r,u)
	logger.info(all)
	return [v,w]

#서버에 DB를 예약번호를 저장합니다.
def adduse2(rsvno,rcpNo,numt, a, r, u):
	now,num,myday,nowtime,mytime = mydate()
	con = sqlite3.connect(mydir + '/db/nh.db',timeout=60)
	con.row_factory = sqlite3.Row
	cur = con.cursor()
	#sql = "SELECT * FROM nh ORDER BY ROWID DESC LIMIT 1"
	sql = "select * from nh where rcvNm = ? and date = ? and prodNm = ? and amount = ?"
	#cur.execute(sql)
	cur.execute(sql, (a,numt,r,u))
	rows = cur.fetchone()
	sql = "UPDATE nh SET rsvNo = ?, rcpNo = ? where rcvNm = ? and date = ? and prodNm = ? and amount = ?"
	cur.execute(sql,(rsvno,rcpNo,a,numt,r,u))
	con.commit()
	con.close()
	comp = '완료'
	return comp

def edit_db(rsvno,rcvHpno,rcvTelno,rcvPostno,rcvAddr,rcvAddrDtl,priceTypeNm):
	now,num,myday,nowtime,mytime = mydate()
	con = sqlite3.connect(mydir + '/db/nh.db',timeout=60)
	con.row_factory = sqlite3.Row
	cur = con.cursor()
	#sql = "SELECT * FROM nh ORDER BY ROWID DESC LIMIT 1"
	sql = "select * from nh where rsvNo = ?"
	#cur.execute(sql)
	cur.execute(sql, (rsvno,))
	rows = cur.fetchone()
	sql = "UPDATE nh SET rcvHpno = ?, rcvTelno = ?, rcvPostno = ?, rcvAddr = ?, rcvAddrDtl = ?, priceTypeNm = ? where rsvNo = ?"
	cur.execute(sql,(rcvHpno,rcvTelno,rcvPostno,rcvAddr,rcvAddrDtl,priceTypeNm, rsvno))
	con.commit()
	con.close()
	comp = '완료'
	return comp
	
#실서버 예약 취소 실구동
def delete_top(rsvno):
	con = sqlite3.connect(mydir + '/db/nh.db',timeout=60)
	con.row_factory = sqlite3.Row
	cur = con.cursor()
	sql = "select * from mydata"
	cur.execute(sql)
	rows = cur.fetchall()
	
	for row in rows:
		id = row['NHID']
		pw = row['NHPASSWD']
	LOGIN_INFO = {'userId': id,
				'pwd': pw,
				'rurl': '/main.do'
				}
	DELETE_INFO = { 'rsvNo': rsvno,
					'searchType': '',
					'searchText': '', 
					'sndTelno':	''
					}
	header = {"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5)\AppleWebKit 537.36 (KHTML, like Gecko) Chrome","Accept":"text/html,application/xhtml+xml,application/xml;\q=0.9,imgwebp,*/*;q=0.8"}
	with requests.Session() as s:
		url = 'https://ex.nhlogis.co.kr/user/login/doLogin.json'
		url2 = 'https://ex.nhlogis.co.kr/resrv/inq/list.do'
		req = s.post(url, data=LOGIN_INFO)
		
		req1 = s.get(url2)
		html = req1.text
		gogo = bs(html, "html.parser")
		loginok = gogo.find('div', {'class':'util-box'})
		if loginok == None:
			print("로그인이 않되었습니다.")
		else:

			list = 'https://ex.nhlogis.co.kr/resrv/inq/delete.json'
			req_list = s.post(list, data=DELETE_INFO).json() 
			i = req_list['data']
			ass2 = req_list['result']
			if ass2 != True:
				print("정보가 없습니다.")
			else:
				at = i['rsvDt']
				aa = i['rcvNm']
				ai = i['rsvNo']
	return [at,aa,ai]

def dbfile(numt,now):
	con = sqlite3.connect(mydir + '/db/nh.db',timeout=60)
	con.row_factory = sqlite3.Row
	cur = con.cursor()
	if numt == 'all':
		sql = "select * from nh"
		cur.execute(sql,)
	else:
		hangul = re.compile(r'[ㄱ-ㅣ가-힣]')
		results = re.findall(hangul, numt)
		if len(results) != 0:
			str = "".join(results)
			sql = "select * from nh where rcvNm = ?"
			cur.execute(sql, (str,))
		elif len(numt) == 11:
			sql = "select * from nh where rcvHpno = ?"
			cur.execute(sql, (numt,))	
		else:
			sql = "select * from nh where date = ?"
			cur.execute(sql, (numt,))
	rows = cur.fetchall()
	msg = []
	if len(rows) == 0:
		#해당 날짜
		hangul = re.compile(r'[ㄱ-ㅣ가-힣]')
		results = re.findall(hangul, numt)
		if len(results) != 0:
			datelink = "".join(results)
		else:
			datelink = now.strptime(numt, "%y%m%d").strftime("%Y-%m-%d")
		all = '{} 정보가 없습니다.'.format(datelink)
		msg.append(all)		
	else:
		#DB의 정보를 읽어옵니다.
		for row in rows:
			a = row['rcvNm']
			b = row['rcvTelno']
			c = row['rcvHpno']
			d = row['rcvPostno']
			e = row['rcvAddr']
			f = row['rcvAddrDtl']
			g = row['prodTypeNm']
			h = row['prodAmt']
			i = row['priceTypeNm']
			j = row['rmk']
			k = row['sndNm']
			l = row['sndTelno']
			m = row['sndHpno']
			n = row['sndPostno']
			o = row['sndAddr']
			p = row['sndAddrDtl']
			q = row['boxQ']
			r = row['prodNm']
			s = row['surcharge']
			t = row['date']
			u = row['amount']
			v = row['rsvNo']
			all = '{}\n{}\n{} {}\n{} {}'.format(a,b,e,f,r,u)
			print(all)
			msg.append(all)
	return msg
	
#DB에 있는 정보를 전체검색하여 기존고객과 신규고객알아보기
def myguest(numt):
	con = sqlite3.connect(mydir + '/db/nh.db',timeout=60)
	con.row_factory = sqlite3.Row
	cur = con.cursor()
	sql = "select * from nh where rcvHpno = ?"
	cur.execute(sql, (numt,))
	rows = cur.fetchall()
	cnt = 1
	for row in rows:
		a = row['rcvNm']
		b = row['rcvHpno']
		c = row['rcvPostno']
		d = row['rcvAddr']
		e = row['rcvAddrDtl']
		f = row['prodNm']
		g = row['date']
		h = row['amount']
		cnt += 1
	mydata  = '{} 님은 총 {} 번째 주문입니다.'.format(a,cnt-1)	
	con.execute('VACUUM')
	con.close()
	return mydata
	
#실서버 예약 수정 실구동
def edit_top(rsvno,context):
	con = sqlite3.connect(mydir + '/db/nh.db',timeout=60)
	con.row_factory = sqlite3.Row
	cur = con.cursor()
	sql = "select * from mydata"
	cur.execute(sql)
	rows = cur.fetchall()
	
	for row in rows:
		id = row['NHID']
		pw = row['NHPASSWD']
	LOGIN_INFO = {'userId': id,
				'pwd': pw,
				'rurl': '/main.do'
				}
	DELETE_INFO = { 'rsvNo': rsvno,
					'searchType': '', 
					'searchText': '',
					'sndTelno': ''
					}
	header = {"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5)\AppleWebKit 537.36 (KHTML, like Gecko) Chrome","Accept":"text/html,application/xhtml+xml,application/xml;\q=0.9,imgwebp,*/*;q=0.8"}
	with requests.Session() as s:
		url = 'https://ex.nhlogis.co.kr/user/login/doLogin.json'
		url2 = 'https://ex.nhlogis.co.kr/resrv/inq/list.do'
		req = s.post(url, data=LOGIN_INFO)
		
		req1 = s.get(url2)
		html = req1.text
		gogo = bs(html, "html.parser")
		loginok = gogo.find('div', {'class':'util-box'})
		if loginok == None:
			print("로그인이 않되었습니다.")
		else:
			list = 'https://ex.nhlogis.co.kr/resrv/inq/select.json'
			req_list = s.post(list, data=DELETE_INFO).json() 		
			i = req_list['data']
			ass2 = req_list['result']
			if ass2 != True:
				print("정보가 없습니다.")
			else:
				ordNm = i['ordNm']
				ordTelno = i['ordTelno']
				#priceType = i['priceType']
				#priceTypeNm = i['priceTypeNm']
				#rcvAddr = i['rcvAddr']
				#rcvAddrDtl = i['rcvAddrDtl']
				#rcvHpno = i['rcvHpno']
				#rcvPostno = i['rcvPostno']
				#rcvTelno = i['rcvTelno']
				ein = context[1]
				rcvPostno,rcvAddr = addr(ein)
				rcvAddrDtl = context[2]
				rcvHpno = context[0]
				rcvTelno = rcvHpno
				if '선불' in context[3]:
					priceTypeNm = '선불'
					priceType = '01'
				else:
					priceTypeNm = '착불'
					priceType = '02'	
				prodAmt = i['prodAmt']
				prodNm = i['prodNm']
				prodType = i['prodType']
				prodTypeNm = i['prodTypeNm']
				rcpNo = i['rcpNo']				
				rcvNm = i['rcvNm']				
				rmk = i['rmk']
				rsvDt = i['rsvDt']
				rsvNo = i['rsvNo']
				sndAddr = i['sndAddr']
				sndAddrDtl = i['sndAddrDtl']
				sndHpno = i['sndHpno']
				sndNm = i['sndNm']
				sndPostno = i['sndPostno']
				sndTelno = i['sndTelno']
				new_string = re.sub("[-]","",rsvDt)
				SAVE_INFO = {'rcpNo': rcpNo,
							'rsvNo': rsvNo,
							'rsvDt': new_string,
							'ordNm': ordNm,
							'ordTelno': ordTelno,
							'sndNm': sndNm,
							'sndTelno': sndTelno,
							'sndHpno': sndHpno,
							'sndPostno': sndPostno,
							'sndAddr': sndAddr,
							'sndAddrDtl': sndAddrDtl,
							'rcvNm': rcvNm,
							'rcvTelno': rcvTelno,
							'rcvHpno': rcvHpno,
							'rcvPostno': rcvPostno,
							'rcvAddr': rcvAddr,
							'rcvAddrDtl': rcvAddrDtl,
							'rmk': rmk,
							'prodNm': prodNm,
							'prodType': prodType,
							'priceType': priceType,
							'prodAmt': prodAmt,
							'prodTypeNm': prodTypeNm,
							'priceTypeNm': priceTypeNm,
							'boxQ': '1',
							'maYn': ''
							}
				list = 'https://ex.nhlogis.co.kr/resrv/reg/save.json'
				req_list = s.post(list, data=SAVE_INFO).json()
				
	return [rcvHpno,rcvTelno,rcvPostno,rcvAddr,rcvAddrDtl,priceTypeNm]
	
@nh.route('/')
@nh.route('index')
def index():
	#SQLITE3 DB 없으면 만들다.
	con = sqlite3.connect(mydir + '/db/nh.db',timeout=60)
	con.execute('CREATE TABLE IF NOT EXISTS mydata (NHID TEXT, NHPASSWD TEXT, NAME TEXT, HP TEXT, ZIP TEXT, ADDR TEXT, ADDR2 TEXT)')	
	con.execute("PRAGMA cache_size = 10000")
	con.execute("PRAGMA locking_mode = NORMAL")
	con.execute("PRAGMA temp_store = MEMORY")
	con.execute("PRAGMA auto_vacuum = 1")
	con.execute("PRAGMA journal_mode=WAL")
	con.execute("PRAGMA synchronous=NORMAL")
	con.close()
	#SQLITE3 DB 없으면 만들다.
	con = sqlite3.connect(mydir + '/db/nh.db',timeout=60)
	con.execute('CREATE TABLE IF NOT EXISTS nh (rcvNm TEXT, rcvTelno TEXT,rcvHpno TEXT,rcvPostno TEXT,rcvAddr TEXT,rcvAddrDtl TEXT,prodTypeNm TEXT,prodAmt TEXT,priceTypeNm TEXT,rmk TEXT,sndNm TEXT,sndTelno TEXT,sndHpno TEXT,sndPostno TEXT,sndAddr TEXT,sndAddrDtl TEXT,boxQ TEXT,prodNm TEXT,surcharge TEXT,date TEXT,amount TEXT,rsvNo TEXT)')	
	con.execute("PRAGMA cache_size = 10000")
	con.execute("PRAGMA locking_mode = NORMAL")
	con.execute("PRAGMA temp_store = MEMORY")
	con.execute("PRAGMA auto_vacuum = 1")
	con.execute("PRAGMA journal_mode=WAL")
	con.execute("PRAGMA synchronous=NORMAL")
	con.close()	
	#기본정보 화면출력
	con = sqlite3.connect(mydir + '/db/nh.db',timeout=60)
	con.row_factory = sqlite3.Row
	cur = con.cursor()
	cur.execute("select * from mydata")
	rows = cur.fetchone()
	if rows:
		nh_id = rows['NHID']
		nh_pwd = rows['NHPASSWD']
		sndNm = rows['NAME']
		sndHpno = rows['HP']
		sndAddr = rows['ADDR']
		sndAddrDtl = rows['ADDR2']
	else:
		nh_id='농협택배 아이디를 입력하세요'
		nh_pwd='농협택배 비밀번호를 입력하세요'
		sndNm = '보내는사람을 입력하세요'
		sndHpno = '보내는사람의 휴대폰번호를 입력하세요'
		sndAddr = '보내는사람의 주소를 입력하세요'
		sndAddrDtl = '보내는사람의 상세주소를 입력하세요'
	return render_template('nh.html', nh_id = nh_id, nh_pwd = nh_pwd, sndNm = sndNm, sndHpno = sndHpno, sndAddr = sndAddr, sndAddrDtl = sndAddrDtl)

#농협택배 리스트 목록 보기
@nh.route('index_list', methods=["GET"])
def index_list():
	if not session.get('logFlag'):
		return redirect(url_for('main.index'))
	else:
		per_page = 10
		page, _, offset = get_page_args(per_page=per_page)
		con = sqlite3.connect(mydir + '/db/nh.db',timeout=60)
		con.execute("PRAGMA cache_size = 10000")
		con.execute("PRAGMA locking_mode = NORMAL")
		con.execute("PRAGMA temp_store = MEMORY")
		con.execute("PRAGMA auto_vacuum = 1")
		con.execute("PRAGMA journal_mode=WAL")
		con.execute("PRAGMA synchronous=NORMAL")
		con.row_factory = sqlite3.Row
		cur = con.cursor()
		cur.execute('SELECT COUNT(*) FROM nh')
		total = cur.fetchone()[0]
		cur.execute('select * from nh ORDER BY date DESC LIMIT ' + str(per_page) + ' OFFSET ' + str(offset))
		wow = cur.fetchall()		
		return render_template('nh_list.html', wow = wow, pagination=Pagination(page=page, total=total, per_page=per_page))

#농협택배 기본정보 입력및 저장
@nh.route('nh_login', methods=["GET"])
def nh_login():
	if not session.get('logFlag'):
		return redirect(url_for('main.index'))
	else:
		#SQLITE3 DB 없으면 만들다.
		con = sqlite3.connect(mydir + '/db/nh.db',timeout=60)
		con.execute('CREATE TABLE IF NOT EXISTS mydata (NHID TEXT, NHPASSWD TEXT, NAME TEXT, HP TEXT, ZIP TEXT, ADDR TEXT, ADDR2 TEXT)')	
		con.execute("PRAGMA cache_size = 10000")
		con.execute("PRAGMA locking_mode = NORMAL")
		con.execute("PRAGMA temp_store = MEMORY")
		con.execute("PRAGMA auto_vacuum = 1")
		con.execute("PRAGMA journal_mode=WAL")
		con.execute("PRAGMA synchronous=NORMAL")
		con.close()
		con = sqlite3.connect(mydir + '/db/nh.db',timeout=60)
		sql = "SELECT * FROM mydata"	
		tt = con.execute(sql,).fetchall()
		if len(tt) != 0:
			pass
		else:
			a = request.args.get('nh_id') #농협아이디
			b = request.args.get('nh_pwd') #농협비밀번호
			c = request.args.get('sndNm') #보내는사람
			d = request.args.get('sndHpno') #휴대폰번호
			ein = request.args.get('sndAddr') #주소
			e,f = addr(ein) #주소를 가지고 우편번호 찾기
			g = request.args.get('sndAddrDtl')
			all = '{} {}\n{} {} {}\n{} {}'.format(a,b,c,d,e,f,g)
			add_data(a,b,c,d,e,f,g)
		return redirect(url_for('nh.index'))

#농협택배 예약취소(목록에서 가능하다)
@nh.route('<rsvno>/<rcvNm>/<rcvHpno>/<rcvAddr>/<rcvAddrDtl>/<prodNm>/<priceTypeNm>/<date>/nh_del', methods=["GET"])
def nh_del(rsvno,rcvNm,rcvHpno,rcvAddr,rcvAddrDtl,prodNm,priceTypeNm,date):
	if not session.get('logFlag'):
		return redirect(url_for('main.index'))
	else:
		if rsvno == 'NULL':
			a = rcvNm
			t = date
			ac = delete_top2(a,t,rsvno)
			if '없음' in ac:
				total = '예약하신접수가 없습니다.'
			else:
				total = '{}\n예약번호 {}\n{} 님 예약취소 되었습니다.'.format(t,rsvno,a)
			all = [total]
		else:
			now,num,myday,nowtime,mytime = mydate()
			at,aa,ai = delete_top(rsvno)
			a = aa
			test = at
			t = now.strptime(test, "%Y-%m-%d").strftime("%y%m%d")
			ac = delete_top2(a,t,rsvno)
			if '없음' in ac:
				total = '예약하신접수가 없습니다.'
			else:
				total = '{}\n예약번호 {}\n{} 님 예약취소 되었습니다.'.format(at,ai,aa)
			all = [total]
		return render_template('msg.html', msg = all)

#농협택배 예약수정(목록에서 가능하다)
@nh.route('<rsvNo>/<rcvHpno>/<rcvAddr>/<rcvAddrDtl>/<priceTypeNm>/nh_edit', methods=["GET"])
def nh_edit(rsvNo,rcvHpno,rcvAddr,rcvAddrDtl,priceTypeNm):
	if not session.get('logFlag'):
		return redirect(url_for('main.index'))
	else:
		#rsvNo = request.args.get('rsvNo')
		#rcvHpno = request.args.get('rcvHpno')
		#rcvAddr = request.args.get('rcvAddr')
		#rcvAddrDtl = request.args.get('rcvAddrDtl')
		#priceTypeNm = request.args.get('priceTypeNm')
		#rsvNo = request.form['rsvNo']
		#rcvHpno = request.form['rcvHpno']
		#rcvAddr = request.form['rcvAddr']
		#rcvAddrDtl = request.form['rcvAddrDtl']
		#priceTypeNm = request.form['priceTypeNm']
		return render_template('nh_edit.html',rsvNo = rsvNo,rcvHpno = rcvHpno,rcvAddr = rcvAddr,rcvAddrDtl = rcvAddrDtl,priceTypeNm = priceTypeNm)

@nh.route("edit_result/<rsvNo>/<rcvHpno>/<rcvAddr>/<rcvAddrDtl>/<priceTypeNm>", methods=['POST'])
def edit_result(rsvNo,rcvHpno,rcvAddr,rcvAddrDtl,priceTypeNm):
	if not session.get('logFlag'):
		return redirect(url_for('main.index'))
	else:
		rsvNo = request.form['rsvNo']
		rcvHpno = request.form['rcvHpno']
		rcvAddr = request.form['rcvAddr']
		rcvAddrDtl = request.form['rcvAddrDtl']
		priceTypeNm = request.form['priceTypeNm']
		total = nh_edit_api(rsvNo,rcvHpno,rcvAddr,rcvAddrDtl,priceTypeNm)
		all = [total.get_json()]
		
		return render_template('msg.html', msg = all)		
#농협택배 예약
@nh.route('nh_add', methods=["GET"])
def nh_add():
	msg = []
	now,num,myday,nowtime,mytime = mydate()
	a = request.args.get('rcvNm') #받는사람
	b = request.args.get('rcvHpno') #휴대폰번호
	c = request.args.get('rcvAddr') #주소
	d = request.args.get('rcvAddrDtl') #상세주소
	e = request.args.get('prodNm') #물품명
	f = request.args.get('prodNm') + '_' + num #물품명
	g = request.args.get('priceTypeNm') #택배 선불/착불
	texter = [a,b,c,d,e,f,g]
	v,w = adduse(texter)
	a = texter[0]
	r = texter[4]
	u = texter[5]
	numt = num
	st_json = jsonfile(numt, a, r, u, v, w)
	if st_json == None:
		pass
	else:
		all2 = rezcomp(st_json)
		for i in all2:
			ck1 = i['rcvNm']
			ck4 = i['rcvAddr']
			ck2 = i['rcvAddrDtl']
			ck3 = i['rcvHpno']
			ck6 = i['priceTypeNm']
			ck7 = i['rcvPostno']
			aa = i['complte']
			rsvno = i['rsvNo']
			rcpNo = i['rcpNo']
		adduse2(rsvno,rcpNo,numt, a, r, u)
		ff = texter[1]
		af = len(ff)
		if af == 11:		
			mydata = myguest(ff)
		else:
			mydata = '처음구매자입니다.'
		not_addr = addr_not(ck7)
		msg_1 = '이름 : {}'.format(ck1)
		msg_2 = '연락처 : {}'.format(ck4)
		msg_3 = '주 소 : {} {}'.format(ck2,ck3)
		msg_4 = '택배비 결재방법은 {} 입니다.'.format(ck6)
		msg_5 = '예약이 {}하였습니다.'.format(aa)
		msg_6 = '{} {}'.format(mydata,not_addr)
		msg_7 = '예약번호는 {}'.format(rsvno)
		all = [msg_1,msg_2,msg_3,msg_4,msg_5,msg_6,msg_7]
	
	return render_template('msg.html', msg = all)

#DB 에만 저장한다.
@nh.route('nh_add_wait', methods=["GET"])
def nh_add_wait():
	now,num,myday,nowtime,mytime = mydate()
	a = request.args.get('rcvNm') #받는사람
	b = request.args.get('rcvHpno') #휴대폰번호
	c = request.args.get('rcvAddr') #주소
	d = request.args.get('rcvAddrDtl') #상세주소
	e = request.args.get('prodNm') #물품명
	f = request.args.get('prodNm') + '_' + num #물품명 DB저장용
	g = request.args.get('priceTypeNm') #택배 선불/착불
	texter = [a,b,c,d,e,f,g]
	test = adduse(texter)
	logger.info('test')	
	return redirect(url_for('nh.index'))
	
#예약 api
@nh.route('<rcvNm>/<rcvHpno>/<rcvAddr>/<rcvAddrDtl>/<prodNm>/<priceTypeNm>/nh_add_api', methods=["GET"])
def nh_add_api(rcvNm,rcvHpno,rcvAddr,rcvAddrDtl,prodNm,priceTypeNm):
	now,num,myday,nowtime,mytime = mydate()
	a = rcvNm
	b = rcvHpno
	c = rcvAddr
	d = rcvAddrDtl
	e = prodNm
	f = prodNm  + '_' + num
	g = priceTypeNm
	texter = [a,b,c,d,e,f,g]
	v,w = adduse(texter)
	a = texter[0]
	r = texter[4]
	u = texter[5]
	numt = num
	st_json = jsonfile(numt, a, r, u, v, w)
	if st_json == None:
		pass
	else:
		all2 = rezcomp(st_json)
		for i in all2:
			ck1 = i['rcvNm']
			ck4 = i['rcvAddr']
			ck2 = i['rcvAddrDtl']
			ck3 = i['rcvHpno']
			ck6 = i['priceTypeNm']
			ck7 = i['rcvPostno']
			aa = i['complte']
			rsvno = i['rsvNo']
			rcpNo = i['rcpNo']
		print(rsvno, rcpNo)
		adduse2(rsvno,rcpNo,numt, a, r, u)
		ff = texter[1]
		af = len(ff)
		if af == 11:		
			mydata = myguest(ff)
		else:
			mydata = '처음구매자입니다.'
		not_addr = addr_not(ck7)
		msg = '{}\n{}\n{} {}\n택배비 결재방법은 {} 입니다.\n예약이 {}하였습니다.\n{}\n{}\n접수번호는 {} 예약번호는 {}'.format(ck1,ck4,ck2,ck3,ck6,aa,mydata,not_addr,rcpNo,rsvno)
		print(msg)
	return jsonify(msg)
	
#DB 예약 검색 api
@nh.route('<search>/nh_search_api', methods=["GET"])
def nh_search_api(search):
	now,num,myday,nowtime,mytime = mydate()
	texter = [search]
	a = texter
	msg = []	
	numt = texter[0]
	hangul = re.compile(r'[ㄱ-ㅣ가-힣]')
	results = re.findall(hangul, numt)
	if len(results) != 0:
		str = "".join(results)
		all = dbfile(numt,now)
	else:
		all = dbfile(numt,now)
	count = 0
	for ii in all:
		print(ii)
		msg.append(ii)
		count += 1
	count_total = count * 4500
	count_all = '총 택배요금은 {}원입니다.'.format(count_total)
	msg.append(count_all)
	print(msg)
	return jsonify(msg)
		
#DB 예약 검색 api
@nh.route('<search>/nh_delivery_api', methods=["GET"])
def nh_delivery_api(search):
	msg = []
	now,num,myday,nowtime,mytime = mydate()
	mml = [search]
	test = mml[0]
	mydata = r_delivery(now,test,myday)
	for ii in mydata:	
		print(ii)
		msg.append(ii)
	print(msg)
	return jsonify(msg)
	
#농협택배 예약취소 API
@nh.route('<rsvno>/nh_del_api', methods=["GET"])
def nh_del_api(rsvno):
	now,num,myday,nowtime,mytime = mydate()
	at,aa,ai = delete_top(rsvno)
	a = aa
	test = at
	t = now.strptime(test, "%Y-%m-%d").strftime("%y%m%d")
	ac = delete_top2(a,t,rsvno)
	if '없음' in ac:
		all = '예약하신접수가 없습니다.'
	else:
		all = '{}\n예약번호 {}\n{} 님 예약취소 되었습니다.'.format(at,ai,aa)
	return jsonify(all)
	
#농협택배 주소테스트 API
@nh.route('<address>/nh_addrtest_api', methods=["GET"])
def nh_addrtest_api(address):
	d,e = addr(address)
	all = '{} {}'.format(d,e)
	return jsonify(all)
	
#농협택배 예약수정 API
@nh.route('<rsvno>/<rcvHpno>/<rcvAddr>/<rcvAddrDtl>/<priceTypeNm>/nh_edit_api', methods=["GET"])
def nh_edit_api(rsvno,rcvHpno,rcvAddr,rcvAddrDtl,priceTypeNm):
	context = [rcvHpno,rcvAddr,rcvAddrDtl,priceTypeNm]
	rcvHpno,rcvTelno,rcvPostno,rcvAddr,rcvAddrDtl,priceTypeNm = edit_top(rsvno,context)
	edit_db(rsvno,rcvHpno,rcvTelno,rcvPostno,rcvAddr,rcvAddrDtl,priceTypeNm)
	all = '{} 성공적으로 수정되었습니다.'.format(rsvno)
	return jsonify(all)
	

