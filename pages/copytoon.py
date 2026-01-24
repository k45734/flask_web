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
    logger.info("== [시스템] 전수 조사 및 규격 검증 엔진 가동 ==")
    logger.info("==================================================")
    print("\n[알림] 텔레그램 수집 프로세스가 시작되었습니다.")
    
    # 1. 시작점 확인
    last_id = int(get_config('last_webtoon_id') or 0)
    logger.info(f"[설정] 현재 DB 저장된 마지막 ID: {last_id}")
    print(f">> 현재 기준점(last_id): {last_id} 번부터 추적 시작")
    
    is_continue = True
    total_new_count = 0
    page_count = 0

    while is_continue:
        page_count += 1
        # 현재 지점보다 조금 앞선 지점(25개)을 요청하여 유연하게 수집
        target_id = last_id + 25 
        url = f'https://t.me/s/webtoonalim?before={target_id}'
        
        logger.info(f"[진행] {page_count}페이지 분석 중... (Target ID: {target_id})")
        print(f"\n--- {page_count}번 페이지 호출 ({url}) ---")
        
        try:
            req = requests.get(url, timeout=15)
            soup = bs(req.text, "html.parser")
            messages = soup.findAll("div", {"class": "tgme_widget_message"})
            
            if not messages:
                logger.warning("[중단] 페이지 내 메시지가 없습니다. 루프를 종료합니다.")
                print("!! 메시지를 찾을 수 없어 수집을 종료합니다.")
                break

            new_data_dict = {'TOON': {}, 'TOON_NORMAL': {}}
            processed_ids = []
            
            for m in messages:
                try:
                    pid = int(m['data-post'].split('/')[-1])
                    
                    # 이미 수집된 ID는 가볍게 print만 찍고 pass
                    if pid <= last_id:
                        print(f"[-] ID:{pid} (이미 수집됨)")
                        continue
                    
                    processed_ids.append(pid)
                    txt = m.find("div", {"class": "tgme_widget_message_text"})
                    
                    if not txt:
                        print(f"[!] ID:{pid} (본문 텍스트 없음 - 건너뜀)")
                        continue
                    
                    # 데이터 해독 시작
                    dec = base64.b64decode(txt.get_text(strip=True).encode('ascii')).decode('utf-8')
                    aac = dec.split('\n\n')

                    # [핵심] 규격 검사 로직 + 로그
                    if len(aac) < 8:
                        logger.warning(f"[구버전] ID:{pid} | 데이터 조각 부족 (len:{len(aac)})")
                        print(f"[종료] ID:{pid} 번에서 구형 데이터 포맷을 발견했습니다.")
                        is_continue = False
                        break
                    
                    if not aac[7].strip().isdigit():
                        logger.warning(f"[구버전] ID:{pid} | aac[7]이 숫자가 아님 ('{aac[7]}')")
                        print(f"[종료] ID:{pid} 번은 유효한 최신 규격이 아닙니다. (총 장수 정보 없음)")
                        is_continue = False
                        break

                    # 규격 통과 시 데이터 분류
                    gbun = aac[8] if len(aac) >= 9 else 'adult'
                    db_t = 'TOON' if gbun == 'adult' else 'TOON_NORMAL'
                    key = (aac[0], aac[1], int(aac[5]))
                    
                    # 실제 데이터 저장 준비
                    new_data_dict[db_t][key] = (aac[0], aac[1], aac[2], aac[3], aac[4], int(aac[5]), int(aac[7]))
                    
                    msg = f" -> [수집성공] ID:{pid} | {aac[0]} | {aac[5]}/{aac[7]}장"
                    logger.info(msg)
                    print(msg)
                    
                except Exception as ex:
                    print(f"[에러] 개별 메시지(ID:{pid}) 분석 중 예외 발생: {ex}")
                    continue

            # 페이지 단위 DB 저장 로그
            with get_list_db() as con:
                added_this_page = 0
                for db_t in ['TOON', 'TOON_NORMAL']:
                    data_list = list(new_data_dict[db_t].values())
                    if not data_list: continue
                    con.executemany(f"INSERT OR REPLACE INTO {db_t} VALUES (?,?,?,?,?,?,?)", data_list)
                    added_this_page += len(data_list)
                con.commit()
                if added_this_page > 0:
                    logger.info(f"[DB] {added_this_page}개 데이터 저장 완료")
                    print(f"== DB에 {added_this_page}개의 새로운 에피소드를 기록했습니다. ==")

            # 다음 루프를 위한 ID 업데이트
            if processed_ids:
                last_id = max(processed_ids)
                set_config('last_webtoon_id', last_id)
                total_new_count += len(processed_ids)
                print(f">> 현재까지 누적 수집 ID: {last_id} (진행 중...)")
                time.sleep(0.5) # 서버 부하 방지용 짧은 휴식
            else:
                print(">> 더 이상 처리할 새로운 ID가 없습니다.")
                is_continue = False
                
        except Exception as e:
            logger.error(f"!!! 수집 메인 루프 치명적 에러: {e}")
            print(f"!!! 시스템 오류 발생으로 수집 중단: {e}")
            break

    print("\n" + "="*50)
    logger.info(f"== [수집종료] 총 {total_new_count}개 메시지 검사 완료 (최종 ID: {last_id}) ==")
    print(f"[완료] 전수 조사가 종료되었습니다. 총 {total_new_count}개를 훑었습니다.")
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