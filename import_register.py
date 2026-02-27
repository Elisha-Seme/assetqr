"""
One-time import of AFOSI Asset Register (31.08.2025).
Run from the assetqr directory with the venv active:
    python import_register.py
"""
import os
import sqlite3
import qrcode
import qrcode.constants

DB_PATH   = os.path.join(os.path.dirname(__file__), 'assetqr.db')
QR_FOLDER = os.path.join(os.path.dirname(__file__), 'static', 'qrcodes')
os.makedirs(QR_FOLDER, exist_ok=True)

# ── Asset data extracted from PDF ──────────────────────────────────────────
ASSETS = [
    {
        'asset_id':      'AFOSI-001',
        'name':          'Kyocera KM 2560 Photocopier',
        'category':      'Equipment',
        'description':   'Photocopier Machine',
        'location':      'AFOSI Programs Working Station',
        'serial_number': 'RTM2024-10500',
        'purchase_date': '2021-01-01',
        'notes':         'Custodian: Prisca Achieng | KSh 30,000 | Condition: Good',
    },
    {
        'asset_id':      'AFOSI-002',
        'name':          'Office Desk 4-Seater Workstation',
        'category':      'Furniture',
        'description':   'Wooden office workstation desk',
        'location':      'AFOSI Programs Working Station',
        'serial_number': 'AFOSI/FUR/2021/001',
        'purchase_date': '2021-01-01',
        'notes':         'Custodian: Prisca Achieng | KSh 15,500 | Condition: Good',
    },
    {
        'asset_id':      'AFOSI-003',
        'name':          'Mesh Office Chair',
        'category':      'Furniture',
        'description':   'Mesh office chair',
        'location':      'AFOSI Programs Working Station',
        'serial_number': 'AFOSI/CHR/2021/001',
        'purchase_date': '2021-01-01',
        'notes':         'Custodian: Prisca Achieng | KSh 7,500 | Condition: Good',
    },
    {
        'asset_id':      'AFOSI-004',
        'name':          'Mesh Office Chair',
        'category':      'Furniture',
        'description':   'Mesh office chair',
        'location':      'AFOSI Programs Working Station',
        'serial_number': 'AFOSI/CHR/2021/002',
        'purchase_date': '2021-01-01',
        'notes':         'Custodian: Davin Omollo | KSh 7,500 | Condition: Good',
    },
    {
        'asset_id':      'AFOSI-005',
        'name':          'Mesh Office Chair',
        'category':      'Furniture',
        'description':   'Mesh office chair',
        'location':      'AFOSI Programs Working Station',
        'serial_number': 'AFOSI/CHR/2021/003',
        'purchase_date': '2021-01-01',
        'notes':         'Custodian: Esther Kiilu | KSh 7,500 | Condition: Good',
    },
    {
        'asset_id':      'AFOSI-006',
        'name':          'Mesh Office Chair',
        'category':      'Furniture',
        'description':   'Mesh office chair',
        'location':      'AFOSI Programs Working Station',
        'serial_number': 'AFOSI/CHR/2021/004',
        'purchase_date': '2021-01-01',
        'notes':         'Custodian: Betty Gatuiri | KSh 7,500 | Condition: Good',
    },
    {
        'asset_id':      'AFOSI-007',
        'name':          'Office Desk (Study Table)',
        'category':      'Furniture',
        'description':   'Study table / office desk',
        'location':      'AFOSI Executive Office',
        'serial_number': 'AFOSI/DESK/2021/001',
        'purchase_date': '2021-01-01',
        'notes':         'Custodian: Eric Nyamwaro | KSh 9,000 | Condition: Good',
    },
    {
        'asset_id':      'AFOSI-008',
        'name':          'Executive Office Chair (Jagger H)',
        'category':      'Furniture',
        'description':   'Office Chair Jagger H',
        'location':      'AFOSI Executive Office',
        'serial_number': 'AFOSI/CHR/2021/005',
        'purchase_date': '2021-01-01',
        'notes':         'Custodian: Eric Nyamwaro | KSh 8,500 | Condition: Good',
    },
    {
        'asset_id':      'AFOSI-009',
        'name':          'Office Desk (Study Table)',
        'category':      'Furniture',
        'description':   'Study table / office desk',
        'location':      'AFOSI Executive Office',
        'serial_number': 'AFOSI/DESK/2021/002',
        'purchase_date': '2021-01-01',
        'notes':         'Custodian: Fredrick Ongaki | KSh 9,000 | Condition: Good',
    },
    {
        'asset_id':      'AFOSI-010',
        'name':          'Ergonomic Headrest Executive Chair',
        'category':      'Furniture',
        'description':   'Ergonomic headrest office chair',
        'location':      'AFOSI Executive Office',
        'serial_number': 'SAFE-2024-40000',
        'purchase_date': '2021-01-01',
        'notes':         'Custodian: Fredrick Ongaki | KSh 8,500 | Condition: Good',
    },
    {
        'asset_id':      'AFOSI-011',
        'name':          'Fireproof Safe Box',
        'category':      'Equipment',
        'description':   'Fireproof safe box',
        'location':      'AFOSI Executive Office',
        'serial_number': 'SAFE-2024-40000',
        'purchase_date': '2024-01-01',
        'notes':         'Custodian: Eric Nyamwaro | KSh 40,000 | Condition: Good',
    },
    {
        'asset_id':      'AFOSI-012',
        'name':          'White Glass Cabinet',
        'category':      'Furniture',
        'description':   'Wooden white cabinet',
        'location':      'AFOSI Staff',
        'serial_number': 'CAB-2024-25000',
        'purchase_date': '2024-01-01',
        'notes':         'Custodian: Prisca Achieng | KSh 25,000 | Condition: Good',
    },
    {
        'asset_id':      'AFOSI-013',
        'name':          'Lenovo ThinkPad Laptop',
        'category':      'Equipment',
        'description':   'Lenovo ThinkPad laptop',
        'location':      'AFOSI Staff',
        'serial_number': 'LTP-2024-THINKPAD-001',
        'purchase_date': '2024-01-01',
        'notes':         'Custodian: Prisca Achieng | KSh 25,000 | Condition: Good',
    },
    {
        'asset_id':      'AFOSI-014',
        'name':          'Lenovo ThinkPad Laptop',
        'category':      'Equipment',
        'description':   'Lenovo ThinkPad laptop',
        'location':      'AFOSI Staff',
        'serial_number': 'LTP-2024-THINKPAD-002',
        'purchase_date': '2024-01-01',
        'notes':         'Custodian: Prisca Achieng | KSh 25,000 | Condition: Good',
    },
    {
        'asset_id':      'AFOSI-015',
        'name':          'HP Intel Core 5 Laptop',
        'category':      'Equipment',
        'description':   'HP Laptop',
        'location':      'AFOSI / We Lead Staff',
        'serial_number': '4RG8245T2D',
        'purchase_date': '2024-01-01',
        'notes':         'Custodian: Elisha Papa | KSh 24,000 | Condition: Good',
    },
    {
        'asset_id':      'AFOSI-016',
        'name':          'HP EliteBook 830 G7 Laptop',
        'category':      'Equipment',
        'description':   '11th Gen Intel Core i7-1185G7 @ 3.00GHz, 14"',
        'location':      'Sheria Ya Vijana Staff',
        'serial_number': '5CG1220D2W',
        'purchase_date': '2021-07-01',
        'notes':         'Custodian: Betty Muriithi | KSh 45,000 | Ref: SEPKES006 | Condition: Good',
    },
    {
        'asset_id':      'AFOSI-017',
        'name':          'HP EliteBook 830 G7 Laptop',
        'category':      'Equipment',
        'description':   '11th Gen Intel Core i7-1185G7 @ 3.00GHz, 14"',
        'location':      'Sheria Ya Vijana Staff',
        'serial_number': '5CG1353PDB',
        'purchase_date': '2021-07-01',
        'notes':         'Custodian: Esther Kiilu | KSh 45,000 | Ref: SEPKES007 | Condition: Good',
    },
    {
        'asset_id':      'AFOSI-018',
        'name':          'HP EliteBook 830 G6 Laptop 14"',
        'category':      'Equipment',
        'description':   'HP Laptop 16GB RAM 256GB ROM',
        'location':      'Sheria Ya Vijana Staff',
        'serial_number': '5CG94442Z2',
        'purchase_date': '2021-07-01',
        'notes':         'Custodian: Davin Omollo | KSh 31,500 | Ref: SEPKES008 | Condition: Good',
    },
    {
        'asset_id':      'AFOSI-019',
        'name':          'HP EliteBook 830 G6 Laptop 14"',
        'category':      'Equipment',
        'description':   'HP Laptop 16GB RAM 500GB ROM',
        'location':      'Sheria Ya Vijana Staff',
        'serial_number': '5CD702008M',
        'purchase_date': '2021-07-01',
        'notes':         'Custodian: Vanessa Gathuri | KSh 31,500 | Ref: SEPKES009 | Condition: Good',
    },
    {
        'asset_id':      'AFOSI-020',
        'name':          'HP EliteBook 830 G6 Laptop 14"',
        'category':      'Equipment',
        'description':   'HP Laptop 16GB RAM 256GB ROM',
        'location':      'Sheria Ya Vijana Staff',
        'serial_number': '5CG04338DA',
        'purchase_date': '2021-07-01',
        'notes':         'Custodian: Magdaleen Watahi | KSh 31,500 | Ref: SEPKES010 | Condition: Good',
    },
    {
        'asset_id':      'AFOSI-021',
        'name':          'Lenovo Legion 5 161RX9 Laptop',
        'category':      'Equipment',
        'description':   'Lenovo Legion 5, 64GB RAM, 1TB ROM',
        'location':      'Sheria Ya Vijana Staff',
        'serial_number': 'PF4Z55H6',
        'purchase_date': '2021-07-01',
        'notes':         'Custodian: Elisha Papa | KSh 240,000 | Ref: SEPKES011 | Condition: Good',
    },
    {
        'asset_id':      'AFOSI-022',
        'name':          'Ramtons Microwave',
        'category':      'Equipment',
        'description':   'Ramtons Microwave oven',
        'location':      'AFOSI Programs Working Station',
        'serial_number': '06791/10024',
        'purchase_date': '2024-06-06',
        'notes':         'Custodian: Prisca Achieng | KSh 10,500 | Condition: Good',
    },
]

# ── Read base_url from settings ────────────────────────────────────────────
def get_base_url(db):
    row = db.execute("SELECT value FROM settings WHERE key='base_url'").fetchone()
    return (row[0] if row else 'http://localhost:5001').rstrip('/')

def make_qr(asset_id, base_url):
    url  = f'{base_url}/asset/{asset_id}'
    qr   = qrcode.QRCode(
        error_correction=qrcode.constants.ERROR_CORRECT_H,  # 30% damage tolerance
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)
    img  = qr.make_image(fill_color='black', back_color='white')
    path = os.path.join(QR_FOLDER, f'qr_{asset_id}.png')
    img.save(path)
    return path

# ── Import ─────────────────────────────────────────────────────────────────
def run():
    db       = sqlite3.connect(DB_PATH)
    base_url = get_base_url(db)
    print(f'Base URL: {base_url}')
    print(f'Importing {len(ASSETS)} assets...\n')

    ok = skipped = 0
    for a in ASSETS:
        existing = db.execute('SELECT id FROM assets WHERE asset_id=?', (a['asset_id'],)).fetchone()
        if existing:
            print(f'  SKIP  {a["asset_id"]} — already exists')
            skipped += 1
            continue

        db.execute('''
            INSERT INTO assets
              (asset_id, name, category, description, location, status,
               serial_number, purchase_date, notes)
            VALUES (?,?,?,?,?,?,?,?,?)
        ''', (
            a['asset_id'], a['name'], a['category'], a['description'],
            a['location'], 'active', a['serial_number'],
            a['purchase_date'], a['notes'],
        ))
        db.commit()

        qr_path = make_qr(a['asset_id'], base_url)
        db.execute('UPDATE assets SET qr_code_path=? WHERE asset_id=?', (qr_path, a['asset_id']))
        db.commit()

        print(f'  OK    {a["asset_id"]}  ->  {a["name"]}')
        ok += 1

    db.execute("INSERT OR REPLACE INTO settings VALUES ('company_name', 'AFOSI')")
    db.commit()
    db.close()

    print(f'\nDONE:  {ok} imported,  {skipped} skipped (already existed)')
    print(f'   QR codes saved to: {os.path.abspath(QR_FOLDER)}')
    print(f'\nOpen http://localhost:5001 to view, export PDF, or print labels.')

if __name__ == '__main__':
    run()
