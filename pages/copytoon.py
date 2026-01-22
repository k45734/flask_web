#-*- coding: utf-8 -*-
import os, sys, sqlite3, logging, asyncio, base64, requests, json, time, re, zipfile, shutil, platform
from flask import Blueprint, render_template, request, session, redirect, url_for
from bs4 import BeautifulSoup as bs
from datetime import datetime
from apscheduler.triggers.cron import CronTrigger

# 페이징 및 스케줄러 라이브러리 예외 처리
try:
    from flask_paginate import Pagination, get_page_args
except ImportError:
    os.system('pip install flask_paginate')
    from flask_paginate import Pagination, get_page_args

# 프로젝트 로거 및 스케줄러 연결
try:
    from pages.main_page import scheduler, logger
except:
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("WebtoonReceiver")

webtoon = Blueprint('webtoon', __name__, url_prefix='/webtoon')

# --- [1. 경로 및 DB 설정] ---
if platform.system() == 'Windows':
    at = os.path.splitdrive(os.getcwd())
    webtoondb = at[0] + '/data/db/webtoon_new.db'
    root = at[0] + '/data'
else:
    webtoondb = '/data/db/webtoon_new.db'
    root = '/data'

def get_db_con():
    con = sqlite3.connect(webtoondb, timeout=60)
    con.execute("PRAGMA journal_mode=WAL")
    return con

# --- [2. 데이터 수신 및 DB 저장] ---
def add_c(title, subtitle, site, url, img, num, complete, gbun, total_count):
    db_table = 'TOON' if gbun == 'adult' else 'TOON_NORMAL'
    con = get_db_con()
    
    # 테이블 생성 및 TOTAL_COUNT 컬럼 자동 추가 (기존 데이터 보존)
    con.execute(f"""CREATE TABLE IF NOT EXISTS {db_table} 
                    (TITLE TEXT, SUBTITLE TEXT, WEBTOON_SITE TEXT, WEBTOON_URL TEXT, 
                     WEBTOON_IMAGE TEXT, WEBTOON_IMAGE_NUMBER TEXT, COMPLETE TEXT)""")
    try:
        con.execute(f"ALTER TABLE {db_table} ADD COLUMN TOTAL_COUNT INTEGER DEFAULT 0")
    except:
        pass
        
    cur = con.cursor()
    # 중복 확인 후 삽입
    cur.execute(f'SELECT 1 FROM {db_table} WHERE WEBTOON_IMAGE = ? AND TITLE = ? AND SUBTITLE = ?', (img, title, subtitle))
    if not cur.fetchone():
        cur.execute(f'INSERT INTO {db_table} (TITLE, SUBTITLE, WEBTOON_SITE, WEBTOON_URL, WEBTOON_IMAGE, WEBTOON_IMAGE_NUMBER, COMPLETE, TOTAL_COUNT) VALUES (?, ?, ?, ?, ?, ?, ?, ?)', 
                    (title, subtitle, site, url, img, num, complete, total_count))
        con.commit()
        msg = f">>> [DB저장] {title} - {subtitle} ({num}/{total_count})"
        print(msg); logger.info(msg)
    con.close()

def tel_send_message(raw_base64_text):
    """서버에서 보낸 base64 메시지를 수신하여 파싱 (NoneType 에러 방지 포함)"""
    # [수정] 인자가 None이거나 비어있는 경우 즉시 리턴하여 에러 방지
    if raw_base64_text is None or not raw_base64_text:
        return

    try:
        # 인자가 bytes가 아니면 인코딩 시도
        if isinstance(raw_base64_text, str):
            raw_base64_text = raw_base64_text.encode('ascii')
            
        decoded = base64.b64decode(raw_base64_text).decode('utf-8')
        aac = decoded.split('\n\n')
        
        # 순서: 0:TITLE, 1:SUBTITLE, 2:SITE, 3:URL, 4:IMAGE, 5:NUM, 6:COMPLETE, 7:TOTAL_COUNT, 8:GBUN
        if len(aac) >= 9:
            add_c(aac[0], aac[1], aac[2], aac[3], aac[4], aac[5], aac[6], aac[8], aac[7])
            print(aac[0], aac[1], aac[2], aac[3], aac[4], aac[5], aac[6], aac[8], aac[7]); logger.error(aac[0], aac[1], aac[2], aac[3], aac[4], aac[5], aac[6], aac[8], aac[7])
    except Exception as e:
        # 에러 발생 시 로그에 상세 출력
        err_msg = f"!!! [파싱오류 상세]: {e} (입력값: {raw_base64_text})"
        print(err_msg); logger.error(err_msg)

# --- [3. 다운로드 로직 (대기 기능)] ---
def down(compress, cbz, alldown, title, subtitle, gbun):
    db_table = 'TOON' if gbun == 'adult' else 'TOON_NORMAL'
    con = get_db_con()
    cur = con.cursor()
    
    msg = f"=== [{gbun.upper()}] 다운로드 프로세스 가동 ==="
    print(msg); logger.info(msg)
    
    # 수집 완료되지 않은 회차 목록 추출
    sql = f"SELECT TITLE, SUBTITLE, TOTAL_COUNT FROM {db_table} WHERE COMPLETE = 'False' GROUP BY TITLE, SUBTITLE"
    cur.execute(sql)
    targets = cur.fetchall()
    
    if not targets:
        print("    > 대기 목록이 없습니다."); con.close(); return

    for t_title, t_sub, t_total in targets:
        cur.execute(f"SELECT COUNT(*) FROM {db_table} WHERE TITLE=? AND SUBTITLE=?", (t_title, t_sub))
        current_cnt = cur.fetchone()[0]
        
        status_msg = f"  - [{t_title}] {t_sub}: 현황({current_cnt}) / 목표({t_total})"
        print(status_msg); logger.info(status_msg)
        
        # 서버에서 알려준 개수와 내 DB 장수가 다르면 대기
        if current_cnt < int(t_total):
            print(f"    ! [대기] {t_total - current_cnt}장이 더 필요합니다."); continue

        print(f"    √ [진행] {t_total}장 전량 확인 완료. 파일 저장 시작.")
        
        folder_path = os.path.join(root, "download", t_title, t_sub)
        os.makedirs(folder_path, exist_ok=True)
        
        cur.execute(f'SELECT WEBTOON_IMAGE, WEBTOON_IMAGE_NUMBER FROM {db_table} WHERE TITLE=? AND SUBTITLE=? ORDER BY WEBTOON_IMAGE_NUMBER ASC', (t_title, t_sub))
        img_list = cur.fetchall()
        
        for img_url, img_num in img_list:
            try:
                file_path = os.path.join(folder_path, f"{img_num}.jpg")
                if not os.path.exists(file_path):
                    res = requests.get(img_url, timeout=20)
                    if res.status_code == 200:
                        with open(file_path, 'wb') as f:
                            f.write(res.content)
            except Exception as e:
                print(f"    ! [다운로드 실패] {img_num}.jpg : {e}")

        # 처리 완료 기록
        cur.execute(f"UPDATE {db_table} SET COMPLETE = 'True' WHERE TITLE=? AND SUBTITLE=?", (t_title, t_sub))
        con.commit()
        print(f"    √ [완료] {t_title} {t_sub} 처리 성공")
        
        if compress == '1':
            make_zip(folder_path, cbz)

    con.close()

def make_zip(folder_path, is_cbz):
    ext = ".cbz" if is_cbz == '1' else ".zip"
    zip_name = folder_path + ext
    with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as z:
        for file in os.listdir(folder_path):
            z.write(os.path.join(folder_path, file), file)
    shutil.rmtree(folder_path)
	
# --- [3. Flask Routes: 목록 및 통계] ---
@webtoon.route('/')
def index():
    """BuildError 해결을 위한 메인 라우트"""
    if not session.get('logFlag'): return redirect(url_for('main.index'))
    return render_template('webtoon.html')
	
@webtoon.route('index_list', methods=["GET"])
def index_list():
    if not session.get('logFlag'): return redirect(url_for('main.index'))
    
    gbun = request.args.get('gbun', 'adult')
    search_keyword = request.args.get('search', '').strip()
    db_name = 'TOON' if gbun == 'adult' else 'TOON_NORMAL'
    
    # [수정] 페이지 번호를 명시적으로 가져옵니다.
    per_page = 10
    page = request.args.get('page', type=int, default=1) # 이 부분이 핵심입니다.
    offset = (page - 1) * per_page
    
    con = get_db_con()
    cur = con.cursor()
    
    try:
        # 검색 조건 설정
        where_clause = ""
        params = []
        if search_keyword:
            where_clause = "WHERE TITLE LIKE ?"
            params.append(f"%{search_keyword}%")

        # 개수 조회 (이전과 동일)
        count_sql = f"SELECT COUNT(*) FROM (SELECT 1 FROM {db_name} {where_clause} GROUP BY TITLE, SUBTITLE)"
        cur.execute(count_sql, params)
        total = cur.fetchone()[0]
        logger.info(f"--- 검색어: [{search_keyword}] / 검색된 총 개수: {total} ---")

        # 데이터 조회 (이전과 동일)
        data_sql = f"SELECT TITLE, SUBTITLE FROM {db_name} {where_clause} GROUP BY TITLE, SUBTITLE ORDER BY TITLE ASC, SUBTITLE DESC LIMIT ? OFFSET ?"
        cur.execute(data_sql, params + [per_page, offset])
        wow = cur.fetchall()
        
    except Exception as e:
        logger.error(f"DB 오류: {e}")
        wow, total = [], 0
    finally:
        con.close()

    # [수정] Pagination 객체 생성 시 bs_version을 4로 유지하고 인자를 명확히 전달
    pagination = Pagination(
        page=page, 
        total=total, 
        per_page=per_page, 
        bs_version=4, # 4로 설정되어 있는지 확인
        search=True if search_keyword else False,
        record_name='wow',
        add_args={
            'gbun': gbun, 
            'search': search_keyword
        }
    )
    
    return render_template('webtoon_list.html', gbun=gbun, wow=wow, pagination=pagination, search=search_keyword)
	
@webtoon.route('alim_list', methods=["GET"])
def alim_list():
    if not session.get('logFlag'): return redirect(url_for('main.index'))
    def stats(table):
        con = get_db_con()
        cur = con.cursor()
        cur.execute(f'SELECT count(*) FROM (SELECT TITLE FROM {table} GROUP BY TITLE)')
        t_cnt = cur.fetchone()[0]
        cur.execute(f'SELECT count(*) FROM {table} WHERE COMPLETE = "False"')
        f_cnt = cur.fetchone()[0]
        cur.execute(f'SELECT count(*) FROM {table} WHERE COMPLETE = "True"')
        tr_cnt = cur.fetchone()[0]
        con.close()
        return {'TOTAL': t_cnt, 'False': f_cnt, 'True': tr_cnt}
    return render_template('webtoon_alim_list.html', rows=[stats('TOON')], rows2=[stats('TOON_NORMAL')])

# --- [4. Flask Routes: 스케줄러 (로그 강화)] ---

@webtoon.route('webtoon_list', methods=['GET'])
def start_sync_route():
    if not session.get('logFlag'): return redirect(url_for('main.index'))
    start_time = request.args.get('start_time')
    try:
        scheduler.add_job(tel_send_message, trigger=CronTrigger.from_crontab(start_time), id='webtoon_list_sync', args=[None], replace_existing=True)
        logger.info(f"[스케줄러] 리스트 동기화가 {start_time} 주기로 예약되었습니다.")
    except Exception as e: logger.error(f"[스케줄러] 동기화 예약 실패: {e}")
    return redirect(url_for('webtoon.index'))

@webtoon.route('webtoon_down', methods=['GET'])
def start_down_route():
    if not session.get('logFlag'): return redirect(url_for('main.index'))
    start_time = request.args.get('start_time')
    gbun = request.args.get('gbun', 'adult')
    try:
        scheduler.add_job(down, trigger=CronTrigger.from_crontab(start_time), id=f'webtoon_auto_down_{gbun}', 
                          args=[request.args.get('compress','1'), request.args.get('cbz','1'), 'True', None, None, gbun], replace_existing=True)
        logger.info(f"[스케줄러] {gbun} 자동 다운로드가 {start_time} 주기로 예약되었습니다.")
    except Exception as e: logger.error(f"[스케줄러] 다운로드 예약 실패: {e}")
    return redirect(url_for('webtoon.index'))

@webtoon.route("now", methods=["GET"])
def now_down():
    if not session.get('logFlag'): return redirect(url_for('main.index'))
    logger.info("[수동실행] 사용자가 즉시 다운로드를 요청했습니다.")
    down(request.args.get('compress'), request.args.get('cbz'), 'True', None, None, request.args.get('gbun'))
    return redirect(url_for('webtoon.index'))

@webtoon.route('db_list_reset')
def db_list_reset():
    set_config('last_webtoon_id', '0')
    logger.info("[리셋] 동기화 추적 ID를 0으로 초기화했습니다.")
    return redirect(url_for('webtoon.index'))