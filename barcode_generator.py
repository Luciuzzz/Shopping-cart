import sqlite3
from pathlib import Path
from barcode import EAN13  # SIN ImageWriter, así no usa Pillow

# Ruta a tu base de datos
DB_PATH = Path(__file__).resolve().parent / "database" / "supermarket.db"
# Carpeta donde se van a guardar los códigos de barras
OUTPUT_DIR = Path(__file__).resolve().parent / "barcodes_svg"


def generate_barcode_svg(digits: str, output_path: Path):
    """
    Genera un código de barras EAN-13 en SVG a partir de 12 o 13 dígitos.
    Ej: digits = '8800010000000'
    output_path: ruta sin extensión (python-barcode agrega .svg solo)
    """
    digits = str(digits)
    if len(digits) not in (12, 13):
        raise ValueError(f"EAN-13 necesita 12 o 13 dígitos, recibido: {digits}")

    # Writer por defecto = SVG, NO depende de Pillow
    ean = EAN13(digits)
    filename = ean.save(str(output_path))  # genera archivo .svg
    return filename


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Leemos productos activos de tu tabla productos
    cur.execute(
        """
        SELECT id, codigo_barr, descripcion
        FROM productos
        WHERE activo = 1 OR activo IS NULL
        """
    )

    rows = cur.fetchall()
    print(f"Productos encontrados: {len(rows)}")

    for prod_id, codigo_barr, descripcion in rows:
        try:
            digits = str(codigo_barr)
            base_name = f"{prod_id}_{digits}"   # nombre base del archivo
            out_path = OUTPUT_DIR / base_name
            file_generated = generate_barcode_svg(digits, out_path)
            print(f"OK - {prod_id} | {descripcion} | {digits} -> {file_generated}")
        except Exception as e:
            print(f"ERROR - {prod_id} | {descripcion} | {codigo_barr}: {e}")

    conn.close()


if __name__ == "__main__":
    main()
