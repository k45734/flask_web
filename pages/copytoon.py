#-*- coding: utf-8 -*-
import os, sys, sqlite3, logging, asyncio, base64, requests, json, time, re, zipfile, shutil, platform, threading
from flask import Blueprint, render_template, request, session, redirect, url_for
from bs4 import BeautifulSoup as bs
from datetime import datetime
from apscheduler.triggers.cron import CronTrigger

try:
    from flask_paginate import Pagination, get_page_args
except ImportError:
    os.system('pip install flask_paginate')
    from flask_paginate import Pagination, get_page_args

try:
    from pages.main_page import scheduler, logger
except:
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("WebtoonReceiver")

webtoon = Blueprint('webtoon', __name__, url_prefix='/webtoon')

# --- [1. 멀티 DB 설정] ---
at = os.path.splitdrive(os.getcwd()) if platform.system() == 'Windows' else ('', '/data')
LIST_DB = at[0] + '/data/db/webtoon_list.db'     
STATUS_DB = at[0] + '/data/db/webtoon_status.db' 
ROOT_PATH = at[0] + '/data'

os.makedirs(os.path.dirname(LIST_DB), exist_ok=True)

def get_list_db():
    con = sqlite3.connect(LIST_DB, timeout=60)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    return con

def get_status_db():
    con = sqlite3.connect(STATUS_DB, timeout=60)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("CREATE TABLE IF NOT EXISTS STATUS (TITLE TEXT, SUBTITLE TEXT, COMPLETE TEXT, PRIMARY KEY(TITLE, SUBTITLE))")
    con.execute("CREATE TABLE IF NOT EXISTS CONFIG (KEY TEXT PRIMARY KEY, VALUE TEXT)")
    return con

def get_config(key):
    try:
        with get_status_db() as con:
            cur = con.cursor()
            cur.execute("SELECT VALUE FROM CONFIG WHERE KEY = ?", (key,))
            row = cur.fetchone()
            return row['VALUE'] if row else None
    except: return None

def set_config(key, value):
    with get_status_db() as con:
        con.execute("INSERT OR REPLACE INTO CONFIG (KEY, VALUE) VALUES (?, ?)", (key, str(value)))
        con.commit()

# --- [2. 수집 및 저장 로직] ---
def add_c(title, subtitle, site, url, img, num, complete, gbun, total_count):
    db_table = 'TOON' if gbun == 'adult' else 'TOON_NORMAL'
    with get_list_db() as con:
        cur = con.cursor()
        cur.execute(f'''CREATE TABLE IF NOT EXISTS {db_table} (TITLE TEXT, SUBTITLE TEXT, WEBTOON_SITE TEXT, WEBTOON_URL TEXT, WEBTOON_IMAGE TEXT, WEBTOON_IMAGE_NUMBER INTEGER, TOTAL_COUNT INTEGER)''')
        cur.execute(f"INSERT OR IGNORE INTO {db_table} VALUES (?,?,?,?,?,?,?)", (title, subtitle, site, url, img, int(num), int(total_count)))
        con.commit()

def tel_send_message(dummy_list):
    logger.info("[동기화] 텔레그램 채널 수집 시작...")
    last_saved_id = int(get_config('last_webtoon_id') or 0)
    url = 'https://t.me/s/webtoonalim'
    with requests.Session() as s:
        try:
            req = s.get(url, timeout=15)
            soup = bs(req.text, "html.parser")
            messages = soup.findAll("div", {"class": "tgme_widget_message"})
            new_count, current_max_id = 0, last_saved_id
            for msg_div in reversed(messages):
                try:
                    post_id = int(msg_div['data-post'].split('/')[-1])
                    if post_id <= last_saved_id: break
                    text_div = msg_div.find("div", {"class": "tgme_widget_message_text"})
                    if not text_div: continue
                    raw_text = text_div.get_text(strip=True)
                    decoded = base64.b64decode(raw_text.encode('ascii')).decode('utf-8')
                    aac = decoded.split('\n\n')
                    if len(aac) >= 8:
                        title, subtitle, site, u_addr, img, num, complete, total_count = aac[:8]
                        gbun = aac[8] if len(aac) >= 9 else 'adult'
                        if 'loading.svg' not in img:
                            add_c(title, subtitle, site, u_addr, img, num, complete, gbun, total_count)
                            new_count += 1
                            current_max_id = max(current_max_id, post_id)
                except: continue
            set_config('last_webtoon_id', current_max_id)
            logger.info(f"[동기화 완료] {new_count}개 추가됨.")
        except Exception as e: logger.error(f"수집 오류: {e}")

# --- [3. 다운로드 및 압축 로직] ---
def make_zip(folder_path, is_cbz):
    ext = ".cbz" if str(is_cbz) == '1' else ".zip"
    zip_name = folder_path + ext
    with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as z:
        for file in os.listdir(folder_path):
            z.write(os.path.join(folder_path, file), file)
    shutil.rmtree(folder_path)

def down(compress, cbz, alldown, title_filter, sub_filter, gbun):
    db_table = 'TOON' if gbun == 'adult' else 'TOON_NORMAL'
    with get_list_db() as con_l:
        cur_l = con_l.cursor()
        cur_l.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{db_table}'")
        if not cur_l.fetchone(): return
        cur_l.execute(f"SELECT TITLE, SUBTITLE, TOTAL_COUNT FROM {db_table} GROUP BY TITLE, SUBTITLE")
        targets = cur_l.fetchall()

    for t_title, t_sub, t_total in targets:
        if title_filter and t_title != title_filter: continue
        if sub_filter and t_sub != sub_filter: continue
        with get_status_db() as con_s:
            cur_s = con_s.cursor()
            cur_s.execute("SELECT COMPLETE FROM STATUS WHERE TITLE=? AND SUBTITLE=?", (t_title, t_sub))
            if (res := cur_s.fetchone()) and res['COMPLETE'] == 'True': continue

        with get_list_db() as con_l:
            cur_l = con_l.cursor()
            cur_l.execute(f"SELECT WEBTOON_IMAGE, WEBTOON_IMAGE_NUMBER FROM {db_table} WHERE TITLE=? AND SUBTITLE=? ORDER BY WEBTOON_IMAGE_NUMBER ASC", (t_title, t_sub))
            img_list = cur_l.fetchall()

        if len(img_list) >= int(t_total or 0) and int(t_total or 0) > 0:
            folder_path = os.path.join(ROOT_PATH, "download", t_title, t_sub)
            os.makedirs(folder_path, exist_ok=True)
            success_count = 0
            for img_url, img_num in img_list:
                file_path = os.path.join(folder_path, f"{img_num:03d}.jpg")
                if not os.path.exists(file_path):
                    try:
                        res = requests.get(img_url, timeout=20)
                        if res.status_code == 200:
                            with open(file_path, 'wb') as f: f.write(res.content)
                            success_count += 1
                    except: continue
            if success_count > 0:
                if str(compress) == '1': make_zip(folder_path, cbz)
                with get_status_db() as con_s:
                    con_s.execute("INSERT OR REPLACE INTO STATUS (TITLE, SUBTITLE, COMPLETE) VALUES (?,?,?)", (t_title, t_sub, 'True'))
                    con_s.commit()

def migrate_old_db():
    old_db_path = at[0] + '/data/db/webtoon_new.db' # 기존 DB 경로
    
    if not os.path.exists(old_db_path):
        logger.error(f"기존 DB 파일이 없습니다: {old_db_path}")
        return

    logger.info("== [데이터 이관 시작] 기존 데이터를 멀티 DB로 분산 이동합니다. ==")
    
    # 1. 기존 DB 연결
    old_con = sqlite3.connect(old_db_path)
    old_con.row_factory = sqlite3.Row
    old_cur = old_con.cursor()

    # 2. 목록 DB(List DB)로 웹툰 정보 복사 (TOON, TOON_NORMAL 테이블)
    with get_list_db() as list_con:
        for table in ['TOON', 'TOON_NORMAL']:
            # 테이블 존재 여부 확인
            old_cur.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
            if old_cur.fetchone():
                logger.info(f"[{table}] 테이블 데이터 복사 중...")
                rows = old_cur.execute(f"SELECT * FROM {table}").fetchall()
                
                # 새 DB에 테이블 생성 및 데이터 삽입
                list_con.execute(f"CREATE TABLE IF NOT EXISTS {table} (TITLE TEXT, SUBTITLE TEXT, WEBTOON_SITE TEXT, WEBTOON_URL TEXT, WEBTOON_IMAGE TEXT, WEBTOON_IMAGE_NUMBER INTEGER, TOTAL_COUNT INTEGER)")
                for row in rows:
                    list_con.execute(f"INSERT OR IGNORE INTO {table} VALUES (?,?,?,?,?,?,?)", 
                                     (row['TITLE'], row['SUBTITLE'], row['WEBTOON_SITE'], row['WEBTOON_URL'], row['WEBTOON_IMAGE'], row['WEBTOON_IMAGE_NUMBER'], row['TOTAL_COUNT']))
        list_con.commit()

    # 3. 상태 DB(Status DB)로 완료 기록 및 설정값 복사
    with get_status_db() as status_con:
        # COMPLETE 여부 이관 (기존 DB의 TOON에서 COMPLETE='True'인 조합만 추출)
        logger.info("[STATUS] 완료 상태 정보 이관 중...")
        for table in ['TOON', 'TOON_NORMAL']:
            old_cur.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
            if old_cur.fetchone():
                # COMPLETE 컬럼이 있는 경우만 추출 (기존 설계에 따라)
                completed_rows = old_cur.execute(f"SELECT DISTINCT TITLE, SUBTITLE FROM {table} WHERE COMPLETE='True'").fetchall()
                for row in completed_rows:
                    status_con.execute("INSERT OR IGNORE INTO STATUS (TITLE, SUBTITLE, COMPLETE) VALUES (?,?,?)", (row['TITLE'], row['SUBTITLE'], 'True'))
        
        # CONFIG 정보 (last_webtoon_id 등) 이관
        old_cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='CONFIG'")
        if old_cur.fetchone():
            configs = old_cur.execute("SELECT * FROM CONFIG").fetchall()
            for cfg in configs:
                status_con.execute("INSERT OR REPLACE INTO CONFIG (KEY, VALUE) VALUES (?,?)", (cfg['KEY'], cfg['VALUE']))
        
        status_con.commit()

    old_con.close()
    logger.info("== [이관 완료] 모든 데이터가 webtoon_list.db와 webtoon_status.db로 성공적으로 이동되었습니다. ==")
    # logger.info("안전을 위해 webtoon_new.db 파일은 직접 삭제하시거나 백업 폴더로 옮겨주세요.")

# --- 라우트로 만들어 실행하기 ---
@webtoon.route('db_migrate')
def run_migration():
    if not session.get('logFlag'): return redirect(url_for('main.index'))
    threading.Thread(target=migrate_old_db).start()
    return "<script>alert('데이터 이관이 백그라운드에서 시작되었습니다. 로그를 확인하세요.'); history.back();</script>"
	
# --- [4. Flask 라우트 (누락 기능 포함)] ---
@webtoon.route('/')
def index():
    if not session.get('logFlag'): return redirect(url_for('main.index'))
    return render_template('webtoon.html', gbun='adult')

@webtoon.route('db_list_reset')
def db_list_reset():
    def reset_task():
        with get_status_db() as con:
            con.execute("DELETE FROM STATUS")
            con.execute("INSERT OR REPLACE INTO CONFIG (KEY, VALUE) VALUES ('last_webtoon_id', '0')")
            con.commit()
    threading.Thread(target=reset_task).start()
    return "<script>alert('상태 및 ID가 초기화되었습니다.'); history.back();</script>"

@webtoon.route("now", methods=["GET"])
def now_down():
    if not session.get('logFlag'): return redirect(url_for('main.index'))
    threading.Thread(target=down, args=(request.args.get('compress','1'), request.args.get('cbz','1'), 'True', request.args.get('title'), request.args.get('subtitle'), request.args.get('gbun','adult'))).start()
    return "<script>alert('다운로드를 시작했습니다.'); history.back();</script>"

# [누락기능] 개별 재다운로드 - 상태 DB에서 해당 항목만 삭제 후 다시 다운로드
@webtoon.route('db_redown', methods=["GET"])
def db_redown():
    title, subtitle, gbun = request.args.get('title'), request.args.get('subtitle'), request.args.get('gbun', 'adult')
    with get_status_db() as con:
        con.execute("DELETE FROM STATUS WHERE TITLE=? AND SUBTITLE=?", (title, subtitle))
        con.commit()
    threading.Thread(target=down, args=('1', '1', 'True', title, subtitle, gbun)).start()
    return "<script>alert('재다운로드를 시작합니다.'); history.back();</script>"

@webtoon.route("now_sync", methods=["GET"])
def now_sync():
    if not session.get('logFlag'): return redirect(url_for('main.index'))
    threading.Thread(target=tel_send_message, args=[None]).start()
    return "<script>alert('즉시 수집을 시작했습니다.'); history.back();</script>"

# [누락기능] 스케줄러 등록 라우트들
@webtoon.route('webtoon_list_sync', methods=['GET'])
def start_sync_route():
    scheduler.add_job(tel_send_message, trigger=CronTrigger.from_crontab(request.args.get('start_time')), id='webtoon_list_sync', args=[None], replace_existing=True)
    return redirect(url_for('webtoon.index'))

@webtoon.route('webtoon_down_start', methods=['GET'])
def start_down_route():
    gbun = request.args.get('gbun')
    scheduler.add_job(down, trigger=CronTrigger.from_crontab(request.args.get('start_time')), id=f"auto_down_{gbun}", args=[request.args.get('compress','1'), request.args.get('cbz','1'), 'True', None, None, gbun], replace_existing=True)
    return redirect(url_for('webtoon.index'))

@webtoon.route('index_list')
def index_list():
    if not session.get('logFlag'): return redirect(url_for('main.index'))
    gbun, search, page = request.args.get('gbun', 'adult'), request.args.get('search', '').strip(), request.args.get('page', type=int, default=1)
    per_page = 15
    with get_list_db() as con:
        cur = con.cursor()
        table = 'TOON' if gbun == 'adult' else 'TOON_NORMAL'
        cur.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
        if not cur.fetchone(): return render_template('webtoon_list.html', wow=[], pagination=None, gbun=gbun)
        where, param = ("WHERE TITLE LIKE ?", [f"%{search}%"]) if search else ("", [])
        cur.execute(f"SELECT TITLE, SUBTITLE FROM {table} {where} GROUP BY TITLE, SUBTITLE ORDER BY TITLE ASC LIMIT ? OFFSET ?", param + [per_page, (page-1)*per_page])
        wow = cur.fetchall()
        cur.execute(f"SELECT COUNT(*) FROM (SELECT 1 FROM {table} {where} GROUP BY TITLE, SUBTITLE)", param)
        total = cur.fetchone()[0]
    pagination = Pagination(page=page, total=total, per_page=per_page, bs_version=4, add_args={'gbun': gbun, 'search': search})
    return render_template('webtoon_list.html', wow=wow, pagination=pagination, gbun=gbun, search=search)