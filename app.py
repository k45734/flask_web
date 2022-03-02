#-*- coding: utf-8 -*-
import sys
try:
	reload(sys)
	sys.setdefaultencoding('utf-8')
except:
	pass
from flask import Flask, flash, redirect, render_template, request, session, abort, url_for
import platform
import os.path, os, logging
from logging.handlers import RotatingFileHandler
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.base import JobLookupError
from apscheduler.triggers.cron import CronTrigger
if platform.system() == 'Windows':
	at = os.path.splitdrive(os.getcwd())
	logdata = at[0] + '/data/log'
else:
	logdata = '/data/log'
def createFolder(directory):
    try:
        if not os.path.exists(directory):
            os.makedirs(directory)
    except OSError:
        print ('Error: Creating directory. ' +  directory)
		

def create_app():
#if __name__ == '__main__':
	createFolder(logdata)
	filepath = logdata + '/flask.log'
	if not os.path.isfile(filepath):
		f = open(logdata + '/flask.log','a', encoding='utf-8')
	rfh = logging.handlers.RotatingFileHandler(filename=logdata + '/flask.log', mode='a', maxBytes=5*1024*1024, backupCount=2, encoding=None, delay=0)
	logging.basicConfig(level=logging.INFO,format="[%(filename)s:%(lineno)d %(levelname)s] - %(message)s",handlers=[rfh])
	logger = logging.getLogger()
	app = Flask(__name__)	
	app.secret_key = os.urandom(12)
	job_defaults = { 'max_instances': 1 }
	scheduler = BackgroundScheduler(job_defaults=job_defaults)
	#scheduler = BackgroundScheduler()
	scheduler.start()
	from pages import main_page
	#from pages import sub_page
	from pages import sub2_page
	from pages import sub3_page
	from pages import sub4_page
	from pages import copytoon
	app.register_blueprint(main_page.bp)
	#app.register_blueprint(sub_page.bp1)
	app.register_blueprint(sub2_page.bp2)
	app.register_blueprint(sub3_page.bp3)
	app.register_blueprint(sub4_page.bp4)
	app.register_blueprint(copytoon.webtoon)
	app.run(host="0.0.0.0", debug=True, threaded=True)
	return app
	
if __name__ == '__main__':
	create_app()