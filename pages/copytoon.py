#-*- coding: utf-8 -*-
import os, sys, sqlite3, logging, asyncio, base64, requests, json, time, re, zipfile, shutil, platform, threading
from flask import Blueprint, render_template, request, session, redirect, url_for
from bs4 import BeautifulSoup as bs
from datetime import datetime
from apscheduler.triggers.cron import CronTrigger

# [필수 라이브러리 체크]
try:
    from flask_paginate import Pagination, get_page_args
except ImportError:
    os.system('pip install flask_paginate')
    from flask_paginate import Pagination, get_page_args

# [스케줄러 및 로거 연결]
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
WEBTOON_PATH = at[0] + '/data/webtoon' # 최종 창고
ROOT_PATH = at[0] + '/data'

os.makedirs(WEBTOON_PATH, exist_ok=True)
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

# --- [2. 핵심 엔진: 최적화 및 다운로드] ---

def db_optimize():
    msg = "== [최적화] DB 용량 최적화 및 조각 모음 시작 =="
    print(msg); logger.info(msg)
    try:
        for db_path in [LIST_DB, STATUS_DB]:
            db_name = os.path.basename(db_path)
            before = os.path.getsize(db_path)
            with sqlite3.connect(db_path) as con:
                con.execute("VACUUM")
            after = os.path.getsize(db_path)
            res_msg = f" -> {db_name}: {before//1024}KB -> {after//1024}KB (절감: {(before-after)//1024}KB)"
            print(res_msg); logger.info(res_msg)
        fin_msg = "== [완료] DB 최적화 작업이 끝났습니다. =="
        print(fin_msg); logger.info(fin_msg)
    except Exception as e:
        err_msg = f"[오류] DB 최적화 실패: {e}"
        print(err_msg); logger.error(err_msg)

def migrate_old_db():
    old_db = at[0] + '/data/db/webtoon_new.db'
    if not os.path.exists(old_db):
        msg = "[이관] 기존 DB(webtoon_new.db)를 찾을 수 없어 중단합니다."
        print(msg); logger.warning(msg); return
    
    msg = "== [이관] 이전 데이터 마이그레이션 시작 =="
    print(msg); logger.info(msg)
    try:
        with sqlite3.connect(old_db) as old_con:
            old_con.row_factory = sqlite3.Row
            with get_list_db() as new_list:
                for table in ['TOON', 'TOON_NORMAL']:
                    rows = old_con.execute(f"SELECT * FROM {table}").fetchall()
                    new_list.executemany(f"INSERT OR IGNORE INTO {table} VALUES (?,?,?,?,?,?,?)", 
                        [(r[0],r[1],r[2],r[3],r[4],r[5],r[6]) for r in rows])
                    msg_t = f" -> [{table}] {len(rows)}건 이관 완료"
                    print(msg_t); logger.info(msg_t)
            with get_status_db() as new_status:
                for table in ['TOON', 'TOON_NORMAL']:
                    rows = old_con.execute(f"SELECT TITLE, SUBTITLE FROM {table} WHERE COMPLETE='True'").fetchall()
                    new_status.executemany("INSERT OR IGNORE INTO STATUS (TITLE, SUBTITLE, COMPLETE) VALUES (?,?,'True')", rows)
                    msg_s = f" -> [{table}] 상태(완료) 데이터 {len(rows)}건 이관 완료"
                    print(msg_s); logger.info(msg_s)
        msg_f = "== [완료] 데이터 이관 작업이 모두 끝났습니다. =="
        print(msg_f); logger.info(msg_f)
    except Exception as e:
        err_f = f"[오류] 데이터 이관 중 실패: {e}"
        print(err_f); logger.error(err_f)

def down(compress, cbz, alldown, title_filter, sub_filter, gbun):
    msg = f"== [{gbun}] 다운로드 엔진 가동 (최적화 모드) =="
    print(msg); logger.info(msg)
    db_table = 'TOON' if gbun == 'adult' else 'TOON_NORMAL'
    
    try:
        with get_list_db() as con_l:
            con_l.execute(f"ATTACH DATABASE '{STATUS_DB}' AS s_db")
            query = f"""
                SELECT a.TITLE, a.SUBTITLE, a.TOTAL_COUNT 
                FROM {db_table} a 
                LEFT JOIN s_db.STATUS s ON a.TITLE = s.TITLE AND a.SUBTITLE = s.SUBTITLE 
                WHERE (s.COMPLETE IS NULL OR s.COMPLETE != 'True')
            """
            if title_filter: query += f" AND a.TITLE = '{title_filter}'"
            query += " GROUP BY a.TITLE, a.SUBTITLE"
            targets = con_l.execute(query).fetchall()
            con_l.execute("DETACH DATABASE s_db")

        msg_scan = f" -> [검사] 미완료 대상 {len(targets)}건 발견 (방대한 5만여 개 중 필터링 완료)"
        print(msg_scan); logger.info(msg_scan)

        for t_title, t_sub, t_total in targets:
            with get_list_db() as con_l:
                cur_l = con_l.cursor()
                cur_l.execute(f"SELECT WEBTOON_IMAGE, WEBTOON_IMAGE_NUMBER FROM {db_table} WHERE TITLE=? AND SUBTITLE=? ORDER BY WEBTOON_IMAGE_NUMBER ASC", (t_title, t_sub))
                img_list = cur_l.fetchall()
            
            cur_c, tar_c = len(img_list), int(t_total or 0)
            check_msg = f" -> [체크] {t_title} - {t_sub} ({cur_c}/{tar_c})"
            print(check_msg); logger.info(check_msg)
            
            if cur_c >= tar_c and tar_c > 0:
                exec_msg = f"    [실행] {t_title} 다운로드 시작 (대상: {tar_c}장)"
                print(exec_msg); logger.info(exec_msg)
                
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
                        zip_msg = f"    [압축] 파일 생성 중: {z_name}"
                        print(zip_msg); logger.info(zip_msg)
                        try:
                            with zipfile.ZipFile(z_name, 'w', zipfile.ZIP_DEFLATED) as z:
                                for file in os.listdir(f_path): z.write(os.path.join(f_path, file), file)
                            shutil.rmtree(f_path)
                        except Exception as ze:
                            err_z = f"    [오류] 압축 중 에러: {ze}"
                            print(err_z); logger.error(err_z)
                    
                    with get_status_db() as con_s:
                        con_s.execute("INSERT OR REPLACE INTO STATUS (TITLE, SUBTITLE, COMPLETE) VALUES (?,?,?)", (t_title, t_sub, 'True'))
                        con_s.commit()
                    fin_msg = f"    [완료] {t_title} - {t_sub} 다운로드 및 상태 저장 성공"
                    print(fin_msg); logger.info(fin_msg)
            else:
                if tar_c > 0:
                    wait_msg = f"    [대기] {t_title}: 주소 부족으로 건너뜀 ({cur_c}/{tar_c})"
                    print(wait_msg); logger.debug(wait_msg)
        
        eng_fin = f"== [{gbun}] 다운로드 루프 종료 =="
        print(eng_fin); logger.info(eng_fin)
    except Exception as e:
        err_total = f"[오류] 엔진 가동 중 치명적 오류: {e}"
        print(err_total); logger.error(err_total)

# --- [3. 수집 및 라우트] ---

def tel_send_message(dummy=None):
    msg = "[수집] 텔레그램 데이터 동기화 시작"
    print(msg); logger.info(msg)
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
                    print(f" -> [수집] {aac[0]} {aac[1]} 추가")
            except: continue
        set_config('last_webtoon_id', max_id)
        fin_msg = f"[수집완료] 신규 {new_c}건 추가 (마지막 ID: {max_id})"
        print(fin_msg); logger.info(fin_msg)
    except Exception as e:
        err_s = f"[오류] 수집 중 에러: {e}"
        print(err_s); logger.error(err_s)

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

@webtoon.route('alim_list')
def alim_list():
    gbun = request.args.get('gbun', 'adult')
    table = 'TOON' if gbun == 'adult' else 'TOON_NORMAL'
    with get_list_db() as con:
        cur = con.cursor()
        cur.execute(f"SELECT * FROM {table} ORDER BY rowid DESC LIMIT 100")
        wow = cur.fetchall()
    return render_template('webtoon_alim.html', wow=wow, gbun=gbun)

@webtoon.route('db_migrate')
def run_migration():
    msg = "[명령] 사용자 요청에 의한 DB 이관 시작"
    print(msg); logger.info(msg)
    threading.Thread(target=migrate_old_db).start()
    return "<script>alert('이관을 시작했습니다.'); history.back();</script>"

@webtoon.route('db_list_reset')
def db_list_reset():
    msg = "[명령] 사용자 요청에 의한 상태 DB 초기화"
    print(msg); logger.info(msg)
    with get_status_db() as con:
        con.execute("DELETE FROM STATUS")
        con.execute("UPDATE CONFIG SET VALUE='0' WHERE KEY='last_webtoon_id'")
        con.commit()
    return "<script>alert('초기화가 완료되었습니다.'); history.back();</script>"

@webtoon.route('db_redown')
def db_redown():
    title, sub, gbun = request.args.get('title'), request.args.get('subtitle'), request.args.get('gbun','adult')
    msg = f"[명령] 개별 재다운로드 요청: {title} - {sub}"
    print(msg); logger.info(msg)
    with get_status_db() as con:
        con.execute("DELETE FROM STATUS WHERE TITLE=? AND SUBTITLE=?", (title, sub))
        con.commit()
    threading.Thread(target=down, args=('1','1','True',title,sub,gbun)).start()
    return "<script>alert('재다운로드를 시작합니다.'); history.back();</script>"

@webtoon.route('db_vacuum')
def run_vacuum():
    msg = "[명령] 사용자 요청에 의한 DB 최적화 실행"
    print(msg); logger.info(msg)
    threading.Thread(target=db_optimize).start()
    return "<script>alert('DB 최적화를 시작했습니다.'); history.back();</script>"

@webtoon.route("now")
def now_down():
    msg = "[명령] 수동 즉시 다운로드 실행"
    print(msg); logger.info(msg)
    threading.Thread(target=down, args=(request.args.get('compress','1'), request.args.get('cbz','1'), 'True', request.args.get('title'), request.args.get('subtitle'), request.args.get('gbun','adult'))).start()
    return "<script>alert('다운로드를 시작했습니다.'); history.back();</script>"

@webtoon.route('webtoon_list_sync')
def start_sync_route():
    t_str = request.args.get('start_time')
    msg = f"[스케줄] 수집 자동화 등록: {t_str}"
    print(msg); logger.info(msg)
    scheduler.add_job(tel_send_message, trigger=CronTrigger.from_crontab(t_str), id='webtoon_list_sync', args=[None], replace_existing=True)
    return redirect(url_for('webtoon.index'))

@webtoon.route('webtoon_down_start')
def start_down_route():
    t_str, gbun = request.args.get('start_time'), request.args.get('gbun')
    msg = f"[스케줄] {gbun} 다운로드 자동화 등록: {t_str}"
    print(msg); logger.info(msg)
    scheduler.add_job(down, trigger=CronTrigger.from_crontab(t_str), id=f"auto_down_{gbun}", args=[request.args.get('compress','1'), request.args.get('cbz','1'), 'True', None, None, gbun], replace_existing=True, max_instances=3)
    return redirect(url_for('webtoon.index'))