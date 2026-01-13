#-*- coding: utf-8 -*-
import os, sys, sqlite3, logging, asyncio, base64, requests, json, time, re, zipfile, shutil, platform
from flask import Blueprint, render_template, request, session, redirect, url_for
from bs4 import BeautifulSoup as bs
from datetime import datetime

# 기존 프로젝트 구조에서 불러오는 모듈 (환경에 맞게 유지)
# from pages.main_page import scheduler, logger 

# 로거 설정 (기존 로거가 없다면 활성화)
logger = logging.getLogger("WebtoonReceiver")

webtoon = Blueprint('webtoon', __name__, url_prefix='/webtoon')

# --- [경로 설정] ---
if platform.system() == 'Windows':
    at = os.path.splitdrive(os.getcwd())
    webtoondb = at[0] + '/data/db/webtoon_new.db'
    root_path = at[0] + '/data'
else:
    webtoondb = '/data/db/webtoon_new.db'
    root_path = '/data'

# --- [유틸리티 함수] ---
def cleanText(readData):
    text = re.sub('[-\\/:*?\"<>|]', '', readData).strip()
    return re.sub("\s{2,}", ' ', text)

def url_to_image(title, subtitle, webtoon_image, webtoon_number, gbun):
    header = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        req = requests.get(webtoon_image, headers=header, timeout=15)
        req.raise_for_status()
        
        parse_t = cleanText(title)
        parse_s = cleanText(subtitle)
        
        # 저장 경로: /data/webtoon/adult(또는 normal)/제목/회차/001.jpg
        dfolder = os.path.join(root_path, 'webtoon', gbun, parse_t, parse_s)
        if not os.path.exists(dfolder):
            os.makedirs(dfolder, exist_ok=True)
            
        fifi = os.path.join(dfolder, f"{webtoon_number}.jpg")
        
        with open(fifi, 'wb') as code:
            code.write(req.content)
        return '완료'
    except Exception as e:
        logger.error(f"이미지 다운로드 에러 ({title}): {e}")
        return '실패'

# --- [DB 저장 로직] ---
def add_c(title, subtitle, webtoon_site, webtoon_url, webtoon_image, webtoon_number, complete, gbun):
    # gbun에 따라 테이블 결정 (성인: TOON, 일반: TOON_NORMAL)
    db_table = 'TOON' if gbun == 'adult' else 'TOON_NORMAL'
    
    try:
        con = sqlite3.connect(webtoondb, timeout=60)
        con.execute(f"CREATE TABLE IF NOT EXISTS {db_table} (TITLE TEXT, SUBTITLE TEXT, WEBTOON_SITE TEXT, WEBTOON_URL TEXT, WEBTOON_IMAGE TEXT, WEBTOON_IMAGE_NUMBER TEXT, COMPLETE TEXT)")
        con.execute("PRAGMA journal_mode=WAL")
        
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        
        # 중복 체크 (이미지 주소, 제목, 회차가 같은지 확인)
        sql = f'SELECT * FROM {db_table} WHERE WEBTOON_IMAGE = ? AND TITLE = ? AND SUBTITLE = ?'
        cur.execute(sql, (webtoon_image, title, subtitle))
        row = cur.fetchone()
        
        if row:
            # 이미 존재하면 상태만 업데이트 (수정 사항 반영용)
            cur.execute(f'UPDATE {db_table} SET WEBTOON_IMAGE_NUMBER = ?, COMPLETE = ? WHERE WEBTOON_IMAGE = ?', 
                        (webtoon_number, complete, webtoon_image))
        else:
            # 신규 저장
            sql = f'INSERT INTO {db_table} (TITLE, SUBTITLE, WEBTOON_SITE, WEBTOON_URL, WEBTOON_IMAGE, WEBTOON_IMAGE_NUMBER, COMPLETE) VALUES (?, ?, ?, ?, ?, ?, ?)'
            cur.execute(sql, (title, subtitle, webtoon_site, webtoon_url, webtoon_image, webtoon_number, complete))
        
        con.commit()
    except Exception as e:
        logger.error(f"DB 저장 에러: {e}")
    finally:
        con.close()
    return '완료'

# --- [텔레그램 메시지 수신 및 파싱] ---
def tel_send_message(dummy_list):
    logger.info('텔레그램 채널에서 웹툰 정보를 가져옵니다.')
    
    now_num_path = os.path.join(root_path, 'now_num.json')
    last_num_path = os.path.join(root_path, 'last_num.json')
    
    # 마지막 번호 로드
    if os.path.isfile(last_num_path):
        with open(last_num_path, "r") as f: last_data = json.load(f)
    else: last_data = ["0"]

    with requests.Session() as s:
        url = 'https://t.me/s/webtoonalim'
        req = s.get(url)
        soup = bs(req.text, "html.parser")
        
        messages = soup.findAll("div", {"class": "tgme_widget_message_text"})
        all_msgs = soup.findAll("div", {"class": "tgme_widget_message"})
        
        if not all_msgs: return '메시지 없음'
        
        # 가장 최근 포스트 번호 추출
        real_now = int(all_msgs[-1]['data-post'].split('/')[-1])
        old_last = int(last_data[0])
        
        logger.info(f"최신 포스트: {real_now} / 마지막 확인: {old_last}")

        # 메시지 역순 처리 (최신 것부터)
        for msg_div in reversed(messages):
            raw_text = msg_div.text
            try:
                # 1. Base64 복호화
                decoded = base64.b64decode(raw_text).decode('utf-8')
                aac = decoded.split('\n\n')
                
                # 2. 데이터 매핑 (7필드 규격 대응)
                # Crawler: TITLE(0), SUBTITLE(1), SITE(2), URL(3), IMG(4), NUM(5), GBUN(6)
                if len(aac) >= 7:
                    title, subtitle, site, url_path, img, num, gbun = aac[:7]
                else:
                    # 필드가 부족할 경우 기본 성인으로 처리
                    title, subtitle, site, url_path, img, num = aac[:6]
                    gbun = 'adult'

                # 3. DB 저장 (add_c 호출)
                # 이미지 주소가 특정 도메인(.com 등)을 포함하면 완료(True) 처리, 아니면 False
                complete_status = "True" if ".com" in img else "False"
                
                if 'loading.svg' not in img:
                    add_c(title, subtitle, site, url_path, img, num, complete_status, gbun)

            except Exception as e:
                continue
                
    # 작업 완료 후 마지막 번호 갱신
    with open(last_num_path, 'w') as f:
        json.dump([str(real_now)], f)
        
    logger.info('웹툰 DB 동기화 완료.')
    return '완료'

# --- [Flask Routes] ---
@webtoon.route('/')
def index():
    if not session.get('logFlag'): return redirect(url_for('main.index'))
    return render_template('webtoon.html')

@webtoon.route('webtoon_list', methods=['GET'])
def start_sync_job():
    # 스케줄러 등록 로직 (사용자 기존 코드 유지)
    start_time = request.args.get('start_time')
    try:
        from pages.main_page import scheduler
        job_id = 'webtoon_sync_job'
        scheduler.add_job(tel_send_message, 'cron', minute=start_time.split(' ')[0], hour=start_time.split(' ')[1], id=job_id, args=[[]])
        logger.info(f"동기화 스케줄러 등록 완료: {job_id}")
    except:
        pass
    return redirect(url_for('webtoon.index'))

# ... (나머지 index_list, down 함수 등 기존 코드 유지) ...