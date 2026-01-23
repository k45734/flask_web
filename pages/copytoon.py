#-*- coding: utf-8 -*-
import os, sys, sqlite3, logging, asyncio, base64, requests, json, time, re, zipfile, shutil, platform, threading
from flask import Blueprint, render_template, request, session, redirect, url_for
from bs4 import BeautifulSoup as bs
from datetime import datetime
from apscheduler.triggers.cron import CronTrigger

# [환경설정] 페이징 라이브러리 자동 설치 및 임포트
try:
    from flask_paginate import Pagination, get_page_args
except ImportError:
    os.system('pip install flask_paginate')
    from flask_paginate import Pagination, get_page_args

# [환경설정] 메인 페이지 스케줄러 및 로거 연결
try:
    from pages.main_page import scheduler, logger
except:
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("WebtoonReceiver")

webtoon = Blueprint('webtoon', __name__, url_prefix='/webtoon')

# --- [1. 멀티 DB 경로 및 유틸리티] ---
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
    except Exception as e:
        print(f"[오류] 설정 읽기 실패: {e}"); return None

def set_config(key, value):
    try:
        with get_status_db() as con:
            con.execute("INSERT OR REPLACE INTO CONFIG (KEY, VALUE) VALUES (?, ?)", (key, str(value)))
            con.commit()
    except Exception as e:
        print(f"[오류] 설정 저장 실패: {e}")

# --- [2. 핵심 수집 및 마이그레이션 로직] ---

def add_c(title, subtitle, site, url, img, num, complete, gbun, total_count):
    db_table = 'TOON' if gbun == 'adult' else 'TOON_NORMAL'
    with get_list_db() as con:
        cur = con.cursor()
        cur.execute(f'''CREATE TABLE IF NOT EXISTS {db_table} (TITLE TEXT, SUBTITLE TEXT, WEBTOON_SITE TEXT, WEBTOON_URL TEXT, WEBTOON_IMAGE TEXT, WEBTOON_IMAGE_NUMBER INTEGER, TOTAL_COUNT INTEGER)''')
        cur.execute(f"INSERT OR IGNORE INTO {db_table} VALUES (?,?,?,?,?,?,?)", (title, subtitle, site, url, img, int(num), int(total_count)))
        con.commit()

def tel_send_message(dummy_list=None):
    msg = "[수집] 텔레그램 수집 프로세스 시작..."
    print(msg); logger.info(msg)
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
                            print(f" -> [수집완료] {title} - {subtitle} ({new_count}개째)")
                except: continue
            
            set_config('last_webtoon_id', current_max_id)
            final_msg = f"[수집 종료] 총 {new_count}건의 데이터가 추가되었습니다. (마지막 ID: {current_max_id})"
            print(final_msg); logger.info(final_msg)
        except Exception as e:
            print(f"[수집 에러] {e}"); logger.error(f"Sync Error: {e}")

def migrate_old_db():
    old_db_path = at[0] + '/data/db/webtoon_new.db'
    if not os.path.exists(old_db_path):
        print(f"[이관 에러] 기존 DB 파일을 찾을 수 없습니다: {old_db_path}"); return

    msg = "== [이관] 데이터 마이그레이션을 시작합니다. =="
    print(msg); logger.info(msg)
    
    try:
        old_con = sqlite3.connect(old_db_path)
        old_con.row_factory = sqlite3.Row
        old_cur = old_con.cursor()

        # 1. 목록 데이터 이관
        with get_list_db() as list_con:
            for table in ['TOON', 'TOON_NORMAL']:
                old_cur.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
                if old_cur.fetchone():
                    rows = old_cur.execute(f"SELECT * FROM {table}").fetchall()
                    print(f" -> [{table}] {len(rows)}건 복사 중...")
                    list_con.execute(f"CREATE TABLE IF NOT EXISTS {table} (TITLE TEXT, SUBTITLE TEXT, WEBTOON_SITE TEXT, WEBTOON_URL TEXT, WEBTOON_IMAGE TEXT, WEBTOON_IMAGE_NUMBER INTEGER, TOTAL_COUNT INTEGER)")
                    for row in rows:
                        list_con.execute(f"INSERT OR IGNORE INTO {table} VALUES (?,?,?,?,?,?,?)", 
                                         (row['TITLE'], row['SUBTITLE'], row['WEBTOON_SITE'], row['WEBTOON_URL'], row['WEBTOON_IMAGE'], row['WEBTOON_IMAGE_NUMBER'], row['TOTAL_COUNT']))
            list_con.commit()

        # 2. 상태 및 설정 데이터 이관
        with get_status_db() as status_con:
            print(" -> [상태 정보] 다운로드 완료 기록 전송 중...")
            for table in ['TOON', 'TOON_NORMAL']:
                old_cur.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
                if old_cur.fetchone():
                    completed_rows = old_cur.execute(f"SELECT DISTINCT TITLE, SUBTITLE FROM {table} WHERE COMPLETE='True'").fetchall()
                    for row in completed_rows:
                        status_con.execute("INSERT OR IGNORE INTO STATUS (TITLE, SUBTITLE, COMPLETE) VALUES (?,?,?)", (row['TITLE'], row['SUBTITLE'], 'True'))
            
            old_cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='CONFIG'")
            if old_cur.fetchone():
                configs = old_cur.execute("SELECT * FROM CONFIG").fetchall()
                for cfg in configs:
                    status_con.execute("INSERT OR REPLACE INTO CONFIG (KEY, VALUE) VALUES (?,?)", (cfg['KEY'], cfg['VALUE']))
            status_con.commit()

        old_con.close()
        print("== [이관 완료] 모든 데이터가 webtoon_list.db와 webtoon_status.db로 이관되었습니다. ==")
    except Exception as e:
        print(f"[이관 오류] {e}"); logger.error(f"Migration Error: {e}")

# --- [3. 다운로드 및 파일 처리] ---

def down(compress, cbz, alldown, title_filter, sub_filter, gbun):
    msg = f"== [{gbun}] 자동 다운로드 시작 =="
    print(msg); logger.info(msg)
    db_table = 'TOON' if gbun == 'adult' else 'TOON_NORMAL'
    
    with get_list_db() as con_l:
        cur_l = con_l.cursor()
        cur_l.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{db_table}'")
        if not cur_l.fetchone():
            print(f"[{db_table}] 테이블이 존재하지 않습니다."); return
        cur_l.execute(f"SELECT TITLE, SUBTITLE, TOTAL_COUNT FROM {db_table} GROUP BY TITLE, SUBTITLE")
        targets = cur_l.fetchall()

    for t_title, t_sub, t_total in targets:
        if title_filter and t_title != title_filter: continue
        if sub_filter and t_sub != sub_filter: continue
        
        with get_status_db() as con_s:
            cur_s = con_s.cursor()
            cur_s.execute("SELECT COMPLETE FROM STATUS WHERE TITLE=? AND SUBTITLE=?", (t_title, t_sub))
            res = cur_s.fetchone()
            if res and res['COMPLETE'] == 'True': continue

        print(f" -> [체크] {t_title} - {t_sub}")
        with get_list_db() as con_l:
            cur_l = con_l.cursor()
            cur_l.execute(f"SELECT WEBTOON_IMAGE, WEBTOON_IMAGE_NUMBER FROM {db_table} WHERE TITLE=? AND SUBTITLE=? ORDER BY WEBTOON_IMAGE_NUMBER ASC", (t_title, t_sub))
            img_list = cur_l.fetchall()

        if len(img_list) >= int(t_total or 0) and int(t_total or 0) > 0:
            print(f"    [다운로드] 이미지 수집 시작 ({len(img_list)}장)")
            folder_path = os.path.join(ROOT_PATH, "download", t_title, t_sub)
            os.makedirs(folder_path, exist_ok=True)
            sc = 0
            for img_url, img_num in img_list:
                f_path = os.path.join(folder_path, f"{img_num:03d}.jpg")
                if not os.path.exists(f_path):
                    try:
                        r = requests.get(img_url, timeout=20)
                        if r.status_code == 200:
                            with open(f_path, 'wb') as f: f.write(r.content)
                            sc += 1
                    except: continue

            if sc > 0:
                if str(compress) == '1':
                    ext = ".cbz" if str(cbz) == '1' else ".zip"
                    z_name = folder_path + ext
                    print(f"    [압축] 파일 생성: {z_name}")
                    with zipfile.ZipFile(z_name, 'w', zipfile.ZIP_DEFLATED) as z:
                        for file in os.listdir(folder_path): z.write(os.path.join(folder_path, file), file)
                    shutil.rmtree(folder_path)
                with get_status_db() as con_s:
                    con_s.execute("INSERT OR REPLACE INTO STATUS (TITLE, SUBTITLE, COMPLETE) VALUES (?,?,?)", (t_title, t_sub, 'True'))
                    con_s.commit()
                print(f"    [완료] {t_title} 처리 성공")

# --- [4. Flask 라우트] ---

@webtoon.route('/')
def index():
    if not session.get('logFlag'): return redirect(url_for('main.index'))
    return render_template('webtoon.html', gbun='adult')

@webtoon.route('index_list')
def index_list():
    if not session.get('logFlag'): return redirect(url_for('main.index'))
    gbun, search, page = request.args.get('gbun', 'adult'), request.args.get('search', '').strip(), request.args.get('page', type=int, default=1)
    per_page = 15
    table = 'TOON' if gbun == 'adult' else 'TOON_NORMAL'
    
    with get_list_db() as con:
        cur = con.cursor()
        cur.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
        if not cur.fetchone(): return render_template('webtoon_list.html', wow=[], pagination=None, gbun=gbun)
        
        where, param = ("WHERE TITLE LIKE ?", [f"%{search}%"]) if search else ("", [])
        cur.execute(f"SELECT TITLE, SUBTITLE FROM {table} {where} GROUP BY TITLE, SUBTITLE ORDER BY TITLE ASC LIMIT ? OFFSET ?", param + [per_page, (page-1)*per_page])
        wow = cur.fetchall()
        cur.execute(f"SELECT COUNT(*) FROM (SELECT 1 FROM {table} {where} GROUP BY TITLE, SUBTITLE)", param)
        total = cur.fetchone()[0]
        
    pagination = Pagination(page=page, total=total, per_page=per_page, bs_version=4, add_args={'gbun': gbun, 'search': search})
    return render_template('webtoon_list.html', wow=wow, pagination=pagination, gbun=gbun, search=search)

@webtoon.route('alim_list')
def alim_list():
    if not session.get('logFlag'): return redirect(url_for('main.index'))
    gbun = request.args.get('gbun', 'adult')
    db_table = 'TOON' if gbun == 'adult' else 'TOON_NORMAL'
    with get_list_db() as con:
        cur = con.cursor()
        cur.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{db_table}'")
        if not cur.fetchone(): return "데이터가 없습니다."
        cur.execute(f"SELECT * FROM {db_table} ORDER BY rowid DESC LIMIT 100")
        wow = cur.fetchall()
    return render_template('webtoon_alim.html', wow=wow, gbun=gbun)

@webtoon.route('db_migrate')
def run_migration():
    if not session.get('logFlag'): return redirect(url_for('main.index'))
    threading.Thread(target=migrate_old_db).start()
    return "<script>alert('마이그레이션을 시작했습니다. 로그를 확인하세요.'); history.back();</script>"

@webtoon.route('db_list_reset')
def db_list_reset():
    def rt():
        print("[리셋] 전체 상태 초기화 작업 시작...")
        with get_status_db() as con:
            con.execute("DELETE FROM STATUS")
            con.execute("INSERT OR REPLACE INTO CONFIG (KEY, VALUE) VALUES ('last_webtoon_id', '0')")
            con.commit()
        print("[리셋] 모든 작업이 완료되었습니다.")
    threading.Thread(target=rt).start()
    return "<script>alert('수집 ID 및 상태가 초기화되었습니다.'); history.back();</script>"

@webtoon.route("now")
def now_down():
    print("[명령] 수동 즉시 다운로드 시작")
    threading.Thread(target=down, args=(request.args.get('compress','1'), request.args.get('cbz','1'), 'True', request.args.get('title'), request.args.get('subtitle'), request.args.get('gbun','adult'))).start()
    return "<script>alert('다운로드를 시작했습니다.'); history.back();</script>"

@webtoon.route('db_redown')
def db_redown():
    title, subtitle = request.args.get('title'), request.args.get('subtitle')
    print(f"[명령] 개별 재다운로드 요청: {title}")
    with get_status_db() as con:
        con.execute("DELETE FROM STATUS WHERE TITLE=? AND SUBTITLE=?", (title, subtitle))
        con.commit()
    threading.Thread(target=down, args=('1', '1', 'True', title, subtitle, request.args.get('gbun', 'adult'))).start()
    return "<script>alert('재다운로드를 시작합니다.'); history.back();</script>"

@webtoon.route('webtoon_list_sync')
def start_sync_route():
    t_str = request.args.get('start_time')
    print(f"[스케줄] 수집 자동화 등록: {t_str}")
    scheduler.add_job(tel_send_message, trigger=CronTrigger.from_crontab(t_str), id='webtoon_list_sync', args=[None], replace_existing=True)
    return redirect(url_for('webtoon.index'))

@webtoon.route('webtoon_down_start')
def start_down_route():
    t_str, gbun = request.args.get('start_time'), request.args.get('gbun')
    print(f"[스케줄] 다운로드 자동화 등록 ({gbun}): {t_str}")
    scheduler.add_job(down, trigger=CronTrigger.from_crontab(t_str), id=f"auto_down_{gbun}", args=[request.args.get('compress','1'), request.args.get('cbz','1'), 'True', None, None, gbun], replace_existing=True, max_instances=3)
    return redirect(url_for('webtoon.index'))