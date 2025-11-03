import flet as ft
import cv2
from pyzbar.pyzbar import decode
import threading
import time

def main(page: ft.Page):
    # Configuración de la página
    page.title = "Supermercado X"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0
    
    # Variables de estado
    current_view = "qr_reader"
    camera_active = False
    cap = None
    
    def show_qr_reader():
        nonlocal current_view, camera_active, cap
        current_view = "qr_reader"
        page.controls.clear()
        camera_active = False
        
        # Detener cámara si estaba activa
        if cap is not None:
            cap.release()
            cv2.destroyAllWindows()
        
        def start_camera(e):
            nonlocal camera_active, cap
            if not camera_active:
                try:
                    # Intentar abrir cámara
                    cap = cv2.VideoCapture(0)
                    if not cap.isOpened():
                        page.show_snack_bar(ft.SnackBar(ft.Text("❌ No se pudo acceder a la cámara")))
                        return
                    
                    camera_active = True
                    start_btn.text = "Detener Cámara"
                    start_btn.bgcolor = "#ff4444"
                    status_text.value = "🔍 Escaneando QR... Apunta al código"
                    status_text.color = "#4CAF50"
                    page.update()
                    
                    # Iniciar hilo para lectura de QR
                    threading.Thread(target=read_qr, daemon=True).start()
                    
                except Exception as ex:
                    page.show_snack_bar(ft.SnackBar(ft.Text(f"❌ Error de cámara: {str(ex)}")))
        
        def stop_camera():
            nonlocal camera_active
            camera_active = False
            start_btn.text = "Iniciar Cámara"
            start_btn.bgcolor = "#4CAF50"
            status_text.value = "Cámara detenida"
            status_text.color = "gray"
            page.update()
        
        def read_qr():
            nonlocal camera_active
            while camera_active:
                try:
                    ret, frame = cap.read()
                    if not ret:
                        break
                    
                    # Decodificar QR
                    decoded_objects = decode(frame)
                    for obj in decoded_objects:
                        qr_data = obj.data.decode('utf-8')
                        print(f"QR detectado: {qr_data}")
                        
                        # Detener cámara y procesar QR
                        stop_camera()
                        page.show_snack_bar(ft.SnackBar(ft.Text(f"✅ QR detectado: {qr_data}")))
                        process_qr_data(qr_data)
                        return
                    
                    time.sleep(0.1)
                except Exception as ex:
                    print(f"Error en lectura QR: {ex}")
                    break
        
        # Elementos de la UI
        status_text = ft.Text("Presiona 'Iniciar Cámara' para escanear QR", size=16, color="gray", text_align=ft.TextAlign.CENTER)
        
        start_btn = ft.ElevatedButton(
            "Iniciar Cámara",
            icon=ft.Icons.CAMERA_ALT,
            on_click=start_camera,
            bgcolor="#4CAF50",
            color="white",
            width=200
        )
        
        qr_content = ft.Container(
            content=ft.Column([
                ft.Icon(ft.Icons.QR_CODE_SCANNER, size=80, color="#4CAF50"),
                ft.Text("Escanear QR del Carrito", size=22, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
                ft.Container(height=10),
                status_text,
                ft.Container(height=30),
                
                # Botones
                start_btn,
                ft.Container(height=20),
                
                ft.Row([
                    ft.TextButton(
                        "Código Manual",
                        icon=ft.Icons.KEYBOARD,
                        on_click=show_manual_input
                    ),
                    ft.TextButton(
                        "Demo Rápida",
                        icon=ft.Icons.FLASH_ON,
                        on_click=login_successful
                    )
                ], alignment=ft.MainAxisAlignment.CENTER),
                
                ft.Container(height=20),
                ft.Text("Nota: En Android, la app solicitará permisos de cámara automáticamente", 
                       size=12, color="gray", text_align=ft.TextAlign.CENTER)
                
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, alignment=ft.MainAxisAlignment.CENTER),
            padding=20,
            alignment=ft.alignment.center,
            expand=True
        )
        
        page.add(qr_content)
    
    def show_manual_input(e=None):
        def submit_code(e):
            code = code_field.value.strip()
            if code:
                process_qr_data(f"carrito_{code}")
                page.close(manual_dialog)
            else:
                page.show_snack_bar(ft.SnackBar(ft.Text("❌ Ingresa un código válido")))
        
        code_field = ft.TextField(
            label="Código del carrito",
            hint_text="Ej: CAR12345",
            width=250,
            autofocus=True
        )
        
        manual_dialog = ft.AlertDialog(
            title=ft.Text("Ingresar Código Manualmente"),
            content=ft.Column([
                ft.Text("Si no puedes escanear el QR, ingresa el código del carrito:"),
                ft.Container(height=10),
                code_field
            ], tight=True),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: page.close(manual_dialog)),
                ft.ElevatedButton("Aceptar", on_click=submit_code, bgcolor="#4CAF50")
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )
        
        page.open(manual_dialog)
    
    def process_qr_data(qr_data):
        """Procesa los datos del QR escaneado"""
        # Procesar datos del QR
        qr_data_lower = qr_data.lower()
        
        # Verificar si es un QR válido de carrito
        if any(keyword in qr_data_lower for keyword in ['carrito', 'cart', 'user', 'usuario', 'client', 'shopping']):
            page.show_snack_bar(ft.SnackBar(ft.Text(f"✅ Carrito asignado: {qr_data}")))
            login_successful()
        else:
            page.show_snack_bar(ft.SnackBar(ft.Text("❌ QR no válido. Debe ser de un carrito.")))
    
    def login_successful(e=None):
        nonlocal current_view, camera_active, cap
        current_view = "main_app"
        
        # Detener cámara si está activa
        if camera_active:
            camera_active = False
            if cap is not None:
                cap.release()
                cv2.destroyAllWindows()
        
        show_main_app()
    
    def logout(e):
        nonlocal current_view
        current_view = "qr_reader"
        page.drawer.open = False
        page.update()
        show_qr_reader()

    # Funciones del drawer principal
    def open_drawer(e):
        page.drawer.open = True
        page.update()
    
    def menu_item_clicked(e):
        page.show_snack_bar(ft.SnackBar(ft.Text(f"Seleccionado: {e.control.data}")))
        page.drawer.open = False
        page.update()

    def show_main_app():
        page.controls.clear()
        
        # HEADER PRINCIPAL
        header = ft.Container(
            content=ft.Row(
                controls=[
                    ft.IconButton(
                        icon=ft.Icons.MENU,
                        icon_color="white",
                        on_click=open_drawer,
                        tooltip="Menú"
                    ),
                    ft.Text(
                        "Supermercado X", 
                        size=20, 
                        weight=ft.FontWeight.BOLD, 
                        color="white",
                        expand=True,
                        text_align=ft.TextAlign.CENTER
                    ),
                    ft.IconButton(
                        icon=ft.Icons.SHOPPING_CART,
                        icon_color="white",
                        on_click=lambda e: page.show_snack_bar(ft.SnackBar(ft.Text("Carrito abierto"))),
                        tooltip="Carrito"
                    )
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER
            ),
            bgcolor="#4CAF50",
            padding=ft.padding.symmetric(horizontal=10, vertical=5),
            height=60
        )
        
        # DRAWER
        page.drawer = ft.NavigationDrawer(
            bgcolor="#2e7d32",
            controls=[
                # Header del drawer
                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.STORE, color="white", size=30),
                        ft.Text("Supermercado X", color="white", size=18, weight=ft.FontWeight.BOLD),
                    ]),
                    padding=20,
                    bgcolor="#1b5e20",
                ),
                
                # Items del menú
                ft.Container(
                    content=ft.ListTile(
                        leading=ft.Icon(ft.Icons.HOME, color="white"),
                        title=ft.Text("Inicio", color="white"),
                        on_click=menu_item_clicked,
                        data="Inicio"
                    ),
                    bgcolor="#2e7d32",
                ),
                ft.Container(
                    content=ft.ListTile(
                        leading=ft.Icon(ft.Icons.SHOPPING_BAG, color="white"),
                        title=ft.Text("Productos", color="white"),
                        on_click=menu_item_clicked,
                        data="Productos"
                    ),
                    bgcolor="#2e7d32",
                ),
                ft.Container(
                    content=ft.ListTile(
                        leading=ft.Icon(ft.Icons.LOCAL_OFFER, color="white"),
                        title=ft.Text("Ofertas", color="white"),
                        on_click=menu_item_clicked,
                        data="Ofertas"
                    ),
                    bgcolor="#2e7d32",
                ),
                ft.Container(
                    content=ft.ListTile(
                        leading=ft.Icon(ft.Icons.SHOPPING_CART, color="white"),
                        title=ft.Text("Mi Carrito", color="white"),
                        on_click=menu_item_clicked,
                        data="Mi Carrito"
                    ),
                    bgcolor="#2e7d32",
                ),
                
                # Espacio flexible
                ft.Container(expand=True),
                
                
                # FOOTER
                ft.Container(
                    content=ft.Column([
                        ft.Divider(color="white"),
                        ft.Text("Soporte 24/7", color="white", size=12, weight=ft.FontWeight.BOLD),
                        ft.Row([
                            ft.Icon(ft.Icons.PHONE, color="white", size=16),
                            ft.Text("+1 234 567 890", color="white", size=12),
                        ]),
                        ft.Container(height=5),
                        ft.Text("App Móvil v1.0", color="white", size=10),
                    ], spacing=5),
                    padding=10,
                    bgcolor="#1b5e20",
                )
            ],
        )
        
        # CONTENIDO PRINCIPAL
        frame1 = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        "¡Bienvenido!",
                        size=18,
                        weight=ft.FontWeight.BOLD,
                        color="white"
                    ),
                    ft.Text(
                        "Sesión iniciada con QR",
                        size=14,
                        color="white"
                    ),
                    ft.ElevatedButton(
                        "Comenzar a Comprar",
                        bgcolor="white",
                        color="#4CAF50",
                        on_click=lambda e: page.show_snack_bar(ft.SnackBar(ft.Text("Navegando a productos")))
                    )
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER
            ),
            gradient=ft.LinearGradient(
                begin=ft.alignment.top_left,
                end=ft.alignment.bottom_right,
                colors=["#4CAF50", "#45a049"]
            ),
            height=150,
            border_radius=10,
            margin=10,
            padding=15,
            alignment=ft.alignment.center
        )
        
        frame2 = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Text(
                                "Categorías",
                                size=18,
                                weight=ft.FontWeight.BOLD,
                                expand=True
                            ),
                            ft.TextButton(
                                "Ver todas",
                                on_click=lambda e: page.show_snack_bar(ft.SnackBar(ft.Text("Todas las categorías")))
                            )
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                    ),
                    ft.Row(
                        controls=[
                            ft.Container(
                                content=ft.Column(
                                    controls=[
                                        ft.Icon(ft.Icons.KITCHEN, size=40, color="#4CAF50"),
                                        ft.Text("Despensa", size=12, text_align=ft.TextAlign.CENTER)
                                    ],
                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                    spacing=5
                                ),
                                padding=10,
                                width=80,
                                height=80,
                                bgcolor="white",
                                border_radius=10,
                                on_click=lambda e: page.show_snack_bar(ft.SnackBar(ft.Text("Despensa")))
                            ),
                            ft.Container(
                                content=ft.Column(
                                    controls=[
                                        ft.Icon(ft.Icons.LOCAL_DRINK, size=40, color="#4CAF50"),
                                        ft.Text("Bebidas", size=12, text_align=ft.TextAlign.CENTER)
                                    ],
                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                    spacing=5
                                ),
                                padding=10,
                                width=80,
                                height=80,
                                bgcolor="white",
                                border_radius=10,
                                on_click=lambda e: page.show_snack_bar(ft.SnackBar(ft.Text("Bebidas")))
                            ),
                            ft.Container(
                                content=ft.Column(
                                    controls=[
                                        ft.Icon(ft.Icons.KITCHEN, size=40, color="#4CAF50"),
                                        ft.Text("Lácteos", size=12, text_align=ft.TextAlign.CENTER)
                                    ],
                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                    spacing=5
                                ),
                                padding=10,
                                width=80,
                                height=80,
                                bgcolor="white",
                                border_radius=10,
                                on_click=lambda e: page.show_snack_bar(ft.SnackBar(ft.Text("Lácteos")))
                            ),
                        ],
                        scroll=ft.ScrollMode.AUTO,
                        spacing=10
                    )
                ],
                spacing=15
            ),
            bgcolor="white",
            padding=15,
            margin=10,
            border_radius=10
        )
        
        main_content = ft.ListView(
            controls=[
                frame1,
                frame2
            ],
            expand=True,
            spacing=0,
            padding=0
        )
        
        page.add(
            ft.Column(
                controls=[
                    header,
                    main_content
                ],
                expand=True,
                spacing=0
            )
        )

    # Iniciar con el lector de QR
    show_qr_reader()

# Ejecutar sin el parámetro permissions
ft.app(target=main)