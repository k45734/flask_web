from requests import get  
import zipfile
import os       
import shutil
from distutils.dir_util import copy_tree

def update(file_name = None):
	url = "https://github.com/k45734/flask_web/archive/refs/heads/main.zip"
	
	if not file_name:
		file_name = url.split('/')[-1]

	with open(file_name, "wb") as file:   
        	response = get(url)               
        	file.write(response.content)      
	fantasy_zip = zipfile.ZipFile('./main.zip')
	fantasy_zip.extractall('./')
	fantasy_zip.close()
	os.remove('./flask_web-main/login.db')
	org = './flask_web-main/app.py'
	org2 = './flask_web-main/pages'
	org3 = './flask_web-main/templates'
	new = './'
	new2 = './pages'
	new3 = './templates'
	shutil.copy(org, new)
	copy_tree(org2, new2)
	copy_tree(org3, new3)
	os.remove('./main.zip')
	shutil.rmtree ('./flask_web-main')
if __name__ == '__main__':
	update()