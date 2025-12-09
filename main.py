import flet as ft
import sqlite3
from pathlib import Path
import threading
import cv2
from pyzbar.pyzbar import decode
import datetime
import base64
import time


# ================== CAPA DE DATOS (SQLite) ==================


class Database:
    def __init__(self, db_path: str | None = None):
        # Usa ./database/supermarket.db
        if db_path is None:
            base_dir = Path(__file__).resolve().parent / "database"
            base_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = base_dir / "supermarket.db"
        else:
            self.db_path = Path(db_path)

    def _get_conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_schema_and_seed(self):
        """
        NO tocamos tus tablas grandes (usuarios, cajas, productos, ventas, etc.).
        Solo aseguramos que existan users/cash_registers/carts/cart_items para el carrito móvil.
        """
        with self._get_conn() as conn:
            cur = conn.cursor()

            # Tabla de usuarios (para el sistema móvil)
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    full_name TEXT,
                    user_type TEXT NOT NULL CHECK(user_type IN ('admin','empleado','caja')),
                    active INTEGER NOT NULL DEFAULT 1
                )
                """
            )

            # Tabla de cajas (móvil)
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS cash_registers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    numero INTEGER NOT NULL,
                    nombre TEXT NOT NULL,
                    ubicacion TEXT,
                    qr_token TEXT UNIQUE NOT NULL,
                    cashier_user_id INTEGER NOT NULL,
                    estado TEXT NOT NULL DEFAULT 'activa',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(cashier_user_id) REFERENCES users(id)
                )
                """
            )

            # Carritos
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS carts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cashier_id INTEGER NOT NULL,
                    status TEXT NOT NULL DEFAULT 'open',
                    created_at TEXT NOT NULL,
                    closed_at TEXT,
                    FOREIGN KEY(cashier_id) REFERENCES cash_registers(id)
                )
                """
            )

            # Ítems de carrito
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS cart_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cart_id INTEGER NOT NULL,
                    product_id INTEGER NOT NULL,
                    quantity INTEGER NOT NULL,
                    unit_price REAL NOT NULL,
                    FOREIGN KEY(cart_id) REFERENCES carts(id)
                )
                """
            )
            # NOTA: el FK a productos no lo forzamos para evitar conflictos con tu esquema.

            # Seed mínimo de users/cash_registers solo si está vacío
            cur.execute("SELECT COUNT(*) AS c FROM users")
            if cur.fetchone()["c"] == 0:
                # Usuarios de prueba para el módulo móvil
                cur.execute(
                    "INSERT INTO users (username, password, full_name, user_type) VALUES (?,?,?,?)",
                    ("admin", "admin123", "Administrador Principal", "admin"),
                )
                cur.execute(
                    "INSERT INTO users (username, password, full_name, user_type) VALUES (?,?,?,?)",
                    ("empleado1", "empleado123", "Empleado 1", "empleado"),
                )
                cur.execute(
                    "INSERT INTO users (username, password, full_name, user_type) VALUES (?,?,?,?)",
                    ("caja1", "caja123", "Caja Principal", "caja"),
                )

                # Obtener id de usuario caja1
                cur.execute("SELECT id FROM users WHERE username = ?", ("caja1",))
                caja_user_id = cur.fetchone()["id"]

                # Caja móvil con QR
                cur.execute(
                    """
                    INSERT INTO cash_registers (numero, nombre, ubicacion, qr_token, cashier_user_id)
                    VALUES (?,?,?,?,?)
                    """,
                    (
                        1,
                        "Caja Móvil 1",
                        "Entrada Principal - Pasillo 1",
                        "CAJA1-SUPER-TOKEN-ABC123XYZ789",
                        caja_user_id,
                    ),
                )

            conn.commit()

    # ---- Cajas / QR (tabla cash_registers del módulo móvil) ----
    def get_cash_register_by_qr(self, qr_token: str):
        with self._get_conn() as conn:
            cur = conn.execute(
                "SELECT * FROM cash_registers WHERE qr_token = ? AND estado = 'activa'",
                (qr_token,),
            )
            return cur.fetchone()

    # ---- Productos (usando tu tabla productos) ----

    def get_product_by_barcode(self, barcode: str):
        """
        Lee de la tabla productos:
        - codigo_barr
        - descripcion
        - precio_venta
        - imagen_url
        y devuelve alias compatibles.
        """
        with self._get_conn() as conn:
            cur = conn.execute(
                """
                SELECT
                    id,
                    descripcion AS name,
                    descripcion AS description,
                    codigo_barr AS barcode,
                    precio_venta AS price,
                    imagen_url AS image_url
                FROM productos
                WHERE codigo_barr = ?
                  AND (activo = 1 OR activo IS NULL)
                """,
                (barcode,)
            )
            return cur.fetchone()

    def list_products(self, search: str = ""):
        """
        Listado de productos desde tabla productos, con alias compatibles.
        """
        with self._get_conn() as conn:
            if search:
                pattern = f"%{search}%"
                cur = conn.execute(
                    """
                    SELECT
                        id,
                        descripcion AS name,
                        descripcion AS description,
                        codigo_barr AS barcode,
                        precio_venta AS price,
                        imagen_url AS image_url
                    FROM productos
                    WHERE (descripcion LIKE ? OR CAST(codigo_barr AS TEXT) LIKE ?)
                      AND (activo = 1 OR activo IS NULL)
                    ORDER BY descripcion
                    """,
                    (pattern, pattern),
                )
            else:
                cur = conn.execute(
                    """
                    SELECT
                        id,
                        descripcion AS name,
                        descripcion AS description,
                        codigo_barr AS barcode,
                        precio_venta AS price,
                        imagen_url AS image_url
                    FROM productos
                    WHERE (activo = 1 OR activo IS NULL)
                    ORDER BY descripcion
                    """
                )
            return cur.fetchall()

    # ---- Carrito (carts / cart_items) ----

    def create_cart(self, cashier_id: int) -> int:
        now = datetime.datetime.now().isoformat(sep=" ", timespec="seconds")
        with self._get_conn() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO carts (cashier_id, status, created_at)
                VALUES (?,?,?)
                """,
                (cashier_id, "open", now),
            )
            return cur.lastrowid

    def add_item_to_cart(self, cart_id: int, product_id: int, quantity: int, unit_price: float):
        with self._get_conn() as conn:
            cur = conn.cursor()
            # Si ya existe ítem de ese producto, solo sumamos cantidad
            cur.execute(
                """
                SELECT id, quantity FROM cart_items
                WHERE cart_id = ? AND product_id = ?
                """,
                (cart_id, product_id),
            )
            existing = cur.fetchone()
            if existing:
                new_qty = existing["quantity"] + quantity
                cur.execute(
                    "UPDATE cart_items SET quantity = ? WHERE id = ?",
                    (new_qty, existing["id"]),
                )
            else:
                cur.execute(
                    """
                    INSERT INTO cart_items (cart_id, product_id, quantity, unit_price)
                    VALUES (?,?,?,?)
                    """,
                    (cart_id, product_id, quantity, unit_price),
                )

    def remove_cart_item(self, cart_item_id: int):
        with self._get_conn() as conn:
            conn.execute("DELETE FROM cart_items WHERE id = ?", (cart_item_id,))

    def get_cart_items(self, cart_id: int):
        """
        Devuelve ítems del carrito + datos de producto (tabla productos).
        """
        with self._get_conn() as conn:
            cur = conn.execute(
                """
                SELECT
                    ci.id,
                    ci.product_id,
                    ci.quantity,
                    ci.unit_price,
                    p.descripcion AS name,
                    p.codigo_barr AS barcode
                FROM cart_items ci
                JOIN productos p ON p.id = ci.product_id
                WHERE ci.cart_id = ?
                """,
                (cart_id,),
            )
            return cur.fetchall()

    def close_cart(self, cart_id: int):
        now = datetime.datetime.now().isoformat(sep=" ", timespec="seconds")
        with self._get_conn() as conn:
            conn.execute(
                """
                UPDATE carts
                SET status = 'closed', closed_at = ?
                WHERE id = ?
                """,
                (now, cart_id),
            )

    # ---- Registrar venta real en tus tablas ventas / detalle_ventas ----

    def create_sale_from_cart(self, cart_id: int, caja_numero: int | None = None) -> int | None:
        """
        Toma los ítems del carrito y crea:
        - una fila en ventas
        - varias filas en detalle_ventas
        Usando tus tablas: usuarios, cajas, aperturas_caja, ventas, detalle_ventas.
        """
        with self._get_conn() as conn:
            cur = conn.cursor()

            items = self.get_cart_items(cart_id)
            if not items:
                return None

            # Total del carrito
            subtotal = 0
            for it in items:
                subtotal += float(it["quantity"]) * float(it["unit_price"])

            # Usuario (primer usuario activo)
            cur.execute(
                "SELECT id FROM usuarios WHERE activo = 1 ORDER BY id LIMIT 1"
            )
            row_user = cur.fetchone()
            if row_user is None:
                raise RuntimeError("No hay usuarios activos en la tabla 'usuarios'.")
            usuario_id = row_user["id"]

            # Caja: intentamos usar el número escaneado
            row_caja = None
            if caja_numero is not None:
                cur.execute(
                    "SELECT id FROM cajas WHERE numero = ? ORDER BY id LIMIT 1",
                    (caja_numero,),
                )
                row_caja = cur.fetchone()

            if row_caja is None:
                cur.execute("SELECT id FROM cajas ORDER BY id LIMIT 1")
                row_caja = cur.fetchone()

            if row_caja is None:
                raise RuntimeError("No hay cajas definidas en la tabla 'cajas'.")

            caja_id = row_caja["id"]

            # Apertura de caja abierta para esa caja (o crear una)
            cur.execute(
                """
                SELECT id FROM aperturas_caja
                WHERE caja_id = ? AND estado = 'abierta'
                ORDER BY fecha_apertura DESC
                LIMIT 1
                """,
                (caja_id,),
            )
            row_ap = cur.fetchone()
            if row_ap is None:
                cur.execute(
                    """
                    INSERT INTO aperturas_caja (caja_id, usuario_id, monto_inicial, estado)
                    VALUES (?,?,0,'abierta')
                    """,
                    (caja_id, usuario_id),
                )
                apertura_id = cur.lastrowid
            else:
                apertura_id = row_ap["id"]

            # Generar número de ticket
            numero_ticket = datetime.datetime.now().strftime("M%Y%m%d%H%M%S")

            # Insertar venta
            cur.execute(
                """
                INSERT INTO ventas (
                    numero_ticket, caja_id, usuario_id, apertura_id,
                    cliente_nombre, cliente_ruc,
                    subtotal, descuento, iva, total,
                    forma_pago, estado
                )
                VALUES (?,?,?,?,NULL,NULL, ?,0,0,?,'efectivo','completada')
                """,
                (
                    numero_ticket,
                    caja_id,
                    usuario_id,
                    apertura_id,
                    subtotal,
                    subtotal,
                ),
            )
            venta_id = cur.lastrowid

            # Insertar detalle_ventas (disparará triggers de stock y totales)
            for it in items:
                cantidad = float(it["quantity"])
                precio = float(it["unit_price"])
                sub = cantidad * precio
                cur.execute(
                    """
                    INSERT INTO detalle_ventas (
                        venta_id, producto_id, cantidad, precio_unitario, subtotal
                    ) VALUES (?,?,?,?,?)
                    """,
                    (
                        venta_id,
                        it["product_id"],
                        cantidad,
                        precio,
                        sub,
                    ),
                )

            conn.commit()
            return venta_id


# ================== ESTADO GLOBAL SENCILLO ==================


class AppState:
    def __init__(self, db: Database):
        self.db = db
        self.cash_register = None  # Row de la caja (cash_registers)
        self.cart_id: int | None = None
        self.qr_scanning = False
        self.barcode_scanning = False   # escáner de barras


# ================== UI EN FLET ==================


def main(page: ft.Page):
    page.title = "Mobile Cart - Supermarket"
    page.vertical_alignment = ft.MainAxisAlignment.START
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window_width = 390
    page.window_height = 844

    db = Database()
    db.init_schema_and_seed()
    state = AppState(db)

    status_text = ft.Text("", color=ft.Colors.RED)

    # Vista previa cámara QR (oculta por defecto)
    camera_image = ft.Image(
        width=300,
        height=300,
        fit=ft.ImageFit.CONTAIN,
        border_radius=10,
        gapless_playback=True,
        visible=False,
    )

    # Vista previa cámara código de barras (oculta por defecto)
    barcode_camera_image = ft.Image(
        width=250,
        height=250,
        fit=ft.ImageFit.CONTAIN,
        border_radius=10,
        gapless_playback=True,
        visible=False,
    )

    # ----------- PANTALLA 1: SELECCIÓN DE CAJA POR QR -----------

    qr_input = ft.TextField(
        label="QR de caja (token)",
        hint_text="Escanea o pega el código",
        expand=True,
    )

    def on_qr_detected(token: str):
        qr_input.value = token
        status_text.value = f"QR detectado: {token}"
        page.update()
        process_qr_token(token)

    def qr_scan_thread():
        state.qr_scanning = True
        cap = cv2.VideoCapture(0)
        last_data = None
        stable_count = 0

        if not cap.isOpened():
            status_text.value = "No se pudo abrir la cámara."
            page.update()
            state.qr_scanning = False
            camera_image.visible = False
            camera_image.update()
            return

        while state.qr_scanning:
            ret, frame = cap.read()
            if not ret:
                status_text.value = "No se pudo leer la cámara."
                page.update()
                break

            # Mostrar preview
            try:
                ok, buffer = cv2.imencode(".jpg", frame)
                if ok:
                    img_b64 = base64.b64encode(buffer).decode("utf-8")
                    camera_image.src_base64 = img_b64
                    camera_image.update()
            except Exception as ex:
                status_text.value = f"Error mostrando cámara: {ex}"
                page.update()

            # Leer QR
            codes = decode(frame)
            if codes:
                data = codes[0].data.decode("utf-8")
                if data == last_data:
                    stable_count += 1
                else:
                    last_data = data
                    stable_count = 1

                if stable_count >= 5:
                    state.qr_scanning = False
                    cap.release()
                    cv2.destroyAllWindows()
                    camera_image.visible = False
                    camera_image.update()
                    on_qr_detected(data)
                    return

            cv2.waitKey(1)
            time.sleep(0.03)

        cap.release()
        cv2.destroyAllWindows()
        state.qr_scanning = False
        camera_image.visible = False
        camera_image.update()

    def start_qr_scan(e):
        if state.qr_scanning:
            status_text.value = "Ya se está escaneando el QR..."
            page.update()
            return
        status_text.value = "Apunta la cámara al código QR de la caja..."
        camera_image.visible = True
        camera_image.update()
        page.update()
        threading.Thread(target=qr_scan_thread, daemon=True).start()

    def process_qr_token(token: str):
        token = token.strip()
        if not token:
            status_text.value = "Ingresa o escanea un QR válido."
            page.update()
            return

        caja = db.get_cash_register_by_qr(token)
        if caja is None:
            status_text.value = "No se encontró una caja activa para ese QR."
            page.update()
            return

        state.cash_register = caja
        state.cart_id = db.create_cart(caja["id"])
        status_text.value = ""
        show_cart_view()

    def on_qr_continue(e):
        process_qr_token(qr_input.value)

    qr_scan_button = ft.ElevatedButton(
        text="Escanear QR con cámara",
        icon=ft.Icons.QR_CODE_SCANNER,
        on_click=start_qr_scan,
    )

    qr_continue_button = ft.FilledButton(
        text="Continuar",
        icon=ft.Icons.ARROW_FORWARD,
        on_click=on_qr_continue,
    )

    qr_view = ft.Column(
        [
            ft.Text(
                "Sistema de carrito móvil",
                style=ft.TextThemeStyle.HEADLINE_MEDIUM,
                text_align=ft.TextAlign.CENTER,
            ),
            ft.Text(
                "Escaneá el QR de la caja para comenzar tu compra.",
                text_align=ft.TextAlign.CENTER,
            ),
            camera_image,
            qr_input,
            qr_scan_button,
            qr_continue_button,
            status_text,
        ],
        alignment=ft.MainAxisAlignment.START,
        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        expand=True,
    )

    # ----------- PANTALLA 2: CARRITO -----------

    barcode_input = ft.TextField(
        label="Código de barras",
        hint_text="Escanear o escribir código de barras",
        expand=True,
    )

    cart_rows: list[ft.DataRow] = []
    cart_table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("Producto")),
            ft.DataColumn(ft.Text("Cant.")),
            ft.DataColumn(ft.Text("P. Unit.")),
            ft.DataColumn(ft.Text("Subtotal")),
            ft.DataColumn(ft.Text("Acciones")),
        ],
        rows=cart_rows,
        column_spacing=10,
        heading_row_height=32,
        data_row_min_height=32,
    )

    total_text = ft.Text(
        "Total: 0 Gs.",
        style=ft.TextThemeStyle.TITLE_MEDIUM,
        weight=ft.FontWeight.BOLD,
    )

    def on_delete_cart_item(cart_item_id: int):
        if state.cart_id is None:
            return
        db.remove_cart_item(cart_item_id)
        refresh_cart_table()

    def refresh_cart_table():
        if state.cart_id is None:
            return
        items = db.get_cart_items(state.cart_id)
        cart_table.rows.clear()
        total = 0.0
        for it in items:
            subtotal = float(it["quantity"]) * float(it["unit_price"])
            total += subtotal
            cart_item_id = it["id"]
            cart_table.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(it["name"])),
                        ft.DataCell(ft.Text(str(it["quantity"]))),
                        ft.DataCell(ft.Text(f"{it['unit_price']:,.2f}")),
                        ft.DataCell(ft.Text(f"{subtotal:,.2f}")),
                        ft.DataCell(
                            ft.IconButton(
                                icon=ft.Icons.DELETE,
                                tooltip="Eliminar",
                                on_click=lambda e, cid=cart_item_id: on_delete_cart_item(
                                    cid
                                ),
                            )
                        ),
                    ]
                )
            )
        total_text.value = f"Total: {total:,.2f} Gs."
        page.update()

    def add_product_to_cart(product_row, qty: int = 1):
        if state.cart_id is None:
            status_text.value = "No hay un carrito activo."
            page.update()
            return
        db.add_item_to_cart(
            state.cart_id,
            product_row["id"],
            qty,
            float(product_row["price"]),
        )
        status_text.value = f"Se agregó {product_row['name']} x{qty}."
        refresh_cart_table()

    def on_add_by_barcode(e):
        code = barcode_input.value.strip()
        if not code:
            status_text.value = "Ingresa un código de barras."
            page.update()
            return
        prod = db.get_product_by_barcode(code)
        if prod is None:
            status_text.value = f"Producto no encontrado para el código {code}."
            page.update()
            return
        add_product_to_cart(prod, qty=1)
        barcode_input.value = ""
        page.update()

    # --- escáner de código de barras con cámara ---

    def on_barcode_detected(code: str):
        barcode_input.value = code
        page.update()
        on_add_by_barcode(None)

    def barcode_scan_thread():
        state.barcode_scanning = True
        cap = cv2.VideoCapture(0)
        last_data = None
        stable_count = 0

        if not cap.isOpened():
            status_text.value = "No se pudo abrir la cámara para barras."
            page.update()
            state.barcode_scanning = False
            barcode_camera_image.visible = False
            barcode_camera_image.update()
            return

        while state.barcode_scanning:
            ret, frame = cap.read()
            if not ret:
                status_text.value = "No se pudo leer la cámara (barras)."
                page.update()
                break

            # preview
            try:
                ok, buffer = cv2.imencode(".jpg", frame)
                if ok:
                    img_b64 = base64.b64encode(buffer).decode("utf-8")
                    barcode_camera_image.src_base64 = img_b64
                    barcode_camera_image.update()
            except Exception as ex:
                status_text.value = f"Error mostrando cámara (barras): {ex}"
                page.update()

            codes = decode(frame)
            if codes:
                data = codes[0].data.decode("utf-8")
                if data == last_data:
                    stable_count += 1
                else:
                    last_data = data
                    stable_count = 1

                if stable_count >= 5:
                    state.barcode_scanning = False
                    cap.release()
                    cv2.destroyAllWindows()
                    barcode_camera_image.visible = False
                    barcode_camera_image.update()
                    on_barcode_detected(data)
                    return

            cv2.waitKey(1)
            time.sleep(0.03)

        cap.release()
        cv2.destroyAllWindows()
        state.barcode_scanning = False
        barcode_camera_image.visible = False
        barcode_camera_image.update()

    def start_barcode_scan(e):
        if state.barcode_scanning:
            status_text.value = "Ya se está escaneando el código de barras..."
            page.update()
            return
        status_text.value = "Apunta la cámara al código de barras del producto..."
        barcode_camera_image.visible = True
        barcode_camera_image.update()
        page.update()
        threading.Thread(target=barcode_scan_thread, daemon=True).start()

    add_barcode_button = ft.FilledButton(
        text="Agregar por código de barras",
        icon=ft.Icons.BARCODE_READER,
        on_click=on_add_by_barcode,
    )

    scan_barcode_button = ft.OutlinedButton(
        text="Escanear con cámara",
        icon=ft.Icons.QR_CODE_SCANNER,
        on_click=start_barcode_scan,
    )

    # ---- listado de productos desde BD (tabla productos) ----

    def open_product_list_dialog(e):
        search_field = ft.TextField(
            label="Buscar producto",
            autofocus=True,
            on_change=lambda ev: update_product_list(ev.control.value),
        )

        product_list_column = ft.Column(
            spacing=5,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

        def update_product_list(search_text: str = ""):
            product_list_column.controls.clear()
            products = db.list_products(search_text)
            if not products:
                product_list_column.controls.append(
                    ft.Text("No se encontraron productos.", italic=True)
                )
            else:
                for p in products:
                    tile = ft.ListTile(
                        leading=ft.Image(
                            src=p["image_url"] or "",
                            width=40,
                            height=40,
                            fit=ft.ImageFit.COVER,
                        ),
                        title=ft.Text(p["name"]),
                        subtitle=ft.Text(
                            f"{p['description'] or ''}\nCod: {p['barcode']} - {p['price']:,.2f} Gs."
                        ),
                        trailing=ft.IconButton(
                            icon=ft.Icons.ADD,
                            on_click=lambda ev, prod=p: (
                                add_product_to_cart(prod, qty=1),
                                close_dialog()
                            ),
                        ),
                    )
                    product_list_column.controls.append(tile)

            page.update()

        def close_dialog(*_):
            page.dialog.open = False
            page.update()

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("Seleccionar producto"),
            content=ft.Container(
                content=ft.Column(
                    [
                        search_field,
                        ft.Divider(),
                        product_list_column,
                    ],
                    expand=True,
                ),
                width=350,
                height=400,
            ),
            actions=[ft.TextButton("Cerrar", on_click=close_dialog)],
        )

        page.dialog = dlg
        page.dialog.open = True
        update_product_list("")
        page.update()

    add_from_list_button = ft.OutlinedButton(
        text="Agregar desde listado",
        icon=ft.Icons.LIST,
        on_click=open_product_list_dialog,
    )

    def on_finish_cart(e):
        if state.cart_id is None:
            status_text.value = "No hay carrito para finalizar."
            page.update()
            return

        try:
            caja_numero = state.cash_register["numero"] if state.cash_register else None
            venta_id = db.create_sale_from_cart(state.cart_id, caja_numero=caja_numero)
            if venta_id is None:
                status_text.value = "El carrito está vacío, no se generó venta."
                page.update()
                return

            # Cerrar carrito
            db.close_cart(state.cart_id)

            status_text.value = f"Compra finalizada. Venta registrada (ID: {venta_id})."
            # Limpiamos estado y volvemos a pantalla de QR
            state.cart_id = None
            state.cash_register = None
            show_qr_view()
        except Exception as ex:
            status_text.value = f"Error al registrar la venta: {ex}"
            page.update()

    finish_button = ft.FilledButton(
        text="Finalizar compra",
        icon=ft.Icons.CHECK_CIRCLE,
        on_click=on_finish_cart,
    )

    def show_cart_view():
        cashier_name = (
            state.cash_register["nombre"] if state.cash_register else "Sin caja"
        )
        page.controls.clear()
        page.appbar = ft.AppBar(
            title=ft.Text(f"Carrito - {cashier_name}"),
            center_title=True,
        )
        content = ft.Column(
            [
                ft.Text(
                    "Agregá tus productos al carrito:",
                    style=ft.TextThemeStyle.TITLE_MEDIUM,
                ),
                ft.Row(
                    [barcode_input],
                    alignment=ft.MainAxisAlignment.START,
                ),
                ft.Row(
                    [add_barcode_button, scan_barcode_button],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                barcode_camera_image,
                ft.Row(
                    [add_from_list_button, finish_button],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                ft.Divider(),
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text(
                                "Productos en el carrito:",
                                style=ft.TextThemeStyle.TITLE_SMALL,
                            ),
                            ft.Container(
                                content=cart_table,
                                expand=True,
                            ),
                        ],
                        expand=True,
                    ),
                    expand=True,
                ),
                total_text,
                status_text,
            ],
            expand=True,
        )
        page.controls.append(content)
        refresh_cart_table()
        page.update()

    def show_qr_view():
        page.controls.clear()
        page.appbar = ft.AppBar(
            title=ft.Text("Seleccionar caja"),
            center_title=True,
        )
        camera_image.visible = False
        barcode_camera_image.visible = False
        page.add(qr_view)
        page.update()

    # Iniciar en pantalla de QR
    show_qr_view()


if __name__ == "__main__":
    ft.app(target=main)