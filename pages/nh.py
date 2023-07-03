#-*- coding: utf-8 -*-
import requests, sys, re, subprocess,os, json, platform, logging, datetime, time,logging.handlers,urllib.request,shutil
from datetime import timedelta
try:
	from openpyxl import Workbook
except ImportError:
	os.system('pip install openpyxl')
	from openpyxl import Workbook
try:
	import sqlite3
except ImportError:
	os.system('pip install sqlite3')
	import sqlite3	
try:
	import argparse
except ImportError:
	os.system('pip install argparse')
	import argparse
try:
	from bs4 import BeautifulSoup as bs
except ImportError:
	os.system('pip install beautifulsoup4')
	from bs4 import BeautifulSoup as bs
try:
	from telegram import Update
	from telegram.ext import Updater, MessageHandler, Filters, CommandHandler, CallbackContext
except ImportError:
	os.system('pip install python-telegram')
	from telegram import Update
	from telegram.ext import Updater, MessageHandler, Filters, CommandHandler, CallbackContext
mydir = os.path.dirname(os.path.realpath(__file__))
output_save_folder_path = mydir + '/db'
if not os.path.exists(output_save_folder_path):
	os.mkdir(output_save_folder_path)
	print('폴더 생성완료')
	try:
		shutil.move(mydir + '/nh.db' , output_save_folder_path)
	except:
		pass
else:
	try:
		shutil.move(mydir + '/nh.db' , output_save_folder_path)
	except:
		pass
	
#테스트용
if platform.system() == 'Windows':
	my_token = '1017461760:AAFE3SMHoQrKS4Fany8AW6NbSUjrEF-bR1U'
	server_api = 'http://127.0.0.1:5000'
#서버용
else:
	my_token = '1024850702:AAGkIdE-IdLg0ENRg8yiDQuVzBux8gIRkI0'
	server_api = 'http://kdtc.iptime.org:19998'

filepath = mydir + '/log/nh.log'
if not os.path.isfile(filepath):
	f = open(filepath,'a', encoding='utf-8')
fileMaxByte = 1024*500
rfh = logging.handlers.RotatingFileHandler(filename=filepath, mode='a', maxBytes=fileMaxByte, backupCount=5, encoding='utf-8', delay=0)
logging.basicConfig(level=logging.INFO,format="[%(asctime)s %(filename)s:%(lineno)d %(levelname)s] - %(message)s",datefmt='%Y-%m-%d %H:%M:%S',handlers=[rfh])
logger = logging.getLogger()
logger.info('start telegram chat bot')

def mydate():
	now = datetime.datetime.now()
	num = now.strftime('%y%m%d')
	myday = now.strftime('%Y-%m-%d')
	nowtime = time.localtime()
	mytime = "%04d%02d%02d" % (nowtime.tm_year, nowtime.tm_mon, nowtime.tm_mday)
	return [now,num,myday,nowtime,mytime]
	
#버젼정보
def ver(update: Update, context: CallbackContext) -> None:
	context.bot.send_message(chat_id=update.message.chat_id, text='현재버젼 2023-07-03')
	logger.info('사용자 [%s] = 명령어 [%s]', update.message.chat_id, update.message.text)
	comp = '완료'
	return comp
	
#도움말 정보입니다.								
def help_command(update: Update, context: CallbackContext) -> None:
	msg = "[명령어 목록입니다]\n/add 받는분 휴대폰번호 받는분주소 받는분상세주소 물품명 갯수 선불/착불\n/del 예약번호\n/search 220109(날짜)\n/delivery 예약접수한날짜"
	context.bot.send_message(chat_id=update.message.chat_id, text=msg)
	logger.info('사용자 [%s] = 명령어 [%s]', update.message.chat_id, update.message.text)
	comp = '완료'
	return comp

#서버를 재시작합니다.	
def reset(update: Update, context: CallbackContext) -> None:
	if 544321507 == update.message.chat_id or 5089453048 == update.message.chat_id :
		a = context.args
		b = len(a)
		if b == 0:
			context.bot.send_message(chat_id=update.message.chat_id, text='비밀번호가 없습니다.')
		else:
			numt = context.args[0]
			if numt == 'super':
				context.bot.send_message(chat_id=update.message.chat_id, text='재시작 명령을 보냈습니다.')
				os.system('/data/nh.sh')
			else:
				context.bot.send_message(chat_id=update.message.chat_id, text='비밀번호가 없습니다.')
	else:
		teee = update.message.chat_id
		context.bot.send_message(chat_id=update.message.chat_id, text=teee)
	logger.info('사용자 [%s] = 명령어 [%s]', update.message.chat_id, update.message.text)
	comp = '완료'
	return comp

#주소가 맞는지 확인합니다.
def addrtest(update: Update, context: CallbackContext) -> None:
	a = ' '.join(context.args)
	b = len(a)
	if b == 0:
		context.bot.send_message(chat_id=update.message.chat_id, text="/addrtest 주소")
		
	else:
		d,e = addr(a)
		all = '{} {}'.format(d,e)
		context.bot.send_message(chat_id=update.message.chat_id, text=all)	
	logger.info('사용자 [%s] = 명령어 [%s]', update.message.chat_id, update.message.text)
	comp = '완료'
	return comp

#택배예약취소하기
def gogo2(update: Update, context: CallbackContext) -> None:
	if 544321507 == update.message.chat_id or 5089453048 == update.message.chat_id:
		with requests.Session() as s:
			headers = {"Cache-Control": "no-cache",   "Pragma": "no-cache",'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36'}
			a = context.args
			b = len(a)
			if b == 0:
				context.bot.send_message(chat_id=update.message.chat_id, text="/del 예약번호")
			else:
				start_url = server_api + '/nh/' + context.args[0] + '/nh_del_api'
				print(start_url)
				url = s.get(server_api, headers=headers)
				check = url.status_code
				if check == 200:
					url = s.get(start_url, headers=headers)
					context.bot.send_message(chat_id=update.message.chat_id, text=url.text)		
	else:
		teee = update.message.chat_id
		context.bot.send_message(chat_id=update.message.chat_id, text=teee)
		context.bot.send_message(chat_id=update.message.chat_id, text="권한이없습니다.")
	logger.info('사용자 [%s] = 명령어 [%s]', update.message.chat_id, update.message.text)
	comp = '완료'
	return comp

#택배예약하기	
def gogo(update: Update, context: CallbackContext) -> None:
	if 544321507 == update.message.chat_id or 5089453048 == update.message.chat_id:
		with requests.Session() as s:
			headers = {"Cache-Control": "no-cache",   "Pragma": "no-cache",'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36'}
			alltext = ' '.join(context.args)
			texter = alltext.split('|')
			b = len(texter)
			if b < 5:
				context.bot.send_message(chat_id=update.message.chat_id, text="/add 받는분|휴대폰번호|받는분주소|받는분상세주소|물품명|선불/착불")
			else:
				alltext = ' '.join(context.args)
				texter = alltext.split('|')
				start_url = server_api + '/nh/' + texter[0] + '/' + texter[1] + '/' + texter[2] + '/' + texter[3] + '/' + texter[4] + '/' + texter[5] + '/nh_add_api'
				print(start_url)
				url = s.get(server_api, headers=headers)
				check = url.status_code
				if check == 200:
					url = s.get(start_url, headers=headers)
					context.bot.send_message(chat_id=update.message.chat_id, text=url.text)		
	else:
		teee = update.message.chat_id
		context.bot.send_message(chat_id=update.message.chat_id, text=teee)
		context.bot.send_message(chat_id=update.message.chat_id, text="권한이없습니다.")
	logger.info('사용자 [%s] = 명령어 [%s]', update.message.chat_id, update.message.text)
	comp = '완료'
	return comp

#실서버에서 택배를 조회해봅니다.		
def delivery(update: Update, context: CallbackContext) -> None:
	now,num,myday,nowtime,mytime = mydate()
	if 544321507 == update.message.chat_id or 5089453048 == update.message.chat_id :
		with requests.Session() as s:
			headers = {"Cache-Control": "no-cache",   "Pragma": "no-cache",'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36'}
			a = context.args
			b = len(a)
			if b == 0:
				start_url = server_api + '/nh/' + num + '/nh_delivery_api'
				print(start_url)
				url = s.get(server_api, headers=headers)
				check = url.status_code
				if check == 200:
					url = s.get(start_url, headers=headers)
			else:
				start_url = server_api + '/nh/' + context.args[0] + '/nh_delivery_api'
				print(start_url)
				url = s.get(server_api, headers=headers)
				check = url.status_code
				if check == 200:
					url = s.get(start_url, headers=headers)			
			last = url.json()
			for msg in last:
				context.bot.send_message(chat_id=update.message.chat_id, text=msg)	
			
	else:
		teee = update.message.chat_id
		context.bot.send_message(chat_id=update.message.chat_id, text=teee)
		context.bot.send_message(chat_id=update.message.chat_id, text="권한이없습니다")
	logger.info('사용자 [%s] = 명령어 [%s]', update.message.chat_id, update.message.text)
	comp = '완료'
	return comp

#서버의 DB확인을 합니다.
def search(update: Update, context: CallbackContext) -> None:
	now,num,myday,nowtime,mytime = mydate()
	if 544321507 == update.message.chat_id or 5089453048 == update.message.chat_id :
		with requests.Session() as s:
			headers = {"Cache-Control": "no-cache",   "Pragma": "no-cache",'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36'}
			a = context.args
			b = len(a)
			if b == 0:
				start_url = server_api + '/nh/' + num + '/nh_search_api'
				print(start_url)
				url = s.get(server_api, headers=headers)
				check = url.status_code
				if check == 200:
					url = s.get(start_url, headers=headers)		
			else:
				start_url = server_api + '/nh/' + context.args[0] + '/nh_search_api'
				print(start_url)
				url = s.get(server_api, headers=headers)
				check = url.status_code
				if check == 200:
					url = s.get(start_url, headers=headers)			
			last = url.json()
			for msg in last:
				context.bot.send_message(chat_id=update.message.chat_id, text=msg)	
				
	else:
		teee = update.message.chat_id
		context.bot.send_message(chat_id=update.message.chat_id, text=teee)
		context.bot.send_message(chat_id=update.message.chat_id, text="권한이없습니다")
	logger.info('사용자 [%s] = 명령어 [%s]', update.message.chat_id, update.message.text)
	comp = '완료'
	return comp
	
def error(update: Update, context: CallbackContext) -> None:
	"""Log Errors caused by Updates."""
	logger.warning('Update "%s" caused error "%s"', update, context.error)
	comp = '완료'
	return comp
		
def main():
	updater = Updater(my_token, use_context=True)
	dp = updater.dispatcher
	dp.add_error_handler(error)
	dp.add_handler(CommandHandler("help", help_command))
	dp.add_handler(CommandHandler("add", gogo)) #예약하기
	dp.add_handler(CommandHandler("del", gogo2)) #예약취소
	dp.add_handler(CommandHandler("delivery", delivery))
	dp.add_handler(CommandHandler("addrtest", addrtest))
	dp.add_handler(CommandHandler("search", search))
	dp.add_handler(CommandHandler("reset", reset))
	dp.add_handler(CommandHandler("ver", ver))
	updater.start_polling()
	updater.idle()
	
if __name__ == "__main__":
	main()