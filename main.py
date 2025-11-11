import flet as ft
import cv2
from pyzbar.pyzbar import decode
import threading
import time
import base64
import numpy as np

def main(page: ft.Page):
    # Configuración de la página
    page.title = "Supermercado X"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0
    
    # Variables de estado
    current_view = "qr_reader"
    camera_active = False
    cap = None
    shopping_cart = []
    
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
    
    def show_qr_reader():
        nonlocal current_view, camera_active, cap
        current_view = "qr_reader"
        page.controls.clear()
        camera_active = False
        
        # Detener cámara si estaba activa
        if cap is not None:
            cap.release()
            cv2.destroyAllWindows()
        
        # Elemento para mostrar la cámara
        camera_display = ft.Image(
            src_base64=None,
            width=300,
            height=300,
            fit=ft.ImageFit.CONTAIN,
            border_radius=10,
            visible=False
        )
        
        def start_camera(e):
            nonlocal camera_active, cap
            if not camera_active:
                try:
                    # Intentar abrir cámara
                    cap = cv2.VideoCapture(0)
                    if not cap.isOpened():
                        page.show_snack_bar(ft.SnackBar(ft.Text("❌ No se pudo acceder a la cámara")))
                        return
                    
                    # Configurar resolución para móvil
                    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                    cap.set(cv2.CAP_PROP_FPS, 30)
                    
                    camera_active = True
                    start_btn.text = "Detener Cámara"
                    start_btn.bgcolor = "#ff4444"
                    status_text.value = "🔍 Escaneando QR... Apunta al código"
                    status_text.color = "#4CAF50"
                    camera_display.visible = True
                    page.update()
                    
                    # Iniciar hilo para mostrar cámara y lectura de QR
                    threading.Thread(target=update_camera_display, daemon=True).start()
                    
                except Exception as ex:
                    page.show_snack_bar(ft.SnackBar(ft.Text(f"❌ Error de cámara: {str(ex)}")))
        
        def stop_camera():
            nonlocal camera_active
            camera_active = False
            start_btn.text = "Iniciar Cámara"
            start_btn.bgcolor = "#4CAF50"
            status_text.value = "Cámara detenida"
            status_text.color = "gray"
            camera_display.visible = False
            page.update()
        
        def update_camera_display():
            nonlocal camera_active
            while camera_active:
                try:
                    ret, frame = cap.read()
                    if not ret:
                        break
                    
                    # Redimensionar frame para móvil
                    frame = cv2.resize(frame, (300, 300))
                    
                    # Dibujar rectángulo de escaneo
                    height, width = frame.shape[:2]
                    center_x, center_y = width // 2, height // 2
                    scan_size = 200
                    
                    # Rectángulo de escaneo en el centro
                    cv2.rectangle(frame, 
                                (center_x - scan_size//2, center_y - scan_size//2),
                                (center_x + scan_size//2, center_y + scan_size//2),
                                (0, 255, 0), 2)
                    
                    # Convertir frame a base64 para mostrar en Flet
                    _, buffer = cv2.imencode('.jpg', frame)
                    frame_base64 = base64.b64encode(buffer).decode('utf-8')
                    
                    # Actualizar imagen en la UI
                    camera_display.src_base64 = frame_base64
                    page.update()
                    
                    # Decodificar QR (solo en el área de escaneo)
                    try:
                        # Recortar área de escaneo
                        scan_area = frame[center_y-scan_size//2:center_y+scan_size//2, 
                                        center_x-scan_size//2:center_x+scan_size//2]
                        
                        decoded_objects = decode(scan_area)
                        for obj in decoded_objects:
                            qr_data = obj.data.decode('utf-8')
                            print(f"QR detectado: {qr_data}")
                            
                            # Dibujar resultado en el frame
                            cv2.putText(frame, "✅ QR DETECTADO", (50, 50), 
                                      cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                            
                            # Actualizar frame final
                            _, final_buffer = cv2.imencode('.jpg', frame)
                            final_base64 = base64.b64encode(final_buffer).decode('utf-8')
                            camera_display.src_base64 = final_base64
                            page.update()
                            
                            # Detener cámara y procesar QR
                            time.sleep(1)  # Mostrar confirmación por 1 segundo
                            stop_camera()
                            page.show_snack_bar(ft.SnackBar(ft.Text(f"✅ QR detectado: {qr_data}")))
                            process_qr_data(qr_data)
                            return
                    
                    except Exception as qr_error:
                        print(f"Error en decodificación QR: {qr_error}")
                    
                    time.sleep(0.03)  # ~30 FPS
                    
                except Exception as ex:
                    print(f"Error en actualización de cámara: {ex}")
                    break
        
        # Elementos de la UI
        status_text = ft.Text("Presiona 'Iniciar Cámara' para escanear QR", 
                             size=16, color="gray", text_align=ft.TextAlign.CENTER)
        
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
                ft.Text("Escanear QR del Carrito", size=22, weight=ft.FontWeight.BOLD, 
                       text_align=ft.TextAlign.CENTER),
                ft.Container(height=10),
                status_text,
                ft.Container(height=20),
                
                # Contenedor de la cámara
                ft.Container(
                    content=camera_display,
                    alignment=ft.alignment.center,
                    bgcolor="#f5f5f5",
                    border_radius=10,
                    padding=10,
                    border=ft.border.all(2, "#e0e0e0")
                ),
                ft.Container(height=20),
                
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
                        on_click=lambda e: login_successful()
                    )
                ], alignment=ft.MainAxisAlignment.CENTER),
                
                ft.Container(height=20),
                ft.Text("Nota: Apunta el código QR al cuadro verde de escaneo", 
                       size=12, color="gray", text_align=ft.TextAlign.CENTER),
                ft.Text("La app solicitará permisos de cámara automáticamente", 
                       size=12, color="gray", text_align=ft.TextAlign.CENTER)
                
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, 
               alignment=ft.MainAxisAlignment.CENTER,
               scroll=ft.ScrollMode.ADAPTIVE),
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
            autofocus=True,
            on_submit=submit_code
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
        qr_data_lower = qr_data.lower()
        
        # Verificar si es un QR válido de carrito
        if any(keyword in qr_data_lower for keyword in ['carrito', 'cart', 'user', 'usuario', 'client', 'shopping']):
            page.show_snack_bar(ft.SnackBar(ft.Text(f"✅ Carrito asignado: {qr_data}")))
            login_successful()
        else:
            page.show_snack_bar(ft.SnackBar(ft.Text("❌ QR no válido. Debe ser de un carrito.")))
    
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
        item = e.control.data
        page.drawer.open = False
        page.update()
        
        if item == "Escaner de Productos":
            show_barcode_scanner()
        elif item == "Mi Carrito":
            show_cart()
        elif item == "Inicio":
            show_main_app()
        elif item == "Cerrar Sesión":
            logout(None)
        else:
            page.show_snack_bar(ft.SnackBar(ft.Text(f"Seleccionado: {item}")))

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
                        on_click=show_cart,
                        tooltip="Mi Carrito"
                    )
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER
            ),
            bgcolor="#4CAF50",
            padding=ft.padding.symmetric(horizontal=10, vertical=5),
            height=60
        )
        
        # DRAWER - SIMPLIFICADO Y FUNCIONAL
        page.drawer = ft.NavigationDrawer(
            controls=[
                ft.NavigationDrawerDestination(
                    icon=ft.Icons.HOME,
                    label="Inicio",
                ),
                ft.NavigationDrawerDestination(
                    icon=ft.Icons.SHOPPING_CART,
                    label="Mi Carrito",
                ),
                ft.NavigationDrawerDestination(
                    icon=ft.Icons.BARCODE_READER,
                    label="Escaner de Productos",
                ),
                ft.NavigationDrawerDestination(
                    icon=ft.Icons.SHOPPING_BAG,
                    label="Productos",
                ),
                ft.Divider(),
                ft.NavigationDrawerDestination(
                    icon=ft.Icons.LOGOUT,
                    label="Cerrar Sesión",
                ),
            ],
            on_change=lambda e: menu_item_clicked_wrapper(e.control.selected_index)
        )
        
        def menu_item_clicked_wrapper(selected_index):
            items = ["Inicio", "Mi Carrito", "Escaner de Productos", "Productos", "Cerrar Sesión"]
            if 0 <= selected_index < len(items):
                menu_item_clicked(type('Event', (), {'control': type('Control', (), {'data': items[selected_index]})()}))
        
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
                        on_click=lambda e: show_barcode_scanner()
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

    def show_barcode_scanner(e=None):
        """Muestra el escáner de código de barras"""
        nonlocal camera_active, cap, current_view
        current_view = "barcode_scanner"
        page.controls.clear()
        camera_active = False
        
        # Detener cámara si estaba activa
        if cap is not None:
            cap.release()
            cv2.destroyAllWindows()
        
        # Elemento para mostrar la cámara
        camera_display = ft.Image(
            src_base64=None,
            width=350,
            height=300,
            fit=ft.ImageFit.CONTAIN,
            border_radius=10,
            visible=False
        )
        
        # Lista de productos escaneados
        scanned_products = ft.Column(
            scroll=ft.ScrollMode.ADAPTIVE,
            expand=True
        )
        
        # Base de datos simulada de productos
        product_database = {
            "123456789012": {"nombre": "Leche Entera 1L", "precio": 2.50, "categoria": "Lácteos"},
            "234567890123": {"nombre": "Pan Integral", "precio": 1.80, "categoria": "Panadería"},
            "345678901234": {"nombre": "Arroz 1kg", "precio": 3.20, "categoria": "Despensa"},
            "456789012345": {"nombre": "Agua Mineral 500ml", "precio": 1.00, "categoria": "Bebidas"},
            "567890123456": {"nombre": "Jabón Líquido", "precio": 4.50, "categoria": "Limpieza"},
            "678901234567": {"nombre": "Cereal Maíz", "precio": 3.80, "categoria": "Despensa"},
            "789012345678": {"nombre": "Yogurt Natural", "precio": 2.20, "categoria": "Lácteos"},
            "890123456789": {"nombre": "Galletas Chocolate", "precio": 2.80, "categoria": "Snacks"},
            "901234567890": {"nombre": "Aceite Oliva 500ml", "precio": 6.50, "categoria": "Despensa"},
            "012345678901": {"nombre": "Refresco Cola 330ml", "precio": 1.50, "categoria": "Bebidas"}
        }
        
        def start_barcode_scan(e):
            nonlocal camera_active, cap
            if not camera_active:
                try:
                    # Intentar abrir cámara
                    cap = cv2.VideoCapture(0)
                    if not cap.isOpened():
                        page.show_snack_bar(ft.SnackBar(ft.Text("❌ No se pudo acceder a la cámara")))
                        return
                    
                    # Configurar resolución
                    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                    cap.set(cv2.CAP_PROP_FPS, 30)
                    
                    camera_active = True
                    start_btn.text = "Detener Escaneo"
                    start_btn.bgcolor = "#ff4444"
                    status_text.value = "🔍 Escaneando códigos de barras..."
                    status_text.color = "#2196F3"
                    camera_display.visible = True
                    page.update()
                    
                    # Iniciar hilo para mostrar cámara y lectura de códigos de barras
                    threading.Thread(target=update_barcode_display, daemon=True).start()
                    
                except Exception as ex:
                    page.show_snack_bar(ft.SnackBar(ft.Text(f"❌ Error de cámara: {str(ex)}")))
            else:
                stop_barcode_scan()
        
        def stop_barcode_scan():
            nonlocal camera_active
            camera_active = False
            start_btn.text = "Iniciar Escaneo"
            start_btn.bgcolor = "#2196F3"
            status_text.value = "Escáner detenido"
            status_text.color = "gray"
            camera_display.visible = False
            page.update()
        
        def update_barcode_display():
            nonlocal camera_active
            last_scanned_time = 0
            scan_cooldown = 2  # segundos entre escaneos
            
            while camera_active:
                try:
                    ret, frame = cap.read()
                    if not ret:
                        break
                    
                    # Redimensionar frame
                    frame = cv2.resize(frame, (350, 300))
                    
                    # Dibujar línea de escaneo en el centro
                    height, width = frame.shape[:2]
                    cv2.line(frame, (0, height//2), (width, height//2), (0, 255, 0), 2)
                    
                    # Convertir frame a base64 para mostrar en Flet
                    _, buffer = cv2.imencode('.jpg', frame)
                    frame_base64 = base64.b64encode(buffer).decode('utf-8')
                    
                    # Actualizar imagen en la UI
                    camera_display.src_base64 = frame_base64
                    
                    # Decodificar códigos de barras
                    current_time = time.time()
                    if current_time - last_scanned_time > scan_cooldown:
                        try:
                            decoded_objects = decode(frame)
                            for obj in decoded_objects:
                                barcode_data = obj.data.decode('utf-8')
                                print(f"Código de barras detectado: {barcode_data}")
                                
                                # Dibujar resultado en el frame
                                cv2.putText(frame, "✅ PRODUCTO DETECTADO", (30, 30), 
                                          cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                                
                                # Actualizar frame final
                                _, final_buffer = cv2.imencode('.jpg', frame)
                                final_base64 = base64.b64encode(final_buffer).decode('utf-8')
                                camera_display.src_base64 = final_base64
                                
                                # Procesar código de barras
                                process_barcode(barcode_data)
                                last_scanned_time = current_time
                                break
                        
                        except Exception as barcode_error:
                            print(f"Error en decodificación: {barcode_error}")
                    
                    page.update()
                    time.sleep(0.03)  # ~30 FPS
                    
                except Exception as ex:
                    print(f"Error en actualización de cámara: {ex}")
                    break
        
        def process_barcode(barcode_data):
            """Procesa el código de barras escaneado"""
            if barcode_data in product_database:
                product = product_database[barcode_data]
                
                # Verificar si el producto ya está en el carrito
                existing_item = next((item for item in shopping_cart if item["codigo"] == barcode_data), None)
                
                if existing_item:
                    existing_item["cantidad"] += 1
                else:
                    # Agregar producto al carrito
                    shopping_cart.append({
                        "codigo": barcode_data,
                        "nombre": product["nombre"],
                        "precio": product["precio"],
                        "cantidad": 1
                    })
                
                # Mostrar notificación
                page.show_snack_bar(ft.SnackBar(
                    ft.Text(f"✅ {product['nombre']} - ${product['precio']} agregado al carrito")
                ))
                
                # Actualizar lista de productos escaneados
                update_scanned_products_list()
                
            else:
                page.show_snack_bar(ft.SnackBar(
                    ft.Text(f"❌ Producto no encontrado: {barcode_data}")
                ))
        
        def update_scanned_products_list():
            """Actualiza la lista de productos escaneados"""
            scanned_products.controls.clear()
            
            if shopping_cart:
                total = 0
                for item in shopping_cart:
                    product_card = ft.Card(
                        content=ft.Container(
                            content=ft.Column([
                                ft.Row([
                                    ft.Text(item["nombre"], size=16, weight=ft.FontWeight.BOLD, expand=True),
                                    ft.Text(f"${item['precio']:.2f}", size=16, color="green"),
                                ]),
                                ft.Row([
                                    ft.Text(f"Código: {item['codigo']}", size=12, color="gray"),
                                    ft.Text(f"Cantidad: x{item['cantidad']}", size=14),
                                ])
                            ]),
                            padding=10
                        ),
                        margin=5
                    )
                    scanned_products.controls.append(product_card)
                    total += item["precio"] * item["cantidad"]
                
                # Agregar total
                scanned_products.controls.append(
                    ft.Container(
                        content=ft.Row([
                            ft.Text("Total:", size=18, weight=ft.FontWeight.BOLD),
                            ft.Text(f"${total:.2f}", size=18, color="green", weight=ft.FontWeight.BOLD),
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        padding=10,
                        bgcolor="#e8f5e8",
                        border_radius=5
                    )
                )
            else:
                scanned_products.controls.append(
                    ft.Container(
                        content=ft.Column([
                            ft.Icon(ft.Icons.SCANNER, size=50, color="gray"),
                            ft.Text("No hay productos escaneados", size=16, color="gray"),
                            ft.Text("Escanea códigos de barras para agregar productos", size=14, color="gray"),
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        padding=20,
                        alignment=ft.alignment.center
                    )
                )
            
            page.update()
        
        def manual_add_product(e):
            """Agregar producto manualmente"""
            def submit_manual(e):
                barcode = manual_code_field.value.strip()
                if barcode:
                    process_barcode(barcode)
                    page.close(manual_dialog)
                else:
                    page.show_snack_bar(ft.SnackBar(ft.Text("❌ Ingresa un código válido")))
            
            manual_code_field = ft.TextField(
                label="Código de barras",
                hint_text="Ej: 123456789012",
                width=250,
                autofocus=True,
                on_submit=submit_manual
            )
            
            manual_dialog = ft.AlertDialog(
                title=ft.Text("Agregar Producto Manualmente"),
                content=ft.Column([
                    ft.Text("Ingresa el código de barras del producto:"),
                    ft.Container(height=10),
                    manual_code_field,
                    ft.Container(height=10),
                    ft.Text("Códigos de ejemplo:", size=12, color="gray"),
                    ft.Text("123456789012 - Leche", size=12, color="gray"),
                    ft.Text("234567890123 - Pan", size=12, color="gray"),
                ], tight=True),
                actions=[
                    ft.TextButton("Cancelar", on_click=lambda e: page.close(manual_dialog)),
                    ft.ElevatedButton("Agregar", on_click=submit_manual, bgcolor="#2196F3")
                ],
                actions_alignment=ft.MainAxisAlignment.END
            )
            
            page.open(manual_dialog)
        
        # Elementos de la UI
        status_text = ft.Text("Presiona 'Iniciar Escaneo' para escanear productos", 
                             size=16, color="gray", text_align=ft.TextAlign.CENTER)
        
        start_btn = ft.ElevatedButton(
            "Iniciar Escaneo",
            icon=ft.Icons.CAMERA_ALT,
            on_click=start_barcode_scan,
            bgcolor="#2196F3",
            color="white",
            width=200
        )
        
        # Header
        header = ft.Container(
            content=ft.Row([
                ft.IconButton(
                    icon=ft.Icons.ARROW_BACK, 
                    icon_color="white", 
                    on_click=lambda _: show_main_app()
                ),
                ft.Text("Escáner de Productos", size=20, weight=ft.FontWeight.BOLD, color="white", expand=True, text_align=ft.TextAlign.CENTER),
                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.SHOPPING_CART, color="white", size=20),
                        ft.Container(
                            content=ft.Text(str(len(shopping_cart)), color="white", size=12, weight=ft.FontWeight.BOLD),
                            bgcolor="#ff4444",
                            border_radius=10,
                            padding=ft.padding.symmetric(horizontal=6, vertical=2)
                        )
                    ]),
                    on_click=show_cart,
                    tooltip="Ver Carrito"
                )
            ]),
            bgcolor="#2196F3",
            padding=10,
            height=60
        )
        
        # Contenido principal
        scanner_content = ft.Container(
            content=ft.Column([
                # Sección del escáner
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.Icons.BARCODE_READER, size=60, color="#2196F3"),
                        ft.Text("Escáner de Códigos de Barras", size=22, weight=ft.FontWeight.BOLD, 
                               text_align=ft.TextAlign.CENTER),
                        ft.Container(height=10),
                        status_text,
                        ft.Container(height=20),
                        
                        # Contenedor de la cámara
                        ft.Container(
                            content=camera_display,
                            alignment=ft.alignment.center,
                            bgcolor="#f5f5f5",
                            border_radius=10,
                            padding=10,
                            border=ft.border.all(2, "#e0e0e0")
                        ),
                        ft.Container(height=20),
                        
                        # Botones de control
                        ft.Row([
                            start_btn,
                        ], alignment=ft.MainAxisAlignment.CENTER),
                        
                        ft.Container(height=10),
                        ft.Row([
                            ft.TextButton(
                                "Agregar Manualmente",
                                icon=ft.Icons.KEYBOARD,
                                on_click=manual_add_product
                            ),
                            ft.TextButton(
                                "Limpiar Lista",
                                icon=ft.Icons.CLEAR_ALL,
                                on_click=lambda e: (shopping_cart.clear(), update_scanned_products_list())
                            )
                        ], alignment=ft.MainAxisAlignment.CENTER),
                        
                        ft.Container(height=20),
                        ft.Text("Nota: Apunta el código de barras a la línea verde de escaneo", 
                               size=12, color="gray", text_align=ft.TextAlign.CENTER),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    padding=20
                ),
                
                # Lista de productos escaneados
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Text("Productos Escaneados", size=18, weight=ft.FontWeight.BOLD, expand=True),
                            ft.Container(
                                content=ft.Text(str(len(shopping_cart)), color="white", size=14, weight=ft.FontWeight.BOLD),
                                bgcolor="#2196F3",
                                border_radius=15,
                                padding=ft.padding.symmetric(horizontal=8, vertical=4)
                            )
                        ]),
                        ft.Container(height=10),
                        scanned_products
                    ]),
                    padding=20,
                    bgcolor="white",
                    expand=True
                )
                
            ], scroll=ft.ScrollMode.ADAPTIVE),
            expand=True
        )
        
        # Inicializar lista de productos
        update_scanned_products_list()
        
        page.add(
            ft.Column(
                controls=[
                    header,
                    scanner_content
                ],
                expand=True,
                spacing=0
            )
        )

    def show_cart(e=None):
        page.controls.clear()
        
        # Header
        header = ft.Container(
            content=ft.Row([
                ft.IconButton(
                    icon=ft.Icons.ARROW_BACK, 
                    icon_color="white", 
                    on_click=lambda _: show_main_app()
                ),
                ft.Text("Mi Carrito", size=20, weight=ft.FontWeight.BOLD, color="white", expand=True, text_align=ft.TextAlign.CENTER),
                ft.IconButton(
                    icon=ft.Icons.DELETE, 
                    icon_color="white", 
                    on_click=lambda _: vaciar_carrito()
                ),
            ]),
            bgcolor="#4CAF50",
            padding=10,
            height=60
        )
        
        # Contenido del carrito
        if not shopping_cart:
            contenido = ft.Column([
                ft.Icon(ft.Icons.SHOPPING_CART_OUTLINED, size=100, color="gray"),
                ft.Text("Carrito vacío", size=18, color="gray"),
                ft.Text("Escanea productos para agregarlos", size=14, color="gray"),
                ft.ElevatedButton(
                    "Ir al Escáner",
                    on_click=lambda e: show_barcode_scanner(),
                    bgcolor="#2196F3",
                    color="white"
                )
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, alignment=ft.MainAxisAlignment.CENTER, expand=True)
        else:
            total = sum(item["precio"] * item["cantidad"] for item in shopping_cart)
            contenido = ft.Column([
                ft.ListView(
                    controls=[
                        ft.Card(
                            content=ft.Container(
                                content=ft.Column([
                                    ft.Row([
                                        ft.Text(item["nombre"], size=16, weight=ft.FontWeight.BOLD, expand=True),
                                        ft.Text(f"${item['precio']:.2f}", size=16, color="green"),
                                    ]),
                                    ft.Row([
                                        ft.Text(f"Código: {item['codigo']}", size=12, color="gray"),
                                        ft.Text(f"Cantidad: x{item['cantidad']}", size=14),
                                        ft.Row([
                                            ft.IconButton(
                                                icon=ft.Icons.REMOVE,
                                                icon_size=16,
                                                on_click=lambda e, code=item['codigo']: modificar_cantidad(code, -1)
                                            ),
                                            ft.IconButton(
                                                icon=ft.Icons.ADD,
                                                icon_size=16,
                                                on_click=lambda e, code=item['codigo']: modificar_cantidad(code, 1)
                                            ),
                                        ])
                                    ])
                                ]),
                                padding=10
                            ),
                            margin=5
                        ) for item in shopping_cart
                    ],
                    expand=True
                ),
                ft.Container(
                    content=ft.Column([
                        ft.Divider(),
                        ft.Row([
                            ft.Text("Total:", size=20, weight=ft.FontWeight.BOLD),
                            ft.Text(f"${total:.2f}", size=20, color="green", weight=ft.FontWeight.BOLD),
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        ft.Container(height=20),
                        ft.Row([
                            ft.ElevatedButton(
                                "Seguir Comprando",
                                on_click=lambda e: show_barcode_scanner(),
                                bgcolor="#2196F3",
                                color="white",
                                expand=True
                            ),
                            ft.ElevatedButton(
                                "Pagar",
                                on_click=lambda e: page.show_snack_bar(ft.SnackBar(ft.Text("Funcionalidad de pago - Próximamente"))),
                                bgcolor="#4CAF50",
                                color="white",
                                expand=True
                            ),
                        ], spacing=10)
                    ]),
                    padding=20,
                    bgcolor="#f5f5f5"
                )
            ])
        
        page.add(ft.Column([header, contenido], expand=True))

    def modificar_cantidad(codigo, cambio):
        """Modifica la cantidad de un producto en el carrito"""
        for item in shopping_cart:
            if item["codigo"] == codigo:
                item["cantidad"] += cambio
                if item["cantidad"] <= 0:
                    shopping_cart.remove(item)
                break
        show_cart()

    def vaciar_carrito():
        shopping_cart.clear()
        page.show_snack_bar(ft.SnackBar(ft.Text("Carrito vaciado")))
        show_cart()
    
    # Iniciar con el lector de QR
    show_qr_reader()
    
# Ejecutar la aplicación
ft.app(target=main)