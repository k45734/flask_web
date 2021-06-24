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
import logging
from logging.handlers import RotatingFileHandler
bp2 = Blueprint('sub2', __name__, url_prefix='/sub2')
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
dfolder = os.path.dirname(os.path.abspath(__file__)) + '/log'
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
@bp2.route('/')
@bp2.route('index')
def second():
	#return 'Hello, python !<br>Flask TEST PAGE 3!'
	return redirect(url_for('main.index'))
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
	bs4_trans=bs4.BeautifulSoup(pathway,"html.parser")
	result=bs4_trans.select_one("#KOSPI_now").text
	return render_template('start.html', testDataHtml=result)