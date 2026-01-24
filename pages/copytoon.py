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
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s - %(message)s')
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

# --- [2. DB 최적화 엔진] ---
def db_optimize():
    logger.info("========================================")
    logger.info("[최적화] 데이터 정비 및 인덱스 최적화 가동")
    logger.info("========================================")
    try:
        with get_list_db() as con:
            for table in ['TOON', 'TOON_NORMAL']:
                cur = con.cursor()
                cur.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
                if not cur.fetchone(): continue

                con.execute(f"DELETE FROM {table} WHERE rowid NOT IN (SELECT MIN(rowid) FROM {table} GROUP BY TITLE, SUBTITLE, WEBTOON_IMAGE_NUMBER)")
                con.execute(f"CREATE UNIQUE INDEX IF NOT EXISTS uidx_{table} ON {table} (TITLE, SUBTITLE, WEBTOON_IMAGE_NUMBER)")
                
                con.execute("DROP TABLE IF EXISTS temp_counts")
                con.execute(f"CREATE TEMPORARY TABLE temp_counts AS SELECT TITLE, SUBTITLE, COUNT(*) as cnt FROM {table} GROUP BY TITLE, SUBTITLE")
                con.execute(f"UPDATE {table} SET TOTAL_COUNT = (SELECT cnt FROM temp_counts WHERE temp_counts.TITLE = {table}.TITLE AND temp_counts.SUBTITLE = {table}.SUBTITLE) WHERE TOTAL_COUNT = 0 OR TOTAL_COUNT IS NULL")
                con.commit()
                logger.info(f" -> [{table}] 최적화 및 보정 완료")

        for db_path in [LIST_DB, STATUS_DB]:
            with sqlite3.connect(db_path) as con: con.execute("VACUUM")
        logger.info("[완료] 모든 최적화 작업 종료")
    except Exception as e: logger.error(f"!!! 최적화 오류: {e}")

def tel_send_message(dummy=None):
    logger.info("==================================================")
    logger.info("== [역주행 엔진] 과거 데이터 전수 조사 가동 ==")
    logger.info("==================================================")
    print("\n[알림] 과거 데이터 역주행 수집을 시작합니다.")

    # 시작점: 현재 DB의 마지막 ID부터 과거로 내려갑니다.
    current_search_id = int(get_config('last_webtoon_id') or 8567115)
    
    # 만약 완전히 처음부터 다시 긁고 싶다면 위 숫자를 아주 큰 값(최신글 번호)으로 설정하세요.
    # 예: current_search_id = 9999999
    
    is_continue = True
    total_new_count = 0
    page_count = 0

    while is_continue:
        page_count += 1
        # [핵심] before 파라미터를 사용하여 search_id '이전'의 글들을 호출
        url = f'https://t.me/s/webtoonalim?before={current_search_id}'
        
        logger.info(f"[역주행] {page_count}페이지 호출 중... (기준 ID: {current_search_id})")
        print(f"\n--- {page_count}번 페이지 추적 ({current_search_id}번 이전) ---")
        
        try:
            req = requests.get(url, timeout=15)
            soup = bs(req.text, "html.parser")
            # 텔레그램 메시지들을 가져옴 (기본적으로 과거->최신 순으로 나열됨)
            messages = soup.findAll("div", {"class": "tgme_widget_message"})
            
            if not messages:
                print("!! 해당 구간에 메시지가 없습니다. 역주행을 종료합니다.")
                break

            new_data_dict = {'TOON': {}, 'TOON_NORMAL': {}}
            processed_ids = []

            # 역주행 시에는 페이지 내의 메시지들을 최신순(뒤에서부터)으로 검사하는 것이 효율적
            for m in reversed(messages):
                try:
                    pid = int(m['data-post'].split('/')[-1])
                    
                    # 이미 분석을 시도했던 번호는 중복 방지를 위해 기록만 하고 통과
                    processed_ids.append(pid)
                    
                    txt = m.find("div", {"class": "tgme_widget_message_text"})
                    if not txt: continue
                    
                    # 데이터 해독
                    dec = base64.b64decode(txt.get_text(strip=True).encode('ascii')).decode('utf-8')
                    aac = dec.split('\n\n')

                    # [규격 검사] 총 장수(aac[7])가 없으면 신께서 명령하신 대로 종료
                    if len(aac) < 8 or not aac[7].strip().isdigit():
                        logger.warning(f"[종료점] ID:{pid} 에서 구형 규격 발견. 역주행을 멈춥니다.")
                        print(f"[*] ID:{pid}: 구형 포맷 발견 -> 여기서부터는 수집하지 않습니다.")
                        is_continue = False
                        break

                    # 규격 통과 시 DB 준비
                    gbun = aac[8] if len(aac) >= 9 else 'adult'
                    db_t = 'TOON' if gbun == 'adult' else 'TOON_NORMAL'
                    key = (aac[0], aac[1], int(aac[5]))
                    
                    new_data_dict[db_t][key] = (aac[0], aac[1], aac[2], aac[3], aac[4], int(aac[5]), int(aac[7]))
                    
                    print(f" -> [분석성공] ID:{pid} | {aac[0]} ({aac[5]}/{aac[7]}장)")
                except: continue

            # DB 저장 (페이지 단위)
            with get_list_db() as con:
                added_count = 0
                for db_t in ['TOON', 'TOON_NORMAL']:
                    data_list = list(new_data_dict[db_t].values())
                    if not data_list: continue
                    # INSERT OR IGNORE를 사용하면 이미 있는 데이터는 건너뛰고 없는 것만 채웁니다.
                    con.executemany(f"INSERT OR IGNORE INTO {db_t} VALUES (?,?,?,?,?,?,?)", data_list)
                    added_count += len(data_list)
                con.commit()
                if added_count > 0:
                    print(f"== 신규 데이터 {added_count}개 DB 추가 완료 ==")

            # [역주행의 핵심] 다음 루프의 기준점을 이번 페이지에서 발견한 '가장 과거 ID'로 설정
            if processed_ids:
                oldest_id = min(processed_ids)
                current_search_id = oldest_id 
                total_new_count += len(processed_ids)
                
                print(f">> 현재 {oldest_id}번까지 내려왔습니다. (계속 내려가는 중...)")
                
                if oldest_id <= 1:
                    print(">> 1번 메시지에 도달했습니다.")
                    is_continue = False
                
                time.sleep(0.5) # 텔레그램 서버를 위한 최소한의 예의
            else:
                is_continue = False
                
        except Exception as e:
            logger.error(f"!!! 역주행 중 치명적 에러: {e}")
            print(f"!!! 오류 발생으로 중단: {e}")
            break

    print("\n" + "="*50)
    logger.info(f"== [역주행 종료] 총 {total_new_count}개 검사 완료 (도착 ID: {current_search_id}) ==")
    print(f"[완료] 역주행 수집이 끝났습니다. 최종 위치: {current_search_id}")
    print("="*50 + "\n")

# --- [4. 다운로드 엔진] ---
def down(compress, cbz, alldown, title_filter, sub_filter, gbun):
    logger.info(f"== [{gbun}] 다운로드 엔진 가동 ==")
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
            # [수정] 다운로드 시작 로그 강화 (현재수/총수)
            logger.info(f" -> [다운로드 시작] {t_title} - {t_sub} ({cur_c}/{tar_c}장)")

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

# --- [5. 웹 라우트] ---
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

@webtoon.route('/alim_list')
def alim_list():
    try:
        with get_status_db() as con_s:
            con_s.row_factory = sqlite3.Row
            rows = con_s.execute("SELECT SUM(CASE WHEN COMPLETE = 'False' THEN 1 ELSE 0 END) as 'False', SUM(CASE WHEN COMPLETE = 'True' THEN 1 ELSE 0 END) as 'True', COUNT(*) as TOTAL FROM STATUS").fetchall()
            rows2 = rows # 실제 환경에 따라 성인/일반 쿼리 분리 가능
        # [수정] 올바른 파일명(webtoon_alim_list.html)으로 호출
        return render_template('webtoon_alim_list.html', rows=rows, rows2=rows2)
    except Exception as e:
        logger.error(f"Alim List Error: {e}")
        return render_template('webtoon_alim_list.html', rows=[], rows2=[])

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
    t_str = request.args.get('start_time', '*/5 * * * *')
    scheduler.add_job(tel_send_message, trigger=CronTrigger.from_crontab(t_str), id='webtoon_list_sync', args=[None], replace_existing=True)
    return redirect(url_for('webtoon.index'))

@webtoon.route('webtoon_down_start')
def start_down_route():
    t_str, gbun = request.args.get('start_time', '*/5 * * * *'), request.args.get('gbun', 'adult')
    scheduler.add_job(down, trigger=CronTrigger.from_crontab(t_str), id=f"auto_down_{gbun}", args=[request.args.get('compress','1'), request.args.get('cbz','1'), 'True', None, None, gbun], replace_existing=True, max_instances=3)
    return redirect(url_for('webtoon.index'))