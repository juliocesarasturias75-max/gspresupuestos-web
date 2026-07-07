#!/usr/bin/env python3
"""
🎯 GENERADOR DE PRESUPUESTOS PROFESIONAL
Versión Mejorada - Fusión Gemini + Claude
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from tkinter import font as tkfont
import json
import os
import re
import shutil
import sys
from io import BytesIO

# ===== FUNCIÓN PARA RUTAS COMPATIBLES CON PYINSTALLER =====
def obtener_ruta_base():
    """Obtiene la carpeta donde está el .exe o el script"""
    if getattr(sys, 'frozen', False):
        # Ejecutable - carpeta del .exe
        return os.path.dirname(sys.executable)
    else:
        # Desarrollo - carpeta del script
        return os.path.dirname(os.path.abspath(__file__))

def obtener_ruta_interna(ruta_relativa):
    """
    Para archivos EMPAQUETADOS DENTRO del .exe (logo_secopvc)
    """
    try:
        ruta_base = sys._MEIPASS
    except AttributeError:
        ruta_base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(ruta_base, ruta_relativa)

def obtener_ruta_externa(ruta_relativa):
    """
    Para archivos EXTERNOS (DATOS_DISTRIBUIDOR, CONDICIONES)
    Van en la misma carpeta que el .exe
    """
    return os.path.join(obtener_ruta_base(), ruta_relativa)

# Importaciones para PDF
try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False
    print("⚠️ PyMuPDF no disponible. Instalar con: pip install pymupdf")

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import BaseDocTemplate, PageTemplate, Frame, SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image as RLImage, PageBreak, NextPageTemplate
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT


class GeneradorPresupuestosPRO:
    def __init__(self, root):
        self.root = root

                # ===== VERIFICACIÓN DE LICENCIA =====
        if not self.verificar_licencia():
            root.destroy()
            return

        self.root.title("🎯 Generador de Presupuestos - Aluminios Seco")
        self.root.state('zoomed')
        self.root.configure(bg='#f0f4f8')
        
        # ===== CONFIGURAR ICONO DE LA APLICACIÓN =====
        try:
            # Intentar cargar el icono desde la carpeta del programa
            ruta_icono = obtener_ruta_externa('icono_secopvc.ico')
            if os.path.exists(ruta_icono):
                self.root.iconbitmap(ruta_icono)
            else:
                # Si no está en la carpeta externa, buscar en recursos internos (para .exe)
                ruta_icono = obtener_ruta_interna('icono_secopvc.ico')
                if os.path.exists(ruta_icono):
                    self.root.iconbitmap(ruta_icono)
        except Exception as e:
            print(f"⚠️ No se pudo cargar el icono: {e}")
        
        # Datos
        self.items = []
        self.dibujos_extraidos = []
        self.pdf_path = None
        self.txt_path = None
        
        # Variables globales
        self.margen_global = tk.DoubleVar(value=20.0)
        self.colocacion_global = tk.DoubleVar(value=50.0)
        
        # Configuración del cliente (persistente)
        self.config_cliente = self.cargar_configuracion()
        
        # Crear interfaz
        self.setup_styles()
        self.crear_interfaz()
    
    def verificar_licencia(self):
        """Verificar clave de activación y fecha de caducidad"""
        import datetime
        
        CLAVE_VALIDA = "SECO-2026-ABC123"
        FECHA_CADUCIDAD = datetime.date(2027, 2, 28)
        
        # Verificar fecha de caducidad
        if datetime.date.today() > FECHA_CADUCIDAD:
            messagebox.showerror(
                "Licencia Caducada",
                "Esta aplicación ha caducado el 28/02/2027.\n\n"
                "Contacte con el proveedor para renovar la licencia."
            )
            return False
         
        # Archivo donde se guarda la clave (en directorio del usuario, no en la carpeta del programa)
        archivo_licencia = os.path.join(os.path.expanduser("~"), "licencia_gspresupuestos.key")
        
        # Verificar si ya existe una clave guardada
        if os.path.exists(archivo_licencia):
            try:
                with open(archivo_licencia, 'r') as f:
                    clave_guardada = f.read().strip()
                if clave_guardada == CLAVE_VALIDA:
                    return True
            except:
                pass
        
        # Solicitar clave de activación
        ventana_activacion = tk.Toplevel(self.root)
        ventana_activacion.title("Activación Requerida")
        ventana_activacion.geometry("400x200")
        ventana_activacion.resizable(False, False)
        ventana_activacion.configure(bg='#f0f4f8')
        
        # Centrar ventana
        ventana_activacion.transient(self.root)
        ventana_activacion.grab_set()
        
        tk.Label(ventana_activacion, 
                text="🔐 Activación de Licencia",
                font=('Segoe UI', 14, 'bold'),
                bg='#f0f4f8').pack(pady=20)
        
        tk.Label(ventana_activacion,
                text="Introduce la clave de activación:",
                font=('Segoe UI', 10),
                bg='#f0f4f8').pack(pady=5)
        
        entrada_clave = tk.Entry(ventana_activacion, 
                                font=('Segoe UI', 11),
                                width=30,
                                justify='center')
        entrada_clave.pack(pady=10)
        entrada_clave.focus()
        
        resultado = {'activado': False}
        
        def verificar_clave():
            clave = entrada_clave.get().strip()
            if clave == CLAVE_VALIDA:
                # Guardar clave
                try:
                    with open(archivo_licencia, 'w') as f:
                        f.write(clave)
                except:
                    pass
                resultado['activado'] = True
                ventana_activacion.destroy()
            else:
                messagebox.showerror(
                    "Clave Incorrecta",
                    "La clave de activación no es válida.\n\n"
                    "Contacte con el proveedor."
                )
                entrada_clave.delete(0, tk.END)
                entrada_clave.focus()
        
        def cancelar():
            ventana_activacion.destroy()
        
        frame_botones = tk.Frame(ventana_activacion, bg='#f0f4f8')
        frame_botones.pack(pady=20)
        
        tk.Button(frame_botones, text="✓ Activar", 
                 command=verificar_clave,
                 bg='#10b981', fg='white',
                 font=('Segoe UI', 8, 'bold'),
                 width=12, height=20,
                 pady=20).pack(side='left', padx=5)
        
        tk.Button(frame_botones, text="✗ Cancelar",
                 command=cancelar,
                 bg='#ef4444', fg='white',
                 font=('Segoe UI', 8, 'bold'),
                 width=12, height=20,
                 pady=20).pack(side='left', padx=5)
        
        entrada_clave.bind('<Return>', lambda e: verificar_clave())
        
        # Ejecutar el mainloop de la ventana de activación
        ventana_activacion.wait_window()
        
        return resultado['activado']
    
    def cargar_configuracion(self):
        """Carga configuración guardada"""
        config_file = os.path.join(os.path.expanduser("~"), "config_cliente_gspresupuestos.json")
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def guardar_configuracion(self):
        """Guarda configuración"""
        try:
            config_file = os.path.join(os.path.expanduser("~"), "config_cliente_gspresupuestos.json")
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config_cliente, f, indent=2, ensure_ascii=False)
            return True
        except:
            return False
    
    def setup_styles(self):
        """Configurar estilos visuales"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Botones
        style.configure('Primary.TButton',
                       font=('Segoe UI', 10, 'bold'),
                       padding=10)
        
        style.configure('Success.TButton',
                       font=('Segoe UI', 10, 'bold'),
                       padding=10)
    
    def crear_interfaz(self):
        """Crear interfaz completa"""
        
        # ===== HEADER =====
        header = tk.Frame(self.root, bg='#1e40af', height=90)
        header.pack(fill='x')
        header.pack_propagate(False)
        
        # Frame para logos
        logo_frame = tk.Frame(header, bg='#1e40af')
        logo_frame.pack(fill='both', expand=True)
        
        # Logo SECOPVC (grande, izquierda) - USANDO RUTA COMPATIBLE
        try:
            from PIL import Image, ImageTk
            # Buscar el logo usando la función de rutas compatible con PyInstaller
            logo_path = obtener_ruta_interna("logo_secopvc.gif")
            if os.path.exists(logo_path):
                logo_seco = Image.open(logo_path)
            logo_seco = logo_seco.resize((200, 60), Image.Resampling.LANCZOS)
            logo_seco_tk = ImageTk.PhotoImage(logo_seco)
            lbl_seco = tk.Label(logo_frame, image=logo_seco_tk, bg='#1e40af')
            lbl_seco.image = logo_seco_tk  # Mantener referencia
            lbl_seco.place(x=20, y=15)
        except Exception as e:
            print(f"Error logo SECOPVC: {e}")
            tk.Label(logo_frame, text="SECOPVC", font=('Segoe UI', 20, 'bold'),
                    bg='#1e40af', fg='white').place(x=20, y=15)
                     
      
        title_font = tkfont.Font(family='Segoe UI', size=14, weight='bold')
        tk.Label(logo_frame, text="🎯 Generador de Presupuestos",
                font=title_font, bg='#1e40af', fg='white').place(relx=1.0, x=-20, y=25, anchor='e')
        
        subtitle_font = tkfont.Font(family='Segoe UI', size=9)
        tk.Label(logo_frame, text="Version 1.0 - 2026",
                font=subtitle_font, bg='#1e40af', fg='#bfdbfe').place(relx=1.0, x=-20, y=55, anchor='e')

         # Días hasta caducidad
        import datetime
        FECHA_CADUCIDAD = datetime.date(2027, 2, 28)
        dias_restantes = (FECHA_CADUCIDAD - datetime.date.today()).days
        
        if dias_restantes > 0:
            texto_caducidad = f"Licencia válida {dias_restantes} días"
            color_caducidad = '#86efac' if dias_restantes > 30 else '#fbbf24'  # Verde o amarillo
        else:
            texto_caducidad = "Licencia caducada"
            color_caducidad = '#f87171'  # Rojo
        
        caducidad_font = tkfont.Font(family='Segoe UI', size=7)
        tk.Label(logo_frame, text=texto_caducidad,
                font=caducidad_font, bg='#1e40af', fg=color_caducidad).place(relx=1.0, x=-20, y=70, anchor='e')


        
        # ===== CONTENEDOR PRINCIPAL =====
        main = tk.Frame(self.root, bg='#f0f4f8')
        main.pack(fill='both', expand=True, padx=15, pady=15)
        
        # PANEL IZQUIERDO - Configuración
        left_panel = tk.Frame(main, bg='white', relief='solid', borderwidth=1, width=320)
        left_panel.pack(side='left', fill='y', padx=(0, 7))
        left_panel.pack_propagate(False)
        
        # PANEL DERECHO - Tabla
        right_panel = tk.Frame(main, bg='white', relief='solid', borderwidth=1)
        right_panel.pack(side='right', fill='both', expand=True)
        
        # Construir paneles
        self.crear_panel_izquierdo(left_panel)
        self.crear_panel_derecho(right_panel)
    
    def crear_panel_izquierdo(self, parent):
        """Panel de configuración"""
        
        # Título
        title_frame = tk.Frame(parent, bg='#1e40af')
        title_frame.pack(fill='x')
        tk.Label(title_frame, text="⚙️ CONFIGURACIÓN",
                font=('Segoe UI', 12, 'bold'), bg='#1e40af', fg='white',
                pady=10).pack()
        
        # Contenedor con scroll
        canvas = tk.Canvas(parent, bg='white', highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable = tk.Frame(canvas, bg='white')
        
        scrollable.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Habilitar scroll con rueda del ratón SOLO cuando el mouse esté sobre este canvas
        def _on_mousewheel_left(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        def _bind_mousewheel_left(event):
            canvas.bind_all("<MouseWheel>", _on_mousewheel_left)
        
        def _unbind_mousewheel_left(event):
            canvas.unbind_all("<MouseWheel>")
        
        canvas.bind("<Enter>", _bind_mousewheel_left)
        canvas.bind("<Leave>", _unbind_mousewheel_left)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # ===== SECCIÓN 1: ARCHIVOS =====
        self.crear_seccion(scrollable, "1️⃣   ARCHIVOS BASE")
        
        btn_frame = tk.Frame(scrollable, bg='white')
        btn_frame.pack(fill='x', padx=15, pady=5)
        
        self.btn_cargar_pdf = tk.Button(btn_frame, text="📂 PDF",
                 bg='#e0f2fe', font=('Segoe UI', 8, 'bold'),
                 command=self.cargar_pdf, pady=3, width=40)
        self.btn_cargar_pdf.pack(anchor='w', pady=2)
        
        self.lbl_pdf = tk.Label(btn_frame, text="Esperando PDF...",
                               font=('Segoe UI', 8), bg='white', fg='#dc2626')
        self.lbl_pdf.pack(anchor='w', pady=1)
        
        self.btn_cargar_txt = tk.Button(btn_frame, text="📄 TXT",
                 bg='#f0fdf4', font=('Segoe UI', 8, 'bold'),
                 command=self.cargar_datos, pady=3, width=40)
        self.btn_cargar_txt.pack(anchor= 'w', pady=2)
        
        self.lbl_datos = tk.Label(btn_frame, text="Esperando TXT...",
                                 font=('Segoe UI', 8), bg='white', fg='#dc2626')
        self.lbl_datos.pack(anchor='w', pady=1)

        #prueba para cargar las condiciones
        self.btn_cargar_condiciones = tk.Button(btn_frame, text="📄 CONDICIONES GENERALES",
                 bg='#f5b2b6', font=('Segoe UI', 8, 'bold'),
                 command=self.cargar_condiciones, pady=3, width=40)
        self.btn_cargar_condiciones.pack(anchor='w', pady=2)
        
        self.lbl_condiciones = tk.Label(btn_frame, text="Esperando TXT...",
                                       font=('Segoe UI', 8), bg='white', fg='#dc2626')
        self.lbl_condiciones.pack(anchor='w')
        
        
        # ===== SECCIÓN 2: DATOS CLIENTE FINAL =====
        self.crear_seccion(scrollable, "2️⃣   DATOS CLIENTE FINAL")
        
        cliente_final_frame = tk.Frame(scrollable, bg='white')
        cliente_final_frame.pack(fill='x', padx=15, pady=5)
        
        # Número de oferta
        tk.Label(cliente_final_frame, text="Nº Oferta:", font=('Segoe UI', 9, 'bold'),
                bg='white').grid(row=0, column=0, sticky='w', pady=5)
        self.entry_num_oferta = ttk.Entry(cliente_final_frame, width=30)
        self.entry_num_oferta.grid(row=0, column=1, sticky='w', pady=5)
        
        # Cliente
        tk.Label(cliente_final_frame, text="Cliente:", font=('Segoe UI', 9, 'bold'),
                bg='white').grid(row=1, column=0, sticky='w', pady=5)
        self.entry_cliente_final = ttk.Entry(cliente_final_frame, width=30)
        self.entry_cliente_final.grid(row=1, column=1, sticky='w', pady=5)
        
        # Dirección cliente
        tk.Label(cliente_final_frame, text="Dirección:", font=('Segoe UI', 9, 'bold'),
                bg='white').grid(row=2, column=0, sticky='w', pady=5)
        self.entry_dir_cliente = ttk.Entry(cliente_final_frame, width=30)
        self.entry_dir_cliente.grid(row=2, column=1, sticky='w', pady=5)
        
        # Teléfono cliente
        tk.Label(cliente_final_frame, text="Teléfono:", font=('Segoe UI', 9, 'bold'),
                bg='white').grid(row=3, column=0, sticky='w', pady=5)
        self.entry_tlf_cliente = ttk.Entry(cliente_final_frame, width=30)
        self.entry_tlf_cliente.grid(row=3, column=1, sticky='w', pady=5)
        
        # Email cliente
        tk.Label(cliente_final_frame, text="Email:", font=('Segoe UI', 9, 'bold'),
                bg='white').grid(row=4, column=0, sticky='w', pady=5)
        self.entry_email_cliente = ttk.Entry(cliente_final_frame, width=30)
        self.entry_email_cliente.grid(row=4, column=1, sticky='w', pady=5)
        
        # Email cliente
        tk.Label(cliente_final_frame, text="Referencia:", font=('Segoe UI', 9, 'bold'),
                bg='white').grid(row=5, column=0, sticky='w', pady=5)
        self.entry_referencia_cliente = ttk.Entry(cliente_final_frame, width=30)
        self.entry_referencia_cliente.grid(row=5, column=1, sticky='w', pady=5)


        cliente_final_frame.columnconfigure(1, weight=1)
        
        # ===== SECCIÓN 3: APLICACIÓN POR EL USUARIO =====
        self.crear_seccion(scrollable, "3️⃣   APLICACIÓN POR EL USUARIO")
        
        margenes_frame = tk.Frame(scrollable, bg='white')
        margenes_frame.pack(fill='x', padx=15, pady=5)
        
        tk.Label(margenes_frame, text="Beneficio (%):",
        font=('Segoe UI', 8, 'bold'), bg='white').grid(row=0, column=0,
        sticky='w', pady=3)

        ttk.Spinbox(margenes_frame, from_=0, to=100,
           textvariable=self.margen_global, width=4).grid(row=0, column=1,
           sticky='w', pady=3, padx=5)

        # LÍNEAS 225-231: Colocación (€) - SEGUNDA PARTE (misma fila)
        tk.Label(margenes_frame, text="Colocación (€):",
        font=('Segoe UI', 8, 'bold'), bg='white').grid(row=0, column=2,
        sticky='w', pady=3, padx=(10, 0))

        ttk.Spinbox(margenes_frame, from_=0, to=10000,
           textvariable=self.colocacion_global, width=4).grid(row=0, column=3,
           sticky='w', pady=3, padx=5)

        tk.Button(margenes_frame, text="⚡ Aplicar",
         bg='#1e40af', fg='white', font=('Segoe UI', 8, 'bold'),
         command=self.actualizar_tabla, pady=5, width=40).grid(row=1, column=0,
         columnspan=4, sticky='', pady=8)
        
        # ===== SECCIÓN 3B: NOTA GLOBAL (NUEVA) =====
        nota_global_frame = tk.Frame(scrollable, bg='white')
        nota_global_frame.pack(fill='x', padx=15, pady=(10, 5))
        
        tk.Label(nota_global_frame, text="📝 Nota para todos los modelos:",
                font=('Segoe UI', 9, 'bold'), bg='white').pack(anchor='w', pady=(0, 5))
        
        # Campo de texto para la nota global (mínimo 50 caracteres de ancho)
        self.entry_nota_global = scrolledtext.ScrolledText(nota_global_frame,
                                                           height=3,
                                                           width=35,
                                                           font=('Segoe UI', 8),
                                                           wrap='word')
        self.entry_nota_global.pack(fill='x', pady=(0, 5))
        
        # Botón para aplicar nota a todos
        tk.Button(nota_global_frame, text="✓ Aplicar Nota a Todos",
                 bg='#1e40af', fg='white', font=('Segoe UI', 8, 'bold'),
                 command=self.aplicar_nota_global, pady=5, width=40).pack()
        
          
    def crear_panel_derecho(self, parent):
        """Panel con tabla de partidas"""
        
        # Título (FIJO - no hace scroll)
        title_frame = tk.Frame(parent, bg='#1e40af')
        title_frame.pack(fill='x')
        tk.Label(title_frame, text="📦 PARTIDAS DEL PRESUPUESTO",
                font=('Segoe UI', 12, 'bold'), bg='#1e40af', fg='white',
                pady=10).pack()

              
        # Info frame con botones (FIJO - no hace scroll)
        info_frame = tk.Frame(parent, bg='#dbeafe')
        info_frame.pack(fill='x', padx=10, pady=10)
        
        # BOTONES dentro del cuadro azul clarito
        btn_container = tk.Frame(info_frame, bg='#dbeafe')
        btn_container.pack(fill='x', pady=5, padx=10)
        
        # BOTONES IZQUIERDA (Acciones sobre partidas)
        btn_left = tk.Frame(btn_container, bg='#dbeafe')
        btn_left.pack(side='left')
        
        tk.Button(btn_left, text="➕ Añadir Partida Manual",
                 font=('Segoe UI', 9, 'bold'),
                 bg='#8b5cf6', fg='white',
                 activebackground='#7c3aed',
                 cursor='hand2',
                 command=self.añadir_partida_manual,
                 width=20).pack(side='left', padx=3)
        
        tk.Button(btn_left, text="  🗑  Eliminar",
                 font=('Segoe UI', 9, 'bold'),
                 bg='#ef4444', fg='white',
                 activebackground='#dc2626',
                 cursor='hand2',
                 command=self.eliminar_partida,
                 width=12).pack(side='left', padx=3)
        
        # BOTONES DERECHA (Gestión de archivo)
        btn_right = tk.Frame(btn_container, bg='#dbeafe')
        btn_right.pack(side='right')
        
        tk.Button(btn_right, text="🆕 Nuevo",
                 font=('Segoe UI', 9, 'bold'),
                 bg='#10b981', fg='white',
                 activebackground='#059669',
                 cursor='hand2',
                 command=self.nuevo_calculo,
                 width=10).pack(side='left', padx=3)
        
        tk.Button(btn_right, text="💾 Guardar",
                 font=('Segoe UI', 9, 'bold'),
                 bg='#10b981', fg='white',
                 activebackground='#0284c7',
                 cursor='hand2',
                 command=self.guardar_calculo,
                 width=10).pack(side='left', padx=3)
        
        tk.Button(btn_right, text="📂 Cargar",
                 font=('Segoe UI', 9, 'bold'),
                 bg='#10b981', fg='white',
                 activebackground='#0891b2',
                 cursor='hand2',
                 command=self.cargar_calculo,
                 width=10).pack(side='left', padx=3)
        
        tk.Button(btn_right, text="❌ Cerrar",
                 font=('Segoe UI', 9, 'bold'),
                 bg='#6b7280', fg='white',
                 activebackground='#4b5563',
                 cursor='hand2',
                 command=self.cerrar_aplicacion,
                 width=10).pack(side='left', padx=3)
        
        
        # ===== CONTENEDOR CON SCROLL (para tabla + resumen + botones PDF) =====
        # Canvas y scrollbar para hacer scroll en todo el contenido
        canvas_container = tk.Frame(parent, bg='white')
        canvas_container.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        
        canvas = tk.Canvas(canvas_container, bg='white', highlightthickness=0)
        scrollbar = ttk.Scrollbar(canvas_container, orient="vertical", command=canvas.yview)
        scrollable_content = tk.Frame(canvas, bg='white')
        
        # Configurar región scrollable basada en el tamaño del contenido
        def update_scrollregion(event=None):
            canvas.configure(scrollregion=canvas.bbox("all"))
        
        scrollable_content.bind("<Configure>", update_scrollregion)
        canvas_window = canvas.create_window((0, 0), window=scrollable_content, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Habilitar scroll con rueda del ratón SOLO cuando el mouse esté sobre este canvas
        def _on_mousewheel_right(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        def _bind_mousewheel_right(event):
            canvas.bind_all("<MouseWheel>", _on_mousewheel_right)
        
        def _unbind_mousewheel_right(event):
            canvas.unbind_all("<MouseWheel>")
        
        canvas.bind("<Enter>", _bind_mousewheel_right)
        canvas.bind("<Leave>", _unbind_mousewheel_right)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Ajustar ancho Y alto del contenido scrollable
        def on_canvas_configure(event):
            # Ajustar ancho al del canvas
            canvas.itemconfig(canvas_window, width=event.width)
            # Actualizar scrollregion
            update_scrollregion()
        
        canvas.bind("<Configure>", on_canvas_configure)
        
        
        # Tabla (AHORA DENTRO DEL CONTENIDO SCROLLABLE)
        table_frame = tk.Frame(scrollable_content, bg='white')
        table_frame.pack(fill='both', expand=True, pady=(0, 10))
        
        # Scrollbars
        scroll_y = ttk.Scrollbar(table_frame, orient='vertical')
        scroll_x = ttk.Scrollbar(table_frame, orient='horizontal')
        
        # Treeview
        columns = ('pos', 'uds', 'desc', 'coste', 'coloc', 'margen', 'pvp', 'total')
        self.tree = ttk.Treeview(table_frame, columns=columns, show='headings',
                                yscrollcommand=scroll_y.set,
                                xscrollcommand=scroll_x.set,
                                height=25)  # Aumentado de 20 a 30 para llenar más espacio
        
        scroll_y.config(command=self.tree.yview)
        scroll_x.config(command=self.tree.xview)
        
        # Configurar columnas
        self.tree.heading('pos', text='Pos.')
        self.tree.heading('uds', text='Uds')
        self.tree.heading('desc', text='Descripción')
        self.tree.heading('coste', text='Coste Base')
        self.tree.heading('margen', text='Margen %')
        self.tree.heading('coloc', text='Colocación')
        self.tree.heading('pvp', text='PVP Unit.')
        self.tree.heading('total', text='Total')
        
        self.tree.column('pos', width=80, anchor='center')
        self.tree.column('uds', width=50, anchor='center')
        self.tree.column('desc', width=400, anchor='w')
        self.tree.column('coste', width=90, anchor='e')
        self.tree.column('margen', width=80, anchor='center')
        self.tree.column('coloc', width=90, anchor='e')
        self.tree.column('pvp', width=90, anchor='e')
        self.tree.column('total', width=100, anchor='e')
        
        # Empaquetar
        self.tree.grid(row=0, column=0, sticky='nsew')
        scroll_y.grid(row=0, column=1, sticky='ns')
        scroll_x.grid(row=1, column=0, sticky='ew')
        
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)
        
        # Doble clic para editar
        self.tree.bind('<Double-1>', self.editar_partida)
        
        # Resumen y Botón (DENTRO DEL CONTENIDO SCROLLABLE)
        resumen_y_boton = tk.Frame(scrollable_content, bg='white')
        resumen_y_boton.pack(fill='x', pady=(0, 10))
        
        # RESUMEN (Izquierda) - Ahora horizontal con separadores
        resumen_frame = tk.Frame(resumen_y_boton, bg='#f3f4f6', relief='solid', borderwidth=1)
        resumen_frame.pack(side='left', fill='both', expand=True, padx=(0, 5))
        
        res_grid = tk.Frame(resumen_frame, bg='#f3f4f6')
        res_grid.pack(fill='x', padx=15, pady=18)
        
        # TOTAL BASE (columna 0-1)
        tk.Label(res_grid, text="Total Base:", font=('Segoe UI', 11, 'bold'),
                bg='#f3f4f6').grid(row=0, column=0, sticky='e', padx=(10, 5), pady=5)
        self.label_total_base = tk.Label(res_grid, text="0.00 €",
                                        font=('Segoe UI', 11),
                                        bg='#f3f4f6')
        self.label_total_base.grid(row=0, column=1, sticky='w', padx=(0, 15), pady=5)
        
        # SEPARADOR 1
        tk.Label(res_grid, text="│", font=('Segoe UI', 14),
                bg='#f3f4f6', fg='#9ca3af').grid(row=0, column=2, padx=10)
        
        # IVA (columna 3-4)
        tk.Label(res_grid, text="IVA (21%):", font=('Segoe UI', 11, 'bold'),
                bg='#f3f4f6').grid(row=0, column=3, sticky='e', padx=(10, 5), pady=5)
        self.label_iva = tk.Label(res_grid, text="0.00 €",
                                 font=('Segoe UI', 11),
                                 bg='#f3f4f6')
        self.label_iva.grid(row=0, column=4, sticky='w', padx=(0, 15), pady=5)
        
        # SEPARADOR 2
        tk.Label(res_grid, text="│", font=('Segoe UI', 14),
                bg='#f3f4f6', fg='#9ca3af').grid(row=0, column=5, padx=10)
        
        # TOTAL FINAL (columna 6-7) - Destacado sin marco
        tk.Label(res_grid, text="TOTAL FINAL:", font=('Segoe UI', 12, 'bold'),
                bg='#f3f4f6', fg='#1e40af').grid(row=0, column=6, sticky='e',
                padx=(15, 5), pady=5)
        self.label_total_final = tk.Label(res_grid, text="0.00 €",
                                         font=('Segoe UI', 13, 'bold'),
                                         bg='#f3f4f6', fg='#1e40af')
        self.label_total_final.grid(row=0, column=7, sticky='w', padx=(0, 10), pady=5)
        
        # ===== SEGUNDA FILA: INFORMACIÓN DE COSTES =====
        # COSTE TOTAL (row=1, columna 0-1)
        tk.Label(res_grid, text="Coste Total:", font=('Segoe UI', 10, 'bold'),
                bg='#f3f4f6', fg='#6b7280').grid(row=1, column=0, sticky='e', padx=(10, 5), pady=5)
        self.label_coste_total = tk.Label(res_grid, text="0.00 €",
                                         font=('Segoe UI', 10),
                                         bg='#f3f4f6', fg='#6b7280')
        self.label_coste_total.grid(row=1, column=1, sticky='w', padx=(0, 15), pady=5)
        
        # SEPARADOR 1 (fila 2)
        tk.Label(res_grid, text="│", font=('Segoe UI', 14),
                bg='#f3f4f6', fg='#9ca3af').grid(row=1, column=2, padx=10)
        
        # BENEFICIO (row=1, columna 3-4)
        tk.Label(res_grid, text="Beneficio:", font=('Segoe UI', 10, 'bold'),
                bg='#f3f4f6', fg='#059669').grid(row=1, column=3, sticky='e', padx=(10, 5), pady=5)
        self.label_beneficio = tk.Label(res_grid, text="0.00 €",
                                       font=('Segoe UI', 10),
                                       bg='#f3f4f6', fg='#059669')
        self.label_beneficio.grid(row=1, column=4, sticky='w', padx=(0, 15), pady=5)
        
        # SEPARADOR 2 (fila 2)
        tk.Label(res_grid, text="│", font=('Segoe UI', 14),
                bg='#f3f4f6', fg='#9ca3af').grid(row=1, column=5, padx=10)
        
        # MARGEN MEDIO (row=1, columna 6-7)
        tk.Label(res_grid, text="Margen Medio:", font=('Segoe UI', 10, 'bold'),
                bg='#f3f4f6', fg='#3b82f6').grid(row=1, column=6, sticky='e', padx=(15, 5), pady=5)
        self.label_margen_medio = tk.Label(res_grid, text="0.0%",
                                          font=('Segoe UI', 10),
                                          bg='#f3f4f6', fg='#3b82f6')
        self.label_margen_medio.grid(row=1, column=7, sticky='w', padx=(0, 10), pady=5)
        
        # BOTÓN (Derecha, misma altura)
        boton_frame = tk.Frame(resumen_y_boton, bg='white')
        boton_frame.pack(side='right', fill='y', padx=(5, 0))
        
        # Botón GENERAR PDF (reducido)
        tk.Button(boton_frame, text="🚀 GENERAR PDF",
                 font=('Segoe UI', 11, 'bold'),
                 bg='#10b981', fg='white',
                 activebackground='#059669',
                 cursor='hand2',
                 command=self.generar_presupuesto,
                 width=20, height=3).pack(fill='x', padx=5, pady=(5, 2))
        
        # Botón RESUMEN CÁLCULOS (nuevo)
        tk.Button(boton_frame, text="📊 RESUMEN CÁLCULOS",
                 font=('Segoe UI', 9, 'bold'),
                 bg='#3b82f6', fg='white',
                 activebackground='#2563eb',
                 cursor='hand2',
                 command=self.generar_resumen_calculos,
                 width=20, height=2).pack(fill='x', padx=5, pady=(2, 5))
    
    def crear_seccion(self, parent, titulo):
        """Crear título de sección"""
        frame = tk.Frame(parent, bg='#f3f4f6', height=35)
        frame.pack(fill='x', pady=(10, 5))
        frame.pack_propagate(False)
        
        tk.Label(frame, text=titulo, font=('Segoe UI', 10, 'bold'),
                bg='#f3f4f6', fg='#374151').pack(anchor='w', padx=10, pady=8)
    
    def estructurar_descripcion(self, texto):
        """Organizar descripción: Tipo → Color → Medidas → Índices → Resto"""
        if not texto:
            return ""
        
        # Limpieza básica
        traducciones = {
            r"\\\'f1": "ñ", r"\\\'e1": "á", r"\\\'e9": "é",
            r"\\\'ed": "í", r"\\\'f3": "ó", r"\\\'fa": "ú",
            r"\\\'b7": "·", r"\'f3": "ó", r"\'e1": "á"
        }
        
        for c, l in traducciones.items():
            texto = texto.replace(c, l)
        
        texto = re.sub(r'\\[a-z0-9-]+', ' ', texto)
        texto = texto.replace('{', '').replace('}', '').replace('\\', '')
        texto = texto.replace('"', '')
        texto = re.sub(r'\s+', ' ', texto).strip()
        
        lineas = []
        
        # LÍNEA 1: TIPO (desde inicio hasta "Color:")
        match_tipo = re.search(r'^(.*?)(?=Color:)', texto, re.IGNORECASE)
        if match_tipo:
            tipo = match_tipo.group(1).strip()
            lineas.append(tipo)
            texto = texto[len(tipo):].strip()
        
        # LÍNEA 2: COLOR (desde "Color:" hasta "Ancho:")
        match_color = re.search(r'Color:\s*(.*?)(?=\s*Ancho:|\s*Alto:|\s*U=|$)', texto, re.IGNORECASE | re.DOTALL)
        if match_color:
            color_texto = match_color.group(1).strip()
            lineas.append(f"• Color: {color_texto}")
            # Eliminar del texto original
            texto = texto.replace(f"Color: {color_texto}", '', 1).replace("Color:", '', 1).strip()
       
        
        # LÍNEA 3: MEDIDAS (Ancho y Alto)
        ancho = re.search(r'Ancho:\s*([0-9.,\s-]+?)(?=\s*Alto:|\s*U=|$)', texto, re.IGNORECASE)
        alto = re.search(r'Alto:\s*([0-9.,\s]+?)(?=\s*U=|$)', texto, re.IGNORECASE)
        
        medidas_partes = []
        if ancho:
            medidas_partes.append(f"Ancho: {ancho.group(1).strip()}")
            texto = texto.replace(ancho.group(0), '', 1)
        if alto:
            medidas_partes.append(f"Alto: {alto.group(1).strip()}")
            texto = texto.replace(alto.group(0), '', 1)
        
        if medidas_partes:
            lineas.append(f"• {' - '.join(medidas_partes)}")
        
        # LÍNEA 4: ÍNDICES (U= ... dB) - acepta números o "PND"
        match_indices = re.search(r'U=\s*[0-9.,]+\s*W/[KÁ]+[·•]?m2?\s*-?\s*Ac[úÁa°]+stica[=:]\s*(?:[0-9]+\s*\([^)]+\)|PND)\s*dB', texto, re.IGNORECASE)
        if match_indices:
            lineas.append(f"• {match_indices.group(0).strip()}")
            texto = texto.replace(match_indices.group(0), '', 1).strip()
            
        # RESTO: Todo lo que queda
        texto = re.sub(r'\s+', ' ', texto).strip()
        if texto:
            lineas.append(f"• {texto}")
        
        return '<br/>'.join(lineas)
    
    def cargar_pdf(self):
        """Cargar PDF y extraer imágenes"""
        if not PYMUPDF_AVAILABLE:
            messagebox.showerror("Error",
                               "PyMuPDF no está instalado.\n\n"
                               "Instalar con: pip install pymupdf")
            return
        
        path = filedialog.askopenfilename(
            title="Seleccionar PDF con imágenes",
            filetypes=[("PDF", "*.pdf")]
        )
        
        if not path:
            return
        
        try:
            self.pdf_path = path
            doc = fitz.open(path)
            self.dibujos_extraidos = []
            
            for page in doc:
                imgs_pagina = []
                
                # Obtener todas las imágenes de la página
                for img in page.get_images(full=True):
                    xref = img[0]
                    rects = page.get_image_rects(xref)
                    
                    if not rects:
                        continue
                    
                    r = rects[0]
                    
                    # Filtrar imágenes por posición y tamaño
                    # (Las imágenes de ventanas suelen estar a la izquierda)
                    if r.x0 < 280 and 40 < r.width < 500:
                        pix = doc.extract_image(xref)
                        imgs_pagina.append({
                            'y': r.y0,
                            'data': BytesIO(pix["image"])
                        })
                
                # Ordenar por posición vertical
                imgs_pagina.sort(key=lambda x: x['y'])
                self.dibujos_extraidos.extend([i['data'] for i in imgs_pagina])
            
            doc.close()
            
            nombre = os.path.basename(path)
            self.lbl_pdf.config(
                text=f"✅ {nombre} ({len(self.dibujos_extraidos)} imágenes)",
                fg='#10b981'
            )
            
            messagebox.showinfo("PDF Cargado",
                              f"✅ PDF cargado correctamente\n\n"
                              f"Imágenes extraídas: {len(self.dibujos_extraidos)}")
            
        except Exception as e:
            messagebox.showerror("Error",
                               f"Error al cargar PDF:\n{str(e)}")
    
    def cargar_datos(self):
        """Cargar datos desde TXT"""
        path = filedialog.askopenfilename(
            title="Seleccionar archivo TXT con datos",
            filetypes=[("TXT", "*.txt"), ("Todos", "*.*")]
        )
        
        if not path:
            return
        
        try:
            self.txt_path = path
            self.items = []
            
            # Leer archivo con detección automática de encoding
            contenido = None
            encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252', 'utf-8-sig']
            
            for enc in encodings:
                try:
                    with open(path, 'r', encoding=enc) as f:
                        contenido = f.read()
                    print(f"✅ Archivo leído correctamente con encoding: {enc}")
                    break
                except (UnicodeDecodeError, UnicodeError):
                    continue
            
            if contenido is None:
                # Si ninguno funciona, usar latin-1 con replace
                with open(path, 'r', encoding='latin-1', errors='replace') as f:
                    contenido = f.read()
                print("⚠️ Usando latin-1 con caracteres de reemplazo")

                            # ===== VERIFICACIÓN DE SEGURIDAD - SOLO ARCHIVOS DE ALUMINIOS SECO =====
            texto_verificacion = "ALUMINIOS SECO, S.L"
            texto_verificacion2 = "B27152727"  # CIF único
            
            if texto_verificacion not in contenido or texto_verificacion2 not in contenido:
                messagebox.showerror(
                    "⛔ Archivo no válido",
                    "Este archivo TXT no es válido.\n\n"
                    "Este programa SOLO funciona con presupuestos\n"
                    "generados por:\n\n"
                    "   🏢 ALUMINIOS SECO, S.L.\n"
                    "   📍 A Cruz do Lobo, 8 - BARREIROS (LUGO)\n\n"
                    "Si necesitas un presupuesto, contacta con\n"
                    "ALUMINIOS SECO en el 982122509"
                )
                self.lbl_datos.config(text="❌ Archivo rechazado", fg='#dc2626')
                return
            
            print("✅ Archivo verificado: ALUMINIOS SECO")
            
               
            # Dividir por posiciones
            bloques = re.split(r'Pos\.', contenido)
            
            for bloque in bloques[1:]:
                lineas = bloque.split('\n')
                
                # Crear item
                # Limpiar el número de posición (puede tener comillas del CSV)
                pos_numero = lineas[0].split(',')[0].strip().replace('"', '').replace("'", '')
                
                item = {
                    'pos': "Pos." + pos_numero,
                    'desc': '',
                    'coste_u': 0.0,
                    'uds': 1,
                    'margen_individual': None,  # None = usa global
                    'colocacion_individual': None,  # None = usa global
                    'notas': '',
                    'dibujo_base64': None  # Dibujo asociado en base64
                }
                
                print(f"\n=== Procesando {item['pos']} ===")
                
                # Extraer descripción
                for linea in lineas:
                    # Limpiar línea de comillas extras y espacios
                    linea_limpia = linea.strip()
                    
                    if "Ancho:" in linea or "Color:" in linea or "Tapajuntas" in linea or "celular" in linea:
                        item['desc'] = self.estructurar_descripcion(linea)
                    
                    # FORMATO 1: Ventanas (con "UDS:")
                    if "UDS:" in linea:
                        # Unidades
                        u_match = re.search(r'UDS:\s*(\d+)', linea)
                        if u_match:
                            item['uds'] = int(u_match.group(1))
                        
                        # Precios (buscar todos los números con formato español)
                        precios = re.findall(r'[\d\.]+,[\d]+', linea)
                        if precios:
                            # El último precio es el total
                            total_str = precios[-1].replace('.', '').replace(',', '.')
                            total_float = float(total_str)
                            item['coste_u'] = total_float / item['uds']
                            print(f"  Formato ventana: {item['uds']} uds x {item['coste_u']}€")
                    
                    # FORMATO 2: Tapajuntas y accesorios (formato CSV con comillas)
                    # Buscar líneas que tengan estructura CSV: "texto","num","num"...
                    if linea_limpia.startswith('"') and linea_limpia.count('"') >= 6:
                        # Dividir por comas FUERA de las comillas
                        import csv
                        try:
                            # Usar csv.reader para parsear correctamente
                            campos = list(csv.reader([linea_limpia]))[0]
                            
                            # Verificar si es una línea de datos (no de cabecera)
                            if len(campos) >= 4 and campos[0] and 'Importe' not in campos[1]:
                                # Campo 0: código (ej: "1077 1 154")
                                # Campo 1: descripción (ej: "Tapajuntas de 45mm...")
                                # Campo 2: unidades (ej: "2,00")
                                # Campo 3: precio unitario (ej: "19,60")
                                
                                # Extraer descripción
                                if 'Tapajuntas' in campos[1] or 'celular' in campos[1]:
                                    item['desc'] = campos[1].strip()
                                
                                # Extraer unidades
                                try:
                                    uds_str = campos[2].replace(',', '.')
                                    item['uds'] = int(float(uds_str))
                                except (ValueError, IndexError):
                                    pass
                                
                                # Extraer precio unitario
                                try:
                                    precio_str = campos[3].replace(',', '.')
                                    item['coste_u'] = float(precio_str)
                                    print(f"  Formato CSV: {item['uds']} uds x {item['coste_u']}€ = {item['uds'] * item['coste_u']}€")
                                except (ValueError, IndexError):
                                    pass
                        except Exception as e:
                            print(f"  Error parseando CSV: {e}")
                
                # Solo añadir si tiene precio
                if item['coste_u'] > 0:
                    print(f"  ✅ Item añadido: {item['pos']} - {item['desc'][:50]}...")
                    self.items.append(item)
                else:
                    print(f"  ❌ Item ignorado (sin precio): {item['pos']}")
            
            nombre = os.path.basename(path)
            self.lbl_datos.config(
                text=f"✅ {nombre} ({len(self.items)} partidas)",
                fg='#10b981'
            )
            
            # Asociar dibujos con partidas si hay dibujos cargados
            self.asociar_dibujos_a_partidas()
            
            # Actualizar tabla
            self.actualizar_tabla()
            
            messagebox.showinfo("Datos Cargados",
                              f"✅ Datos cargados correctamente\n\n"
                              f"Partidas encontradas: {len(self.items)}")
            
        except Exception as e:
            messagebox.showerror("Error",
                               f"Error al cargar datos:\n{str(e)}")
            import traceback
            traceback.print_exc()

    def cargar_condiciones(self):
        """Cargar condiciones generales desde TXT"""
        path = filedialog.askopenfilename(
            title="Seleccionar archivo de Condiciones Generales",
            filetypes=[("TXT", "*.txt"), ("Todos", "*.*")]
        )
        
        if not path:
            return
        
        try:
            self.condiciones_path = path
            
            # Leer archivo
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                self.condiciones_texto = f.read()
            
            nombre = os.path.basename(path)
            self.lbl_condiciones.config(
                text=f"✅ {nombre}",
                fg='#10b981'
            )
            
            messagebox.showinfo("Condiciones Cargadas",
                              f"✅ Condiciones generales cargadas correctamente\n\n{nombre}")
            
        except Exception as e:
            messagebox.showerror("Error",
                               f"Error al cargar condiciones:\n{str(e)}")
            
        except Exception as e:
            messagebox.showerror("Error",
                               f"Error al cargar condiciones:\n{str(e)}")

    def asociar_dibujos_a_partidas(self):
        """Asociar cada dibujo extraído con su partida correspondiente"""
        import base64
        
        if not self.dibujos_extraidos:
            return
        
        # Asociar dibujos con partidas (uno a uno)
        for idx, item in enumerate(self.items):
            if idx < len(self.dibujos_extraidos):
                try:
                    # Convertir BytesIO a base64
                    self.dibujos_extraidos[idx].seek(0)
                    img_bytes = self.dibujos_extraidos[idx].read()
                    img_base64 = base64.b64encode(img_bytes).decode('utf-8')
                    item['dibujo_base64'] = img_base64
                except Exception as e:
                    print(f"Error al asociar dibujo {idx}: {e}")
                    item['dibujo_base64'] = None
            else:
                item['dibujo_base64'] = None
        
        print(f"✅ Dibujos asociados: {sum(1 for i in self.items if i.get('dibujo_base64'))}/{len(self.items)}")
        
        # Limpiar lista global después de asociar (ya no se necesita)
        # Cada item tiene su dibujo en base64
        self.dibujos_extraidos = []
    
    
    def actualizar_tabla(self):
        """Actualizar tabla con cálculos"""
        # Limpiar tabla
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        if not self.items:
            self.label_total_base.config(text="0.00 €")
            self.label_iva.config(text="0.00 €")
            self.label_total_final.config(text="0.00 €")
            self.label_coste_total.config(text="0.00 €")
            self.label_beneficio.config(text="0.00 €")
            self.label_margen_medio.config(text="0.0%")
            return
        
        # Añadir items
        total_base = 0
        coste_total = 0
        suma_margenes = 0
        num_items = 0
        
        for item in self.items:
            # Usar margen individual o global
            margen = item.get('margen_individual')
            if margen is None:
                margen = self.margen_global.get()
            
            # Usar colocación individual o global
            colocacion = item.get('colocacion_individual')
            if colocacion is None:
                colocacion = self.colocacion_global.get()
            
            # 🔒 GUARDAR valores aplicados para que el PDF use EXACTAMENTE estos
            item['margen_aplicado'] = margen
            item['colocacion_aplicada'] = colocacion
            
            # Calcular costes
            coste_item = item['coste_u'] * item['uds']
            coste_total += coste_item
            
            # Calcular PVP
            pvp_u = (item['coste_u'] + colocacion) * (1 + margen / 100)
            subtotal = pvp_u * item['uds']
            total_base += subtotal
            
            # Acumular márgenes para promedio
            suma_margenes += margen
            num_items += 1
            
            # Descripción corta para tabla
            desc_corta = item['desc'].replace('<br/>', ' ').replace('<b>', '').replace('</b>', '')
            if len(desc_corta) > 50:
                desc_corta = desc_corta[:50] + '...'
            
            self.tree.insert('', 'end', values=(
                item['pos'],
                item['uds'],
                desc_corta,
                f"{item['coste_u']:.2f} €",
                f"{colocacion:.2f} €",
                f"{margen:.1f}%",
                f"{pvp_u:.2f} €",
                f"{subtotal:.2f} €"
            ))
        
        # Actualizar resumen
        iva = total_base * 0.21
        total_final = total_base + iva
        
        # Calcular beneficio y margen medio
        beneficio = total_base - coste_total
        margen_medio = (suma_margenes / num_items) if num_items > 0 else 0
        
        # Actualizar labels fila 1 (totales principales)
        self.label_total_base.config(text=f"{total_base:,.2f} €")
        self.label_iva.config(text=f"{iva:,.2f} €")
        self.label_total_final.config(text=f"{total_final:,.2f} €")
        
        # Actualizar labels fila 2 (información de costes)
        self.label_coste_total.config(text=f"{coste_total:,.2f} €")
        self.label_beneficio.config(text=f"{beneficio:,.2f} €")
        self.label_margen_medio.config(text=f"{margen_medio:.1f}%")
    
    def aplicar_nota_global(self):
        """Aplicar nota global a todos los items"""
        if not self.items:
            messagebox.showwarning("Sin elementos",
                                 "No hay elementos cargados para aplicar la nota.")
            return
        
        # Obtener la nota del campo de texto
        nota = self.entry_nota_global.get('1.0', 'end-1c').strip()
        
        if not nota:
            messagebox.showwarning("Campo vacío",
                                 "Escribe una nota antes de aplicar.")
            return
        
        # Aplicar la nota a todos los items
        for item in self.items:
            item['nota_individual'] = nota
        
        messagebox.showinfo("✅ Nota aplicada",
                          f"Se ha aplicado la nota a {len(self.items)} elemento(s).\n\n"
                          f"Puedes editar la nota individualmente desde el botón ✏️ de cada posición.")
        
        # Actualizar la tabla (aunque la nota no se ve aquí, se aplicará en el PDF)
        self.actualizar_tabla()
    
    def editar_partida(self, event):
        """Editar partida individual"""
        selection = self.tree.selection()
        if not selection:
            return
        
        # Obtener índice
        item_id = selection[0]
        index = self.tree.index(item_id)
        item = self.items[index]
        
        # Ventana de edición
        edit_win = tk.Toplevel(self.root)
        edit_win.title(f"Editar {item['pos']}")
        edit_win.geometry("550x550")
        edit_win.configure(bg='white')
        edit_win.transient(self.root)
        edit_win.grab_set()
        
        # Centrar
        edit_win.update_idletasks()
        x = (edit_win.winfo_screenwidth() // 2) - (edit_win.winfo_width() // 2)
        y = (edit_win.winfo_screenheight() // 2) - (edit_win.winfo_height() // 2)
        edit_win.geometry(f"+{x}+{y}")
        
        # Contenido
        tk.Label(edit_win, text=f"Editar: {item['pos']}",
                font=('Segoe UI', 14, 'bold'), bg='white',
                fg='#1e40af').pack(pady=15)
        
        # Descripción corta
        desc_texto = item['desc'].replace('<br/>', ' ').replace('<b>', '').replace('</b>', '')[:100]
        tk.Label(edit_win, text=desc_texto,
                font=('Segoe UI', 9), bg='white',
                fg='#6b7280', wraplength=500).pack(pady=5)
        
        form = tk.Frame(edit_win, bg='white')
        form.pack(fill='both', expand=True, padx=30, pady=20)
        
        # Margen individual
        tk.Label(form, text="Margen individual (%):",
                font=('Segoe UI', 10, 'bold'), bg='white').grid(row=0, column=0,
                sticky='w', pady=10)
        
        margen_actual = item.get('margen_individual')
        if margen_actual is None:
            margen_actual = self.margen_global.get()
        
        var_margen = tk.DoubleVar(value=margen_actual)
        ttk.Spinbox(form, from_=0, to=100, textvariable=var_margen,
                   width=20).grid(row=0, column=1, sticky='ew', pady=10, padx=10)
        
        # Colocación individual
        tk.Label(form, text="Colocación individual (€):",
                font=('Segoe UI', 10, 'bold'), bg='white').grid(row=1, column=0,
                sticky='w', pady=10)
        
        coloc_actual = item.get('colocacion_individual')
        if coloc_actual is None:
            coloc_actual = self.colocacion_global.get()
        
        var_coloc = tk.DoubleVar(value=coloc_actual)
        ttk.Spinbox(form, from_=0, to=10000, textvariable=var_coloc,
                   width=20).grid(row=1, column=1, sticky='ew', pady=10, padx=10)
        
        # Nota individual (NUEVO)
        tk.Label(form, text="📝 Nota individual:",
                font=('Segoe UI', 10, 'bold'), bg='white').grid(row=2, column=0,
                sticky='nw', pady=10)
        
        nota_actual = item.get('nota_individual', '')
        text_nota_individual = scrolledtext.ScrolledText(form, height=3, width=35,
                                                         font=('Segoe UI', 9))
        text_nota_individual.grid(row=2, column=1, sticky='ew', pady=10, padx=10)
        text_nota_individual.insert('1.0', nota_actual)
        
        # Notas personalizadas (existente, ahora en row=3)
        tk.Label(form, text="Notas personalizadas:",
                font=('Segoe UI', 10, 'bold'), bg='white').grid(row=3, column=0,
                sticky='nw', pady=10)
        
        text_notas = scrolledtext.ScrolledText(form, height=6, width=35,
                                              font=('Segoe UI', 9))
        text_notas.grid(row=3, column=1, sticky='ew', pady=10, padx=10)
        text_notas.insert('1.0', item.get('notas', ''))
        
        form.columnconfigure(1, weight=1)
        
        # Botones
        btn_frame = tk.Frame(edit_win, bg='white')
        btn_frame.pack(pady=20)
        
        def guardar():
            item['margen_individual'] = var_margen.get()
            item['colocacion_individual'] = var_coloc.get()
            item['nota_individual'] = text_nota_individual.get('1.0', 'end-1c').strip()
            item['notas'] = text_notas.get('1.0', 'end-1c')
            self.actualizar_tabla()
            edit_win.destroy()
        
        tk.Button(btn_frame, text="💾 Guardar",
                 font=('Segoe UI', 10, 'bold'),
                 bg='#10b981', fg='white', padx=20, pady=8,
                 command=guardar).pack(side='left', padx=5)
        
        tk.Button(btn_frame, text="❌ Cancelar",
                 font=('Segoe UI', 10),
                 bg='#6b7280', fg='white', padx=20, pady=8,
                 command=edit_win.destroy).pack(side='left', padx=5)
    
    def añadir_partida_manual(self):
        """Ventana para añadir una partida manualmente"""
        # Ventana
        add_win = tk.Toplevel(self.root)
        add_win.title("➕ Añadir Partida Manual")
        add_win.geometry("600x550")
        add_win.configure(bg='white')
        add_win.resizable(False, False)
        
        # Centrar ventana
        add_win.transient(self.root)
        add_win.grab_set()
        
        # Título
        tk.Label(add_win, text="➕ Nueva Partida", 
                font=('Segoe UI', 14, 'bold'),
                bg='white', fg='#1e40af').pack(pady=15)
        
        # Frame para campos
        campos_frame = tk.Frame(add_win, bg='white')
        campos_frame.pack(fill='both', expand=True, padx=30, pady=10)
        
        # Campo: Descripción
        tk.Label(campos_frame, text="Descripción:", 
                font=('Segoe UI', 10, 'bold'),
                bg='white').grid(row=0, column=0, sticky='w', pady=10)
        
        text_desc = tk.Text(campos_frame, height=4, width=50, 
                           font=('Segoe UI', 10), wrap='word')
        text_desc.grid(row=0, column=1, pady=10, padx=10)
        
        # Campo: Unidades
        tk.Label(campos_frame, text="Unidades:", 
                font=('Segoe UI', 10, 'bold'),
                bg='white').grid(row=1, column=0, sticky='w', pady=10)
        
        entry_uds = tk.Entry(campos_frame, font=('Segoe UI', 10), width=20)
        entry_uds.grid(row=1, column=1, sticky='w', pady=10, padx=10)
        entry_uds.insert(0, "1")
        
        # Campo: Coste Base
        tk.Label(campos_frame, text="Coste Base (€):", 
                font=('Segoe UI', 10, 'bold'),
                bg='white').grid(row=2, column=0, sticky='w', pady=10)
        
        entry_coste = tk.Entry(campos_frame, font=('Segoe UI', 10), width=20)
        entry_coste.grid(row=2, column=1, sticky='w', pady=10, padx=10)
        entry_coste.insert(0, "0.00")
        
        # Campo: Margen % (opcional)
        tk.Label(campos_frame, text="Margen % (opcional):", 
                font=('Segoe UI', 10),
                bg='white', fg='#6b7280').grid(row=3, column=0, sticky='w', pady=10)
        
        entry_margen = tk.Entry(campos_frame, font=('Segoe UI', 10), width=20)
        entry_margen.grid(row=3, column=1, sticky='w', pady=10, padx=10)
        entry_margen.insert(0, "")
        
        tk.Label(campos_frame, text="(vacío = usar margen global)", 
                font=('Segoe UI', 8),
                bg='white', fg='#9ca3af').grid(row=4, column=1, sticky='w', padx=10)
        
        # Campo: Colocación (opcional)
        tk.Label(campos_frame, text="Colocación € (opcional):", 
                font=('Segoe UI', 10),
                bg='white', fg='#6b7280').grid(row=5, column=0, sticky='w', pady=10)
        
        entry_coloc = tk.Entry(campos_frame, font=('Segoe UI', 10), width=20)
        entry_coloc.grid(row=5, column=1, sticky='w', pady=10, padx=10)
        entry_coloc.insert(0, "")
        
        tk.Label(campos_frame, text="(vacío = usar colocación global)", 
                font=('Segoe UI', 8),
                bg='white', fg='#9ca3af').grid(row=6, column=1, sticky='w', padx=10)
        
        # Botones
        btn_frame = tk.Frame(add_win, bg='white')
        btn_frame.pack(pady=20)
        
        def guardar_nueva_partida():
            """Guardar la nueva partida"""
            try:
                # Validar descripción
                descripcion = text_desc.get('1.0', 'end-1c').strip()
                if not descripcion:
                    messagebox.showwarning("Campo vacío", 
                                         "La descripción no puede estar vacía")
                    return
                
                # Validar unidades
                try:
                    uds = int(entry_uds.get())
                    if uds <= 0:
                        raise ValueError
                except:
                    messagebox.showwarning("Valor inválido", 
                                         "Las unidades deben ser un número entero positivo")
                    return
                
                # Validar coste
                try:
                    coste = float(entry_coste.get().replace(',', '.'))
                    if coste < 0:
                        raise ValueError
                except:
                    messagebox.showwarning("Valor inválido", 
                                         "El coste debe ser un número válido")
                    return
                
                # Margen (opcional)
                margen_individual = None
                margen_text = entry_margen.get().strip()
                if margen_text:
                    try:
                        margen_individual = float(margen_text.replace(',', '.'))
                    except:
                        messagebox.showwarning("Valor inválido", 
                                             "El margen debe ser un número válido")
                        return
                
                # Colocación (opcional)
                colocacion_individual = None
                coloc_text = entry_coloc.get().strip()
                if coloc_text:
                    try:
                        colocacion_individual = float(coloc_text.replace(',', '.'))
                    except:
                        messagebox.showwarning("Valor inválido", 
                                             "La colocación debe ser un número válido")
                        return
                
                # Generar posición
                nueva_pos = f"Pos.{len(self.items) + 1}\""
                
                # Crear item
                nuevo_item = {
                    'pos': nueva_pos,
                    'desc': descripcion,
                    'coste_u': coste,
                    'uds': uds,
                    'margen_individual': margen_individual,
                    'colocacion_individual': colocacion_individual,
                    'notas': '(Partida manual)',
                    'dibujo_base64': None  # Las partidas manuales no tienen dibujo
                }
                
                # Añadir a la lista
                self.items.append(nuevo_item)
                
                # Actualizar tabla
                self.actualizar_tabla()
                
                # Cerrar ventana
                add_win.destroy()
                
                messagebox.showinfo("✅ Partida añadida", 
                                  f"Se ha añadido la partida {nueva_pos}")
                
            except Exception as e:
                messagebox.showerror("Error", f"Error al añadir partida:\n{str(e)}")
        
        tk.Button(btn_frame, text="💾 Guardar Partida",
                 font=('Segoe UI', 10, 'bold'),
                 bg='#10b981', fg='white', padx=20, pady=8,
                 command=guardar_nueva_partida).pack(side='left', padx=5)
        
        tk.Button(btn_frame, text="❌ Cancelar",
                 font=('Segoe UI', 10),
                 bg='#6b7280', fg='white', padx=20, pady=8,
                 command=add_win.destroy).pack(side='left', padx=5)
    
    def eliminar_partida(self):
        """Eliminar la partida seleccionada"""
        seleccion = self.tree.selection()
        
        if not seleccion:
            messagebox.showwarning("Sin selección", 
                                 "Selecciona una partida para eliminar")
            return
        
        # Obtener índice
        item_id = seleccion[0]
        index = self.tree.index(item_id)
        
        # Confirmar eliminación
        item = self.items[index]
        respuesta = messagebox.askyesno("Confirmar eliminación", 
                                       f"¿Eliminar la partida {item['pos']}?\n\n"
                                       f"{item['desc'][:50]}...")
        
        if respuesta:
            # Eliminar de la lista
            del self.items[index]
            
            # Actualizar tabla
            self.actualizar_tabla()
            
            messagebox.showinfo("✅ Eliminado", "Partida eliminada correctamente")
    
    def guardar_calculo(self):
        """Guardar el cálculo actual en un archivo JSON"""
        import datetime
        
        # Verificar que hay datos para guardar
        if not self.items:
            messagebox.showwarning("Sin datos", 
                                 "No hay partidas para guardar")
            return
        
        # Preparar datos para guardar
        datos_calculo = {
            'version': '1.0',
            'fecha_guardado': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'items': self.items,
            'margen_global': self.margen_global.get(),
            'colocacion_global': self.colocacion_global.get(),
            'cliente': {
                'num_oferta': self.entry_num_oferta.get(),
                'cliente_final': self.entry_cliente_final.get(),
                'direccion': self.entry_dir_cliente.get(),
                'telefono': self.entry_tlf_cliente.get(),
                'email': self.entry_email_cliente.get(),
                'referencia': self.entry_referencia_cliente.get()
            },
            'nota_modelos': self.entry_nota_global.get('1.0', 'end-1c'),
            'condiciones_generales': getattr(self, 'condiciones_texto', None)
        }
        
        # Función auxiliar para limpiar nombres de archivo
        def limpiar_nombre_archivo(texto):
            """Eliminar caracteres no válidos para nombres de archivo"""
            if not texto:
                return ""
            # Reemplazar caracteres problemáticos por guión bajo
            caracteres_invalidos = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
            for char in caracteres_invalidos:
                texto = texto.replace(char, '_')
            # Eliminar espacios múltiples y al inicio/final
            texto = ' '.join(texto.split())
            # Limitar longitud
            return texto[:50] if len(texto) > 50 else texto
        
        # Obtener datos para el nombre
        num_oferta = limpiar_nombre_archivo(self.entry_num_oferta.get()) or "SIN_NUM"
        cliente = limpiar_nombre_archivo(self.entry_cliente_final.get()) or "SIN_CLIENTE"
        referencia = limpiar_nombre_archivo(self.entry_referencia_cliente.get()) or "SIN_REF"
        
        # Construir nombre del archivo: NUM_CLIENTE_REF.json
        nombre_sugerido = f"{num_oferta}_{cliente}_{referencia}.json"
        
        # Diálogo para guardar
        archivo = filedialog.asksaveasfilename(
            title="Guardar Cálculo",
            defaultextension=".json",
            initialfile=nombre_sugerido,
            filetypes=[
                ("Archivo JSON", "*.json"),
                ("Todos los archivos", "*.*")
            ]
        )
        
        if archivo:
            try:
                with open(archivo, 'w', encoding='utf-8') as f:
                    json.dump(datos_calculo, f, indent=2, ensure_ascii=False)
                
                messagebox.showinfo("✅ Guardado", 
                                  f"Cálculo guardado correctamente en:\n{os.path.basename(archivo)}")
            except Exception as e:
                messagebox.showerror("Error", 
                                   f"Error al guardar el archivo:\n{str(e)}")
    
    def cargar_calculo(self):
        """Cargar un cálculo previamente guardado"""
        # Confirmar si hay datos sin guardar
        if self.items:
            respuesta = messagebox.askyesno(
                "Confirmar carga",
                "¿Cargar un cálculo guardado?\n\n"
                "Se perderán los datos actuales si no los has guardado."
            )
            if not respuesta:
                return
        
        # Diálogo para abrir archivo
        archivo = filedialog.askopenfilename(
            title="Cargar Cálculo",
            filetypes=[
                ("Archivo JSON", "*.json"),
                ("Todos los archivos", "*.*")
            ]
        )
        
        if archivo:
            try:
                with open(archivo, 'r', encoding='utf-8') as f:
                    datos_calculo = json.load(f)
                
                # Validar estructura básica
                if 'items' not in datos_calculo:
                    messagebox.showerror("Error", 
                                       "El archivo no tiene el formato correcto")
                    return
                
                # Cargar items
                self.items = datos_calculo['items']
                
                # Restaurar dibujos desde base64 a BytesIO
                import base64
                self.dibujos_extraidos = []
                for item in self.items:
                    if item.get('dibujo_base64'):
                        try:
                            img_bytes = base64.b64decode(item['dibujo_base64'])
                            self.dibujos_extraidos.append(BytesIO(img_bytes))
                        except:
                            self.dibujos_extraidos.append(None)
                    else:
                        self.dibujos_extraidos.append(None)
                
                # Cargar márgenes globales
                if 'margen_global' in datos_calculo:
                    self.margen_global.set(datos_calculo['margen_global'])
                if 'colocacion_global' in datos_calculo:
                    self.colocacion_global.set(datos_calculo['colocacion_global'])
                
                # Cargar datos del cliente
                if 'cliente' in datos_calculo:
                    cliente = datos_calculo['cliente']
                    self.entry_num_oferta.delete(0, tk.END)
                    self.entry_num_oferta.insert(0, cliente.get('num_oferta', ''))
                    
                    self.entry_cliente_final.delete(0, tk.END)
                    self.entry_cliente_final.insert(0, cliente.get('cliente_final', ''))
                    
                    self.entry_dir_cliente.delete(0, tk.END)
                    self.entry_dir_cliente.insert(0, cliente.get('direccion', ''))
                    
                    self.entry_tlf_cliente.delete(0, tk.END)
                    self.entry_tlf_cliente.insert(0, cliente.get('telefono', ''))
                    
                    self.entry_email_cliente.delete(0, tk.END)
                    self.entry_email_cliente.insert(0, cliente.get('email', ''))
                    
                    self.entry_referencia_cliente.delete(0, tk.END)
                    self.entry_referencia_cliente.insert(0, cliente.get('referencia', ''))
                
                # Cargar nota de modelos
                if 'nota_modelos' in datos_calculo:
                    self.entry_nota_global.delete('1.0', 'end')
                    self.entry_nota_global.insert('1.0', datos_calculo['nota_modelos'])
                
                # Cargar condiciones generales
                if 'condiciones_generales' in datos_calculo and datos_calculo['condiciones_generales']:
                    self.condiciones_texto = datos_calculo['condiciones_generales']
                    self.lbl_condiciones.config(
                        text="✅ Condiciones restauradas del archivo guardado",
                        fg='#10b981'
                    )
                
                # Actualizar tabla
                self.actualizar_tabla()
                
                # Deshabilitar botones de carga (protección)
                self.btn_cargar_pdf.config(state='disabled', bg='#d1d5db')
                self.btn_cargar_txt.config(state='disabled', bg='#d1d5db')
                self.btn_cargar_condiciones.config(state='disabled', bg='#d1d5db')
                
                # Actualizar indicador de archivo cargado
                nombre_archivo = os.path.basename(archivo)
                self.lbl_datos.config(
                    text=f"✅ {nombre_archivo} ({len(self.items)} partidas) - CÁLCULO GUARDADO",
                    fg='#10b981'
                )
                self.lbl_pdf.config(
                    text=f"📂 Dibujos restaurados del archivo guardado",
                    fg='#10b981'
                )
                
                messagebox.showinfo("✅ Cargado", 
                                  f"Cálculo cargado correctamente\n"
                                  f"{len(self.items)} partidas recuperadas\n\n"
                                  f"Los botones de carga están deshabilitados\n"
                                  f"para proteger la coherencia de los datos.")
                
            except json.JSONDecodeError:
                messagebox.showerror("Error", 
                                   "El archivo no es un JSON válido")
            except Exception as e:
                messagebox.showerror("Error", 
                                   f"Error al cargar el archivo:\n{str(e)}")
    
    def nuevo_calculo(self):
        """Iniciar un nuevo cálculo desde cero"""
        # Confirmar si hay datos sin guardar
        if self.items:
            respuesta = messagebox.askyesnocancel(
                "Nuevo Cálculo",
                "¿Deseas guardar el cálculo actual antes de crear uno nuevo?\n\n"
                "Sí = Guardar y crear nuevo\n"
                "No = Crear nuevo sin guardar\n"
                "Cancelar = Volver"
            )
            
            if respuesta is None:  # Cancelar
                return
            elif respuesta:  # Sí, guardar primero
                self.guardar_calculo()
        
        # Limpiar partidas
        self.items = []
        self.dibujos_extraidos = []
        
        # Limpiar campos del cliente
        self.entry_num_oferta.delete(0, tk.END)
        self.entry_cliente_final.delete(0, tk.END)
        self.entry_dir_cliente.delete(0, tk.END)
        self.entry_tlf_cliente.delete(0, tk.END)
        self.entry_email_cliente.delete(0, tk.END)
        self.entry_referencia_cliente.delete(0, tk.END)
        
        # Limpiar nota de modelos
        self.entry_nota_global.delete('1.0', 'end')
        
        # Limpiar condiciones generales
        if hasattr(self, 'condiciones_texto'):
            self.condiciones_texto = None
        
        # Resetear márgenes a valores por defecto
        self.margen_global.set(20.0)
        self.colocacion_global.set(50.0)
        
        # Limpiar indicadores de archivos
        self.lbl_pdf.config(text="Esperando PDF...", fg='#6b7280')
        self.lbl_datos.config(text="Esperando TXT...", fg='#6b7280')
        self.lbl_condiciones.config(text="Esperando TXT...", fg='#6b7280')
        
        # Habilitar botones de carga
        self.btn_cargar_pdf.config(state='normal', bg='#e0f2fe')
        self.btn_cargar_txt.config(state='normal', bg='#f0fdf4')
        self.btn_cargar_condiciones.config(state='normal', bg='#f5b2b6')
        
        # Actualizar tabla
        self.actualizar_tabla()
        
        messagebox.showinfo("🆕 Nuevo Cálculo", 
                          "Listo para comenzar un nuevo presupuesto")
    
    def cerrar_aplicacion(self):
        """Cerrar la aplicación con confirmación"""
        # Confirmar si hay datos sin guardar
        if self.items:
            respuesta = messagebox.askyesnocancel(
                "Cerrar Aplicación",
                "¿Deseas guardar el cálculo actual antes de salir?\n\n"
                "Sí = Guardar y salir\n"
                "No = Salir sin guardar\n"
                "Cancelar = Volver"
            )
            
            if respuesta is None:  # Cancelar
                return
            elif respuesta:  # Sí, guardar primero
                self.guardar_calculo()
        
        # Cerrar la aplicación
        self.root.quit()
        self.root.destroy()
    
    def generar_presupuesto(self):
        """Generar PDF final"""
        # Validaciones
        if not self.items:
            messagebox.showwarning("Faltan Datos",
                                 "Primero carga el archivo TXT con los datos")
            return
        
        # Pedir nombre de archivo
        output_path = filedialog.asksaveasfilename(
            title="Guardar Presupuesto",
            defaultextension=".pdf",
            filetypes=[("PDF", "*.pdf")]
        )
        
        if not output_path:
            return
        
        try:
            self.generar_pdf(output_path)
            messagebox.showinfo("¡Éxito!",
                              f"✅ Presupuesto generado correctamente\n\n{output_path}")
            
            # Abrir carpeta
            if os.name == 'nt':  # Windows
                os.startfile(os.path.dirname(output_path))
            
        except Exception as e:
            messagebox.showerror("Error",
                               f"Error al generar PDF:\n{str(e)}")
            import traceback
            traceback.print_exc()
    
    def generar_pdf(self, output_path):
        """Generar PDF con ReportLab"""

                       # Función helper para formatear precios con coma decimal (formato español)
        def formato_precio(valor):
            """Formatear precio: 1234.56 → 1.234,56 €"""
            # Formatear con 2 decimales
            texto = f"{valor:.2f}"
            # Separar parte entera y decimal
            if '.' in texto:
                parte_entera, parte_decimal = texto.split('.')
            else:
                parte_entera, parte_decimal = texto, "00"
            
            # Añadir separador de miles (punto)
            if len(parte_entera) > 3:
                parte_entera = f"{int(parte_entera):,}".replace(',', '.')
            
            # Retornar con coma decimal
            return f"{parte_entera},{parte_decimal} €"
        
        # Crear documento
        doc = SimpleDocTemplate(output_path, pagesize=A4)
        
        # Frame para primera página (margen superior pequeño)
        frame_primera = Frame(15*mm, 25*mm, 180*mm, 297*mm - 25*mm - 15*mm, id='primera')
        
        # Frame para páginas 2+ (margen superior grande para encabezado)
        frame_otras = Frame(15*mm, 25*mm, 180*mm, 297*mm - 25*mm - 35*mm, id='otras')
        
        # Definir templates
        template_primera = PageTemplate(id='Primera', frames=[frame_primera], onPage=self.primera_pagina)
        template_otras = PageTemplate(id='Otras', frames=[frame_otras], onPage=self.otras_paginas)
        
        doc.addPageTemplates([template_primera, template_otras])
        
        story = []
        styles = getSampleStyleSheet()
        
        # Estilos personalizados
        style_desc = ParagraphStyle(
            'Desc',
            parent=styles['Normal'],
            fontSize=7.5,
            leading=9.5
        )
        
        style_val = ParagraphStyle(
            'Val',
            parent=styles['Normal'],
            alignment=TA_RIGHT,
            fontSize=9
        )
        
        style_header = ParagraphStyle(
            'H',
            parent=styles['Normal'],
            alignment=TA_CENTER,
            fontSize=9,
            fontName='Helvetica-Bold'
        )
        
        style_info = ParagraphStyle(
            'Info',
            parent=styles['Normal'],
            fontSize=9,
            leading=11
        )
        
        style_info_bold = ParagraphStyle(
            'InfoBold',
            parent=styles['Normal'],
            fontSize=9,
            fontName='Helvetica-Bold',
            leading=11
        )
        
        # ===== LOGO CENTRADO EN LA CABECERA =====
        # Buscar logo en DATOS_DISTRIBUIDOR usando ruta compatible con PyInstaller
        posibles_rutas = [
            obtener_ruta_externa(os.path.join("DATOS_DISTRIBUIDOR", "LOGO_EMPRESA")),
            obtener_ruta_externa(os.path.join("DATOS_DISTRIBUIDOR", "LOGO_EMPRESA.jpg")),
            obtener_ruta_externa(os.path.join("DATOS_DISTRIBUIDOR", "LOGO_EMPRESA.png")),
            obtener_ruta_externa(os.path.join("DATOS_DISTRIBUIDOR", "logo_empresa.jpg")),
        ]
        
        logo_cargado = False
        for logo_path in posibles_rutas:
            if os.path.exists(logo_path):
                try:
                    print(f"✅ Logo encontrado en: {logo_path}")
                    logo_img = RLImage(logo_path, width=180*mm, height=25*mm, kind='proportional')                    # Tabla para centrar el logo
                    logo_table = Table([[logo_img]], colWidths=[180*mm])
                    logo_table.setStyle(TableStyle([
                        ('ALIGN', (0, 0), (0, 0), 'CENTER'),
                        ('VALIGN', (0, 0), (0, 0), 'MIDDLE'),
                    ]))
                    story.append(logo_table)
                    story.append(Spacer(1, 3))
                    logo_cargado = True
                    break
                except Exception as e:
                    print(f"❌ Error cargando logo desde {logo_path}: {e}")
                    continue
        
        if not logo_cargado:
            # Si no hay logo, poner texto centrado más grande
            print("⚠️ Logo no encontrado, usando texto")
            story.append(Paragraph("<b><font size=14>VIGO Y PRADO S.L.</font></b>", style_header))
            story.append(Spacer(1, 8))
        
        # ===== CUADRO DE PRESUPUESTO Y CLIENTE =====
        # Tabla con 2 columnas: Info presupuesto | Info cliente
        info_data = []
        
        # Columna izquierda: Datos del presupuesto
        num_oferta = self.entry_num_oferta.get() or "[NUM. OFERTA]"
        
        import datetime
        fecha = datetime.datetime.now().strftime("%d.%m.%Y")
        
        presupuesto_info = f"<b>PRESUPUESTO {num_oferta}</b><br/>"
        presupuesto_info += f"Fecha: {fecha}<br/>"
        
        # Añadir referencia si existe
        referencia = self.entry_referencia_cliente.get() or ""
        if referencia:
            presupuesto_info += f"<br/>Referencia: {referencia}"
        
        presupuesto_cell = Paragraph(presupuesto_info, style_info_bold)
        
        # Columna derecha: Datos del cliente final
        cliente_final = self.entry_cliente_final.get() or "[CLIENTE]"
        dir_cliente = self.entry_dir_cliente.get() or ""
        tlf_cliente = self.entry_tlf_cliente.get() or ""
        email_cliente = self.entry_email_cliente.get() or ""
        
        cliente_info = f"<b>{cliente_final}</b><br/>"
        if dir_cliente:
            cliente_info += f"{dir_cliente}<br/>"
        if tlf_cliente:
            cliente_info += f"Tel: {tlf_cliente}<br/>"
        if email_cliente:
            cliente_info += f"{email_cliente}"
        
        cliente_cell = Paragraph(cliente_info, style_info)
        
        info_data.append([presupuesto_cell, cliente_cell])
        
        info_table = Table(info_data, colWidths=[92*mm, 93*mm])
        info_table.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#1e40af')),
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f0f9ff')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ]))
        
        story.append(info_table)
        story.append(Spacer(1, 15))
        
        # Tabla principal
        data = [[
            Paragraph('DIBUJO', style_header),
            Paragraph('DESCRIPCIÓN', style_header),
            Paragraph('UDS', style_header),
            Paragraph('PRECIO UNIT.', style_header),
            Paragraph('TOTAL', style_header)
        ]]
        
        total_base = 0
        
        for idx, item in enumerate(self.items):
            # Calcular precio
            # 🔒 USAR VALORES APLICADOS (guardados cuando se pulsó Aplicar)
            # NO usar self.margen_global.get() ni self.colocacion_global.get()
            # porque pueden haber cambiado sin aplicarse
            
            margen = item.get('margen_aplicado')
            if margen is None:
                # Si no hay valor aplicado, usar el individual o 0
                margen = item.get('margen_individual', 0)
            
            colocacion = item.get('colocacion_aplicada')
            if colocacion is None:
                # Si no hay valor aplicado, usar el individual o 0
                colocacion = item.get('colocacion_individual', 0)
            
            pvp_u = (item['coste_u'] + colocacion) * (1 + margen / 100)
            subtotal = pvp_u * item['uds']
            total_base += subtotal
            
            # Imagen - solo usar dibujo del item (evita desincronización)
            img = "S/D"
            if item.get('dibujo_base64'):
                try:
                    import base64
                    img_bytes = base64.b64decode(item['dibujo_base64'])
                    img_bytesio = BytesIO(img_bytes)
                    img = RLImage(img_bytesio, width=38*mm, height=28*mm)
                except Exception as e:
                    print(f"Error al cargar dibujo del item: {e}")
                    img = "S/D"
            
            # Descripción con nota individual y notas personalizadas
            desc_completa = f"<b>{item['pos']}</b><br/>{item['desc']}"
            
            # Añadir notas personalizadas (si existen)
            if item.get('notas'):
                desc_completa += f"<br/><br/><b>NOTA:</b> {item['notas']}"
            
            # Añadir nota individual AL FINAL (si existe)
            if item.get('nota_individual'):
                desc_completa += f"<br/><br/>{item['nota_individual']}"
            
            data.append([
                img,
                Paragraph(desc_completa, style_desc),
                Paragraph(str(item['uds']), style_val),
                Paragraph(formato_precio(pvp_u), style_val),
                Paragraph(formato_precio(subtotal), style_val)
            ])
        
        # Crear tabla
        t = Table(data, colWidths=[40*mm, 95*mm, 12*mm, 24*mm, 24*mm])
        t.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.2, colors.grey),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#eeeeee')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        
        story.append(t)
        story.append(Spacer(1, 15))
        
        # Resumen
        iva = total_base * 0.21
        total_final = total_base + iva

       # Estilos para el resumen
        style_resumen = ParagraphStyle(
            'Resumen',
            parent=styles['Normal'],
            fontSize=10
        )
        
        style_total = ParagraphStyle(
            'Total',
            parent=styles['Normal'],
            fontSize=12,
            fontName='Helvetica-Bold'
        )

       
        resumen_data = [
           
            [Paragraph('BASE IMPONIBLE:', style_resumen), 
             Paragraph(formato_precio(total_base), style_resumen)],
            [Paragraph('I.V.A. (21%):', style_resumen), 
             Paragraph(formato_precio(iva), style_resumen)],
            [Paragraph('TOTAL PRESUPUESTO:', style_total), 
             Paragraph(formato_precio(total_final), style_total)]

        ]
        
        resumen_tab = Table(resumen_data, colWidths=[155*mm, 30*mm])
        resumen_tab.setStyle(TableStyle([
            ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),  # TODO a la derecha
            ('LEFTPADDING', (1, 0), (1, -1), 15),
            ('LINEABOVE', (1, 2), (1, 2), 1.5, colors.black),  # Línea sobre el total
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, 1), 3),
            ('BOTTOMPADDING', (0, 2), (1, 2), 5),
            ('VALIGN', (0, 0), (-1, -1), 'MIDLE'),
        ]))
        
        story.append(resumen_tab)

        # ===== SEPARADOR DECORATIVO =====
        story.append(Spacer(1, 20))
        line_style = ParagraphStyle('line', alignment=TA_CENTER, fontSize=7)
        story.append(Paragraph("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", line_style))
        story.append(Spacer(1, 15))
        
        # ===== CONDICIONES GENERALES =====
        if hasattr(self, 'condiciones_texto') and self.condiciones_texto:
            story.append(Paragraph("<b>CONDICIONES GENERALES:</b>", styles['Heading3']))
            story.append(Spacer(1, 8))
            
            # Dividir el texto en párrafos
            condiciones_parrafos = self.condiciones_texto.split('\n')
            for parrafo in condiciones_parrafos:
                if parrafo.strip():  # Solo si no está vacío
                    story.append(Paragraph(parrafo, styles['Normal']))
                    story.append(Spacer(1, 3))
            
            story.append(Spacer(1, 15))
            
            # ===== SEPARADOR ANTES DE FIRMA =====
            story.append(Paragraph("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", line_style))
            story.append(Spacer(1, 20))
        
        # ===== ACEPTACIÓN Y FIRMA =====
        firma_style = ParagraphStyle(
            'Firma',
            parent=styles['Normal'],
            fontSize=11,
            leading=18
        )
        
        story.append(Paragraph("<b>Aceptación del presupuesto:</b>", firma_style))
        story.append(Spacer(1, 25))
        story.append(Paragraph("Firmado: ...........................................", firma_style))
        story.append(Spacer(1, 10))

                
        # Observaciones (ELIMINADO - ya no existe el campo)
        # if not (hasattr(self, 'condiciones_texto') and self.condiciones_texto):
        #     if self.text_observaciones.get('1.0', 'end-1c').strip():
        #         story.append(Spacer(1, 20))
        #         story.append(Paragraph("<b>Observaciones:</b>", styles['Heading3']))
        #         story.append(Spacer(1, 5))
        #         story.append(Paragraph(self.text_observaciones.get('1.0', 'end-1c'),
        #                              styles['Normal']))
        
        # Construir PDF con numeración de páginas
        doc.build(story, onFirstPage=self.primera_pagina, onLaterPages=self.otras_paginas)

    def generar_resumen_calculos(self):
        """Genera PDF con resumen de cálculos internos (sin dibujos)"""
        if not self.items:
            messagebox.showwarning("Sin elementos",
                                 "No hay elementos para generar el resumen.")
            return
        
        # Obtener datos del presupuesto
        num_oferta = self.entry_num_oferta.get() or "[NUM. OFERTA]"
        cliente = self.entry_cliente_final.get() or "[CLIENTE]"
        
        # Diálogo guardar
        output_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF", "*.pdf")],
            initialfile=f"Resumen_Calculos_{num_oferta.replace('/', '-')}.pdf"
        )
        
        if not output_path:
            return
        
        try:
            # Crear PDF
            doc = SimpleDocTemplate(output_path, pagesize=A4,
                                  leftMargin=15*mm, rightMargin=15*mm,
                                  topMargin=15*mm, bottomMargin=15*mm)
            
            story = []
            styles = getSampleStyleSheet()
            
            # === TÍTULO ===
            titulo_style = ParagraphStyle(
                'TituloResumen',
                parent=styles['Heading1'],
                fontSize=16,
                textColor=colors.HexColor('#1e40af'),
                alignment=TA_CENTER,
                spaceAfter=10
            )
            story.append(Paragraph("RESUMEN DE CÁLCULOS INTERNOS", titulo_style))
            
            # === DATOS DEL PRESUPUESTO ===
            import datetime
            fecha = datetime.datetime.now().strftime("%d.%m.%Y")
            
            info_style = ParagraphStyle(
                'InfoResumen',
                parent=styles['Normal'],
                fontSize=10,
                alignment=TA_CENTER,
                spaceAfter=15
            )
            info_texto = f"<b>Oferta:</b> {num_oferta} | <b>Cliente:</b> {cliente} | <b>Fecha:</b> {fecha}"
            story.append(Paragraph(info_texto, info_style))
            story.append(Spacer(1, 10))
            
            # === TABLA DE CÁLCULOS ===
            # Encabezados
            tabla_data = [[
                Paragraph("<b>Pos.</b>", styles['Normal']),
                Paragraph("<b>Descripción</b>", styles['Normal']),
                Paragraph("<b>Uds</b>", styles['Normal']),
                Paragraph("<b>Coste Base</b>", styles['Normal']),
                Paragraph("<b>Coloc</b>", styles['Normal']),     
                Paragraph("<b>% Bº.</b>", styles['Normal']),
                Paragraph("<b>PVP Unit.</b>", styles['Normal']),
                Paragraph("<b>Total</b>", styles['Normal'])
            ]]
            
            # Función auxiliar para formatear precios
            def formato_precio(valor):
                return f"{valor:,.2f} €".replace(',', 'X').replace('.', ',').replace('X', '.')
            
            # Calcular totales
            total_base = 0.0
            
            # Añadir cada item
            for item in self.items:
                # Obtener valores
                coste_base = item.get('coste_u', 0.0)
                uds = item.get('uds', 1)
                
                # Margen y colocación (individuales o globales)
                margen = item.get('margen_individual')
                if margen is None:
                    margen = self.margen_global.get()
                
                colocacion = item.get('colocacion_individual')
                if colocacion is None:
                    colocacion = self.colocacion_global.get()
                
                # Calcular PVP unitario
                pvp_u = (coste_base + colocacion) * (1 + margen / 100)
                subtotal = pvp_u * uds
                total_base += subtotal
                
                # Descripción simplificada (solo texto, sin HTML)
                desc_html = item['desc']
                desc_limpia = desc_html.replace('<br/>', ' ').replace('<b>', '').replace('</b>', '')
                # Limitar longitud
                if len(desc_limpia) > 50:
                    desc_limpia = desc_limpia[:47] + "..."
                
                # Añadir fila (orden cambiado: Coste Base → Colocación → Margen)
                tabla_data.append([
                    item['pos'],
                    Paragraph(desc_limpia, styles['Normal']),
                    str(uds),
                    formato_precio(coste_base),
                    formato_precio(colocacion),
                    f"{margen:.1f}%",
                    formato_precio(pvp_u),
                    formato_precio(subtotal)
                ])
            
            # Crear tabla
            tabla = Table(tabla_data, colWidths=[
                15*mm,  # Pos
                60*mm,  # Descripción
                12*mm,  # Uds
                22*mm,  # Coste Base
                15*mm,  # Margen
                20*mm,  # Colocación
                22*mm,  # PVP Unit
                24*mm   # Total
            ])
            
            tabla.setStyle(TableStyle([
                # Encabezado
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e5e7eb')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 8),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('TOPPADDING', (0, 0), (-1, 0), 8),
                
                # Datos
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 7),
                ('ALIGN', (0, 1), (0, -1), 'CENTER'),  # Pos centrada
                ('ALIGN', (1, 1), (1, -1), 'LEFT'),    # Descripción izquierda
                ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),  # Números a la derecha
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING', (0, 1), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
                
                # Bordes
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('LINEBELOW', (0, 0), (-1, 0), 1.5, colors.black),
                
                # Filas alternadas
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9fafb')])
            ]))
            
            story.append(tabla)
            story.append(Spacer(1, 15))
            
            # === TOTALES ===
            iva = total_base * 0.21
            total_final = total_base + iva
            
            totales_style = ParagraphStyle(
                'Totales',
                parent=styles['Normal'],
                fontSize=10,
                alignment=TA_RIGHT,
                spaceAfter=3
            )
            
            total_final_style = ParagraphStyle(
                'TotalFinal',
                parent=styles['Normal'],
                fontSize=12,
                fontName='Helvetica-Bold',
                alignment=TA_RIGHT,
                spaceAfter=5
            )
            
            story.append(Paragraph(f"TOTAL BASE: {formato_precio(total_base)}", totales_style))
            story.append(Paragraph(f"IVA (21%): {formato_precio(iva)}", totales_style))
            story.append(Paragraph("_" * 60, totales_style))
            story.append(Paragraph(f"TOTAL FINAL: {formato_precio(total_final)}", total_final_style))
            
            # === PIE DE PÁGINA ===
            story.append(Spacer(1, 20))
            pie_style = ParagraphStyle(
                'Pie',
                parent=styles['Normal'],
                fontSize=8,
                textColor=colors.grey,
                alignment=TA_CENTER
            )
            story.append(Paragraph("Este documento es un resumen interno de cálculos. No es válido como presupuesto oficial.", pie_style))
            
            # Construir PDF
            doc.build(story)
            
            messagebox.showinfo("✅ Resumen generado",
                              f"Resumen de cálculos guardado en:\n{output_path}")
        
        except Exception as e:
            messagebox.showerror("Error",
                               f"Error al generar resumen:\n{str(e)}")


    def primera_pagina(self, canvas, doc):
       """Primera página: solo pie y número"""
       page_num = canvas._pageNumber
       canvas.saveState()
       
       # PIE DE PÁGINA - Usando ruta compatible con PyInstaller
       posibles_rutas_pie = [
           obtener_ruta_externa(os.path.join("DATOS_DISTRIBUIDOR", "DATOS_PIE")),
           obtener_ruta_externa(os.path.join("DATOS_DISTRIBUIDOR", "DATOS_PIE.txt")),
       ]
       pie_texto = ""
       for ruta_pie in posibles_rutas_pie:
           if os.path.exists(ruta_pie):
               try:
                   with open(ruta_pie, 'r', encoding='utf-8') as f:
                       pie_texto = f.read().strip()
                   break
               except: pass
       if pie_texto:
           canvas.setFont('Helvetica', 8)
           canvas.setFillColorRGB(0.3, 0.3, 0.3)
           lineas = pie_texto.split('\n')
           y_position = 12*mm
           for linea in reversed(lineas):
               if linea.strip():
                   canvas.drawCentredString(105*mm, y_position, linea.strip())
                   y_position += 3*mm
       # NÚMERO DE PÁGINA
       canvas.setFont('Helvetica', 9)
       canvas.setFillColorRGB(0.5, 0.5, 0.5)
       canvas.drawRightString(200*mm - 15*mm, 15*mm, f"Pág. {page_num}")
       canvas.restoreState()

    def otras_paginas(self, canvas, doc):
       """Páginas 2+: encabezado, pie y número"""
       page_num = canvas._pageNumber
       canvas.saveState()
       
       # ENCABEZADO
       from reportlab.lib import colors
       num_oferta = self.entry_num_oferta.get() or "[NUM. OFERTA]"
       cliente = self.entry_cliente_final.get() or "[CLIENTE]"
       import datetime
       fecha = datetime.datetime.now().strftime("%d.%m.%Y")
       canvas.setFillColorRGB(0.941, 0.976, 1.0)
       canvas.setStrokeColorRGB(0.118, 0.251, 0.686)
       canvas.setLineWidth(1)
       canvas.rect(15*mm, 297*mm - 20*mm, 180*mm, 8*mm, fill=1, stroke=1)
       canvas.setFillColorRGB(0, 0, 0)
       canvas.setFont('Helvetica', 9)
       y_pos = 297*mm - 16*mm
       canvas.drawString(20*mm, y_pos, f"PRESUPUESTO {num_oferta}")
       canvas.drawCentredString(105*mm, y_pos, f"Cliente: {cliente}")
       canvas.drawRightString(190*mm, y_pos, fecha)
       
           
       # ===== PIE DE PÁGINA (centro) - Usando ruta compatible con PyInstaller =====
       posibles_rutas_pie = [
           obtener_ruta_externa(os.path.join("DATOS_DISTRIBUIDOR", "DATOS_PIE")),
           obtener_ruta_externa(os.path.join("DATOS_DISTRIBUIDOR", "DATOS_PIE.txt")),
       ]
       
       pie_texto = ""
       for ruta_pie in posibles_rutas_pie:
           if os.path.exists(ruta_pie):
               try:
                   with open(ruta_pie, 'r', encoding='utf-8') as f:
                       pie_texto = f.read().strip()
                   break
               except Exception as e:
                   print(f"Error leyendo pie: {e}")
       
       # Dibujar pie de página centrado (si existe)
       if pie_texto:
           canvas.setFont('Helvetica', 8)
           canvas.setFillColorRGB(0.3, 0.3, 0.3)  # Gris oscuro
           
           # Dividir en líneas si tiene saltos de línea
           lineas = pie_texto.split('\n')
           y_position = 12*mm  # Posición desde abajo
           
           for linea in reversed(lineas):  # De abajo hacia arriba
               if linea.strip():
                   canvas.drawCentredString(105*mm, y_position, linea.strip())
                   y_position += 3*mm  # Subir para la siguiente línea
       
       # ===== NÚMERO DE PÁGINA (esquina derecha) =====
       text = f"Pág. {page_num}"
       canvas.setFont('Helvetica', 9)
       canvas.setFillColorRGB(0.5, 0.5, 0.5)  # Gris
       canvas.drawRightString(200*mm - 15*mm, 15*mm, text)
       
       canvas.restoreState()
def main():
    root = tk.Tk()
    app = GeneradorPresupuestosPRO(root)
    root.mainloop()


if __name__ == "__main__":
    main()
