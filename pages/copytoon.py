#-*- coding: utf-8 -*-
import os, sys, sqlite3, logging, asyncio, base64, requests, json, time, re, zipfile, shutil, platform, threading,io
from flask import Blueprint, render_template, request, session, redirect, url_for
from bs4 import BeautifulSoup as bs
from datetime import datetime
from apscheduler.triggers.cron import CronTrigger
import ast

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
    # 아래 줄들을 추가하여 자동 생성을 보장합니다.
    con.execute("CREATE TABLE IF NOT EXISTS TOON (TITLE TEXT, SUBTITLE TEXT, WEBTOON_SITE TEXT, WEBTOON_URL TEXT, WEBTOON_IMAGE TEXT, WEBTOON_IMAGE_NUMBER INTEGER, TOTAL_COUNT INTEGER)")
    con.execute("CREATE TABLE IF NOT EXISTS TOON_NORMAL (TITLE TEXT, SUBTITLE TEXT, WEBTOON_SITE TEXT, WEBTOON_URL TEXT, WEBTOON_IMAGE TEXT, WEBTOON_IMAGE_NUMBER INTEGER, TOTAL_COUNT INTEGER)")
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

# --- [3. 수집 엔진 (최종 지능형 역주행)] ---
def tel_send_message(dummy=None):
    token = get_config('bot_token')
    target_chat_id = get_config('chat_id')
    
    if not token or not target_chat_id:
        logger.error("봇 토큰 또는 채팅 ID가 설정되지 않았습니다.")
        return

    logger.info("== [API 기반 전용 봇] 동기화 엔진 가동 ==")
    
    # 텔레그램 봇 API 호출 (getUpdates 사용)
    api_url = f"https://api.telegram.org/bot{token}/getUpdates"
    try:
        res = requests.get(api_url, timeout=15).json()
        if not res.get("ok"): return

        for update in res.get("result", []):
            msg = update.get("message", {})
            # 지정된 채팅방에서 온 메시지만 처리
            if str(msg.get("chat", {}).get("id")) != str(target_chat_id): continue
            
            # 1. 문서(JSON 파일)가 포함된 경우
            if "document" in msg:
                file_id = msg["document"]["file_id"]
                # 파일 다운로드 경로 획득
                f_res = requests.get(f"https://api.telegram.org/bot{token}/getFile?file_id={file_id}").json()
                file_path = f_res["result"]["file_path"]
                file_url = f"https://api.telegram.org/file/bot{token}/{file_path}"
                
                # 파일 내용 읽기
                data_json = requests.get(file_url).json()
                # 이후 기존 데이터 저장 로직 수행...
                
            # 2. 혹은 기존처럼 텍스트(DATA:)가 포함된 경우
            elif "text" in msg and "DATA:" in msg["text"]:
                # 기존의 텍스트 파싱 로직 수행...
                pass

    except Exception as e:
        logger.error(f"API 수집 에러: {e}")

def down(compress, cbz, alldown, title_filter, sub_filter, gbun):
    logger.info(f"==================================================")
    logger.info(f"== [{gbun}] 다운로드 엔진 가동 (경로 분리 모드) ==")
    logger.info(f"==================================================")
    print(f"\n[다운로드] {gbun} 구역 작업 시작...")

    db_table = 'TOON' if gbun == 'adult' else 'TOON_NORMAL'
    
    try:
        # 1. gbun 기반 최상위 경로 생성 및 확인
        target_gbun_path = os.path.join(WEBTOON_PATH, gbun)
        if not os.path.exists(target_gbun_path):
            os.makedirs(target_gbun_path, exist_ok=True)
            print(f">> [폴더생성] 새로운 구분 폴더를 만들었습니다: {target_gbun_path}")

        # 2. 다운로드 대상 쿼리 (STATUS_DB와 결합)
        with get_list_db() as con_l:
            con_l.execute(f"ATTACH DATABASE '{STATUS_DB}' AS s_db")
            query = f"SELECT a.TITLE, a.SUBTITLE, a.TOTAL_COUNT FROM {db_table} a LEFT JOIN s_db.STATUS s ON a.TITLE = s.TITLE AND a.SUBTITLE = s.SUBTITLE WHERE (s.COMPLETE IS NULL OR s.COMPLETE != 'True') AND a.TOTAL_COUNT > 0"
            if title_filter: query += f" AND a.TITLE = '{title_filter}'"
            query += " GROUP BY a.TITLE, a.SUBTITLE"
            targets = con_l.execute(query).fetchall()
            con_l.execute("DETACH DATABASE s_db")

        print(f">> 분석 결과: 총 {len(targets)}개의 에피소드가 대기 중입니다.")

        for t_title, t_sub, t_total in targets:
            # 3. 이미지 리스트 확보
            with get_list_db() as con_l:
                cur_l = con_l.cursor()
                cur_l.execute(f"SELECT WEBTOON_IMAGE, WEBTOON_IMAGE_NUMBER FROM {db_table} WHERE TITLE=? AND SUBTITLE=? ORDER BY WEBTOON_IMAGE_NUMBER ASC", (t_title, t_sub))
                img_list = cur_l.fetchall()
            
            cur_c, tar_c = len(img_list), int(t_total or 0)
            
            # 진행 상황 판단 로그
            status_msg = f" -> [{gbun.upper()}] [{t_title}] {t_sub} ({cur_c}/{tar_c}장)"
            logger.info(status_msg)
            print(status_msg, end=" ", flush=True)

            # 4. 수집 완료 여부 검사 (cur_c >= tar_c)
            if cur_c > 0 and cur_c >= tar_c:
                print(" -> [조건충족! 다운로드 개시]")
                
                # 최종 저장 경로 설정 (WEBTOON_PATH/gbun/제목/부제목)
                f_path = os.path.join(target_gbun_path, t_title, t_sub)
                os.makedirs(f_path, exist_ok=True)
                
                sc = 0 # 성공 카운트
                for img_url, img_num in img_list:
                    img_file = os.path.join(f_path, f"{img_num:03d}.jpg")
                    
                    if not os.path.exists(img_file):
                        try:
                            r = requests.get(img_url, timeout=20)
                            if r.status_code == 200:
                                with open(img_file, 'wb') as f: f.write(r.content)
                                sc += 1
                        except Exception as e:
                            logger.error(f"   ! 이미지 다운로드 실패 (번호:{img_num}): {e}")
                            continue
                
                # 5. 후처리 (압축 및 완료 기록)
                if sc > 0 or os.path.exists(f_path):
                    if str(compress) == '1':
                        ext = ".cbz" if str(cbz) == '1' else ".zip"
                        z_name = f_path + ext
                        print(f"    └ [압축] {os.path.basename(z_name)} 생성 중...", end="")
                        
                        with zipfile.ZipFile(z_name, 'w', zipfile.ZIP_DEFLATED) as z:
                            for file in os.listdir(f_path): 
                                z.write(os.path.join(f_path, file), file)
                        
                        shutil.rmtree(f_path) # 원본 폴더 삭제
                        print(" 완료!")
                    
                    # 상태 DB 업데이트
                    with get_status_db() as con_s:
                        con_s.execute("INSERT OR REPLACE INTO STATUS (TITLE, SUBTITLE, COMPLETE) VALUES (?,?,?)", (t_title, t_sub, 'True'))
                        con_s.commit()
                    logger.info(f"    └ [성공] {t_title} - {t_sub} 완료 처리됨")
            else:
                # 조건 미달 시 이유 출력
                shortage = tar_c - cur_c
                print(f" -> [대기] {shortage}장 부족함 (수집 대기 중)")

        print(f"\n[알림] {gbun} 구역 작업이 완료되었습니다.")
        logger.info(f"==================================================")
        logger.info(f"== [{gbun}] 다운로드 엔진 종료 ==")
        logger.info(f"==================================================")

    except Exception as e: 
        logger.error(f"!!! Down Error: {e}")
        print(f"!!! 다운로드 중 치명적 오류 발생: {e}")

# --- [5. 웹 라우트] ---
@webtoon.route('/')
def index():
    if not session.get('logFlag'): return redirect(url_for('main.index'))
    # 저장된 설정값 불러오기
    bot_token = get_config('bot_token')
    chat_id = get_config('chat_id')
    return render_template('webtoon.html', gbun='adult', bot_token=bot_token, chat_id=chat_id)

@webtoon.route('index_list')
def index_list():
    gbun, search, page = request.args.get('gbun', 'adult'), request.args.get('search', '').strip(), request.args.get('page', type=int, default=1)
    table = 'TOON' if gbun == 'adult' else 'TOON_NORMAL'
    with get_list_db() as con:
        cur = con.cursor()
        cur.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
        if not cur.fetchone(): return render_template('webtoon_list.html', wow=[], pagination=None, gbun=gbun)
        
        where, param = ("WHERE TITLE LIKE ?", [f"%{search}%"]) if search else ("", [])
        
        # --- 수정된 쿼리: COUNT(*)를 사용하여 현재 DB에 저장된 이미지 개수를 실시간으로 가져옵니다 ---
        query = f"""
            SELECT 
                TITLE, 
                SUBTITLE, 
                TOTAL_COUNT, 
                COUNT(*) as CURRENT_COUNT 
            FROM {table} 
            {where} 
            GROUP BY TITLE, SUBTITLE 
            ORDER BY TITLE ASC 
            LIMIT 15 OFFSET {(page-1)*15}
        """
        cur.execute(query, param)
        wow = cur.fetchall()
        
        cur.execute(f"SELECT COUNT(*) FROM (SELECT 1 FROM {table} {where} GROUP BY TITLE, SUBTITLE)", param)
        total = cur.fetchone()[0]
        
    pagination = Pagination(page=page, total=total, per_page=15, bs_version=4, add_args={'gbun': gbun, 'search': search})
    return render_template('webtoon_list.html', wow=wow, pagination=pagination, gbun=gbun, search=search)

@webtoon.route('/alim_list')
def alim_list():
    try:
        def get_db_data(table_name):
            with get_list_db() as con:
                # 1. 상단 요약용 (전체 현황: 완료 + 미완료 모두 계산)
                summary_query = f"""
                    SELECT 
                        SUM(CASE WHEN is_complete = 1 THEN 1 ELSE 0 END) as COMPLETE,
                        SUM(CASE WHEN is_complete = 0 THEN 1 ELSE 0 END) as INCOMPLETE,
                        COUNT(*) as TOTAL
                    FROM (
                        SELECT CASE WHEN COUNT(*) >= TOTAL_COUNT AND TOTAL_COUNT > 0 THEN 1 ELSE 0 END as is_complete
                        FROM {table_name} GROUP BY TITLE, SUBTITLE
                    )
                """
                summary = con.execute(summary_query).fetchone()

                # 2. 하단 리스트용 (100% 완료된 에피소드만 추출)
                list_query = f"""
                    SELECT TITLE, SUBTITLE, TOTAL_COUNT, COUNT(*) as CURRENT_COUNT
                    FROM {table_name}
                    GROUP BY TITLE, SUBTITLE
                    HAVING COUNT(*) >= TOTAL_COUNT AND TOTAL_COUNT > 0
                    ORDER BY TITLE ASC, SUBTITLE DESC
                """
                details = con.execute(list_query).fetchall()
                
                return summary, details

        adult_sum, adult_list = get_db_data('TOON')
        normal_sum, normal_list = get_db_data('TOON_NORMAL')

        return render_template('webtoon_alim_list.html', 
                               adult=adult_sum, adult_list=adult_list,
                               normal=normal_sum, normal_list=normal_list)
    except Exception as e:
        logger.error(f"현황판 로드 에러: {e}")
        return render_template('webtoon_alim_list.html', adult=None, normal=None)

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
    # 폼에서 넘어온 토큰 정보 저장
    bot_token = request.args.get('bot_token')
    chat_id = request.args.get('chat_id')
    if bot_token: set_config('bot_token', bot_token)
    if chat_id: set_config('chat_id', chat_id)
    
    t_str = request.args.get('start_time', '*/5 * * * *')
    scheduler.add_job(tel_send_message, trigger=CronTrigger.from_crontab(t_str), 
                      id='webtoon_list_sync', args=[None], replace_existing=True)
    return redirect(url_for('webtoon.index'))

@webtoon.route('webtoon_down_start')
def start_down_route():
    t_str, gbun = request.args.get('start_time', '*/5 * * * *'), request.args.get('gbun', 'adult')
    scheduler.add_job(down, trigger=CronTrigger.from_crontab(t_str), id=f"auto_down_{gbun}", args=[request.args.get('compress','1'), request.args.get('cbz','1'), 'True', None, None, gbun], replace_existing=True, max_instances=3)
    return redirect(url_for('webtoon.index'))