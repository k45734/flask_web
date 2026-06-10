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
    con.execute("CREATE TABLE IF NOT EXISTS TOON (TITLE TEXT, SUBTITLE TEXT, WEBTOON_IMAGE TEXT, WEBTOON_IMAGE_NUMBER INTEGER, TOTAL_COUNT INTEGER)")
    con.execute("CREATE TABLE IF NOT EXISTS TOON_NORMAL (TITLE TEXT, SUBTITLE TEXT, WEBTOON_IMAGE TEXT, WEBTOON_IMAGE_NUMBER INTEGER, TOTAL_COUNT INTEGER)")
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
    해독된 데이터의 제목과 회차명을 출력하며 DB(adult/normal)에 정확한 규격으로 적재합니다.
    중복 시 새 이미지 주소로 실시간 갱신하며, 실제 도메인 변경 시 알림 로그를 출력합니다.
    """
    try:
        # 1. 데이터 복원 (압축 해제 또는 Base64 디코딩)
        if is_compressed:
            encoded_data = msg_text.replace("DATA_Z:", "")
            raw_bytes = base64.b64decode(encoded_data)
            json_str = zlib.decompress(raw_bytes).decode('utf-8')
            payload_list = json.loads(json_str)
        else:
            encoded_data = msg_text.replace("DATA:", "")
            json_str = base64.b64decode(encoded_data).decode('utf-8')
            payload_list = json.loads(json_str)
        
        total_count = len(payload_list)
        success_count = 0
        
        log_and_print(f"      🔍 패키지 내부 데이터 해독 중 (총 {total_count}개 항목)...")

        # 도메인 변경 체크 기록용 셋
        cleared_episodes = set()

        with get_list_db() as con:
            for item_data in payload_list:
                try:
                    # 2. 항목별 2차 해독
                    if isinstance(item_data, str):
                        item_raw = base64.b64decode(item_data).decode('utf-8')
                        item = ast.literal_eval(item_raw)
                    else:
                        item = item_data
                    
                    # 3. [서버 전송 규격 매핑 교정]
                    title = item[0]
                    subtitle = item[1]
                    img_url = item[2] if len(item) > 2 else "" # 2번째 인덱스가 실제 이미지 URL (src)
                    
                    # [방어코드] img_url이 정상적인 주소 형태(http)가 아니면 잘못된 패킷이므로 스킵
                    if not isinstance(img_url, str) or not img_url.startswith('http'):
                        logger.error(f"      ❌ 잘못된 이미지 URL 스킵 처리: {img_url} (값 오류)")
                        continue

                    # [방어] img_num(3번) NoneType 및 타입 안정성 확보
                    raw_img_num = item[3] if len(item) > 3 else 1
                    img_num = int(raw_img_num) if raw_img_num is not None else 1
                    
                    # [방어] total_img_count(4번) NoneType 및 타입 안정성 확보
                    raw_total_count = item[4] if len(item) > 4 else 0
                    total_img_count = int(raw_total_count) if raw_total_count is not None else 0
                    
                    # 4. 성인(adult) / 일반(normal) 테이블 결정
                    target_table = 'TOON' 
                    if len(item) > 8 and item[8] is not None:
                        target_table = 'TOON' if item[8] == 'adult' else 'TOON_NORMAL'

                    # [안전장치] 첫 번째 이미지 수신 시, 기존 주소와 대조하여 도메인 변경 여부 확인 및 로그 출력
                    ep_key = (title, subtitle, target_table)
                    if img_num == 1 and ep_key not in cleared_episodes:
                        # 1. 기존 DB에 저장되어 있던 1번 이미지의 주소를 조회
                        old_row = con.execute(f"""
                            SELECT WEBTOON_IMAGE FROM {target_table} 
                            WHERE TITLE=? AND SUBTITLE=? AND WEBTOON_IMAGE_NUMBER=1
                        """, (title, subtitle)).fetchone()
                        
                        # 2. 기존에 주소가 있었는데, 새로 들어온 주소와 '실제 도메인'이 다른 경우에만 감지
                        if old_row and old_row[0]:
                            # 가변 토큰(?token=...) 제외하고 순수 주소 앞부분만 비교
                            old_pure_url = old_row[0].split('?')[0].strip()
                            new_pure_url = img_url.split('?')[0].strip()

                            if old_pure_url != new_pure_url:
                                log_and_print(f"🔄 [{target_table}] {title} > {subtitle} : 최신 이미지 도메인(주소) 업데이트 완료")
                        
                        # 1번 이미지를 만났다면 검사가 끝났으므로 이번 동기화 주기에서 제외하도록 중복 처리 등록
                        cleared_episodes.add(ep_key)

                    # 5. DB Insert 실행 (중복 시 새 이미지 주소로 실시간 갱신)
                    con.execute(f"""
                        INSERT INTO {target_table} 
                        (TITLE, SUBTITLE, WEBTOON_IMAGE, WEBTOON_IMAGE_NUMBER, TOTAL_COUNT) 
                        VALUES (?, ?, ?, ?, ?)
                        ON CONFLICT(TITLE, SUBTITLE, WEBTOON_IMAGE_NUMBER) 
                        DO UPDATE SET WEBTOON_IMAGE = EXCLUDED.WEBTOON_IMAGE
                    """, (title, subtitle, img_url, img_num, total_img_count))
                    
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
def sanitize_filename(name):
    # 1. 대괄호 [ ] 만 찾아내서 삭제합니다 (내용은 그대로 유지)
    name = re.sub(r'[\[\]]', '', name)
    
    # 2. 파일명 금지 문자들을 언더바(_)로 교체합니다
    name = re.sub(r'[\\/*?:"<>|]', "_", name)
    
    # 3. 공백이 여러 개 겹치면 하나로 줄이고, 앞뒤 공백을 자릅니다
    return re.sub(r'\s+', ' ', name).strip()
	
def format_subtitle(sub):
    # 정규식으로 숫자 찾기
    match = re.search(r'(\d+)', sub)
    if match:
        number = match.group(1)
        # 숫자를 3자리로 변환 (예: 1 -> 001)
        return sub.replace(number, f"{int(number):03d}")
    return sub	
# --- [4. 강화된 다운로드 엔진] ---
def down(compress, cbz, alldown, title_filter, sub_filter, gbun):
    logger.info(f"== [{gbun}] 다운로드 엔진 가동 ==")
    
    total, used, free = shutil.disk_usage(WEBTOON_PATH)
    free_gb = free // (2**30)
    
    if free_gb < 2:
        log_and_print(f"!!! [중단] 디스크 공간 부족: {free_gb}GB 남음", "error")
        return

    db_table = 'TOON' if gbun == 'adult' else 'TOON_NORMAL'
    
    try:
        target_gbun_path = os.path.join(WEBTOON_PATH, gbun)
        os.makedirs(target_gbun_path, exist_ok=True)

        with get_list_db() as con_l:
            con_l.execute(f"ATTACH DATABASE '{STATUS_DB}' AS s_db")
            query = f"SELECT a.TITLE, a.SUBTITLE FROM {db_table} a LEFT JOIN s_db.STATUS s ON a.TITLE = s.TITLE AND a.SUBTITLE = s.SUBTITLE WHERE (s.COMPLETE IS NULL OR s.COMPLETE != 'True') AND a.TOTAL_COUNT > 0"
            if title_filter: 
                query += f" AND a.TITLE = '{title_filter}'"
            query += " GROUP BY a.TITLE, a.SUBTITLE"
            
            targets = con_l.execute(query).fetchall()
            log_and_print(f">> 분석 결과: {len(targets)}건 대기 중")

            for t_title, t_sub in targets:
                # DB 검색용 원본 이름 보존
                raw_title = t_title
                raw_sub = t_sub

                # 파일/폴더 생성용 정제 이름
                t_title_clean = sanitize_filename(t_title.replace(" ", "").strip())
                t_sub_clean = sanitize_filename(t_sub.replace(" ", "").strip())
                
                match = re.search(r'(\d+)', t_sub_clean)
                formatted_sub = t_sub_clean
                if match:
                    number = match.group(1)
                    formatted_sub = t_sub_clean.replace(number, f"{int(number):03d}")

                try:
                    log_and_print(f"작업 시작 : {t_title_clean} - {formatted_sub}")
                    
                    # 쿼리 조건절에는 정제 전 원본 변수인 raw_title, raw_sub 매핑
                    img_list = con_l.execute(f"SELECT DISTINCT WEBTOON_IMAGE, WEBTOON_IMAGE_NUMBER FROM {db_table} WHERE TITLE=? AND SUBTITLE=? ORDER BY WEBTOON_IMAGE_NUMBER ASC", (raw_title, raw_sub)).fetchall()
                    
                    cur_c = len(img_list)
                    tar_c = cur_c
                    
                    log_and_print(f" -> [{gbun.upper()}] {t_title} {formatted_sub} ({cur_c}/{tar_c})")

                    if cur_c > 0:
                        f_path = os.path.join(target_gbun_path, t_title_clean, formatted_sub)
                        if not os.path.exists(f_path):
                            os.makedirs(f_path, exist_ok=True)
                        
                        # 이미지 다운로드
                        for img_url, img_num in img_list:
                            img_file = os.path.join(f_path, f"{img_num:03d}.jpg")
                            success = False
                            for attempt in range(3):
                                if not os.path.exists(img_file) or os.path.getsize(img_file) < 1:
                                    try:
                                        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
                                        r = requests.get(img_url, timeout=15, headers=headers)
                                        if r.status_code == 200 and len(r.content) > 0:
                                            with open(img_file, 'wb') as f: 
                                                f.write(r.content)
                                            success = True
                                            break
                                        else:
                                            log_and_print(f"  - [{gbun}] {t_title} - {formatted_sub} [시도 {attempt}/3] 다운로드 실패 ({img_num:03d}.jpg): HTTP {r.status_code}")
                                            time.sleep(1)
                                    except Exception as e: 
                                        log_and_print(f"  - [{gbun}] {t_title} - {formatted_sub} [시도 {attempt}/3] 에러 발생 ({img_num:03d}.jpg): {e}")
                                        time.sleep(1)
                                        continue
                                else:
                                    success = True
                                    break
                            if not success:
                                log_and_print(f"!!! [최종 실패] 이미지 URL 확인 필요: {img_num:03d}.jpg")
                                log_and_print(f" [{gbun}] {t_title} - {formatted_sub} URL: {img_url}", "error")

                        actual_files = [f for f in os.listdir(f_path) if os.path.isfile(os.path.join(f_path, f))]
                        if len(actual_files) < tar_c:
                            log_and_print(f"-> [{gbun}] {t_title} - {formatted_sub} [미달] {len(actual_files)}장 수집됨")
                            continue
                        
                        # 압축 전, 모든 파일의 쓰기 완료를 보장하는 동기화 로직
                        for file in actual_files:
                            fp = os.path.join(f_path, file)
                            try:
                                with open(fp, 'ab') as f: 
                                    f.flush()
                                    os.fsync(f.fileno()) 
                            except Exception as e:
                                log_and_print(f"파일 동기화 중 오류: {file} - {e}")
                        time.sleep(2) # 파일 안정화를 위한 미세 쿨다운
                        
                        # --- [개선된 압축 및 자동 검수/재시도 블록] ---
                        is_compression_success = True # 압축 미사용 유저 혹은 압축 성공 판정용 플래그
                        
                        if str(compress) == '1':
                            ext = ".cbz" if str(cbz) == '1' else ".zip"
                            parent_dir = os.path.dirname(f_path)
                            z_name = os.path.join(parent_dir, f"{formatted_sub}{ext}")
                            temp_z_name = z_name + ".tmp" 
                            
                            max_retries = 3
                            is_valid_zip = False
                            
                            for retry_attempt in range(1, max_retries + 1):
                                if os.path.exists(temp_z_name):
                                    try: os.remove(temp_z_name)
                                    except: pass

                                try:
                                    log_and_print(f"   📦 [{gbun}] 압축 진행 중... (시도 {retry_attempt}/{max_retries})")
                                    
                                    # 표준 압축 규격(ZIP_DEFLATED) 가동 및 파일 내부 최상위 배치(arcname)
                                    with zipfile.ZipFile(temp_z_name, 'w', zipfile.ZIP_DEFLATED) as z:
                                        for file in sorted(actual_files):
                                            fp = os.path.join(f_path, file)
                                            if os.path.exists(fp):
                                                if os.path.getsize(fp) > 0:
                                                    z.write(fp, arcname=file)
                                                else:
                                                    logger.error(f"⚠️ [{gbun}] {t_title} - {file} 파일이 0바이트라 압축에서 제외됨")
                                    
                                    # 압축 무결성 검수 (testzip)
                                    if os.path.exists(temp_z_name) and os.path.getsize(temp_z_name) > 0:
                                        with zipfile.ZipFile(temp_z_name, 'r') as verify_z:
                                            bad_file = verify_z.testzip()
                                            if bad_file is None:
                                                is_valid_zip = True
                                                break
                                            else:
                                                log_and_print(f"❌ [검수 실패] {t_title} - {formatted_sub} 내부 손상 발견: {bad_file} -> 재시도", "error")
                                                
                                except Exception as e:
                                    log_and_print(f"⚠️ [압축 에러] {t_title} - {formatted_sub} (시도 {retry_attempt} 실패): {e}", "error")
                                
                                time.sleep(0.5) # 디스크 쿨다운

                            if is_valid_zip:
                                if os.path.exists(z_name):
                                    try: os.remove(z_name)
                                    except: pass
                            
                                # 임시 파일을 최종 본명(.cbz)으로 변경
                                shutil.move(temp_z_name, z_name)
                                
                                # 💡 [초강력 방어 가드] 최종 파일(.cbz)이 디스크에 온전히 존재하고 정상 용량일 때만 원본 폴더 정리!
                                if os.path.exists(z_name) and os.path.getsize(z_name) > 0:
                                    shutil.rmtree(f_path, ignore_errors=True)
                                    log_and_print(f"-> [{gbun}] {t_title} - {formatted_sub} 무결성 검수 통과 및 압축 완료 (원본 폴더 정리)")
                                else:
                                    log_and_print(f"⚠️ [경고] {t_title} - {formatted_sub} 최종 파일 유실 감지! 원본 안전을 위해 폴더를 삭제하지 않습니다.", "error")
                                    is_compression_success = False # DB 등록 보류
                            else:
                                log_and_print(f"💥 [치명적 오류] {t_title} - {formatted_sub} 총 {max_retries}회 압축 시도했으나 실패. 다음 주기에 재시도합니다.", "error")
                                if os.path.exists(temp_z_name):
                                    try: os.remove(temp_z_name)
                                    except: pass
                                is_compression_success = False # DB 등록을 막기 위해 플래그 하락
                        
                        # 압축이 필요 없거나, 압축 검수가 완벽히 성공했을 때만 완료 처리(STATUS DB) 등록
                        if is_compression_success:
                            with get_status_db() as con_s:
                                con_s.execute("INSERT OR REPLACE INTO STATUS (TITLE, SUBTITLE, COMPLETE) VALUES (?,?,?)", (raw_title, raw_sub, 'True'))
                                con_s.commit()
                            log_and_print(f"-> [{gbun}] {t_title} - {formatted_sub} DB등록 완료")
                        else:
                            log_and_print(f"-> [{gbun}] {t_title} - {formatted_sub} 압축 에러/유실로 인해 이번 주기 DB 완료 등록 보류")
                        
                except Exception as loop_e:
                    logger.error(f"회차 처리 중 오류 [{gbun}] {t_title} - {t_sub} : {loop_e}")

    except Exception as e:
        logger.error(f"Down Error: {e}")
    logger.info(f"== [{gbun}] 다운로드 엔진 완료 ==")

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
                COUNT(DISTINCT WEBTOON_IMAGE_NUMBER) as CURRENT_COUNT 
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