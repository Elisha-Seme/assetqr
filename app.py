import os
import re
import csv
import io
import shutil
import sqlite3
from datetime import datetime
from io import BytesIO

from flask import Flask, render_template, request, jsonify, send_file, g
import qrcode
import qrcode.constants
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Image as RLImage

app = Flask(__name__)

# ── Vercel / environment detection ────────────────────────────────────────────
IS_VERCEL   = bool(os.environ.get('VERCEL'))
_BASE_DIR   = os.path.dirname(os.path.abspath(__file__))

# On Vercel the deployment bundle is read-only; copy DB to /tmp for write access.
def _db_path():
    if IS_VERCEL:
        tmp = '/tmp/assetqr.db'
        if not os.path.exists(tmp):
            src = os.path.join(_BASE_DIR, 'assetqr.db')
            if os.path.exists(src):
                shutil.copy2(src, tmp)
        return tmp
    return os.path.join(_BASE_DIR, 'assetqr.db')

def _qr_folder():
    if IS_VERCEL:
        d = '/tmp/qrcodes'
        os.makedirs(d, exist_ok=True)
        return d
    return os.path.join(_BASE_DIR, 'static', 'qrcodes')

DB_PATH   = _db_path()
QR_FOLDER = _qr_folder()
if not IS_VERCEL:
    os.makedirs(QR_FOLDER, exist_ok=True)


# ── Database ──────────────────────────────────────────────────────────────────

def get_db():
    if 'db' not in g:
        # Re-resolve path each request so Vercel /tmp copy is used correctly
        g.db = sqlite3.connect(_db_path())
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(e=None):
    db = g.pop('db', None)
    if db:
        db.close()

def init_db():
    db = sqlite3.connect(DB_PATH)
    db.executescript('''
        CREATE TABLE IF NOT EXISTS assets (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            asset_id      TEXT    UNIQUE NOT NULL,
            name          TEXT    NOT NULL,
            category      TEXT    DEFAULT '',
            description   TEXT    DEFAULT '',
            location      TEXT    DEFAULT '',
            status        TEXT    DEFAULT 'active',
            serial_number TEXT    DEFAULT '',
            purchase_date TEXT    DEFAULT '',
            custodian     TEXT    DEFAULT '',
            donor         TEXT    DEFAULT '',
            value_ksh     TEXT    DEFAULT '',
            notes         TEXT    DEFAULT '',
            qr_code_path  TEXT    DEFAULT '',
            created_at    TEXT    DEFAULT (datetime('now')),
            updated_at    TEXT    DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS settings (
            key   TEXT PRIMARY KEY,
            value TEXT NOT NULL DEFAULT ''
        );

        INSERT OR IGNORE INTO settings VALUES ('base_url',      'http://localhost:5001');
        INSERT OR IGNORE INTO settings VALUES ('company_name',  'My Organization');
        INSERT OR IGNORE INTO settings VALUES ('qr_color',      '#000000');
    ''')
    # Migration: add new columns to existing DBs that predate this schema
    for col in ('custodian', 'donor', 'value_ksh'):
        try:
            db.execute(f"ALTER TABLE assets ADD COLUMN {col} TEXT DEFAULT ''")
        except Exception:
            pass  # column already exists
    db.commit()
    db.close()


# ── Helpers ───────────────────────────────────────────────────────────────────

def setting(key, default=''):
    # BASE_URL env var overrides the DB value (needed for Vercel deployments)
    if key == 'base_url' and os.environ.get('BASE_URL'):
        return os.environ['BASE_URL'].rstrip('/')
    row = get_db().execute('SELECT value FROM settings WHERE key=?', (key,)).fetchone()
    return row['value'] if row else default

def slugify(text):
    text = (text or '').lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    return text[:30].strip('-')

def next_asset_id(name, db):
    base = slugify(name) or 'asset'
    n = db.execute('SELECT COUNT(*) FROM assets').fetchone()[0] + 1
    cand = f'{base}-{n:04d}'
    while db.execute('SELECT 1 FROM assets WHERE asset_id=?', (cand,)).fetchone():
        n += 1
        cand = f'{base}-{n:04d}'
    return cand

def make_qr(asset_id):
    base_url  = setting('base_url', 'http://localhost:5001')
    qr_color  = setting('qr_color', '#000000')
    url       = f'{base_url}/asset/{asset_id}'
    qr = qrcode.QRCode(
        error_correction=qrcode.constants.ERROR_CORRECT_H,  # 30% damage tolerance
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)
    img  = qr.make_image(fill_color=qr_color, back_color='white')
    folder = _qr_folder()
    path   = os.path.join(folder, f'qr_{asset_id}.png')
    img.save(path)
    return path


# ── Page routes ───────────────────────────────────────────────────────────────

@app.route('/')
def dashboard():
    db = get_db()
    stats = {
        'total':      db.execute('SELECT COUNT(*) FROM assets').fetchone()[0],
        'active':     db.execute("SELECT COUNT(*) FROM assets WHERE status='active'").fetchone()[0],
        'maintenance':db.execute("SELECT COUNT(*) FROM assets WHERE status='maintenance'").fetchone()[0],
        'retired':    db.execute("SELECT COUNT(*) FROM assets WHERE status='retired'").fetchone()[0],
        'categories': db.execute("SELECT COUNT(DISTINCT category) FROM assets WHERE category!=''").fetchone()[0],
    }
    by_cat = db.execute(
        "SELECT category, COUNT(*) cnt FROM assets WHERE category!='' GROUP BY category ORDER BY cnt DESC LIMIT 8"
    ).fetchall()
    recent = db.execute('SELECT * FROM assets ORDER BY created_at DESC LIMIT 10').fetchall()
    return render_template('index.html', stats=stats, by_cat=by_cat, recent=recent)


@app.route('/assets')
def assets_page():
    db  = get_db()
    q   = request.args.get('q', '')
    cat = request.args.get('cat', '')
    st  = request.args.get('status', '')

    sql, params = 'SELECT * FROM assets WHERE 1=1', []
    if q:
        sql += ' AND (name LIKE ? OR asset_id LIKE ? OR location LIKE ? OR description LIKE ? OR serial_number LIKE ?)'
        params += [f'%{q}%'] * 5
    if cat:
        sql += ' AND category=?'; params.append(cat)
    if st:
        sql += ' AND status=?'; params.append(st)
    sql += ' ORDER BY name'

    assets = db.execute(sql, params).fetchall()
    cats   = [r[0] for r in db.execute(
        "SELECT DISTINCT category FROM assets WHERE category!='' ORDER BY category"
    ).fetchall()]
    return render_template('assets.html', assets=assets, cats=cats, q=q, cat=cat, status=st)


@app.route('/asset/<asset_id>')
def asset_detail(asset_id):
    db    = get_db()
    asset = db.execute('SELECT * FROM assets WHERE asset_id=?', (asset_id,)).fetchone()
    if not asset:
        return render_template('404.html', msg=f'Asset "{asset_id}" not found'), 404
    company = setting('company_name', 'Asset Registry')
    base_url = setting('base_url', 'http://localhost:5001')
    qr_url  = f'{base_url}/asset/{asset_id}'
    return render_template('asset_detail.html', asset=asset, company=company, qr_url=qr_url)


@app.route('/import')
def import_page():
    return render_template('import.html')


@app.route('/settings')
def settings_page():
    db = get_db()
    s  = {r['key']: r['value'] for r in db.execute('SELECT * FROM settings').fetchall()}
    return render_template('settings.html', s=s)


# ── API ───────────────────────────────────────────────────────────────────────

@app.route('/api/assets', methods=['GET'])
def api_list():
    db = get_db()
    return jsonify([dict(r) for r in db.execute('SELECT * FROM assets ORDER BY name').fetchall()])


@app.route('/api/assets', methods=['POST'])
def api_create():
    d  = request.json or {}
    db = get_db()
    name = (d.get('name') or '').strip()
    if not name:
        return jsonify({'error': 'Name is required'}), 400

    asset_id = (d.get('asset_id') or '').strip() or next_asset_id(name, db)
    if db.execute('SELECT 1 FROM assets WHERE asset_id=?', (asset_id,)).fetchone():
        return jsonify({'error': f'Asset ID "{asset_id}" already exists'}), 409

    db.execute('''
        INSERT INTO assets (asset_id, name, category, description, location,
                            status, serial_number, purchase_date,
                            custodian, donor, value_ksh, notes)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
    ''', (asset_id, name,
          d.get('category',''), d.get('description',''), d.get('location',''),
          d.get('status','active'), d.get('serial_number',''),
          d.get('purchase_date',''), d.get('custodian',''),
          d.get('donor',''), d.get('value_ksh',''), d.get('notes','')))
    db.commit()

    qp = make_qr(asset_id)
    db.execute('UPDATE assets SET qr_code_path=? WHERE asset_id=?', (qp, asset_id))
    db.commit()
    return jsonify(dict(db.execute('SELECT * FROM assets WHERE asset_id=?', (asset_id,)).fetchone())), 201


@app.route('/api/assets/bulk', methods=['POST'])
def api_bulk():
    items = (request.json or {}).get('items', [])
    db    = get_db()
    ok, fail, errors = 0, 0, []

    for item in items:
        name = (item.get('name') or '').strip()
        if not name:
            fail += 1; errors.append('Blank name skipped'); continue

        asset_id = (item.get('asset_id') or '').strip() or next_asset_id(name, db)
        while db.execute('SELECT 1 FROM assets WHERE asset_id=?', (asset_id,)).fetchone():
            asset_id += '-x'

        try:
            db.execute('''
                INSERT INTO assets (asset_id, name, category, description, location,
                                    status, serial_number, purchase_date,
                                    custodian, donor, value_ksh, notes)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
            ''', (asset_id, name,
                  item.get('category',''), item.get('description',''), item.get('location',''),
                  item.get('status','active'), item.get('serial_number',''),
                  item.get('purchase_date',''), item.get('custodian',''),
                  item.get('donor',''), item.get('value_ksh',''), item.get('notes','')))
            db.commit()
            qp = make_qr(asset_id)
            db.execute('UPDATE assets SET qr_code_path=? WHERE asset_id=?', (qp, asset_id))
            db.commit()
            ok += 1
        except Exception as ex:
            fail += 1; errors.append(f'{name}: {ex}')

    return jsonify({'success': ok, 'failed': fail, 'errors': errors})


@app.route('/api/assets/<int:aid>', methods=['GET'])
def api_get(aid):
    db  = get_db()
    row = db.execute('SELECT * FROM assets WHERE id=?', (aid,)).fetchone()
    if not row:
        return jsonify({'error': 'Not found'}), 404
    return jsonify(dict(row))


@app.route('/api/assets/<int:aid>', methods=['PUT'])
def api_update(aid):
    d   = request.json or {}
    db  = get_db()
    row = db.execute('SELECT * FROM assets WHERE id=?', (aid,)).fetchone()
    if not row:
        return jsonify({'error': 'Not found'}), 404

    db.execute('''
        UPDATE assets SET name=?, category=?, description=?, location=?,
            status=?, serial_number=?, purchase_date=?,
            custodian=?, donor=?, value_ksh=?, notes=?,
            updated_at=datetime('now')
        WHERE id=?
    ''', (d.get('name', row['name']), d.get('category', row['category']),
          d.get('description', row['description']), d.get('location', row['location']),
          d.get('status', row['status']), d.get('serial_number', row['serial_number']),
          d.get('purchase_date', row['purchase_date']),
          d.get('custodian', row['custodian']), d.get('donor', row['donor']),
          d.get('value_ksh', row['value_ksh']), d.get('notes', row['notes']),
          aid))
    db.commit()
    return jsonify(dict(db.execute('SELECT * FROM assets WHERE id=?', (aid,)).fetchone()))


@app.route('/api/assets/<int:aid>', methods=['DELETE'])
def api_delete(aid):
    db  = get_db()
    row = db.execute('SELECT * FROM assets WHERE id=?', (aid,)).fetchone()
    if not row:
        return jsonify({'error': 'Not found'}), 404
    if row['qr_code_path'] and os.path.exists(row['qr_code_path']):
        try:
            os.remove(row['qr_code_path'])
        except Exception:
            pass
    db.execute('DELETE FROM assets WHERE id=?', (aid,))
    db.commit()
    return jsonify({'success': True})


@app.route('/api/assets/<int:aid>/regen-qr', methods=['POST'])
def api_regen_qr(aid):
    db  = get_db()
    row = db.execute('SELECT * FROM assets WHERE id=?', (aid,)).fetchone()
    if not row:
        return jsonify({'error': 'Not found'}), 404
    qp = make_qr(row['asset_id'])
    db.execute('UPDATE assets SET qr_code_path=? WHERE id=?', (qp, aid))
    db.commit()
    return jsonify({'success': True, 'path': f'/static/qrcodes/qr_{row["asset_id"]}.png'})


@app.route('/api/settings', methods=['POST'])
def api_settings():
    d  = request.json or {}
    db = get_db()
    for k, v in d.items():
        db.execute('INSERT OR REPLACE INTO settings VALUES (?,?)', (k, v))
    db.commit()
    if 'base_url' in d or 'qr_color' in d:
        for r in db.execute('SELECT asset_id FROM assets').fetchall():
            make_qr(r['asset_id'])
    return jsonify({'success': True})


# ── Exports ───────────────────────────────────────────────────────────────────

def _query_assets(db):
    ids_p = request.args.get('ids', '')
    q     = request.args.get('q', '')
    cat   = request.args.get('cat', '')
    st    = request.args.get('status', '')

    if ids_p:
        id_list = [int(x) for x in ids_p.split(',') if x.strip().isdigit()]
        ph = ','.join('?'*len(id_list))
        return db.execute(f'SELECT * FROM assets WHERE id IN ({ph}) ORDER BY name', id_list).fetchall()

    sql, params = 'SELECT * FROM assets WHERE 1=1', []
    if q:
        sql += ' AND (name LIKE ? OR asset_id LIKE ? OR location LIKE ?)'; params += [f'%{q}%']*3
    if cat:
        sql += ' AND category=?'; params.append(cat)
    if st:
        sql += ' AND status=?'; params.append(st)
    return db.execute(sql+' ORDER BY name', params).fetchall()


@app.route('/export/pdf')
def export_pdf():
    db      = get_db()
    assets  = _query_assets(db)
    company = setting('company_name', 'Asset Registry')

    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=landscape(A4),
                            leftMargin=1.2*cm, rightMargin=1.2*cm,
                            topMargin=1.5*cm, bottomMargin=1*cm)
    styles = getSampleStyleSheet()
    s8  = ParagraphStyle('s8',  parent=styles['Normal'], fontSize=8,  leading=10)
    sb  = ParagraphStyle('sb',  parent=styles['Normal'], fontSize=8,  leading=10, fontName='Helvetica-Bold')
    sc  = ParagraphStyle('sc',  parent=styles['Normal'], fontSize=7,  leading=9,  textColor=colors.HexColor('#64748b'))
    hdr = ParagraphStyle('hdr', parent=styles['Normal'], fontSize=15, fontName='Helvetica-Bold', spaceAfter=4)
    sub = ParagraphStyle('sub', parent=styles['Normal'], fontSize=8,  textColor=colors.HexColor('#64748b'), spaceAfter=10)

    STATUS_CLR = {'active':'#16a34a', 'maintenance':'#d97706', 'retired':'#dc2626'}

    col_w = [2.2*cm, 2.5*cm, 4.5*cm, 2.8*cm, 3*cm, 2*cm, 3*cm, 3.2*cm, 4.3*cm]
    rows  = [['QR Code','Asset ID','Name','Category','Location','Status','Serial No.','Custodian','Donor / Programme']]

    for a in assets:
        qr_cell = Paragraph('—', s8)
        if a['qr_code_path'] and os.path.exists(a['qr_code_path']):
            try:
                qr_cell = RLImage(a['qr_code_path'], width=1.8*cm, height=1.8*cm)
            except Exception:
                pass
        sc_st = ParagraphStyle('scs', parent=s8,
                               textColor=colors.HexColor(STATUS_CLR.get(a['status'], '#374151')))
        rows.append([
            qr_cell,
            Paragraph(a['asset_id'] or '', s8),
            Paragraph(a['name'] or '', sb),
            Paragraph(a['category'] or '', s8),
            Paragraph(a['location'] or '', s8),
            Paragraph((a['status'] or '').title(), sc_st),
            Paragraph(a['serial_number'] or '', sc),
            Paragraph(a['custodian'] or '', sc),
            Paragraph(a['donor'] or '', sc),
        ])

    tbl = Table(rows, colWidths=col_w, repeatRows=1)
    tbl.setStyle(TableStyle([
        ('BACKGROUND',    (0,0),(-1,0),   colors.HexColor('#1e293b')),
        ('TEXTCOLOR',     (0,0),(-1,0),   colors.white),
        ('FONTNAME',      (0,0),(-1,0),   'Helvetica-Bold'),
        ('FONTSIZE',      (0,0),(-1,0),   8),
        ('ALIGN',         (0,0),(-1,0),   'CENTER'),
        ('VALIGN',        (0,0),(-1,-1),  'MIDDLE'),
        ('ALIGN',         (0,1),(0,-1),   'CENTER'),
        ('ROWBACKGROUNDS',(0,1),(-1,-1),  [colors.white, colors.HexColor('#f8fafc')]),
        ('GRID',          (0,0),(-1,-1),  0.4, colors.HexColor('#e2e8f0')),
        ('LINEBELOW',     (0,0),(-1,0),   2,   colors.HexColor('#0f172a')),
        ('TOPPADDING',    (0,0),(-1,-1),  5),
        ('BOTTOMPADDING', (0,0),(-1,-1),  5),
        ('LEFTPADDING',   (0,0),(-1,-1),  5),
        ('RIGHTPADDING',  (0,0),(-1,-1),  5),
    ]))

    doc.build([
        Paragraph(f'{company} — Asset QR Registry', hdr),
        Paragraph(f'Generated {datetime.now().strftime("%d %b %Y %H:%M")}  |  {len(assets)} asset(s)', sub),
        tbl,
    ])
    buf.seek(0)
    fname = f'assets_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
    return send_file(buf, mimetype='application/pdf', as_attachment=True, download_name=fname)


@app.route('/export/labels')
def export_labels():
    db     = get_db()
    assets = _query_assets(db)

    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            leftMargin=0.8*cm, rightMargin=0.8*cm,
                            topMargin=0.8*cm, bottomMargin=0.8*cm)
    styles = getSampleStyleSheet()
    s_name = ParagraphStyle('ln', parent=styles['Normal'], fontSize=7, leading=9,
                            alignment=TA_CENTER, fontName='Helvetica-Bold')
    s_id   = ParagraphStyle('li', parent=styles['Normal'], fontSize=6, leading=7,
                            alignment=TA_CENTER, textColor=colors.HexColor('#475569'))

    COLS  = 4
    LBL_W = 4.5*cm
    LBL_H = 5.4*cm

    grid_rows, cur = [], []
    for a in assets:
        inner = []
        if a['qr_code_path'] and os.path.exists(a['qr_code_path']):
            try:
                inner.append([RLImage(a['qr_code_path'], width=3.4*cm, height=3.4*cm)])
            except Exception:
                inner.append([Paragraph('QR', s_id)])
        else:
            inner.append([Paragraph('QR', s_id)])
        inner.append([Paragraph(f"<b>{(a['name'] or '')[:28]}</b>", s_name)])
        inner.append([Paragraph(a['asset_id'] or '', s_id)])
        if a['location']:
            inner.append([Paragraph(a['location'][:25], s_id)])

        inner_t = Table(inner, colWidths=[LBL_W - 0.6*cm])
        inner_t.setStyle(TableStyle([
            ('ALIGN', (0,0),(-1,-1), 'CENTER'),
            ('VALIGN',(0,0),(-1,-1), 'MIDDLE'),
            ('TOPPADDING',   (0,0),(-1,-1), 1),
            ('BOTTOMPADDING',(0,0),(-1,-1), 1),
        ]))
        cell = Table([[inner_t]], colWidths=[LBL_W], rowHeights=[LBL_H])
        cell.setStyle(TableStyle([
            ('BOX',           (0,0),(-1,-1), 0.5, colors.HexColor('#cbd5e1')),
            ('ALIGN',         (0,0),(-1,-1), 'CENTER'),
            ('VALIGN',        (0,0),(-1,-1), 'MIDDLE'),
            ('BACKGROUND',    (0,0),(-1,-1), colors.white),
            ('TOPPADDING',    (0,0),(-1,-1), 4),
            ('BOTTOMPADDING', (0,0),(-1,-1), 4),
        ]))
        cur.append(cell)
        if len(cur) == COLS:
            grid_rows.append(cur); cur = []

    if cur:
        while len(cur) < COLS:
            cur.append('')
        grid_rows.append(cur)

    if grid_rows:
        grid = Table(grid_rows, colWidths=[LBL_W]*COLS)
        grid.setStyle(TableStyle([
            ('ALIGN', (0,0),(-1,-1), 'CENTER'),
            ('VALIGN',(0,0),(-1,-1), 'MIDDLE'),
        ]))
        doc.build([grid])

    buf.seek(0)
    fname = f'qr_labels_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
    return send_file(buf, mimetype='application/pdf', as_attachment=True, download_name=fname)


@app.route('/export/csv')
def export_csv():
    db     = get_db()
    assets = _query_assets(db)
    out    = io.StringIO()
    w      = csv.writer(out)
    w.writerow(['asset_id','name','category','location','status','serial_number',
                'description','custodian','donor','value_ksh','purchase_date','notes','created_at'])
    for a in assets:
        w.writerow([a['asset_id'], a['name'], a['category'], a['location'], a['status'],
                    a['serial_number'], a['description'],
                    a['custodian'], a['donor'], a['value_ksh'],
                    a['purchase_date'], a['notes'], a['created_at']])
    out.seek(0)
    fname = f'assets_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    return send_file(io.BytesIO(out.getvalue().encode()),
                     mimetype='text/csv', as_attachment=True, download_name=fname)


if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5001)
