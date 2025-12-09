import sqlite3
from pathlib import Path
import qrcode

DB_PATH = Path("database/supermarket.db")   # ajusta
OUT_DIR = Path("qr_cajas")
OUT_DIR.mkdir(exist_ok=True)

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row

rows = conn.execute("SELECT id, numero, nombre, qr_token FROM cajas").fetchall()

for row in rows:
    data = row["qr_token"]  # *** LO QUE EL LECTOR DEBE LEER ***
    img = qrcode.make(data)
    filename = OUT_DIR / f"caja_{row['numero']}_id{row['id']}.png"
    img.save(filename)
    print(f"QR generado: {filename} (token: {data})")

conn.close()