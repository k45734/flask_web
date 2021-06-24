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
		f = open('./log/flask.log','a', encoding='UTF8')
	logger = logging.getLogger(__name__)
	fileHandler = RotatingFileHandler('./log/flask.log', maxBytes=1024*5, backupCount=5) 
	fileHandler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] [%(filename)s:%(lineno)s] >> %(message)s')) 
	logger.addHandler(fileHandler) 
	logger.setLevel(logging.DEBUG)
	logger.debug("test debug log") 
	logger.info("info log") 
	logger.warning("warring !!!!") 
	logger.error("bug bug bug bug") 
	logger.critical("critical !! ~~")

	#logging.basicConfig(format = '%(asctime)s:%(levelname)s:%(message)s', 
	#					datefmt = '%m/%d/%Y %I:%M:%S %p', 
	#					filename = "./log/flask.log", 
	#					level = logging.DEBUG
	#					)
	app = Flask(__name__)	
	app.secret_key = os.urandom(12)
	#app.config['SECRET_KEY'] = os.urandom(12)
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