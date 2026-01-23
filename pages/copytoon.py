#-*- coding: utf-8 -*-
import os, sys, sqlite3, logging, asyncio, base64, requests, json, time, re, zipfile, shutil, platform, threading
from flask import Blueprint, render_template, request, session, redirect, url_for
from bs4 import BeautifulSoup as bs
from datetime import datetime
from apscheduler.triggers.cron import CronTrigger

# [필수 라이브러리 및 스케줄러]
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

# --- [1. 경로 및 DB 설정: Timeout 강화] ---
at = os.path.splitdrive(os.getcwd()) if platform.system() == 'Windows' else ('', '/data')
LIST_DB = at[0] + '/data/db/webtoon_list.db'     
STATUS_DB = at[0] + '/data/db/webtoon_status.db' 
WEBTOON_PATH = at[0] + '/data/webtoon' 

os.makedirs(WEBTOON_PATH, exist_ok=True)
os.makedirs(os.path.dirname(LIST_DB), exist_ok=True)

def get_list_db():
    # Timeout 300초 유지 + WAL 모드 최적화
    con = sqlite3.connect(LIST_DB, timeout=300)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA synchronous=NORMAL")
    return con

def get_status_db():
    con = sqlite3.connect(STATUS_DB, timeout=300)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("CREATE TABLE IF NOT EXISTS STATUS (TITLE TEXT, SUBTITLE TEXT, COMPLETE TEXT, PRIMARY KEY(TITLE, SUBTITLE))")
    con.execute("CREATE TABLE IF NOT EXISTS CONFIG (KEY TEXT PRIMARY KEY, VALUE TEXT)")
    return con

def get_config(key):
    try:
        with get_status_db() as con:
            cur = con.cursor(); cur.execute("SELECT VALUE FROM CONFIG WHERE KEY = ?", (key,))
            row = cur.fetchone(); return row['VALUE'] if row else None
    except: return None

def set_config(key, value):
    with get_status_db() as con:
        con.execute("INSERT OR REPLACE INTO CONFIG (KEY, VALUE) VALUES (?, ?)", (key, str(value)))
        con.commit()

# --- [2. 핵심 엔진: 임시 테이블 보정 및 고속 다운로드] ---

def db_optimize():
    print("== [최적화] DB 진공 청소 시작 =="); logger.info("DB Vacuum Start")
    try:
        for db_path in [LIST_DB, STATUS_DB]:
            with sqlite3.connect(db_path) as con: con.execute("VACUUM")
        print("== [완료] DB 최적화 종료 ==")
    except Exception as e: logger.error(f"Optimize Error: {e}")

def down(compress, cbz, alldown, title_filter, sub_filter, gbun):
    msg = f"== [{gbun}] 엔진 가동 (Lock-Free 보정 모드) =="
    print(msg); logger.info(msg)
    db_table = 'TOON' if gbun == 'adult' else 'TOON_NORMAL'
    
    try:
        # [STEP 1] 임시 테이블을 이용한 고속 보정 (Locked 방지 핵심)
        with get_list_db() as con_p:
            print(" -> [보정] 임시 인덱스 생성 및 계산 중..."); logger.info("Fixing counts...")
            # 1. 메모리에 현재 카운트를 미리 계산
            con_p.execute(f"CREATE TEMPORARY TABLE temp_counts AS SELECT TITLE, SUBTITLE, COUNT(*) as cnt FROM {db_table} WHERE TOTAL_COUNT = 0 OR TOTAL_COUNT IS NULL GROUP BY TITLE, SUBTITLE")
            # 2. 본 테이블에 한 번에 업데이트 (이 쿼리는 매우 빠릅니다)
            cur_p = con_p.execute(f"""
                UPDATE {db_table} SET TOTAL_COUNT = (
                    SELECT cnt FROM temp_counts WHERE temp_counts.TITLE = {db_table}.TITLE AND temp_counts.SUBTITLE = {db_table}.SUBTITLE
                ) WHERE EXISTS (SELECT 1 FROM temp_counts WHERE temp_counts.TITLE = {db_table}.TITLE AND temp_counts.SUBTITLE = {db_table}.SUBTITLE)
            """)
            con_p.commit()
            if cur_p.rowcount > 0:
                print(f" -> [보정 완료] {cur_p.rowcount}건 동기화 성공"); logger.info(f"Fixed {cur_p.rowcount} entries")

        # [STEP 2] 미완료 대상 추출 (JOIN 최적화)
        with get_list_db() as con_l:
            con_l.execute(f"ATTACH DATABASE '{STATUS_DB}' AS s_db")
            query = f"SELECT a.TITLE, a.SUBTITLE, a.TOTAL_COUNT FROM {db_table} a LEFT JOIN s_db.STATUS s ON a.TITLE = s.TITLE AND a.SUBTITLE = s.SUBTITLE WHERE (s.COMPLETE IS NULL OR s.COMPLETE != 'True')"
            if title_filter: query += f" AND a.TITLE = '{title_filter}'"
            query += " GROUP BY a.TITLE, a.SUBTITLE"
            targets = con_l.execute(query).fetchall()
            con_l.execute("DETACH DATABASE s_db")

        print(f" -> [검사] 미완료 {len(targets)}건 발견"); logger.info(f"Targets: {len(targets)}")

        # [STEP 3] 다운로드 루프
        for t_title, t_sub, t_total in targets:
            with get_list_db() as con_l:
                cur_l = con_l.cursor()
                cur_l.execute(f"SELECT WEBTOON_IMAGE, WEBTOON_IMAGE_NUMBER FROM {db_table} WHERE TITLE=? AND SUBTITLE=? ORDER BY WEBTOON_IMAGE_NUMBER ASC", (t_title, t_sub))
                img_list = cur_l.fetchall()
            
            cur_c, tar_c = len(img_list), int(t_total or 0)
            print(f" -> [체크] {t_title} - {t_sub} ({cur_c}/{tar_c})"); logger.info(f"Check: {t_title} ({cur_c}/{tar_c})")
            
            if cur_c > 0 and cur_c >= tar_c:
                print(f"    [실행] {t_title} 다운로드 시작"); logger.info(f"Down Start: {t_title}")
                f_path = os.path.join(WEBTOON_PATH, t_title, t_sub)
                os.makedirs(f_path, exist_ok=True)
                
                sc = 0
                for img_url, img_num in img_list:
                    img_file = os.path.join(f_path, f"{img_num:03d}.jpg")
                    if not os.path.exists(img_file):
                        try:
                            r = requests.get(img_url, timeout=20)
                            if r.status_code == 200:
                                with open(img_file, 'wb') as f: f.write(r.content)
                                sc += 1
                        except: continue
                
                if sc > 0 or os.path.exists(f_path):
                    if str(compress) == '1':
                        ext = ".cbz" if str(cbz) == '1' else ".zip"
                        z_name = f_path + ext
                        print(f"    [압축] 생성: {z_name}")
                        with zipfile.ZipFile(z_name, 'w', zipfile.ZIP_DEFLATED) as z:
                            for file in os.listdir(f_path): z.write(os.path.join(f_path, file), file)
                        shutil.rmtree(f_path)
                    
                    with get_status_db() as con_s:
                        con_s.execute("INSERT OR REPLACE INTO STATUS (TITLE, SUBTITLE, COMPLETE) VALUES (?,?,?)", (t_title, t_sub, 'True'))
                        con_s.commit()
                    print(f"    [완료] {t_title} - {t_sub} 처리 성공")
        
        print(f"== [{gbun}] 엔진 작업 종료 =="); logger.info(f"Engine Finish: {gbun}")
    except Exception as e: logger.error(f"Critical Engine Error: {e}")

# --- [3. 수집 및 라우트] ---

def tel_send_message(dummy=None):
    print("[수집] 데이터 동기화 개시"); logger.info("Sync Start")
    last_id = int(get_config('last_webtoon_id') or 0)
    try:
        req = requests.get('https://t.me/s/webtoonalim', timeout=15)
        soup = bs(req.text, "html.parser")
        messages = soup.findAll("div", {"class": "tgme_widget_message"})
        new_c, max_id = 0, last_id
        for m in reversed(messages):
            pid = int(m['data-post'].split('/')[-1])
            if pid <= last_id: break
            txt = m.find("div", {"class": "tgme_widget_message_text"})
            if not txt: continue
            try:
                dec = base64.b64decode(txt.get_text(strip=True).encode('ascii')).decode('utf-8')
                aac = dec.split('\n\n')
                if len(aac) >= 8:
                    gbun = aac[8] if len(aac)>=9 else 'adult'
                    db_t = 'TOON' if gbun == 'adult' else 'TOON_NORMAL'
                    with get_list_db() as con:
                        con.execute(f"CREATE TABLE IF NOT EXISTS {db_t} (TITLE TEXT, SUBTITLE TEXT, WEBTOON_SITE TEXT, WEBTOON_URL TEXT, WEBTOON_IMAGE TEXT, WEBTOON_IMAGE_NUMBER INTEGER, TOTAL_COUNT INTEGER)")
                        con.execute(f"INSERT OR IGNORE INTO {db_t} VALUES (?,?,?,?,?,?,?)", (aac[0], aac[1], aac[2], aac[3], aac[4], int(aac[5]), int(aac[7])))
                    new_c += 1; max_id = max(max_id, pid)
                    print(f" -> [수집] {aac[0]} 추가")
            except: continue
        set_config('last_webtoon_id', max_id)
        print(f"[완료] {new_c}건 수집 (ID: {max_id})"); logger.info(f"Sync Done: {new_c}")
    except Exception as e: logger.error(f"Sync Error: {e}")

@webtoon.route('/')
def index():
    if not session.get('logFlag'): return redirect(url_for('main.index'))
    return render_template('webtoon.html', gbun='adult')

@webtoon.route('index_list')
def index_list():
    gbun, search, page = request.args.get('gbun', 'adult'), request.args.get('search', '').strip(), request.args.get('page', type=int, default=1)
    table = 'TOON' if gbun == 'adult' else 'TOON_NORMAL'
    with get_list_db() as con:
        cur = con.cursor()
        cur.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
        if not cur.fetchone(): return render_template('webtoon_list.html', wow=[], pagination=None, gbun=gbun)
        where, param = ("WHERE TITLE LIKE ?", [f"%{search}%"]) if search else ("", [])
        cur.execute(f"SELECT TITLE, SUBTITLE FROM {table} {where} GROUP BY TITLE, SUBTITLE ORDER BY TITLE ASC LIMIT 15 OFFSET {(page-1)*15}", param)
        wow = cur.fetchall()
        cur.execute(f"SELECT COUNT(*) FROM (SELECT 1 FROM {table} {where} GROUP BY TITLE, SUBTITLE)", param)
        total = cur.fetchone()[0]
    pagination = Pagination(page=page, total=total, per_page=15, bs_version=4, add_args={'gbun': gbun, 'search': search})
    return render_template('webtoon_list.html', wow=wow, pagination=pagination, gbun=gbun, search=search)

@webtoon.route('db_list_reset')
def db_list_reset():
    with get_status_db() as con:
        con.execute("DELETE FROM STATUS"); con.execute("UPDATE CONFIG SET VALUE='0' WHERE KEY='last_webtoon_id'"); con.commit()
    return "<script>alert('리셋 완료'); history.back();</script>"

@webtoon.route('db_vacuum')
def run_vacuum():
    threading.Thread(target=db_optimize).start()
    return "<script>alert('최적화 시작'); history.back();</script>"

@webtoon.route("now")
def now_down():
    threading.Thread(target=down, args=(request.args.get('compress','1'), request.args.get('cbz','1'), 'True', request.args.get('title'), request.args.get('subtitle'), request.args.get('gbun','adult'))).start()
    return "<script>alert('다운로드 시작'); history.back();</script>"

@webtoon.route('webtoon_list_sync')
def start_sync_route():
    t_str = request.args.get('start_time')
    scheduler.add_job(tel_send_message, trigger=CronTrigger.from_crontab(t_str), id='webtoon_list_sync', args=[None], replace_existing=True)
    return redirect(url_for('webtoon.index'))

@webtoon.route('webtoon_down_start')
def start_down_route():
    t_str, gbun = request.args.get('start_time'), request.args.get('gbun')
    scheduler.add_job(down, trigger=CronTrigger.from_crontab(t_str), id=f"auto_down_{gbun}", args=[request.args.get('compress','1'), request.args.get('cbz','1'), 'True', None, None, gbun], replace_existing=True, max_instances=3)
    return redirect(url_for('webtoon.index'))