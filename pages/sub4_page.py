import os, platform, sqlite3
from flask import Blueprint, render_template, request, session, redirect, url_for, send_file
try:
    from openpyxl import Workbook
except ImportError:
    os.system('pip install openpyxl')
    from openpyxl import Workbook

bp4 = Blueprint('sub4', __name__, url_prefix='/sub4')

# DB 경로 설정
if platform.system() == 'Windows':
    at = os.path.splitdrive(os.getcwd())
    sub4db = at[0] + '/data/db/shop.db'
    sub4dbl = at[0] + '/data/db'
else:
    sub4db = '/data/db/shop.db'
    sub4dbl = '/data/db'

def get_db_con():
    """데이터베이스 연결 및 설정 최적화"""
    con = sqlite3.connect(sub4db, timeout=60)
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA synchronous=NORMAL")
    con.row_factory = sqlite3.Row
    return con

@bp4.route('/')
@bp4.route('/index')
def second():
    """재고 목록 및 상품별 요약 대시보드 조회"""
    if not session.get('logFlag'):
        return redirect(url_for('main.index'))
    
    con = get_db_con()
    con.execute('CREATE TABLE IF NOT EXISTS shop (idx integer primary key autoincrement, MY_DATE TEXT, PRODUCT_NAME TEXT, RECEIVING TEXT, SHIPPING TEXT, TOTAL TEXT)')
    
    cur = con.cursor()
    
    # 1. 전체 입출고 내역 조회 (최신순)
    cur.execute("SELECT * FROM shop ORDER BY idx DESC")
    rows = cur.fetchall()
    
    # 2. 대시보드용: 상품별 현재고 요약 계산 (Group By 활용)
    cur.execute("""
        SELECT PRODUCT_NAME, 
               SUM(CAST(RECEIVING AS INTEGER)) as T_REC, 
               SUM(CAST(SHIPPING AS INTEGER)) as T_SHI,
               (SUM(CAST(RECEIVING AS INTEGER)) - SUM(CAST(SHIPPING AS INTEGER))) as CURRENT_STOCK
        FROM shop 
        GROUP BY PRODUCT_NAME
    """)
    summary = cur.fetchall()
    
    con.close()
    return render_template('stock.html', rows=rows, summary=summary)

@bp4.route("/start", methods=['POST'])
def start():
    """신규 재고 등록 및 마이너스 재고 방지 로직"""
    if not session.get('logFlag'):
        return redirect(url_for('main.index'))

    MY_DATE = request.form.get('MY_DATE')
    PRODUCT_NAME = request.form.get('PRODUCT_NAME')
    RECEIVING = int(request.form.get('RECEIVING') or 0)
    SHIPPING = int(request.form.get('SHIPPING') or 0)

    con = get_db_con()
    cur = con.cursor()
    
    # 해당 상품의 현재 총 재고 확인
    cur.execute("""
        SELECT (SUM(CAST(RECEIVING AS INTEGER)) - SUM(CAST(SHIPPING AS INTEGER))) as CURRENT_TOTAL 
        FROM shop WHERE PRODUCT_NAME = ?
    """, (PRODUCT_NAME,))
    res = cur.fetchone()
    current_total = res['CURRENT_TOTAL'] if res['CURRENT_TOTAL'] is not None else 0
    
    # [검증] 출고량이 현재 보유 재고보다 많으면 차단
    if SHIPPING > (current_total + RECEIVING):
        con.close()
        return "<script>alert('재고가 부족합니다! (현재고: " + str(current_total) + "개)'); history.back();</script>"
    
    # 새로운 합계 계산 후 저장
    new_total = current_total + RECEIVING - SHIPPING
    cur.execute("INSERT INTO shop (MY_DATE, PRODUCT_NAME, RECEIVING, SHIPPING, TOTAL) VALUES (?, ?, ?, ?, ?)", 
                (MY_DATE, PRODUCT_NAME, str(RECEIVING), str(SHIPPING), str(new_total)))
    con.commit()
    con.close()
    return redirect(url_for('sub4.second'))

@bp4.route("/edit", methods=["GET"])
def edit():
    """수정 화면 호출"""
    if not session.get('logFlag'):
        return redirect(url_for('main.index'))
    
    data = {
        'idx': request.args.get('idx'),
        'MY_DATE': request.args.get('MY_DATE'),
        'PRODUCT_NAME': request.args.get('PRODUCT_NAME'),
        'RECEIVING': request.args.get('RECEIVING', '0'),
        'SHIPPING': request.args.get('SHIPPING', '0'),
        'TOTAL': request.args.get('TOTAL', '0')
    }
    return render_template('stock_edit.html', **data)

@bp4.route("/edit_result", methods=["POST", "GET"])
def edit_result():
    """재고 수정 처리 (단일 행 수정)"""
    if not session.get('logFlag'):
        return redirect(url_for('main.index'))

    idx = request.args.get('idx') or request.form.get('idx')
    MY_DATE = request.args.get('MY_DATE') or request.form.get('MY_DATE')
    PRODUCT_NAME = request.args.get('PRODUCT_NAME') or request.form.get('PRODUCT_NAME')
    RECEIVING = request.args.get('RECEIVING') or request.form.get('RECEIVING') or '0'
    SHIPPING = request.args.get('SHIPPING') or request.form.get('SHIPPING') or '0'
    
    # 수정된 행의 개별 합계 업데이트
    TOTAL = int(RECEIVING) - int(SHIPPING)
    
    con = get_db_con()
    cur = con.cursor()
    cur.execute("UPDATE shop SET PRODUCT_NAME=?, RECEIVING=?, SHIPPING=?, TOTAL=?, MY_DATE=? WHERE idx=?",
                (PRODUCT_NAME, RECEIVING, SHIPPING, str(TOTAL), MY_DATE, idx))
    con.commit()
    con.close()
    return redirect(url_for('sub4.second'))

@bp4.route("/del", methods=["GET"])
def databasedel():
    """재고 데이터 삭제"""
    if not session.get('logFlag'):
        return redirect(url_for('main.index'))
    
    idx = request.args.get('idx')
    con = get_db_con()
    cur = con.cursor()
    cur.execute("DELETE FROM shop WHERE idx = ?", (idx,))
    con.commit()
    con.close()
    return redirect(url_for('sub4.second'))

@bp4.route("/csv_import")
def csv_import():
    """현재 DB 내역으로 엑셀 파일 생성"""
    if not session.get('logFlag'):
        return redirect(url_for('main.index'))
    
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "inventory"
    sheet.append(["번호", "날짜", "물품명", "입고", "출고", "재고합계"])
    
    con = get_db_con()
    rows = con.execute('SELECT * FROM shop').fetchall()
    for row in rows:
        sheet.append([row['idx'], row['MY_DATE'], row['PRODUCT_NAME'], row['RECEIVING'], row['SHIPPING'], row['TOTAL']])
    con.close()

    if not os.path.exists(sub4dbl): os.makedirs(sub4dbl)
    workbook.save(sub4dbl + "/inventory.xlsx")
    return redirect(url_for('sub4.second'))

@bp4.route("/csv_download")
def csv_download():
    """생성된 엑셀 파일 다운로드"""
    file_path = sub4dbl + "/inventory.xlsx"
    return send_file(file_path, as_attachment=True)