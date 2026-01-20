#-*- coding: utf-8 -*-
import os, sys, sqlite3, logging, asyncio, base64, requests, json, time, re, zipfile, shutil, platform
from flask import Blueprint, render_template, request, session, redirect, url_for
from bs4 import BeautifulSoup as bs
from datetime import datetime

# 스케줄러 및 페이징 라이브러리
from apscheduler.triggers.cron import CronTrigger
try:
    from flask_paginate import Pagination, get_page_args
except ImportError:
    os.system('pip install flask_paginate')
    from flask_paginate import Pagination, get_page_args

# 프로젝트 로거 및 스케줄러 연결
try:
    from pages.main_page import scheduler, logger
except:
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("WebtoonReceiver")

webtoon = Blueprint('webtoon', __name__, url_prefix='/webtoon')

# --- [1. 경로 및 DB 설정] ---
if platform.system() == 'Windows':
    at = os.path.splitdrive(os.getcwd())
    webtoondb = at[0] + '/data/db/webtoon_new.db'
    root = at[0] + '/data'
else:
    webtoondb = '/data/db/webtoon_new.db'
    root = '/data'

def get_db_con():
    con = sqlite3.connect(webtoondb, timeout=60)
    con.execute("PRAGMA journal_mode=WAL")
    con.row_factory = sqlite3.Row
    return con

def get_config(key):
    try:
        con = get_db_con()
        cur = con.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS CONFIG (KEY TEXT PRIMARY KEY, VALUE TEXT)")
        cur.execute("SELECT VALUE FROM CONFIG WHERE KEY = ?", (key,))
        row = cur.fetchone()
        return row[0] if row else "0"
    except: return "0"
    finally: con.close()

def set_config(key, value):
    try:
        con = get_db_con()
        con.execute("INSERT OR REPLACE INTO CONFIG VALUES (?, ?)", (key, value))
        con.commit()
    finally: con.close()

# --- [2. 비즈니스 로직: 동기화 및 다운로드] ---

def cleanText(readData):
    return re.sub('[-\\/:*?\"<>|]', '', readData.replace('/', '')).strip()

def tel_send_message(dummy_list):
    logger.info('[동기화] 텔레그램 채널에서 최신 리스트 확인 중...')
    last_saved_id = int(get_config('last_webtoon_id'))
    url = 'https://t.me/s/webtoonalim'
    with requests.Session() as s:
        try:
            req = s.get(url, timeout=15)
            soup = bs(req.text, "html.parser")
            messages = soup.findAll("div", {"class": "tgme_widget_message"})
            if not messages: 
                logger.info("[동기화] 새로운 메시지가 없습니다.")
                return
            
            new_count = 0
            for msg in reversed(messages):
                post_id = int(msg['data-post'].split('/')[-1])
                if post_id <= last_saved_id: break
                
                text_div = msg.find("div", {"class": "tgme_widget_message_text"})
                if not text_div: continue
                
                try:
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
                        new_count += 1
                except: continue
            logger.info(f'[동기화] 작업 완료. {new_count}개의 새로운 리스트 추가됨.')
        except Exception as e: logger.error(f"[동기화] 오류 발생: {e}")

def add_c(title, subtitle, site, url, img, num, complete, gbun):
    db_table = 'TOON' if gbun == 'adult' else 'TOON_NORMAL'
    con = get_db_con()
    con.execute(f"CREATE TABLE IF NOT EXISTS {db_table} (TITLE TEXT, SUBTITLE TEXT, WEBTOON_SITE TEXT, WEBTOON_URL TEXT, WEBTOON_IMAGE TEXT, WEBTOON_IMAGE_NUMBER TEXT, COMPLETE TEXT)")
    cur = con.cursor()
    cur.execute(f'SELECT * FROM {db_table} WHERE WEBTOON_IMAGE = ? AND TITLE = ? AND SUBTITLE = ?', (img, title, subtitle))
    if not cur.fetchone():
        cur.execute(f'INSERT INTO {db_table} VALUES (?, ?, ?, ?, ?, ?, ?)', (title, subtitle, site, url, img, num, complete))
        con.commit()
    con.close()

def down(compress, cbz, alldown, title, subtitle, gbun):
    logger.info(f'[다운로드-{gbun}] 작업을 시작합니다. (압축여부: {compress}, CBZ여부: {cbz})')
    db_table = 'TOON' if gbun == 'adult' else 'TOON_NORMAL'
    con = get_db_con()
    cur = con.cursor()
    
    if alldown == 'True':
        cur.execute(f'SELECT TITLE, SUBTITLE, group_concat(WEBTOON_IMAGE,"|"), group_concat(WEBTOON_IMAGE_NUMBER), group_concat(COMPLETE) FROM {db_table} GROUP BY TITLE, SUBTITLE')
    else:
        cur.execute(f'SELECT TITLE, SUBTITLE, group_concat(WEBTOON_IMAGE,"|"), group_concat(WEBTOON_IMAGE_NUMBER), group_concat(COMPLETE) FROM {db_table} WHERE TITLE=? AND SUBTITLE=? GROUP BY SUBTITLE', (title, subtitle))
    
    rows = cur.fetchall()
    total_rows = len(rows)
    logger.info(f'[다운로드-{gbun}] 대상 수량: {total_rows} 건')

    for idx, row in enumerate(rows):
        img_urls, img_nums, comp_status = row[2].split('|'), row[3].split(','), row[4].split(',')
        if 'False' in comp_status:
            logger.info(f'[{idx+1}/{total_rows}] {row["TITLE"]} - {row["SUBTITLE"]} 다운로드 시작')
            for u, n in zip(img_urls, img_nums):
                if ".com" not in u and 'loading.svg' not in u:
                    if url_to_image(row['TITLE'], row['SUBTITLE'], u, n, gbun) == '완료':
                        add_d(row['SUBTITLE'], row['TITLE'], u, gbun)
            
            if compress == '0':
                logger.info(f'[압축] {row["TITLE"]} 압축 중...')
                manazip(row['TITLE'], row['SUBTITLE'], cbz, gbun)
    
    con.close()
    logger.info(f'[다운로드-{gbun}] 모든 스케줄링 작업이 완료되었습니다.')

def url_to_image(title, subtitle, webtoon_image, webtoon_number, gbun):
    try:
        req = requests.get(webtoon_image, headers={"User-Agent":"Mozilla/5.0"}, timeout=30)
        p1, p2 = cleanText(title), cleanText(subtitle)
        folder = os.path.join(root, 'webtoon', gbun, p1, p2)
        os.makedirs(folder, exist_ok=True)
        path = os.path.join(folder, f"{webtoon_number}.jpg")
        with open(path, 'wb') as f: f.write(req.content)
        return '완료'
    except Exception as e:
        logger.error(f'[이미지 에러] {title} {webtoon_number}번: {e}')
        return '실패'

def add_d(subtitle, title, webtoon_image, gbun):
    db_table = 'TOON' if gbun == 'adult' else 'TOON_NORMAL'
    con = get_db_con()
    con.execute(f'UPDATE {db_table} SET COMPLETE = "True" WHERE SUBTITLE = ? AND TITLE = ? AND WEBTOON_IMAGE = ?', (subtitle, title, webtoon_image))
    con.commit()
    con.close()

def manazip(title, subtitle, cbz, gbun):
    p1, p2 = cleanText(title), cleanText(subtitle)
    folder = os.path.join(root, 'webtoon', gbun, p1)
    target = os.path.join(folder, p2)
    if os.path.isdir(target):
        ext = '.cbz' if cbz == '0' else '.zip'
        zip_path = os.path.join(folder, f"{p2}{ext}")
        with zipfile.ZipFile(zip_path, 'w') as f_zip:
            for _, _, files in os.walk(target):
                for file in files:
                    if file.endswith('.jpg'):
                        f_zip.write(os.path.join(target, file), file, compress_type=zipfile.ZIP_DEFLATED)
        shutil.rmtree(target)
    return '완료'

# --- [3. Flask Routes: 목록 및 통계] ---
@webtoon.route('/')
def index():
    """BuildError 해결을 위한 메인 라우트"""
    if not session.get('logFlag'): return redirect(url_for('main.index'))
    return render_template('webtoon.html')
	
@webtoon.route('index_list', methods=["GET"])
def index_list():
    if not session.get('logFlag'): return redirect(url_for('main.index'))
    
    gbun = request.args.get('gbun', 'adult')
    search_keyword = request.args.get('search', '').strip()
    db_name = 'TOON' if gbun == 'adult' else 'TOON_NORMAL'
    
    per_page = 10
    page, _, offset = get_page_args(per_page=per_page)
    
    con = get_db_con()
    cur = con.cursor()
    
    try:
        # [수정 포인트] 테이블이 없으면 에러가 나므로, 먼저 테이블을 생성해줍니다.
        cur.execute(f"""
            CREATE TABLE IF NOT EXISTS {db_name} (
                TITLE TEXT, 
                SUBTITLE TEXT, 
                WEBTOON_SITE TEXT, 
                WEBTOON_URL TEXT, 
                WEBTOON_IMAGE TEXT, 
                WEBTOON_IMAGE_NUMBER TEXT, 
                COMPLETE TEXT
            )
        """)
        con.commit()

        # 검색 조건 설정
        where_clause = ""
        params = []
        if search_keyword:
            where_clause = "WHERE TITLE LIKE ?"
            params.append(f"%{search_keyword}%")

        # 개수 조회
        count_sql = f"SELECT COUNT(*) FROM (SELECT DISTINCT TITLE, SUBTITLE FROM {db_name} {where_clause})"
        cur.execute(count_sql, params)
        total = cur.fetchone()[0]

        # 데이터 조회
        data_sql = f"""
            SELECT TITLE, SUBTITLE FROM {db_name} 
            {where_clause}
            GROUP BY TITLE, SUBTITLE 
            ORDER BY TITLE ASC, SUBTITLE DESC 
            LIMIT ? OFFSET ?
        """
        cur.execute(data_sql, params + [per_page, offset])
        wow = cur.fetchall()
        
    except Exception as e:
        logger.error(f"DB 조회 중 오류 발생: {e}")
        wow = []
        total = 0
    finally:
        con.close()
    
    pagination = Pagination(page=page, total=total, per_page=per_page, bs_version=4, search=bool(search_keyword),add_args={'gbun': gbun, 'search': search_keyword})
    return render_template('webtoon_list.html', gbun=gbun, wow=wow, pagination=pagination, search=search_keyword)

@webtoon.route('alim_list', methods=["GET"])
def alim_list():
    if not session.get('logFlag'): return redirect(url_for('main.index'))
    def stats(table):
        con = get_db_con()
        cur = con.cursor()
        cur.execute(f'SELECT count(*) FROM (SELECT TITLE FROM {table} GROUP BY TITLE)')
        t_cnt = cur.fetchone()[0]
        cur.execute(f'SELECT count(*) FROM {table} WHERE COMPLETE = "False"')
        f_cnt = cur.fetchone()[0]
        cur.execute(f'SELECT count(*) FROM {table} WHERE COMPLETE = "True"')
        tr_cnt = cur.fetchone()[0]
        con.close()
        return {'TOTAL': t_cnt, 'False': f_cnt, 'True': tr_cnt}
    return render_template('webtoon_alim_list.html', rows=[stats('TOON')], rows2=[stats('TOON_NORMAL')])

# --- [4. Flask Routes: 스케줄러 (로그 강화)] ---

@webtoon.route('webtoon_list', methods=['GET'])
def start_sync_route():
    if not session.get('logFlag'): return redirect(url_for('main.index'))
    start_time = request.args.get('start_time')
    try:
        scheduler.add_job(tel_send_message, trigger=CronTrigger.from_crontab(start_time), id='webtoon_list_sync', args=[None], replace_existing=True)
        logger.info(f"[스케줄러] 리스트 동기화가 {start_time} 주기로 예약되었습니다.")
    except Exception as e: logger.error(f"[스케줄러] 동기화 예약 실패: {e}")
    return redirect(url_for('webtoon.index'))

@webtoon.route('webtoon_down', methods=['GET'])
def start_down_route():
    if not session.get('logFlag'): return redirect(url_for('main.index'))
    start_time = request.args.get('start_time')
    gbun = request.args.get('gbun', 'adult')
    try:
        scheduler.add_job(down, trigger=CronTrigger.from_crontab(start_time), id=f'webtoon_auto_down_{gbun}', 
                          args=[request.args.get('compress','1'), request.args.get('cbz','1'), 'True', None, None, gbun], replace_existing=True)
        logger.info(f"[스케줄러] {gbun} 자동 다운로드가 {start_time} 주기로 예약되었습니다.")
    except Exception as e: logger.error(f"[스케줄러] 다운로드 예약 실패: {e}")
    return redirect(url_for('webtoon.index'))

@webtoon.route("now", methods=["GET"])
def now_down():
    if not session.get('logFlag'): return redirect(url_for('main.index'))
    logger.info("[수동실행] 사용자가 즉시 다운로드를 요청했습니다.")
    down(request.args.get('compress'), request.args.get('cbz'), 'True', None, None, request.args.get('gbun'))
    return redirect(url_for('webtoon.index'))

@webtoon.route('db_list_reset')
def db_list_reset():
    set_config('last_webtoon_id', '0')
    logger.info("[리셋] 동기화 추적 ID를 0으로 초기화했습니다.")
    return redirect(url_for('webtoon.index'))