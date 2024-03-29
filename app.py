#-*- coding: utf-8 -*-
import sys
try:
	reload(sys)
	sys.setdefaultencoding('utf-8')
except:
	pass

import os

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
	app.run(host="0.0.0.0", debug=False, threaded=True, use_reloader=False)
	return app
	
if __name__ == '__main__':
	#2023-03-30 DB파일 이전
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
		try:
			shutil.move(wwin + '/jobs.sqlite' , output_save_folder_path)
		except:
			pass
		try:
			shutil.move(wwin + '/database.db' , output_save_folder_path)
		except:
			pass
		try:
			shutil.move(wwin + '/telegram.db' , output_save_folder_path)
		except:
			pass
		try:
			shutil.move(wwin + '/news.db' , output_save_folder_path)
		except:
			pass
		try:
			shutil.move(wwin + '/funmom.db' , output_save_folder_path)
		except:
			pass
		try:
			shutil.move(wwin + '/quiz.db' , output_save_folder_path)
		except:
			pass
		try:
			shutil.move(wwin + '/unse.db' , output_save_folder_path)
		except:
			pass
		try:
			shutil.move(wwin + '/delivery.db' , output_save_folder_path)
		except:
			pass
		try:
			shutil.move(wwin + '/rclone.db' , output_save_folder_path)
		except:
			pass
		try:
			shutil.move(wwin + '/webtoon_new.db' , output_save_folder_path)
		except:
			pass
		try:
			shutil.move(wwin + '/ip_list.db' , output_save_folder_path)
		except:
			pass
		try:
			shutil.move(wwin + '/shop.db' , output_save_folder_path)
		except:
			pass
	else:
		try:
			shutil.move(wwin + '/jobs.sqlite' , output_save_folder_path)
		except:
			pass
		try:
			shutil.move(wwin + '/database.db' , output_save_folder_path)
		except:
			pass
		try:
			shutil.move(wwin + '/telegram.db' , output_save_folder_path)
		except:
			pass
		try:
			shutil.move(wwin + '/news.db' , output_save_folder_path)
		except:
			pass
		try:
			shutil.move(wwin + '/funmom.db' , output_save_folder_path)
		except:
			pass
		try:
			shutil.move(wwin + '/quiz.db' , output_save_folder_path)
		except:
			pass
		try:
			shutil.move(wwin + '/unse.db' , output_save_folder_path)
		except:
			pass
		try:
			shutil.move(wwin + '/delivery.db' , output_save_folder_path)
		except:
			pass
		try:
			shutil.move(wwin + '/rclone.db' , output_save_folder_path)
		except:
			pass
		try:
			shutil.move(wwin + '/webtoon_new.db' , output_save_folder_path)
		except:
			pass
		try:
			shutil.move(wwin + '/ip_list.db' , output_save_folder_path)
		except:
			pass
		try:
			shutil.move(wwin + '/shop.db' , output_save_folder_path)
		except:
			pass
		
	#VNSTAT 설치 및 실행
	if platform.system() == 'Windows':
		pass
	else:
		if os.path.exists('/usr/bin/vnstat'):
			subprocess.call('/usr/sbin/vnstatd -d', shell=True)
			subprocess.call('/usr/bin/vnstat -i eth0', shell=True)
		else:
			subprocess.call('apk update', shell=True)
			subprocess.call('apk add vnstat', shell=True)
			subprocess.call('/usr/sbin/vnstatd -d', shell=True)
			subprocess.call('/usr/bin/vnstat -i eth0', shell=True)
	create_app()