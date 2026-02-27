"""
AFOSI Asset Register import — clears existing records and reimports from source data.
Run:  python import_register.py
"""
import os
import sqlite3
import qrcode
import qrcode.constants

DB_PATH   = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assetqr.db')
QR_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'qrcodes')
os.makedirs(QR_FOLDER, exist_ok=True)

# ── Full corrected asset register ──────────────────────────────────────────
ASSETS = [
    {
        'asset_id':      'AFOSI-001',
        'name':          'Photocopier Machine',
        'category':      'Equipment',
        'description':   'Kyocera KM 2560',
        'location':      'Programs Working Station',
        'serial_number': 'RTM2024-10500',
        'purchase_date': '2021-01-01',
        'custodian':     'Prisca Achieng',
        'donor':         'AFOSI',
        'value_ksh':     '30000',
        'notes':         'Ref: REF/INV/2021/001',
    },
    {
        'asset_id':      'AFOSI-002',
        'name':          'Office Desk 4-Seater Working Area',
        'category':      'Furniture',
        'description':   'Wooden office workstation desk',
        'location':      'Programs Working Station',
        'serial_number': 'AFOSI/FUR/2021/001',
        'purchase_date': '2021-01-01',
        'custodian':     'Prisca Achieng',
        'donor':         'AFOSI',
        'value_ksh':     '15500',
        'notes':         'Ref: INV/2021/002',
    },
    {
        'asset_id':      'AFOSI-003',
        'name':          'Office Chair',
        'category':      'Furniture',
        'description':   'Mesh office chair',
        'location':      'Programs Working Station',
        'serial_number': 'AFOSI/CHR/2021/001',
        'purchase_date': '2021-01-01',
        'custodian':     'Prisca Achieng',
        'donor':         'AFOSI',
        'value_ksh':     '7500',
        'notes':         'Ref: INV/2021/003 | Tag: AOSI 003 (original register)',
    },
    {
        'asset_id':      'AFOSI-004',
        'name':          'Office Chair',
        'category':      'Furniture',
        'description':   'Mesh office chair',
        'location':      'Programs Working Station',
        'serial_number': 'AFOSI/CHR/2021/002',
        'purchase_date': '2021-01-01',
        'custodian':     'Davin Omollo',
        'donor':         'AFOSI',
        'value_ksh':     '7500',
        'notes':         'Ref: INV/2021/004',
    },
    {
        'asset_id':      'AFOSI-005',
        'name':          'Office Chair',
        'category':      'Furniture',
        'description':   'Mesh office chair',
        'location':      'Programs Working Station',
        'serial_number': 'AFOSI/CHR/2021/003',
        'purchase_date': '2021-01-01',
        'custodian':     'Esther Kiilu',
        'donor':         'AFOSI',
        'value_ksh':     '7500',
        'notes':         'Ref: INV/2021/005',
    },
    {
        'asset_id':      'AFOSI-006',
        'name':          'Office Chair',
        'category':      'Furniture',
        'description':   'Mesh office chair',
        'location':      'Programs Working Station',
        'serial_number': 'AFOSI/CHR/2021/004',
        'purchase_date': '2021-01-01',
        'custodian':     'Betty Gatuiri',
        'donor':         'AFOSI',
        'value_ksh':     '7500',
        'notes':         'Ref: INV/2021/006',
    },
    {
        'asset_id':      'AFOSI-007',
        'name':          'Office Desk',
        'category':      'Furniture',
        'description':   'Study table',
        'location':      'Executive Office',
        'serial_number': 'AFOSI/DESK/2021/001',
        'purchase_date': '2021-01-01',
        'custodian':     'Eric Nyamwaro',
        'donor':         'AFOSI',
        'value_ksh':     '9000',
        'notes':         'Ref: INV/2021/007',
    },
    {
        'asset_id':      'AFOSI-008',
        'name':          'Executive Office Chair',
        'category':      'Furniture',
        'description':   'Office Chair Jagger H',
        'location':      'Executive Office',
        'serial_number': 'AFOSI/CHR/2021/005',
        'purchase_date': '2021-01-01',
        'custodian':     'Eric Nyamwaro',
        'donor':         'AFOSI',
        'value_ksh':     '8500',
        'notes':         'Ref: INV/2021/008',
    },
    {
        'asset_id':      'AFOSI-009',
        'name':          'Office Desk',
        'category':      'Furniture',
        'description':   'Study table',
        'location':      'Executive Office',
        'serial_number': 'AFOSI/DESK/2021/002',
        'purchase_date': '2021-01-01',
        'custodian':     'Fredrick Ongaki',
        'donor':         'AFOSI',
        'value_ksh':     '9000',
        'notes':         'Ref: INV/2021/09',
    },
    {
        'asset_id':      'AFOSI-010',
        'name':          'Executive Office Chair',
        'category':      'Furniture',
        'description':   'Ergonomic headrest office chair',
        'location':      'Executive Office',
        'serial_number': 'SAFE-2024-40000',
        'purchase_date': '2021-01-01',
        'custodian':     'Fredrick Ongaki',
        'donor':         'AFOSI',
        'value_ksh':     '8500',
        'notes':         'Ref: INV/2021/010',
    },
    {
        'asset_id':      'AFOSI-011',
        'name':          'Safe',
        'category':      'Equipment',
        'description':   'Fireproof safe box',
        'location':      'Executive Office',
        'serial_number': 'SAFE-2024-40000',
        'purchase_date': '2024-01-01',
        'custodian':     'Eric Nyamwaro',
        'donor':         'AFOSI',
        'value_ksh':     '40000',
        'notes':         'Ref: INV/2024/011',
    },
    {
        'asset_id':      'AFOSI-012',
        'name':          'White Glass Cabinet',
        'category':      'Furniture',
        'description':   'Wooden white cabinet',
        'location':      'Staff',
        'serial_number': 'CAB-2024-25000',
        'purchase_date': '2024-01-01',
        'custodian':     'Prisca Achieng',
        'donor':         'AFOSI',
        'value_ksh':     '25000',
        'notes':         'Ref: INV/2024/012',
    },
    {
        'asset_id':      'AFOSI-013',
        'name':          'ThinkPad Laptop',
        'category':      'Equipment',
        'description':   'Lenovo ThinkPad',
        'location':      'Staff',
        'serial_number': 'LTP-2024-THINKPAD-001',
        'purchase_date': '2024-01-01',
        'custodian':     'Prisca Achieng',
        'donor':         'AFOSI',
        'value_ksh':     '25000',
        'notes':         'Ref: INV/2024/013',
    },
    {
        'asset_id':      'AFOSI-014',
        'name':          'ThinkPad Laptop',
        'category':      'Equipment',
        'description':   'Lenovo ThinkPad',
        'location':      'Staff',
        'serial_number': 'LTP-2024-THINKPAD-002',
        'purchase_date': '2024-01-01',
        'custodian':     'Prisca Achieng',
        'donor':         'AFOSI',
        'value_ksh':     '25000',
        'notes':         'Ref: INV/2024/014',
    },
    {
        'asset_id':      'AFOSI-015',
        'name':          'HP Intel Core 5 Laptop',
        'category':      'Equipment',
        'description':   'HP Laptop',
        'location':      'Staff',
        'serial_number': '4RG8245T2D',
        'purchase_date': '2024-01-01',
        'custodian':     'Elisha Papa',
        'donor':         'AFOSI / We Lead',
        'value_ksh':     '24000',
        'notes':         'Ref: INV/2024/015',
    },
    {
        'asset_id':      'AFOSI-016',
        'name':          'HP EliteBook 830 G7 Laptop',
        'category':      'Equipment',
        'description':   '11th Gen Intel Core i7-1185G7 @ 3.00GHz',
        'location':      'Staff',
        'serial_number': '5CG1220D2W',
        'purchase_date': '2021-07-01',
        'custodian':     'Betty Muriithi',
        'donor':         'Sheria Ya Vijana',
        'value_ksh':     '45000',
        'notes':         'Ref: SEPKES006',
    },
    {
        'asset_id':      'AFOSI-017',
        'name':          'HP EliteBook 830 G7 Laptop',
        'category':      'Equipment',
        'description':   '11th Gen Intel Core i7-1185G7 @ 3.00GHz',
        'location':      'Staff',
        'serial_number': '5CG1353PDB',
        'purchase_date': '2021-07-01',
        'custodian':     'Esther Kiilu',
        'donor':         'Sheria Ya Vijana',
        'value_ksh':     '45000',
        'notes':         'Ref: SEPKES007',
    },
    {
        'asset_id':      'AFOSI-018',
        'name':          'HP EliteBook 830 G6 Laptop 14"',
        'category':      'Equipment',
        'description':   'HP Laptop 16GB RAM 256GB ROM',
        'location':      'Staff',
        'serial_number': '5CG94442Z2',
        'purchase_date': '2021-07-01',
        'custodian':     'Davin Omollo',
        'donor':         'Sheria Ya Vijana',
        'value_ksh':     '31500',
        'notes':         'Ref: SEPKES008',
    },
    {
        'asset_id':      'AFOSI-019',
        'name':          'HP EliteBook 830 G6 Laptop 14"',
        'category':      'Equipment',
        'description':   'HP Laptop 16GB RAM 500GB ROM',
        'location':      'Staff',
        'serial_number': '5CD702008M',
        'purchase_date': '2021-07-01',
        'custodian':     'Vanessa Gathuri',
        'donor':         'Sheria Ya Vijana',
        'value_ksh':     '31500',
        'notes':         'Ref: SEPKES009',
    },
    {
        'asset_id':      'AFOSI-020',
        'name':          'HP EliteBook 830 G6 Laptop 14"',
        'category':      'Equipment',
        'description':   'HP Laptop 16GB RAM 256GB ROM',
        'location':      'Staff',
        'serial_number': '5CG04338DA',
        'purchase_date': '2021-07-01',
        'custodian':     'Magdaleen Watahi',
        'donor':         'Sheria Ya Vijana',
        'value_ksh':     '31500',
        'notes':         'Ref: SEPKES010',
    },
    {
        'asset_id':      'AFOSI-021',
        'name':          'Lenovo Legion 5 161RX9',
        'category':      'Equipment',
        'description':   'Lenovo Legion 5, 64GB RAM, 1TB ROM',
        'location':      'Staff',
        'serial_number': 'PF4Z55H6',
        'purchase_date': '2021-07-01',
        'custodian':     'Elisha Papa',
        'donor':         'Sheria Ya Vijana',
        'value_ksh':     '240000',
        'notes':         'Ref: SEPKES011',
    },
    {
        'asset_id':      'AFOSI-022',
        'name':          'Microwave',
        'category':      'Equipment',
        'description':   'Ramtons Microwave',
        'location':      'Programs Working Station',
        'serial_number': '06791/10024',
        'purchase_date': '2024-06-06',
        'custodian':     'Prisca Achieng',
        'donor':         'AFOSI',
        'value_ksh':     '10500',
        'notes':         'Ref: RTM2024-10500',
    },
]


def get_base_url(db):
    row = db.execute("SELECT value FROM settings WHERE key='base_url'").fetchone()
    return (row[0] if row else 'http://localhost:5001').rstrip('/')


def make_qr(asset_id, base_url):
    url  = f'{base_url}/asset/{asset_id}'
    qr   = qrcode.QRCode(
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)
    img  = qr.make_image(fill_color='black', back_color='white')
    path = os.path.join(QR_FOLDER, f'qr_{asset_id}.png')
    img.save(path)
    return path


def run():
    db       = sqlite3.connect(DB_PATH)
    base_url = get_base_url(db)

    # Ensure new columns exist (migration for existing DB)
    for col in ('custodian', 'donor', 'value_ksh'):
        try:
            db.execute(f"ALTER TABLE assets ADD COLUMN {col} TEXT DEFAULT ''")
            db.commit()
        except Exception:
            pass

    print(f'Base URL : {base_url}')
    print(f'Updating {len(ASSETS)} assets (upsert)...\n')

    ok = 0
    for a in ASSETS:
        existing = db.execute('SELECT id FROM assets WHERE asset_id=?', (a['asset_id'],)).fetchone()
        if existing:
            db.execute('''
                UPDATE assets SET
                    name=?, category=?, description=?, location=?, status='active',
                    serial_number=?, purchase_date=?, custodian=?, donor=?,
                    value_ksh=?, notes=?, updated_at=datetime('now')
                WHERE asset_id=?
            ''', (
                a['name'], a['category'], a['description'], a['location'],
                a['serial_number'], a['purchase_date'],
                a['custodian'], a['donor'], a['value_ksh'], a['notes'],
                a['asset_id'],
            ))
            action = 'UPDATED'
        else:
            db.execute('''
                INSERT INTO assets
                  (asset_id, name, category, description, location, status,
                   serial_number, purchase_date, custodian, donor, value_ksh, notes)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
            ''', (
                a['asset_id'], a['name'], a['category'], a['description'],
                a['location'], 'active', a['serial_number'], a['purchase_date'],
                a['custodian'], a['donor'], a['value_ksh'], a['notes'],
            ))
            action = 'INSERTED'
        db.commit()

        qr_path = make_qr(a['asset_id'], base_url)
        db.execute('UPDATE assets SET qr_code_path=? WHERE asset_id=?', (qr_path, a['asset_id']))
        db.commit()

        print(f'  {action:8s}  {a["asset_id"]}  {a["name"]} ({a["custodian"]})')
        ok += 1

    db.execute("INSERT OR REPLACE INTO settings VALUES ('company_name', 'AFOSI')")
    db.commit()
    db.close()

    print(f'\nDONE: {ok} assets processed.')
    print(f'QR codes saved to: {os.path.abspath(QR_FOLDER)}')


if __name__ == '__main__':
    run()
