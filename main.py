import flet as ft

def main(page: ft.Page):
    # Configuración de la página estilo móvil
    page.title = "Supermercado X"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0
    page.bgcolor = "#f5f5f5"
    
    def open_drawer(e):
        page.drawer.open = True
        page.update()
    
    def close_drawer(e):
        page.drawer.open = False
        page.update()
    
    def on_drawer_change(e):
        page.show_snack_bar(ft.SnackBar(ft.Text(f"Seleccionado: {e.control.selected_index}")))
        close_drawer(e)
    
    # Drawer (menú lateral)
    '''page.drawer = ft.NavigationDrawer(
        bgcolor="#FF5252",
        on_change=on_drawer_change,
        controls=[
            ft.Container(
                content=ft.Text("Menú", color="white", size=18, weight=ft.FontWeight.BOLD),
                padding=20,
                bgcolor="#ff5252"
            ),
            ft.NavigationDrawerDestination(
                label="Inicio",
                icon=ft.Icons.HOME
            ),
            ft.NavigationDrawerDestination(
                label="Productos",
                icon=ft.Icons.SHOPPING_BAG
            ),
            ft.NavigationDrawerDestination(
                label="Ofertas", 
                icon=ft.Icons.LOCAL_OFFER
            ),
            ft.NavigationDrawerDestination(
                label="Carrito",
                icon=ft.Icons.SHOPPING_CART
            ),
            ft.NavigationDrawerDestination(
                label="Mi Cuenta",
                icon=ft.Icons.PERSON
            ),
        ],
    )'''
    # DRAWER personalizado con Containers
    page.drawer = ft.NavigationDrawer(
        bgcolor="#2e7d32",  # Fondo verde oscuro
        controls=[

            ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.STORE, color="white", size=30),
                    ft.Text("Supermercado X", color="white", size=18, weight=ft.FontWeight.BOLD),
                ]),
                padding=20,
                bgcolor="#1b5e20",
            ),
            
            ft.Container(
                content=ft.ListTile(
                    leading=ft.Icon(ft.Icons.HOME, color="white"),
                    title=ft.Text("Inicio", color="white"),
                    #on_click=menu_item_clicked,
                    data="Inicio"
                ),
                bgcolor="#2e7d32",
            ),
            ft.Container(
                content=ft.ListTile(
                    leading=ft.Icon(ft.Icons.SHOPPING_BAG, color="white"),
                    title=ft.Text("Productos", color="white"),
                    #on_click=menu_item_clicked,
                    data="Productos"
                ),
                bgcolor="#2e7d32",
            ),
            ft.Container(
                content=ft.ListTile(
                    leading=ft.Icon(ft.Icons.LOCAL_OFFER, color="white"),
                    title=ft.Text("Ofertas", color="white"),
                    #on_click=menu_item_clicked,
                    data="Ofertas"
                ),
                bgcolor="#2e7d32",
            ),
            ft.Container(
                content=ft.ListTile(
                    leading=ft.Icon(ft.Icons.SHOPPING_CART, color="white"),
                    title=ft.Text("Carrito", color="white"),
                    #on_click=menu_item_clicked,
                    data="Carrito"
                ),
                bgcolor="#2e7d32",
            ),
            
              # Espacio flexible
            ft.Container(expand=True),
            
            # FOOTER COMPACTO
            ft.Container(
                content=ft.Column([
                    ft.Divider(color="white"),
                    ft.Row([
                        ft.Column([
                            ft.Text("¿Necesitas ayuda?", color="white", size=12, weight=ft.FontWeight.BOLD),
                            ft.Text("Llámanos: (123) 456-7890", color="white", size=10),
                            ft.Text("Email: ayuda@superx.com", color="white", size=10),
                        ], expand=True),
                        ft.Icon(ft.Icons.HEADSET_MIC, color="white", size=30),
                    ]),
                    ft.Container(height=10),
                    ft.Text("© 2024 Supermercado X - v1.0", 
                           color="white", size=9, text_align=ft.TextAlign.CENTER),
                ], spacing=8),
                padding=15,
                bgcolor="#1b5e20",
            )
        ],
    )
    
    # HEADER
    header = ft.Container(
        content=ft.Row(
            controls=[
                # Botón menú a la izquierda
                ft.IconButton(
                    icon=ft.Icons.STORE,
                    icon_color="white",
                    on_click=open_drawer,
                    tooltip="Menú"
                ),
                # Título centrado
                ft.Text(
                    "Supermercado X", 
                    size=20, 
                    weight=ft.FontWeight.BOLD, 
                    color="white",
                    expand=True,
                    text_align=ft.TextAlign.CENTER
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER
        ),
        bgcolor="#FF5252",  # Verde supermercado
        padding=ft.padding.symmetric(horizontal=10, vertical=5),
        height=60
    )
    
    # FRAME 1 - Banner u ofertas destacadas
    frame1 = ft.Container(
        content=ft.Column(
            controls=[
                ft.Text(
                    "Ofertas de la Semana",
                    size=18,
                    weight=ft.FontWeight.BOLD,
                    color="white"
                ),
                ft.Text(
                    "Hasta 50% de descuento",
                    size=14,
                    color="white"
                ),
                ft.ElevatedButton(
                    "Ver Ofertas",
                    bgcolor="white",
                    color="#FF5252",
                    on_click=lambda e: page.show_snack_bar(ft.SnackBar(ft.Text("Navegando a ofertas")))
                )
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER
        ),
        gradient=ft.LinearGradient(
            begin=ft.alignment.top_left,
            end=ft.alignment.bottom_right,
            colors=["#FF5252", "#FF5252"]
        ),
        height=150,
        border_radius=10,
        margin=10,
        padding=15,
        alignment=ft.alignment.center
    )
    
    # FRAME 2 - Categorías o productos
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
                        # Categoría 1
                        ft.Container(
                            content=ft.Column(
                                controls=[
                                    ft.Icon(ft.Icons.KITCHEN, size=40, color="#FF5252"),
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
                        # Categoría 2
                        ft.Container(
                            content=ft.Column(
                                controls=[
                                    ft.Icon(ft.Icons.LOCAL_DRINK, size=40, color="#FF5252"),
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
                        # Categoría 3
                        ft.Container(
                            content=ft.Column(
                                controls=[
                                    ft.Icon(ft.Icons.KITCHEN, size=40, color="#FF5252"),
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
                        # Categoría 4
                        ft.Container(
                            content=ft.Column(
                                controls=[
                                    ft.Icon(ft.Icons.FASTFOOD, size=40, color="#FF5252"),
                                    ft.Text("Snacks", size=12, text_align=ft.TextAlign.CENTER)
                                ],
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                spacing=5
                            ),
                            padding=10,
                            width=80,
                            height=80,
                            bgcolor="white",
                            border_radius=10,
                            on_click=lambda e: page.show_snack_bar(ft.SnackBar(ft.Text("Snacks")))
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
    
    # FRAME 3 - Productos destacados
    frame3 = ft.Container(
        content=ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Text(
                            "Productos Destacados",
                            size=18,
                            weight=ft.FontWeight.BOLD,
                            expand=True
                        ),
                        ft.TextButton(
                            "Ver más",
                            on_click=lambda e: page.show_snack_bar(ft.SnackBar(ft.Text("Más productos")))
                        )
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                ),
                ft.Row(
                    controls=[
                        # Producto 1
                        ft.Container(
                            content=ft.Column(
                                controls=[
                                    ft.Container(
                                        content=ft.Icon(ft.Icons.SHOPPING_BAG, size=30, color="#FF5252"),
                                        bgcolor="#f0f0f0",
                                        padding=10,
                                        border_radius=10,
                                        width=60,
                                        height=60
                                    ),
                                    ft.Text("Arroz 1kg", size=12, weight=ft.FontWeight.BOLD),
                                    ft.Text("$2.50", size=14, color="#FF5252", weight=ft.FontWeight.BOLD),
                                    ft.FilledButton(
                                        "Agregar",
                                        width=80,
                                        height=30,
                                        on_click=lambda e: page.show_snack_bar(ft.SnackBar(ft.Text("Arroz agregado al carrito")))
                                    )
                                ],
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                spacing=8
                            ),
                            padding=10,
                            width=120,
                            bgcolor="white",
                            border_radius=10,
                            border=ft.border.all(1, "#e0e0e0")
                        ),
                        # Producto 2
                        ft.Container(
                            content=ft.Column(
                                controls=[
                                    ft.Container(
                                        content=ft.Icon(ft.Icons.LOCAL_DRINK, size=30, color="#FF5252"),
                                        bgcolor="#f0f0f0",
                                        padding=10,
                                        border_radius=10,
                                        width=60,
                                        height=60
                                    ),
                                    ft.Text("Leche 1L", size=12, weight=ft.FontWeight.BOLD),
                                    ft.Text("$1.80", size=14, color="#FF5252", weight=ft.FontWeight.BOLD),
                                    ft.FilledButton(
                                        "Agregar",
                                        width=80,
                                        height=30,
                                        on_click=lambda e: page.show_snack_bar(ft.SnackBar(ft.Text("Leche agregada al carrito")))
                                    )
                                ],
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                spacing=8
                            ),
                            padding=10,
                            width=120,
                            bgcolor="white",
                            border_radius=10,
                            border=ft.border.all(1, "#e0e0e0")
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
    
    # CONTENIDO PRINCIPAL con scroll
    main_content = ft.ListView(
        controls=[
            frame1,
            frame2,
            frame3
        ],
        expand=True,
        spacing=0,
        padding=0
    )
    
    # LAYOUT FINAL
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

ft.app(target=main)