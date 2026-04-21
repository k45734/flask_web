#-*- coding: utf-8 -*-
import os, sys, sqlite3, logging, asyncio, base64, requests, json, time, re, zipfile, shutil, platform, threading,io
from flask import Blueprint, render_template, request, session, redirect, url_for
from bs4 import BeautifulSoup as bs
from datetime import datetime
from apscheduler.triggers.cron import CronTrigger
import ast
import zlib
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
def log_and_print(msg, level="info"):
    """출력과 로그 기록을 동시에 처리하는 통합 함수"""
    if level == "info":
        logger.info(msg)
    elif level == "error":
        logger.error(msg)
    elif level == "warning":
        logger.warning(msg)
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")
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
            cur = con.cursor()
            cur.execute("SELECT VALUE FROM CONFIG WHERE KEY = ?", (key,))
            row = cur.fetchone()
            return row['VALUE'] if row else None
    except Exception as e:
        # 에러 발생 시 로그를 남겨서 원인을 파악하기 쉽게 함
        logger.error(f"설정값 로드 오류 ({key}): {e}")
        return None

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
    """봇 API를 사용하여 텔레그램 채널의 압축 데이터를 수신"""
    log_and_print("=== 텔레그램 데이터 동기화 엔진 가동 ===")

    token = get_config('bot_token')
    if not token:
        log_and_print("!!! [중단] 봇 토큰이 설정되지 않았습니다.", "error")
        return

    last_id = get_config('last_telegram_update_id')
    last_id = int(last_id) if last_id else 0
    log_and_print(f">> 현재 기준 Update ID: {last_id}")

    url = f"https://api.telegram.org/bot{token}/getUpdates"
    params = {"offset": last_id + 1, "timeout": 20}

    try:
        res = requests.get(url, params=params, timeout=25)
        data = res.json()
        
        if not data.get("ok"):
            log_and_print(f"!!! API 오류: {data.get('description')}", "error")
            return
        
        updates = data.get("result", [])
        if not updates:
            log_and_print(">> 새로운 데이터가 없습니다.")
            return

        log_and_print(f">> 수신된 패키지: {len(updates)}개 발견")
        new_last_id = last_id

        for idx, update in enumerate(updates, 1):
            msg_obj = update.get("channel_post")
            if not msg_obj: continue
            
            msg_text = msg_obj.get("text", "")
            update_id = update["update_id"]
            
            # 데이터 유형 판별 및 처리
            if msg_text.startswith("DATA_Z:"):
                log_and_print(f"   [{idx}/{len(updates)}] 압축 데이터(DATA_Z) 해독 시작... (ID: {update_id})")
                decode_and_save_to_db(msg_text, is_compressed=True)
            elif msg_text.startswith("DATA:"):
                log_and_print(f"   [{idx}/{len(updates)}] 일반 데이터(DATA) 해독 시작... (ID: {update_id})")
                decode_and_save_to_db(msg_text, is_compressed=False)
            else:
                log_and_print(f"   [{idx}/{len(updates)}] 일반 메시지 스킵 (ID: {update_id})")
            
            if update_id > new_last_id:
                new_last_id = update_id

        # 기준점 업데이트
        if new_last_id > last_id:
            set_config('last_telegram_update_id', new_last_id)
            log_and_print(f"🚀 동기화 완료: 기준점 갱신 ({new_last_id})")

    except Exception as e:
        log_and_print(f"!!! 수신 엔진 치명적 오류: {e}", "error")

def decode_and_save_to_db(msg_text, is_compressed=False):
    """
    해독된 데이터의 제목과 회차명을 출력하며 DB(adult/normal)에 적재합니다.
    """
    try:
        # 1. 데이터 복원 (압축 해제 또는 Base64 디코딩)
        if is_compressed:
            # DATA_Z: 접두어 제거 후 zlib 압축 해제
            encoded_data = msg_text.replace("DATA_Z:", "")
            raw_bytes = base64.b64decode(encoded_data)
            json_str = zlib.decompress(raw_bytes).decode('utf-8')
            payload_list = json.loads(json_str)
        else:
            # DATA: 접두어 제거 후 Base64 디코딩
            encoded_data = msg_text.replace("DATA:", "")
            json_str = base64.b64decode(encoded_data).decode('utf-8')
            payload_list = json.loads(json_str)
        
        total_count = len(payload_list)
        success_count = 0
        
        log_and_print(f"      🔍 패키지 내부 데이터 해독 중 (총 {total_count}개 항목)...")

        with get_list_db() as con:
            for item_data in payload_list:
                try:
                    # 2. 항목별 2차 해독 (Base64 -> String -> List/Tuple)
                    if isinstance(item_data, str):
                        item_raw = base64.b64decode(item_data).decode('utf-8')
                        item = ast.literal_eval(item_raw)
                    else:
                        item = item_data
                    
                    # 3. 데이터 매핑 (서버 전송 규격 기준)
                    # item 구조: [제목, 부제목, 사이트, URL, 이미지경로, 순번, 완료여부, 총갯수, (추가될구분자)]
                    title = item[0]
                    subtitle = item[1]
                    site = item[2]
                    url = item[3]
                    img_url = item[4]
                    img_num = int(item[5])
                    total_img_count = int(item[7])
                    
                    # 4. [중요] adult/normal 테이블 결정 로직
                    # 서버(webtoon_server.py)에서 전송 시 8번째 인덱스 등에 'adult'/'normal'을 넣어준다고 가정하거나,
                    # 현재는 기본적으로 'TOON'(adult)에 넣되 필요시 로직을 분기합니다.
                    # 만약 데이터 내부에 구분자가 없다면 호출 시점의 gbun을 참고해야 합니다.
                    target_table = 'TOON' 
                    if len(item) > 8:
                        target_table = 'TOON' if item[8] == 'adult' else 'TOON_NORMAL'

                    # 5. DB Insert 실행
                    con.execute(f"""
                        INSERT OR IGNORE INTO {target_table} 
                        (TITLE, SUBTITLE, WEBTOON_SITE, WEBTOON_URL, WEBTOON_IMAGE, WEBTOON_IMAGE_NUMBER, TOTAL_COUNT) 
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (title, subtitle, site, url, img_url, img_num, total_img_count))
                    
                    # 진행 상황 출력 (첫 번째 이미지일 때만 출력하여 로그 폭주 방지)
                    if str(img_num).endswith('1'):
                        log_and_print(f"      ✨ 해독됨: [{target_table}] {title} > {subtitle}")
                    
                    success_count += 1
                except Exception as e:
                    logger.error(f"      ❌ 개별 항목 처리 오류: {e}")
                    continue
            con.commit()
        
        log_and_print(f"      ✅ 최종 완료: {success_count}/{total_count} 항목 DB 저장 성공")
        return True
    except Exception as e:
        log_and_print(f"   ❌ 데이터 해독 패키지 처리 실패: {e}", "error")
        return False
		
def down(compress, cbz, alldown, title_filter, sub_filter, gbun):
    logger.info(f"==================================================")
    logger.info(f"== [{gbun}] 다운로드 엔진 가동 (안전 모드) ==")
    logger.info(f"==================================================")
    print(f"\n[다운로드] {gbun} 구역 작업 시작...")

    db_table = 'TOON' if gbun == 'adult' else 'TOON_NORMAL'
    
    try:
        # 1. gbun 기반 최상위 경로 생성 및 확인
        target_gbun_path = os.path.join(WEBTOON_PATH, gbun)
        os.makedirs(target_gbun_path, exist_ok=True)

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
            status_msg = f" -> [{gbun.upper()}] [{t_title}] {t_sub} ({cur_c}/{tar_c}장)"
            logger.info(status_msg)
            print(status_msg, end=" ", flush=True)

            # 4. 수집 완료 여부 검사 (이미지 수가 목표치에 도달했는지 확인)
            if cur_c > 0 and cur_c >= tar_c:
                print(" -> [다운로드 개시]")
                f_path = os.path.join(target_gbun_path, t_title, t_sub)
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
                        except Exception as e:
                            logger.error(f"   ! 이미지 다운로드 실패 (번호:{img_num}): {e}")
                            continue

                # 5. [강화된 후처리] 실제 파일 개수 검증 후 압축
                actual_files = [f for f in os.listdir(f_path) if os.path.isfile(os.path.join(f_path, f))]
                
                if len(actual_files) < tar_c:
                    print(f" -> [중단] 파일 부족 ({len(actual_files)}/{tar_c}장)")
                    logger.warning(f"파일 누락으로 압축 스킵: {t_title} - {t_sub}")
                    continue

                try:
                    if str(compress) == '1':
                        ext = ".cbz" if str(cbz) == '1' else ".zip"
                        z_name = f_path + ext
                        print(f"    └ [압축] {os.path.basename(z_name)}...", end="")
                        
                        with zipfile.ZipFile(z_name, 'w', zipfile.ZIP_DEFLATED) as z:
                            for file in actual_files:
                                file_path = os.path.join(f_path, file)
                                if os.path.exists(file_path):
                                    z.write(file_path, file)
                        
                        shutil.rmtree(f_path) 
                        print(" 완료!")
                    
                    # 모든 과정 성공 시에만 완료 처리
                    with get_status_db() as con_s:
                        con_s.execute("INSERT OR REPLACE INTO STATUS (TITLE, SUBTITLE, COMPLETE) VALUES (?,?,?)", (t_title, t_sub, 'True'))
                        con_s.commit()
                    logger.info(f"    └ [성공] {t_title} 완료")

                except Exception as e:
                    print(f" 실패! ({e})")
                    logger.error(f"압축/완료 처리 중 오류: {e}")
            else:
                shortage = tar_c - cur_c
                print(f" -> [대기] {shortage}장 부족")

        print(f"\n[알림] {gbun} 구역 작업 종료.")
        logger.info(f"== [{gbun}] 다운로드 엔진 종료 ==")
            
    except Exception as e: 
        logger.error(f"!!! Down Error: {e}")
        print(f"!!! 치명적 오류 발생: {e}")

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
                    HAVING COUNT(*) < TOTAL_COUNT AND TOTAL_COUNT > 0
                    ORDER BY TITLE ASC, SUBTITLE DESC;
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
        con.execute("DELETE FROM STATUS"); con.execute("UPDATE CONFIG SET VALUE='0' WHERE KEY='last_telegram_update_id'"); con.commit()
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