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
    """봇 API를 사용하여 텔레그램 채널의 이중 인코딩 데이터를 수신 (Log & Print 완전 동기화)"""
    msg = "== [API 기반 동기화] 텔레그램 봇 데이터 수신 가동 =="
    logger.info(msg)
    print(f"\n{msg}")

    # 1. 설정값 불러오기
    token = get_config('bot_token')
    if not token:
        msg = "!!! [경고] 봇 토큰이 설정되지 않았습니다. 설정을 확인해주세요."
        logger.error(msg)
        print(msg)
        return

    last_id = get_config('last_telegram_update_id')
    last_id = int(last_id) if last_id else 0
    msg = f">> 현재 동기화 기준 ID: {last_id}"
    logger.info(msg)
    print(msg)

    # 2. 텔레그램 getUpdates API 호출
    url = f"https://api.telegram.org/bot{token}/getUpdates"
    params = {"offset": last_id + 1, "timeout": 20}

    try:
        msg = f">> 텔레그램 서버에 업데이트 확인 요청 중... (offset: {last_id + 1})"
        logger.info(msg)
        print(msg)
        
        res = requests.get(url, params=params, timeout=25)
        data = res.json()
        
        if not data.get("ok"):
            msg = f"!!! 텔레그램 API 오류: {data.get('description')}"
            logger.error(msg)
            print(msg)
            return
        
        updates = data.get("result", [])
        msg = f">> 수신된 업데이트 패키지 개수: {len(updates)}개"
        logger.info(msg)
        print(msg)

        new_last_id = last_id

        for idx, update in enumerate(updates, 1):
            msg_obj = update.get("channel_post")
            if not msg_obj:
                continue
            
            msg_text = msg_obj.get("text", "")
            update_id = update["update_id"]
            
            msg = f"   [{idx}/{len(updates)}] Update ID {update_id} 분석 중..."
            logger.info(msg)
            print(msg, end=" ")

            if msg_text.startswith("DATA:"):
                # ✅ 수정된 이중 해독 함수 호출
                if decode_and_save_to_db(msg_text):
                    msg = f"✅ 처리 성공 (Update ID: {update_id})"
                    logger.info(msg)
                    print("-> [성공]")
                else:
                    msg = f"❌ 처리 실패 (Update ID: {update_id})"
                    logger.error(msg)
                    print("-> [실패]")
            else:
                msg = f"⏩ 데이터 형식 아님 (Update ID: {update_id})"
                logger.info(msg)
                print("-> [건너뜀]")
            
            if update_id > new_last_id:
                new_last_id = update_id

        # 3. 다음 실행을 위한 기준점 저장
        if new_last_id > last_id:
            set_config('last_telegram_update_id', new_last_id)
            msg = f"🚀 동기화 완료: 기준점이 {new_last_id}(으)로 갱신되었습니다."
            logger.info(msg)
            print(f"\n{msg}")
        else:
            msg = ">> 새로운 데이터가 없어 기준점을 유지합니다."
            logger.info(msg)
            print(f"\n{msg}")

    except Exception as e:
        msg = f"!!! [치명적 오류] 데이터 수신 중 예외 발생: {e}"
        logger.error(msg)
        print(msg)

def decode_and_save_to_db(msg_text):
    """이중 인코딩 데이터를 해독하여 DB에 적재 (Log & Print 완전 동기화)"""
    try:
        # 1. 1차 해독
        encoded_data = msg_text.replace("DATA:", "")
        decoded_json = base64.b64decode(encoded_data).decode('utf-8')
        payload_list = json.loads(decoded_json)
        
        total_items = len(payload_list)
        success_count = 0
        
        with get_list_db() as con:
            for item_b64 in payload_list:
                try:
                    # 2. 2차 해독
                    item_str = base64.b64decode(item_b64).decode('utf-8')
                    # 3. 객체 복원
                    item = ast.literal_eval(item_str)
                    
                    # 4. DB 적재
                    con.execute("""
                        INSERT OR IGNORE INTO TOON 
                        (TITLE, SUBTITLE, WEBTOON_SITE, WEBTOON_URL, WEBTOON_IMAGE, WEBTOON_IMAGE_NUMBER, TOTAL_COUNT) 
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (item[0], item[1], item[2], item[3], item[4], int(item[5]), int(item[7])))
                    success_count += 1
                    print(f"✅ 성공: {item[0]} > {item[1]}")
                    logging.info(f"SUCCESS: {item[0]} ({item[1]})")
                except Exception as e:
					error_msg = f"❌ 실패: {str(e)}"
                    print("-" * 50)
                    print(error_msg)
                    print(f"   데이터 샘플: {item_b64[:30]}...")
                    print("-" * 50)
            
                    logging.error(f"FAILED : {str(e)} | Data: {item_b64}")
            continue
                    continue
            con.commit()
        
        msg = f"📦 DB 적재 결과: {success_count}/{total_items}개 완료"
        logger.info(msg)
        print(f" ({success_count}/{total_items})", end="")
        return True if success_count > 0 else False

    except Exception as e:
        msg = f"!!! [디코딩 오류] 데이터 구조 파싱 실패: {e}"
        logger.error(msg)
        print(f"\n{msg}")
        return False
		
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