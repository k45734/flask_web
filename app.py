#-*- coding: utf-8 -*-
import sys
try:
	reload(sys)
	sys.setdefaultencoding('utf-8')
except:
	pass
import random
from flask import Flask
import os
import datetime
import requests
from flask import Flask, flash, redirect, render_template, request, session, abort, url_for
import os.path
from flask_ipblock import IPBlock
from flask_ipblock.documents import IPNetwork
import logging
from logging.handlers import RotatingFileHandler
from pytz import timezone
import sqlite3
import time
from flask_sqlalchemy import SQLAlchemy
import psutil

def createFolder(directory):
    try:
        if not os.path.exists(directory):
            os.makedirs(directory)
    except OSError:
        print ('Error: Creating directory. ' +  directory)
		

def create_app():
#if __name__ == '__main__':
	createFolder('./log')
	filepath = './log/flask.log'
	if not os.path.isfile(filepath):
		f = open('./log/flask.log','a', encoding='utf-8')
	#logger = logging.getLogger(__name__)
	#logging.basicConfig(format = '%(asctime)s:%(levelname)s:%(message)s', 
	#					datefmt = '%m/%d/%Y %I:%M:%S %p', 
	#					filename = "./log/flask.log", 
	#					encoding='utf-8',
	#					level = logging.DEBUG
	#					)
	log_formatter = logging.Formatter('%(asctime)s %(levelname)s %(funcName)s(%(lineno)d) %(message)s')
	logFile = './log/flask.log'
	my_handler = RotatingFileHandler(logFile, 
									mode='a', 
									maxBytes=5*1024*1024, 
									backupCount=2, 
									encoding='utf-8', 
									delay=0)
	my_handler.setFormatter(log_formatter)
	my_handler.setLevel(logging.DEBUG)
	app_log = logging.getLogger(__name__)
	app_log.setLevel(logging.DEBUG)
	app_log.addHandler(my_handler)
	app = Flask(__name__)	
	app.secret_key = os.urandom(12)
	from pages import main_page
	#from pages import sub_page
	from pages import sub2_page
	from pages import sub3_page
	from pages import sub4_page
	app.register_blueprint(main_page.bp)
	#app.register_blueprint(sub_page.bp1)
	app.register_blueprint(sub2_page.bp2)
	app.register_blueprint(sub3_page.bp3)
	app.register_blueprint(sub4_page.bp4)
	app.run(host="0.0.0.0", debug=True, threaded=True)
	return app
	
if __name__ == '__main__':
	create_app()