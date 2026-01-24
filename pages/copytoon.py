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

# --- [1. 경로 및 DB 설정] ---
at = os.path.splitdrive(os.getcwd()) if platform.system() == 'Windows' else ('', '/data')
LIST_DB = at[0] + '/data/db/webtoon_list.db'     
STATUS_DB = at[0] + '/data/db/webtoon_status.db' 
WEBTOON_PATH = at[0] + '/data/webtoon' 

os.makedirs(WEBTOON_PATH, exist_ok=True)
os.makedirs(os.path.dirname(LIST_DB), exist_ok=True)

def get_list_db():
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

# --- [2. 핵심 엔진: DB 최적화 및 보정] ---
def db_optimize():
    logger.info("========================================")
    logger.info("[최적화] 초고속 임시 테이블 보정 및 인덱스 정비 가동")
    logger.info("========================================")
    
    try:
        with get_list_db() as con:
            for table in ['TOON', 'TOON_NORMAL']:
                cur = con.cursor()
                cur.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
                if not cur.fetchone(): continue

                # [추가] 중복 데이터 1차 청소 (인덱스 생성 전 필수 작업)
                logger.info(f" -> [{table}] 기존 중복 데이터 청소 중...")
                con.execute(f"""
                    DELETE FROM {table} 
                    WHERE rowid NOT IN (
                        SELECT MIN(rowid) FROM {table} 
                        GROUP BY TITLE, SUBTITLE, WEBTOON_IMAGE_NUMBER
                    )
                """)

                # [추가] 고유 인덱스 설정 (앞으로의 중복 원천 차단)
                con.execute(f"CREATE UNIQUE INDEX IF NOT EXISTS uidx_{table} ON {table} (TITLE, SUBTITLE, WEBTOON_IMAGE_NUMBER)")
                
                logger.info(f" -> [{table}] 대량 보정 분석 및 최적화 중...")
                con.execute("DROP TABLE IF EXISTS temp_counts")
                con.execute(f"""
                    CREATE TEMPORARY TABLE temp_counts AS 
                    SELECT TITLE, SUBTITLE, COUNT(*) as cnt 
                    FROM {table} 
                    GROUP BY TITLE, SUBTITLE
                """)
                
                cur = con.execute(f"""
                    UPDATE {table} 
                    SET TOTAL_COUNT = (
                        SELECT cnt FROM temp_counts 
                        WHERE temp_counts.TITLE = {table}.TITLE 
                        AND temp_counts.SUBTITLE = {table}.SUBTITLE
                    ) 
                    WHERE TOTAL_COUNT = 0 OR TOTAL_COUNT IS NULL
                """)
                con.commit()
                logger.info(f" -> [{table}] {cur.rowcount}건 보정 및 인덱스 정비 완료!")

        for db_path in [LIST_DB, STATUS_DB]:
            with sqlite3.connect(db_path) as con: 
                con.execute("VACUUM")
                logger.info(f" -> [VACUUM] {os.path.basename(db_path)} 최적화 완료")
        
        logger.info("========================================")
        logger.info("[완료] 모든 최적화 작업이 끝났습니다.")
        logger.info("========================================")
    except Exception as e: 
        logger.error(f"!!! [에러] 최적화 엔진 오류: {e}")
def tel_send_message(dummy=None):
    logger.info("========================================")
    logger.info("[수집] 중복 정화 및 긴급 복구 모드 가동")
    logger.info("========================================")
    
    last_id = int(get_config('last_webtoon_id') or 0)
    
    try:
        req = requests.get('https://t.me/s/webtoonalim', timeout=15)
        soup = bs(req.text, "html.parser")
        messages = soup.findAll("div", {"class": "tgme_widget_message"})
        
        new_data_dict = {'TOON': {}, 'TOON_NORMAL': {}}
        max_id = last_id

        # 1. 메모리 단계에서 최신 데이터만 남기기
        for m in reversed(messages):
            try:
                pid = int(m['data-post'].split('/')[-1])
                if pid <= last_id: break
                
                txt = m.find("div", {"class": "tgme_widget_message_text"})
                if not txt: continue
                
                dec = base64.b64decode(txt.get_text(strip=True).encode('ascii')).decode('utf-8')
                aac = dec.split('\n\n')
                if len(aac) < 8: continue

                gbun = aac[8] if len(aac) >= 9 else 'adult'
                db_t = 'TOON' if gbun == 'adult' else 'TOON_NORMAL'
                
                # 중복 판단 키: 제목, 소제목, 이미지번호
                key = (aac[0], aac[1], int(aac[5]))
                new_data_dict[db_t][key] = (aac[0], aac[1], aac[2], aac[3], aac[4], int(aac[5]), int(aac[7]))
                
                max_id = max(max_id, pid)
                logger.info(f" -> [분석] ID:{pid} | {aac[0]} ({aac[5]}번)")
            except: continue

        # 2. DB 저장 시도 (에러 발생 시 인덱스 자동 삭제 및 복구)
        with get_list_db() as con:
            for db_t in ['TOON', 'TOON_NORMAL']:
                data_list = list(new_data_dict[db_t].values())
                if not data_list: continue
                
                try:
                    # 유니크 인덱스 생성 시도
                    con.execute(f"CREATE TABLE IF NOT EXISTS {db_t} (TITLE TEXT, SUBTITLE TEXT, WEBTOON_SITE TEXT, WEBTOON_URL TEXT, WEBTOON_IMAGE TEXT, WEBTOON_IMAGE_NUMBER INTEGER, TOTAL_COUNT INTEGER)")
                    con.execute(f"CREATE UNIQUE INDEX IF NOT EXISTS uidx_{db_t} ON {db_t} (TITLE, SUBTITLE, WEBTOON_IMAGE_NUMBER)")
                    
                    # 데이터 저장 시도
                    con.executemany(f"INSERT OR REPLACE INTO {db_t} VALUES (?,?,?,?,?,?,?)", data_list)
                except sqlite3.IntegrityError:
                    # [최후의 수단] 에러 시 해당 테이블을 밀어버리고 새로 받기
                    logger.warning(f"!!! [{db_t}] 데이터 꼬임 발견. 테이블 초기화 후 재구축합니다.")
                    con.execute(f"DROP TABLE IF EXISTS {db_t}")
                    # 다시 생성 후 저장
                    con.execute(f"CREATE TABLE {db_t} (TITLE TEXT, SUBTITLE TEXT, WEBTOON_SITE TEXT, WEBTOON_URL TEXT, WEBTOON_IMAGE TEXT, WEBTOON_IMAGE_NUMBER INTEGER, TOTAL_COUNT INTEGER)")
                    con.execute(f"CREATE UNIQUE INDEX uidx_{db_t} ON {db_t} (TITLE, SUBTITLE, WEBTOON_IMAGE_NUMBER)")
                    con.executemany(f"INSERT INTO {db_t} VALUES (?,?,?,?,?,?,?)", data_list)
            con.commit()

        set_config('last_webtoon_id', max_id)
        logger.info(f"[종료] 수집 완료 (최신 ID: {max_id})")
        
    except Exception as e: 
        logger.error(f"!!! [비상] 엔진 에러: {e}")

# --- [4. 다운로드 및 라우트 로직 (기존 유지)] ---
def down(compress, cbz, alldown, title_filter, sub_filter, gbun):
    msg = f"== [{gbun}] 다운로드 엔진 가동 =="
    logger.info(msg)
    db_table = 'TOON' if gbun == 'adult' else 'TOON_NORMAL'
    
    try:
        with get_list_db() as con_l:
            con_l.execute(f"ATTACH DATABASE '{STATUS_DB}' AS s_db")
            query = f"SELECT a.TITLE, a.SUBTITLE, a.TOTAL_COUNT FROM {db_table} a LEFT JOIN s_db.STATUS s ON a.TITLE = s.TITLE AND a.SUBTITLE = s.SUBTITLE WHERE (s.COMPLETE IS NULL OR s.COMPLETE != 'True') AND a.TOTAL_COUNT > 0"
            if title_filter: query += f" AND a.TITLE = '{title_filter}'"
            query += " GROUP BY a.TITLE, a.SUBTITLE"
            targets = con_l.execute(query).fetchall()
            con_l.execute("DETACH DATABASE s_db")

        for t_title, t_sub, t_total in targets:
            with get_list_db() as con_l:
                cur_l = con_l.cursor()
                cur_l.execute(f"SELECT WEBTOON_IMAGE, WEBTOON_IMAGE_NUMBER FROM {db_table} WHERE TITLE=? AND SUBTITLE=? ORDER BY WEBTOON_IMAGE_NUMBER ASC", (t_title, t_sub))
                img_list = cur_l.fetchall()
            
            cur_c, tar_c = len(img_list), int(t_total or 0)
            if cur_c > 0 and cur_c >= tar_c:
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
                        with zipfile.ZipFile(z_name, 'w', zipfile.ZIP_DEFLATED) as z:
                            for file in os.listdir(f_path): z.write(os.path.join(f_path, file), file)
                        shutil.rmtree(f_path)
                    
                    with get_status_db() as con_s:
                        con_s.execute("INSERT OR REPLACE INTO STATUS (TITLE, SUBTITLE, COMPLETE) VALUES (?,?,?)", (t_title, t_sub, 'True'))
                        con_s.commit()
        logger.info(f"== [{gbun}] 다운로드 엔진 종료 ==")
    except Exception as e: logger.error(f"Down Error: {e}")

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
        cur.execute(f"SELECT TITLE, SUBTITLE, TOTAL_COUNT FROM {table} {where} GROUP BY TITLE, SUBTITLE ORDER BY TITLE ASC LIMIT 15 OFFSET {(page-1)*15}", param)
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