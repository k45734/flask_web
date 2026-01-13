#-*- coding: utf-8 -*-
import os, sys, sqlite3, logging, asyncio, base64, requests, json, time, re, zipfile, shutil, platform
from flask import Blueprint, render_template, request, session, redirect, url_for
from bs4 import BeautifulSoup as bs
from datetime import datetime

# 기존 프로젝트 로거 및 스케줄러 연결 (환경에 맞게 수정)
try:
    from pages.main_page import scheduler, logger
except:
    logger = logging.getLogger("WebtoonReceiver")

webtoon = Blueprint('webtoon', __name__, url_prefix='/webtoon')

# --- [1. 경로 및 환경 설정] ---
if platform.system() == 'Windows':
    at = os.path.splitdrive(os.getcwd())
    webtoondb = at[0] + '/data/db/webtoon_new.db'
    root = at[0] + '/data'
else:
    webtoondb = '/data/db/webtoon_new.db'
    root = '/data'

# --- [2. DB 최적화 및 유틸리티] ---
def db_optimization():
    try:
        con = sqlite3.connect(webtoondb, timeout=60)
        con.execute('VACUUM')
        con.commit()
    except: con.rollback()
    finally: con.close()
    return '완료'

def cleanText(readData):
    text = readData.replace('/', '')
    text = re.sub('[-\\/:*?\"<>|]', '', text).strip()
    return re.sub("\s{2,}", ' ', text)

# --- [3. 이미지 다운로드 및 압축 로직] ---
def url_to_image(title, subtitle, webtoon_image, webtoon_number, gbun):
    header = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        req = requests.get(webtoon_image, headers=header, timeout=30)
        req.raise_for_status()
        
        parse = cleanText(title)
        parse2 = cleanText(subtitle)
        
        dfolder = os.path.join(root, 'webtoon', gbun, parse, parse2)
        if not os.path.exists(dfolder):
            os.makedirs(dfolder, exist_ok=True)
            
        filename = f"{webtoon_number}.jpg"
        fifi = os.path.join(dfolder, filename)
        
        if not os.path.isfile(fifi):
            with open(fifi, 'wb') as code:
                code.write(req.content)
        return '완료'
    except Exception as e:
        logger.error(f"다운로드 실패: {title} {subtitle} - {e}")
        return '실패'

def manazip(title, subtitle, cbz, gbun):
    parse = cleanText(title)
    parse2 = cleanText(subtitle)
    dfolder = os.path.join(root, 'webtoon', gbun, parse)
    target_dir = os.path.join(dfolder, parse2)
    
    if os.path.isdir(target_dir):
        ext = '.cbz' if cbz == '0' else '.zip'
        zip_path = os.path.join(dfolder, f"{parse2}{ext}")
        with zipfile.ZipFile(zip_path, 'w') as f_zip:
            for folder, subfolders, files in os.walk(target_dir):
                for file in files:
                    if file.endswith('.jpg'):
                        f_zip.write(os.path.join(folder, file), file, compress_type=zipfile.ZIP_DEFLATED)
        time.sleep(1)
        shutil.rmtree(target_dir)
    return '완료'

# --- [4. DB 저장 및 완료 처리] ---
def add_c(title, subtitle, webtoon_site, webtoon_url, webtoon_image, webtoon_number, complete, gbun):
    # 크롤러가 보낸 gbun에 따라 테이블 결정
    db_table = 'TOON' if gbun == 'adult' else 'TOON_NORMAL'
    try:
        con = sqlite3.connect(webtoondb, timeout=60)
        con.execute(f"CREATE TABLE IF NOT EXISTS {db_table} (TITLE TEXT, SUBTITLE TEXT, WEBTOON_SITE TEXT, WEBTOON_URL TEXT, WEBTOON_IMAGE TEXT, WEBTOON_IMAGE_NUMBER TEXT, COMPLETE TEXT)")
        con.execute("PRAGMA journal_mode=WAL")
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        
        # 중복 및 수정 확인
        cur.execute(f'SELECT * FROM {db_table} WHERE WEBTOON_IMAGE = ? AND TITLE = ? AND SUBTITLE = ?', (webtoon_image, title, subtitle))
        row = cur.fetchone()
        
        if row:
            if row['WEBTOON_IMAGE'] != webtoon_image or row['COMPLETE'] == 'False':
                cur.execute(f'UPDATE {db_table} SET WEBTOON_IMAGE_NUMBER = ?, COMPLETE = ? WHERE WEBTOON_IMAGE = ?', (webtoon_number, complete, webtoon_image))
                con.commit()
        else:
            cur.execute(f'INSERT INTO {db_table} VALUES (?, ?, ?, ?, ?, ?, ?)', (title, subtitle, webtoon_site, webtoon_url, webtoon_image, webtoon_number, complete))
            con.commit()
    finally: con.close()
    return '완료'

def add_d(subtitle, title, webtoon_image, gbun):
    db_table = 'TOON' if gbun == 'adult' else 'TOON_NORMAL'
    try:
        con = sqlite3.connect(webtoondb, timeout=60)
        con.execute(f'UPDATE {db_table} SET COMPLETE = "True" WHERE SUBTITLE = ? AND TITLE = ? AND WEBTOON_IMAGE = ?', (subtitle, title, webtoon_image))
        con.commit()
    finally: con.close()
    return '완료'

# --- [5. 텔레그램 메시지 동기화 (핵심 복구)] ---
def tel_send_message(dummy_list):
    logger.info('웹툰 DB정보를 받아옵니다.')
    file_path = os.path.join(root, 'last_num.json')
    file_check = os.path.join(root, 'now_num.json')

    if os.path.isfile(file_path):
        with open(file_path, "r") as f: json_data = json.load(f)
    else:
        json_data = ["0"]

    with requests.Session() as s:
        url2 = 'https://t.me/s/webtoonalim'
        req = s.get(url2)
        soup = bs(req.text, "html.parser")
        aa1 = soup.findAll("div", {"class":"tgme_widget_message"})
        
        if not aa1: return '메시지 없음'
        
        last_post = aa1[-1]['data-post']
        real_now = int(last_post.split('/')[-1])
        
        # now_num.json 로직 복구
        if os.path.isfile(file_check):
            with open(file_check, 'r', encoding='utf-8') as f:
                data = json.load(f)
                now_list, old_list, new_list = data[0]['NOW'], data[0]['OLD'], data[0]['NEW']
        else:
            now_list, old_list, new_list = real_now, int(json_data[0]), real_now

        while True:
            if new_list <= old_list:
                # 상태 저장 후 종료
                wow = [{'NOW': real_now, 'OLD': now_list, 'NEW': real_now}]
                with open(file_check, 'w') as outfile: json.dump(wow, outfile)
                break
            
            # 페이지 데이터 요청
            PAGE_INFO = {'before': new_list}
            req = s.post(url2, data=PAGE_INFO)
            soup = bs(req.text, "html.parser")
            mm = soup.findAll("div", {"class":"tgme_widget_message_text"})
            
            for i in mm:
                try:
                    decoded = base64.b64decode(i.text).decode('utf-8')
                    aac = decoded.split('\n\n')
                    # 7필드 파싱
                    title, subtitle, site, url, img, num = aac[0], aac[1], aac[2], aac[3], aac[4], aac[5]
                    gbun = aac[6] if len(aac) >= 7 else 'adult'
                    
                    complete = "True" if ".com" in img else "False"
                    if 'loading.svg' not in img:
                        add_c(title, subtitle, site, url, img, num, complete, gbun)
                except: continue
            
            new_list -= 20 # 원본 로직 유지
            time.sleep(1)

    with open(file_path, 'w') as outfile: json.dump([str(real_now)], outfile)
    logger.info('웹툰 DB 동기화 종료.')
    return '완료'

# --- [6. 다운로드 메인 함수] ---
def down(compress, cbz, alldown, title, subtitle, gbun):
    db_table = 'TOON' if gbun == 'adult' else 'TOON_NORMAL'
    con = sqlite3.connect(webtoondb, timeout=60)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    
    if alldown == 'True':
        sql = f'SELECT TITLE, SUBTITLE, group_concat(WEBTOON_IMAGE,"|"), group_concat(WEBTOON_IMAGE_NUMBER), group_concat(COMPLETE) FROM {db_table} GROUP BY TITLE, SUBTITLE'
        cur.execute(sql)
    else:
        sql = f'SELECT TITLE, SUBTITLE, group_concat(WEBTOON_IMAGE,"|"), group_concat(WEBTOON_IMAGE_NUMBER), group_concat(COMPLETE) FROM {db_table} WHERE TITLE=? AND SUBTITLE=? GROUP BY SUBTITLE'
        cur.execute(sql, (title, subtitle))
    
    rows = cur.fetchall()
    for row in rows:
        img_urls = row[2].split('|')
        img_nums = row[3].split(',')
        comp_status = row[4].split(',')
        
        if 'False' in comp_status:
            for u, n in zip(img_urls, img_nums):
                if ".com" not in u and 'loading.svg' not in u:
                    if url_to_image(row['TITLE'], row['SUBTITLE'], u, n, gbun) == '완료':
                        add_d(row['SUBTITLE'], row['TITLE'], u, gbun)
            
            if compress == '0':
                manazip(row['TITLE'], row['SUBTITLE'], cbz, gbun)
    con.close()
    return '완료'

# --- [7. Flask Routes] ---
@webtoon.route('/')
def index():
    # DB 테이블 생성 로직 생략 (add_c에서 자동 생성됨)
    return render_template('webtoon.html')

@webtoon.route('webtoon_list', methods=['GET'])
def start_sync():
    start_time = request.args.get('start_time')
    # scheduler 관련 코드는 사용자님의 환경에 맞게 유지
    return redirect(url_for('webtoon.index'))

@webtoon.route("now", methods=["GET"])
def now_down():
    gbun = request.args.get('gbun')
    down(request.args.get('compress'), request.args.get('cbz'), 'True', None, None, gbun)
    return redirect(url_for('webtoon.index'))