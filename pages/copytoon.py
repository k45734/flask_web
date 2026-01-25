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
    logger.info("== [완전체] 최신글 자동 감지 & 역주행 엔진 가동 ==")
    logger.info("==================================================")
    print("\n[알림] 전수 조사를 위한 최신 ID 감지를 시작합니다.")

    # 1. 진짜 최신 ID 자동 감지 (대문 페이지 접속)
    try:
        # 파라미터 없이 접속하여 현재 채널의 가장 최신글들을 가져옵니다.
        init_req = requests.get('https://t.me/s/webtoonalim', timeout=15)
        init_soup = bs(init_req.text, "html.parser")
        init_messages = init_soup.findAll("div", {"class": "tgme_widget_message"})
        
        if not init_messages:
            logger.error("[중단] 텔레그램 채널 메시지를 로드할 수 없습니다.")
            print("!! 채널 접속 실패. 인터넷 연결이나 URL을 확인하세요.")
            return

        # 페이지 내에서 가장 큰 숫자가 현재의 진짜 최신 ID입니다.
        real_latest_id = max([int(m['data-post'].split('/')[-1]) for m in init_messages])
        logger.info(f"[감지] 텔레그램 서버 최신 ID: {real_latest_id}")
        print(f">> 실시간 최신글 번호 감지 성공: {real_latest_id}번")
        
    except Exception as e:
        logger.error(f"!!! 최신 ID 감지 중 치명적 오류: {e}")
        print(f"!!! 최신 번호를 알아낼 수 없어 수집을 중단합니다: {e}")
        return

    # 2. 수집 시작점 설정
    # DB에 기록된 마지막 수집 지점이 있으면 거기서부터, 없으면 방금 찾은 최신 ID부터 시작합니다.
    current_search_id = int(get_config('last_webtoon_id') or real_latest_id)
    print(f">> 수집 시작 지점: {current_search_id}번 (과거 방향으로 역주행)")

    is_continue = True
    total_new_count = 0
    page_count = 0

    while is_continue:
        page_count += 1
        # [핵심] before 파라미터로 search_id 이전의 과거 데이터 20~25개를 강제 호출
        url = f'https://t.me/s/webtoonalim?before={current_search_id}'
        
        logger.info(f"[역주행] {page_count}페이지 호출 (기준 ID: {current_search_id})")
        print(f"\n--- {page_count}번 페이지 추적 중 ({current_search_id}번 이전) ---")
        
        try:
            req = requests.get(url, timeout=15)
            soup = bs(req.text, "html.parser")
            messages = soup.findAll("div", {"class": "tgme_widget_message"})
            
            if not messages:
                print("!! 더 이상 읽을 메시지가 없습니다. 역주행을 종료합니다.")
                break

            new_data_dict = {'TOON': {}, 'TOON_NORMAL': {}}
            processed_ids = []

            # 페이지 내 메시지를 최신순(뒤에서부터)으로 분석하여 효율 극대화
            for m in reversed(messages):
                try:
                    pid = int(m['data-post'].split('/')[-1])
                    processed_ids.append(pid)
                    
                    txt = m.find("div", {"class": "tgme_widget_message_text"})
                    if not txt: continue
                    
                    # 데이터 복호화 및 분리
                    dec = base64.b64decode(txt.get_text(strip=True).encode('ascii')).decode('utf-8')
                    aac = dec.split('\n\n')

                    # [신의 필터] 규격 검사: 총 장수(aac[7]) 정보가 없으면 구형 데이터로 판단하고 즉시 멈춤
                    if len(aac) < 8 or not aac[7].strip().isdigit():
                        logger.warning(f"[규격미달] ID:{pid} 에서 구형 포맷 발견. 수집 종료.")
                        print(f"[*] ID:{pid}: 더 이상 최신 규격이 아닙니다. 여기서 역주행을 중단합니다.")
                        is_continue = False
                        break

                    # 데이터 분류 및 저장 준비
                    gbun = aac[8] if len(aac) >= 9 else 'adult'
                    db_t = 'TOON' if gbun == 'adult' else 'TOON_NORMAL'
                    key = (aac[0], aac[1], int(aac[5]))
                    
                    # (제목, 부제목, 사이트, URL, 이미지, 회차, 총장수) 순서로 저장
                    new_data_dict[db_t][key] = (aac[0], aac[1], aac[2], aac[3], aac[4], int(aac[5]), int(aac[7]))
                    
                    print(f" -> [수집성공] ID:{pid} | {aac[0]} ({aac[5]}/{aac[7]}장)")
                except: continue

            # DB 저장 (페이지 단위로 즉시 반영)
            with get_list_db() as con:
                added_page_count = 0
                for db_t in ['TOON', 'TOON_NORMAL']:
                    data_list = list(new_data_dict[db_t].values())
                    if not data_list: continue
                    # IGNORE를 사용하여 이미 수집된 최신 데이터는 건드리지 않고 비어있는 과거만 채움
                    con.executemany(f"INSERT OR IGNORE INTO {db_t} VALUES (?,?,?,?,?,?,?)", data_list)
                    added_page_count += len(data_list)
                con.commit()
                if added_page_count > 0:
                    print(f"== DB에 {added_page_count}개의 새로운 데이터를 안전하게 저장했습니다. ==")

            # 다음 구간 설정을 위해 이번 페이지에서 가장 낮은 ID를 찾음
            if processed_ids:
                oldest_id = min(processed_ids)
                current_search_id = oldest_id # 기준점을 낮춰서 더 과거로 전진
                total_new_count += len(processed_ids)
                
                # 진행 상황 업데이트 및 설정 저장
                set_config('last_webtoon_id', current_search_id)
                print(f">> 현재 {oldest_id}번까지 역주행 완료... (계속 내려가는 중)")
                
                if oldest_id <= 1:
                    print(">> 텔레그램 1번 메시지에 도달했습니다.")
                    is_continue = False
                
                time.sleep(0.5) # 서버 부하 방지
            else:
                is_continue = False
                
        except Exception as e:
            logger.error(f"!!! 수집 루프 중 치명적 에러: {e}")
            print(f"!!! 시스템 오류로 인해 중단됨: {e}")
            break

    print("\n" + "="*50)
    logger.info(f"== [전수 조사 완료] 총 {total_new_count}개 검증 완료 (최종 위치: {current_search_id}) ==")
    print(f"[완료] 역주행 수집이 성공적으로 끝났습니다.")
    print(f"최종적으로 {current_search_id}번까지 훑었습니다.")
    print("="*50 + "\n")

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