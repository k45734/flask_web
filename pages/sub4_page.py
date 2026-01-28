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
    con = sqlite3.connect(sub4db, timeout=60)
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA synchronous=NORMAL")
    con.row_factory = sqlite3.Row
    return con

@bp4.route('/')
@bp4.route('/index')
def second():
    con = get_db_con()
    con.execute('CREATE TABLE IF NOT EXISTS shop (idx integer primary key autoincrement, MY_DATE TEXT, PRODUCT_NAME TEXT, RECEIVING TEXT, SHIPPING TEXT, TOTAL TEXT)')
    
    if not session.get('logFlag'):
        return redirect(url_for('main.index'))
    
    cur = con.cursor()
    cur.execute("SELECT * FROM shop ORDER BY idx DESC")
    rows = cur.fetchall()
    con.close()
    return render_template('stock.html', rows=rows)

@bp4.route("/start", methods=['POST'])
def start():
    if not session.get('logFlag'):
        return redirect(url_for('main.index'))

    MY_DATE = request.form.get('MY_DATE')
    PRODUCT_NAME = request.form.get('PRODUCT_NAME')
    RECEIVING = request.form.get('RECEIVING') or '0'
    SHIPPING = request.form.get('SHIPPING') or '0'

    con = get_db_con()
    cur = con.cursor()
    
    # 해당 상품의 가장 최근 재고(TOTAL) 가져오기 (변수 'a' 해결)
    cur.execute("SELECT TOTAL FROM shop WHERE PRODUCT_NAME = ? ORDER BY idx DESC LIMIT 1", (PRODUCT_NAME,))
    last_row = cur.fetchone()
    previous_total = int(last_row['TOTAL']) if last_row else 0
    
    # 새로운 TOTAL 계산
    TOTAL = previous_total + int(RECEIVING) - int(SHIPPING)
    
    cur.execute("INSERT INTO shop (MY_DATE, PRODUCT_NAME, RECEIVING, SHIPPING, TOTAL) VALUES (?, ?, ?, ?, ?)", 
                (MY_DATE, PRODUCT_NAME, RECEIVING, SHIPPING, str(TOTAL)))
    con.commit()
    con.close()
    return redirect(url_for('sub4.second'))

@bp4.route("/edit", methods=["GET"])
def edit():
    if not session.get('logFlag'):
        return redirect(url_for('main.index'))
    
    # 수정 페이지 이동 시 현재 값들을 전달
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
    if not session.get('logFlag'):
        return redirect(url_for('main.index'))

    idx = request.args.get('idx') or request.form.get('idx')
    MY_DATE = request.args.get('MY_DATE') or request.form.get('MY_DATE')
    PRODUCT_NAME = request.args.get('PRODUCT_NAME') or request.form.get('PRODUCT_NAME')
    RECEIVING = request.args.get('RECEIVING') or request.form.get('RECEIVING') or '0'
    SHIPPING = request.args.get('SHIPPING') or request.form.get('SHIPPING') or '0'
    
    # 단순 계산 로직 (수정 시 현재 행의 입/출고 기준으로 재계산)
    TOTAL = int(RECEIVING) - int(SHIPPING)
    
    con = get_db_con()
    cur = con.cursor()
    cur.execute("UPDATE shop SET PRODUCT_NAME=?, RECEIVING=?, SHIPPING=?, TOTAL=?, MY_DATE=? WHERE idx=?",
                (PRODUCT_NAME, RECEIVING, SHIPPING, str(TOTAL), MY_DATE, idx))
    con.commit()
    con.close()
    return redirect(url_for('sub4.second'))

@bp4.route("/del", methods=["GET"]) # stock.html의 'del' 링크와 일치시킴
def databasedel():
    if not session.get('logFlag'):
        return redirect(url_for('main.index'))
    
    idx = request.args.get('idx')
    con = get_db_con()
    cur = con.cursor()
    cur.execute("DELETE FROM shop WHERE idx = ?", (idx,))
    con.commit()
    con.close()
    return redirect(url_for('sub4.second'))

@bp4.route("/csv_import") # 엑셀 생성 및 이동
def csv_import():
    if not session.get('logFlag'):
        return redirect(url_for('main.index'))
    
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "inventory"
    sheet.append(["번호", "날짜", "물품명", "입고", "출고", "합계"])
    
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
    file_path = sub4dbl + "/inventory.xlsx"
    return send_file(file_path, as_attachment=True)