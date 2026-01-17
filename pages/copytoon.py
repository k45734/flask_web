#-*- coding: utf-8 -*-
import os, sys, sqlite3, logging, asyncio, base64, requests, json, time, re, zipfile, shutil, platform
from flask import Blueprint, render_template, request, session, redirect, url_for
from bs4 import BeautifulSoup as bs
from datetime import datetime

# 스케줄러 관련 필수 임포트
from apscheduler.triggers.cron import CronTrigger

# 프로젝트 로거 및 스케줄러 연결
try:
    from pages.main_page import scheduler, logger
except:
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("WebtoonReceiver")

webtoon = Blueprint('webtoon', __name__, url_prefix='/webtoon')

# --- [1. 경로 및 설정 관리 (SQLite CONFIG 테이블 활용)] ---
if platform.system() == 'Windows':
    at = os.path.splitdrive(os.getcwd())
    webtoondb = at[0] + '/data/db/webtoon_new.db'
    root = at[0] + '/data'
else:
    webtoondb = '/data/db/webtoon_new.db'
    root = '/data'

def get_config(key):
    try:
        con = sqlite3.connect(webtoondb, timeout=60)
        cur = con.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS CONFIG (KEY TEXT PRIMARY KEY, VALUE TEXT)")
        cur.execute("SELECT VALUE FROM CONFIG WHERE KEY = ?", (key,))
        row = cur.fetchone()
        return row[0] if row else "0"
    except: return "0"
    finally: con.close()

def set_config(key, value):
    try:
        con = sqlite3.connect(webtoondb, timeout=60)
        con.execute("INSERT OR REPLACE INTO CONFIG VALUES (?, ?)", (key, value))
        con.commit()
    finally: con.close()

# --- [2. DB 저장 및 유틸리티] ---
def cleanText(readData):
    text = readData.replace('/', '')
    text = re.sub('[-\\/:*?\"<>|]', '', text).strip()
    return re.sub("\s{2,}", ' ', text)

def add_c(title, subtitle, webtoon_site, webtoon_url, webtoon_image, webtoon_number, complete, gbun):
    db_table = 'TOON' if gbun == 'adult' else 'TOON_NORMAL'
    try:
        con = sqlite3.connect(webtoondb, timeout=60)
        con.execute(f"CREATE TABLE IF NOT EXISTS {db_table} (TITLE TEXT, SUBTITLE TEXT, WEBTOON_SITE TEXT, WEBTOON_URL TEXT, WEBTOON_IMAGE TEXT, WEBTOON_IMAGE_NUMBER TEXT, COMPLETE TEXT)")
        con.execute("PRAGMA journal_mode=WAL")
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        cur.execute(f'SELECT * FROM {db_table} WHERE WEBTOON_IMAGE = ? AND TITLE = ? AND SUBTITLE = ?', (webtoon_image, title, subtitle))
        if not cur.fetchone():
            cur.execute(f'INSERT INTO {db_table} VALUES (?, ?, ?, ?, ?, ?, ?)', (title, subtitle, webtoon_site, webtoon_url, webtoon_image, webtoon_number, complete))
            con.commit()
    finally: con.close()

def add_d(subtitle, title, webtoon_image, gbun):
    db_table = 'TOON' if gbun == 'adult' else 'TOON_NORMAL'
    try:
        con = sqlite3.connect(webtoondb, timeout=60)
        con.execute(f'UPDATE {db_table} SET COMPLETE = "True" WHERE SUBTITLE = ? AND TITLE = ? AND WEBTOON_IMAGE = ?', (subtitle, title, webtoon_image))
        con.commit()
    finally: con.close()

# --- [3. 텔레그램 리스트 동기화 (설정값 자동 기록)] ---
def tel_send_message(dummy_list):
    logger.info('웹툰 리스트 동기화를 시작합니다.')
    last_saved_id = int(get_config('last_webtoon_id'))
    url = 'https://t.me/s/webtoonalim'
    with requests.Session() as s:
        try:
            req = s.get(url, timeout=15)
            soup = bs(req.text, "html.parser")
            messages = soup.findAll("div", {"class": "tgme_widget_message"})
            if not messages: return
            
            for msg in reversed(messages):
                post_id = int(msg['data-post'].split('/')[-1])
                if post_id <= last_saved_id: break
                
                text_div = msg.find("div", {"class": "tgme_widget_message_text"})
                if not text_div: continue
                
                raw_text = text_div.text
                try: decoded = base64.b64decode(raw_text).decode('utf-8')
                except: decoded = raw_text
                
                aac = decoded.split('\n\n')
                if len(aac) < 6: continue
                
                title, subtitle, site, u_addr, img, num = aac[0], aac[1], aac[2], aac[3], aac[4], aac[5]
                gbun = aac[6] if len(aac) >= 7 else 'adult'
                complete = "True" if (".com" in img or "https" in img) else "False"
                
                if 'loading.svg' not in img:
                    add_c(title, subtitle, site, u_addr, img, num, complete, gbun)
                    set_config('last_webtoon_id', str(post_id))
        except Exception as e: logger.error(f"동기화 에러: {e}")
    logger.info('웹툰 리스트 동기화 완료.')

# --- [4. 다운로드 및 압축 로직] ---
def url_to_image(title, subtitle, webtoon_image, webtoon_number, gbun):
    header = {"User-Agent":"Mozilla/5.0"}
    try:
        req = requests.get(webtoon_image, headers=header, timeout=30)
        parse, parse2 = cleanText(title), cleanText(subtitle)
        dfolder = os.path.join(root, 'webtoon', gbun, parse, parse2)
        os.makedirs(dfolder, exist_ok=True)
        fifi = os.path.join(dfolder, f"{webtoon_number}.jpg")
        if not os.path.isfile(fifi):
            with open(fifi, 'wb') as code: code.write(req.content)
        return '완료'
    except: return '실패'

def manazip(title, subtitle, cbz, gbun):
    parse, parse2 = cleanText(title), cleanText(subtitle)
    dfolder = os.path.join(root, 'webtoon', gbun, parse)
    target_dir = os.path.join(dfolder, parse2)
    if os.path.isdir(target_dir):
        ext = '.cbz' if cbz == '0' else '.zip'
        zip_path = os.path.join(dfolder, f"{parse2}{ext}")
        with zipfile.ZipFile(zip_path, 'w') as f_zip:
            for folder, subs, files in os.walk(target_dir):
                for file in files:
                    if file.endswith('.jpg'):
                        f_zip.write(os.path.join(folder, file), file, compress_type=zipfile.ZIP_DEFLATED)
        shutil.rmtree(target_dir)
    return '완료'

def down(compress, cbz, alldown, title, subtitle, gbun):
    logger.info(f'[{gbun}] 다운로드 작업을 시작합니다.')
    db_table = 'TOON' if gbun == 'adult' else 'TOON_NORMAL'
    try:
        con = sqlite3.connect(webtoondb)
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        
        if alldown == 'True':
            cur.execute(f'SELECT TITLE, SUBTITLE, group_concat(WEBTOON_IMAGE,"|"), group_concat(WEBTOON_IMAGE_NUMBER), group_concat(COMPLETE) FROM {db_table} GROUP BY TITLE, SUBTITLE')
        else:
            cur.execute(f'SELECT TITLE, SUBTITLE, group_concat(WEBTOON_IMAGE,"|"), group_concat(WEBTOON_IMAGE_NUMBER), group_concat(COMPLETE) FROM {db_table} WHERE TITLE=? AND SUBTITLE=? GROUP BY SUBTITLE', (title, subtitle))
        
        rows = cur.fetchall()
        for row in rows:
            img_urls, img_nums, comp_status = row[2].split('|'), row[3].split(','), row[4].split(',')
            if 'False' in comp_status:
                for u, n in zip(img_urls, img_nums):
                    if ".com" not in u and 'loading.svg' not in u:
                        if url_to_image(row['TITLE'], row['SUBTITLE'], u, n, gbun) == '완료':
                            add_d(row['SUBTITLE'], row['TITLE'], u, gbun)
                if compress == '0':
                    manazip(row['TITLE'], row['SUBTITLE'], cbz, gbun)
    except Exception as e: logger.error(f"다운로드 중 오류: {e}")
    finally: con.close()
    logger.info(f'[{gbun}] 다운로드 작업 완료.')

# --- [5. Flask Routes (스케줄러 2종)] ---

@webtoon.route('/')
def index():
    if not session.get('logFlag'): return redirect(url_for('main.index'))
    return render_template('webtoon.html')

# (1) 리스트 동기화 예약
@webtoon.route('webtoon_list', methods=['GET'])
def start_sync_route():
    if not session.get('logFlag'): return redirect(url_for('main.index'))
    start_time = request.args.get('start_time')
    job_id = 'webtoon_list_sync'
    try:
        scheduler.add_job(tel_send_message, trigger=CronTrigger.from_crontab(start_time), id=job_id, args=[None], replace_existing=True)
        logger.info(f"리스트 동기화 스케줄 등록: {start_time}")
    except Exception as e: logger.error(f"리스트 예약 에러: {e}")
    return redirect(url_for('webtoon.index'))

# (2) 자동 다운로드 예약 (성인/일반 구분)
@webtoon.route('webtoon_down', methods=['GET'])
def start_down_route():
    if not session.get('logFlag'): return redirect(url_for('main.index'))
    start_time = request.args.get('start_time')
    gbun = request.args.get('gbun', 'adult')
    compress = request.args.get('compress', '1')
    cbz = request.args.get('cbz', '1')
    
    # 구분별로 별도 스케줄 ID 부여 (중복 방지)
    job_id = f'webtoon_auto_down_{gbun}'
    
    try:
        scheduler.add_job(
            down, 
            trigger=CronTrigger.from_crontab(start_time), 
            id=job_id, 
            args=[compress, cbz, 'True', None, None, gbun],
            replace_existing=True
        )
        logger.info(f"자동 다운로드 스케줄 등록 ({gbun}): {start_time}")
    except Exception as e: logger.error(f"다운로드 예약 에러: {e}")
    return redirect(url_for('webtoon.index'))

@webtoon.route("now", methods=["GET"])
def now_down():
    if not session.get('logFlag'): return redirect(url_for('main.index'))
    down(request.args.get('compress'), request.args.get('cbz'), 'True', None, None, request.args.get('gbun'))
    return redirect(url_for('webtoon.index'))

@webtoon.route('db_list_reset', methods=['GET'])
def db_list_reset():
    if not session.get('logFlag'): return redirect(url_for('main.index'))
    set_config('last_webtoon_id', '0')
    logger.info("리스트 동기화 위치가 초기화되었습니다.")
    return redirect(url_for('webtoon.index'))