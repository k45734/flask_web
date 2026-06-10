#-*- coding: utf-8 -*-
import sys
try:
	reload(sys)
	sys.setdefaultencoding('utf-8')
except:
	pass

import os
import socket  # 💡 소켓 라이브러리 상단 추가

try:
	from flask import Flask, flash, redirect, render_template, request, session, abort, url_for
except ImportError:
	os.system('pip install flask')
	import Flask, flash, redirect, render_template, request, session, abort, url_for

try:
	import psutil
except ImportError:
    os.system('pip install psutil')
    import psutil

try:
	import requests
except ImportError:
	os.system('pip install requests')
	import requests

try:
	from pytz import timezone
except ImportError:
	os.system('pip install pytz')
	from pytz import timezone

try:
    from apscheduler.schedulers.background import BackgroundScheduler
except ImportError:
	os.system('pip install apscheduler')
	from apscheduler.schedulers.background import BackgroundScheduler
    
try:
    from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
except ImportError:
    os.system('pip install sqlalchemy')
    from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore

try:
    import os.path, json, os, re, time, logging, io, subprocess, platform, telegram, threading, sqlite3, random,urllib.request, asyncio
except ImportError:
    os.system('pip install telegram')
    import os.path, json, os, re, time, logging, io, subprocess, platform, telegram, threading, sqlite3, random,urllib.request, asyncio
    
import platform,subprocess
import os.path, os,shutil
if platform.system() == 'Windows':
	at = os.path.splitdrive(os.getcwd())
	logdata = at[0] + '/data/log'
	dbdata = at[0] + '/data/db'
else:
	logdata = '/data/log'
	dbdata = '/data/db'
	
def createFolder(directory):
    try:
        if not os.path.exists(directory):
            os.makedirs(directory)
    except OSError:
        print ('Error: Creating directory. ' +  directory)
		

def create_app():
	createFolder(logdata)
	app = Flask(__name__)	
	app.secret_key = os.urandom(12)
	
	# 💡 블루프린트 및 모듈들을 로드합니다 (이때 scheduler 객체가 메모리에 올라옵니다)
	from pages import main_page
	from pages import sub2_page
	from pages import sub3_page
	from pages import sub4_page
	from pages import copytoon
	from pages import rclone
	from pages import nh
	
	app.register_blueprint(main_page.bp)
	app.register_blueprint(sub2_page.bp2)
	app.register_blueprint(sub3_page.bp3)
	app.register_blueprint(sub4_page.bp4)
	app.register_blueprint(copytoon.webtoon)
	app.register_blueprint(rclone.rclone)
	app.register_blueprint(nh.nh)

	# ✨ [핵심 조치] Flask 웹 서버 가동 직전, 소켓 락 검증 후 스케줄러 최종 기동
	try:
		# 전역 변수로 binder를 유지하여 함수가 끝나도 소켓 자물쇠가 풀리지 않게 방어
		global binder
		binder = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		binder.bind(('127.0.0.1', 49999))
		
		# 포트 선점에 성공했다면 이 프로세스가 메인(1번 워커)이므로 스케줄러 가동
		if not main_page.scheduler.running:
			main_page.scheduler.start()
			print("🚀 [스케줄러 시스템] 메인 프로세스 검증 완료 - 스케줄러를 안전하게 구동합니다.")
	except socket.error:
		# 이미 49999 포트가 닫혀있다면 다른 프로세스가 스케줄러를 돌리고 있는 중임
		print("⚠️ [스케줄러 시스템] 이미 다른 프로세스에서 스케줄러가 실행 중이므로 가동을 양보합니다.")

	# 웹 서버 구동 (use_reloader=False 필수: True일 경우 내부적으로 프로세스를 2번 띄움)
	app.run(host="0.0.0.0", debug=False, threaded=True, use_reloader=False)
	return app
	
if __name__ == '__main__':
	# DB파일 이전 로직
	if platform.system() == 'Windows':
		at = os.path.splitdrive(os.getcwd())
		wwin = at[0] + '/data'
	else:
		wwin = '/data'
	current_path = os.getcwd()
	output_save_folder_path = dbdata
	if not os.path.exists(output_save_folder_path):
		os.mkdir(output_save_folder_path)
		print('폴더 생성완료')
	
	# 다량의 shutil.move 로직 (중복 제거 및 정리)
	db_files = ['jobs.sqlite', 'database.db', 'telegram.db', 'news.db', 'funmom.db', 
	            'quiz.db', 'unse.db', 'delivery.db', 'rclone.db', 'webtoon_new.db', 'ip_list.db', 'shop.db']
	for db_f in db_files:
		try: shutil.move(wwin + f'/{db_f}', output_save_folder_path)
		except: pass
		
	# VNSTAT 설치 및 실행
	if platform.system() != 'Windows':
		if os.path.exists('/usr/bin/vnstat'):
			subprocess.call('/usr/sbin/vnstatd -d', shell=True)
			subprocess.call('/usr/bin/vnstat -i eth0', shell=True)
		else:
			subprocess.call('apk update', shell=True)
			subprocess.call('apk add vnstat', shell=True)
			subprocess.call('/usr/sbin/vnstatd -d', shell=True)
			subprocess.call('/usr/bin/vnstat -i eth0', shell=True)

	# 💡 깔끔하게 앱 팩토리 구동
	create_app()