#-*- coding: utf-8 -*-
import sys
try:
	reload(sys)
	sys.setdefaultencoding('utf-8')
except:
	pass
from flask import Flask, flash, redirect, render_template, request, session, abort, url_for
import platform
import os.path, os
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
	createFolder(logdata)
	app = Flask(__name__)	
	app.secret_key = os.urandom(12)
	from pages import main_page
	from pages import sub2_page
	from pages import sub3_page
	from pages import sub4_page
	from pages import copytoon
	app.register_blueprint(main_page.bp)
	app.register_blueprint(sub2_page.bp2)
	app.register_blueprint(sub3_page.bp3)
	app.register_blueprint(sub4_page.bp4)
	app.register_blueprint(copytoon.webtoon)
	app.run(host="0.0.0.0", debug=False, threaded=True, use_reloader=False)
	return app
	
if __name__ == '__main__':
	create_app()