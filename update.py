from requests import get  
import zipfile
import os       
import shutil

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
	org = './flask_web-main'
	copy = './data'
	shutil.move(org, copy)
	os.remove('./main.zip')
if __name__ == '__main__':
	update()
	#download(url)