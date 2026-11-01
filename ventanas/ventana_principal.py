import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import webbrowser
from ui.estilo import C
from ui.componentes import crear_slider
from ui import reporte
from core.estado_global import EstadoGlobal, MESES, N_MIN, N_MAX, FUENTE_PDF_NOMBRE, FUENTE_PDF_URL
from ventanas.registro import TEMAS
from ventanas.vista_previa import VistaPrevia
from ventanas.ventana_historial import VentanaHistorial
from core.base_datos import BaseDatos
from ventanas.ventana_sir import VentanaSIR
from ventanas.ventana_error import VentanaError
from ventanas.ventana_spline import VentanaSpline
from ventanas.ventana_derivacion import VentanaDerivacion
from ventanas.ventana_simpson import VentanaSimpson
from ventanas.ventana_nr import VentanaNewtonRaphson

CLASES_TEMA = {
    'sir': VentanaSIR,
    'error': VentanaError,
    'spline': VentanaSpline,
    'derivacion': VentanaDerivacion,
    'simpson': VentanaSimpson,
    'nr': VentanaNewtonRaphson,
}

COLORES_TEMA = {'sir': C['I'], 'error': C['nr_f'], 'spline': C['spline'],
                'derivacion': C['deriv'], 'simpson': C['simps'], 'nr': C['nr_b']}

DESCRIPCIONES_TEMA = {clave: cls.DESCRIPCION for clave, cls in CLASES_TEMA.items()}


class VentanaPrincipal(tk.Tk):
    def __init__(self):
        super().__init__()
        self.estado = EstadoGlobal()
        self.base_datos = BaseDatos()
        self.ventana_historial = None
        self.panel_actual = None
        self.clave_actual = None
        self.simulacion_aplicada = False
        self.botones_metodo = {}
        self.sliders_maestros = {}

        self.title('🦠 PandemiaSimulador — COVID-19 en el DMQ')
        self.geometry('1300x900')
        self.minsize(1080, 700)
        self.configure(bg=C['bg'])

        self._configurar_estilo_ttk()
        self._construir_cabecera()

        self.notebook = ttk.Notebook(self, style='Pandemia.TNotebook')
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=16, pady=(4, 16))

        self.tab_guia = tk.Frame(self.notebook, bg=C['bg'])
        self.tab_simulacion = tk.Frame(self.notebook, bg=C['bg'])
        self.notebook.add(self.tab_guia, text='  📘  Guía de Uso  ')
        self.notebook.add(self.tab_simulacion, text='  🎛  Panel de Simulación  ')

        self._construir_guia(self.tab_guia)
        self._construir_simulacion(self.tab_simulacion)

        self.actualizar_todo()
        self.notebook.bind('<<NotebookTabChanged>>', lambda e: self.after(80, self.vista_previa.refrescar))
        self.after(250, self.vista_previa.actualizar)

    def _configurar_estilo_ttk(self):
        estilo = ttk.Style(self)
        estilo.theme_use('clam')
        estilo.configure('Pandemia.TNotebook', background=C['bg'], borderwidth=0)
        estilo.configure('Pandemia.TNotebook.Tab', background=C['panel'], foreground=C['txt2'],
                          font=('Consolas', 10, 'bold'), padding=(16, 10), borderwidth=0)
        estilo.map('Pandemia.TNotebook.Tab',
                   background=[('selected', C['acento'])],
                   foreground=[('selected', '#0D1117')])
        estilo.configure('Pandemia.Vertical.TScrollbar', background=C['panel'], troughcolor=C['bg'],
                          bordercolor=C['bg'], arrowcolor=C['txt2'])

    def _construir_cabecera(self):
        tk.Label(self, text='🦠 PANDEMIA SIMULADOR — COVID-19 EN EL DISTRITO METROPOLITANO DE QUITO',
                 bg=C['bg'], fg=C['txt'], font=('Consolas', 16, 'bold')).pack(pady=(16, 2))
        tk.Label(self, text='Modelo SIR + Métodos Numéricos, calibrado con datos reales del DMQ (análisis mensual)',
                 bg=C['bg'], fg=C['txt2'], font=('Consolas', 10)).pack(pady=(0, 6))

    def _crear_area_scrollable(self, contenedor):
        lienzo = tk.Canvas(contenedor, bg=C['bg'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(contenedor, orient='vertical', command=lienzo.yview,
                                  style='Pandemia.Vertical.TScrollbar')
        interior = tk.Frame(lienzo, bg=C['bg'])

        interior.bind('<Configure>', lambda e: lienzo.configure(scrollregion=lienzo.bbox('all')))
        ventana_id = lienzo.create_window((0, 0), window=interior, anchor='nw')
        lienzo.bind('<Configure>', lambda e: lienzo.itemconfig(ventana_id, width=e.width))
        lienzo.configure(yscrollcommand=scrollbar.set)

        lienzo.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        return interior

    def _construir_guia(self, contenedor):
        interior = self._crear_area_scrollable(contenedor)

        def seccion(texto, color=C['acento']):
            tk.Label(interior, text=texto, bg=C['bg'], fg=color, font=('Consolas', 12, 'bold'),
                     anchor='w').pack(fill=tk.X, padx=26, pady=(20, 8))

        def parrafo(texto):
            tk.Label(interior, text=texto, bg=C['bg'], fg=C['txt'], font=('Consolas', 10),
                     wraplength=900, justify=tk.LEFT, anchor='w').pack(fill=tk.X, padx=26, pady=2)

        def enlace(texto, url):
            lbl = tk.Label(interior, text=texto, bg=C['bg'], fg=C['acento'], font=('Consolas', 10, 'underline'),
                          wraplength=900, justify=tk.LEFT, anchor='w', cursor='hand2')
            lbl.pack(fill=tk.X, padx=26, pady=(2, 8))
            lbl.bind('<Button-1>', lambda e: webbrowser.open(url))

        def formula_destacada(texto):
            marco = tk.Frame(interior, bg=C['panel'])
            marco.pack(fill=tk.X, padx=26, pady=4)
            tk.Label(marco, text=texto, bg=C['panel'], fg=C['nodo'], font=('Consolas', 10, 'bold'),
                     anchor='w', justify=tk.LEFT).pack(fill=tk.X, padx=12, pady=6)

        def tarjeta_metodo(clave, titulo, descripcion, color):
            marco = tk.Frame(interior, bg=C['panel'], highlightbackground=color, highlightthickness=1)
            marco.pack(fill=tk.X, padx=26, pady=5)
            tk.Label(marco, text=titulo, bg=C['panel'], fg=color, font=('Consolas', 10, 'bold'),
                     anchor='w').pack(fill=tk.X, padx=14, pady=(10, 2))
            tk.Label(marco, text=descripcion, bg=C['panel'], fg=C['txt2'], font=('Consolas', 9),
                     wraplength=880, justify=tk.LEFT, anchor='w').pack(fill=tk.X, padx=14, pady=(0, 10))

        seccion('¿Qué es este software?')
        parrafo('Es un simulador educativo de la pandemia de COVID-19, calibrado con datos reales del '
                'Distrito Metropolitano de Quito (DMQ), pensado para la materia de Métodos Numéricos. '
                'Combina un modelo matemático de propagación de enfermedades (el Modelo SIR) con seis '
                'métodos numéricos distintos, para que cada uno se pueda ver funcionar sobre los mismos '
                'datos generados por la simulación: no son ejercicios sueltos, todos parten de la misma '
                'epidemia de COVID-19 simulada. Todo el análisis se presenta en meses.')

        seccion('¿Qué es el Modelo SIR?')
        parrafo('SIR significa Susceptibles, Infectados y Recuperados: son los tres grupos en los que se '
                'divide una población durante una epidemia como la del COVID-19. Con el paso de los meses, '
                'personas Susceptibles se contagian del virus y pasan a Infectados, y los Infectados '
                'eventualmente se recuperan (o generan inmunidad) y pasan a Recuperados. Ese movimiento '
                'entre grupos se describe con tres ecuaciones diferenciales:')
        formula_destacada('dS/dt = -β·S·I/N        dI/dt = β·S·I/N - γ·I        dR/dt = γ·I')
        parrafo('β (beta) es qué tan fácil se contagia el COVID-19 (la tasa de transmisión o '
                'contagiosidad), y γ (gamma) qué tan rápido se recupera la gente. La razón R0 = β/γ es el '
                'número reproductivo básico: dice si la epidemia crece (R0 > 1) o se apaga (R0 < 1), y es '
                'el mismo tipo de indicador que usaron el MSP y la OMS durante la pandemia para declarar '
                'niveles de alerta. Internamente cada mes se calcula con pasos más finos para que el '
                'resultado sea numéricamente estable y preciso, aunque en pantalla solo se muestra un dato '
                'por mes.')

        seccion('¿Cómo se usa paso a paso?')
        parrafo('1.  Ve a la pestaña "Panel de Simulación" y ajusta β, γ, I0 y N con los sliders (todavía '
                'no se recalcula nada, solo estás eligiendo los datos).\n'
                '2.  Cuando estés listo, pulsa el botón "▶ Aplicar Simulación". Ahí se calcula todo, '
                'aparecen los botones para elegir qué resultado quieres ver y se habilita el botón "💾 '
                'Guardar reporte completo en PDF".\n'
                '3.  Pulsa el resultado que te interese (por ejemplo "Evolución de la Epidemia"); se abre '
                'justo debajo, dentro de la misma pantalla, con sus 4 gráficas numeradas.\n'
                '4.  Arriba de las gráficas hay teoría y fórmulas; abajo hay un análisis de cada gráfica '
                'individual: qué se ve, por qué se ve así y qué significa (con su conclusión).\n'
                '5.  Dentro de cada ventana hay un botón "💾 Guardar reporte de [ese resultado]" que '
                'exporta solo esa ventana (gráficas + parámetros + fórmulas + análisis) en un PDF.\n'
                '6.  Arriba del todo, el botón "💾 Guardar reporte completo en PDF" exporta en un solo '
                'archivo las 6 ventanas completas (todo menos esta guía).\n'
                '7.  Para elegir otro resultado, simplemente pulsa otro botón del listado: el anterior se '
                'cierra solo.\n'
                '8.  El botón "🔄 Reiniciar" deja todos los parámetros y resultados como al abrir el '
                'programa por primera vez.')

        seccion('Fuente de los datos de Quito')
        parrafo('Los parámetros con los que arranca el simulador están calibrados con cifras reales de '
                'COVID-19 del Distrito Metropolitano de Quito (DMQ), semana epidemiológica 45 (corte al 13 '
                'de noviembre de 2021): N ≈ 2 584 622 habitantes es la población del DMQ mayor a 5 años '
                'usada por el informe para calcular la cobertura de vacunación, e I0 = 330 aproxima los '
                'casos activos sumando los casos nuevos confirmados de las dos últimas semanas del informe '
                '(SE44=204 + SE45=126), un rango cercano a los 10-14 días que dura una persona siendo '
                'infecciosa. β y γ se ajustaron para reflejar el escenario de epidemia controlada (R0<1, '
                'nivel de alerta "Medio") que describe el informe en ese periodo. La simulación proyecta '
                f'{MESES} meses hacia adelante desde ese punto de partida.')
        parrafo('La población N se trata como una constante casi fija: el slider solo permite moverla '
                '±10 000 habitantes alrededor del dato real (entre 2 574 622 y 2 594 622), porque en el '
                'periodo simulado la población de Quito no cambia de forma relevante para el modelo — ese '
                'margen solo representa la incertidumbre normal de un censo o proyección poblacional.')
        parrafo(f'Fuente: Secretaría de Salud del Municipio del Distrito Metropolitano de Quito, '
                f'"{FUENTE_PDF_NOMBRE}".')
        enlace(f'📎  {FUENTE_PDF_URL}', FUENTE_PDF_URL)

        seccion('Los 6 resultados disponibles')
        for clave, texto, _ in TEMAS:
            tarjeta_metodo(clave, texto, DESCRIPCIONES_TEMA[clave], COLORES_TEMA[clave])

        tk.Button(interior, text='🎛  Ir al Panel de Simulación  →', bg=C['acento'], fg='#0D1117',
                  font=('Consolas', 11, 'bold'), relief=tk.FLAT, bd=0, padx=18, pady=12,
                  cursor='hand2', command=lambda: self.notebook.select(self.tab_simulacion)
                  ).pack(pady=28)

    def _construir_simulacion(self, contenedor):
        interior = self._crear_area_scrollable(contenedor)
        self._construir_controles_maestros(interior)
        self._construir_botones_accion(interior)
        self._construir_vista_previa(interior)
        self._construir_estado(interior)
        self._construir_selector_metodos(interior)
        self.frame_resultado = tk.Frame(interior, bg=C['bg'])
        self.frame_resultado.pack(fill=tk.BOTH, expand=True, padx=4, pady=(0, 20))

    def _construir_controles_maestros(self, contenedor):
        marco = tk.LabelFrame(contenedor, text=' 1. Elige los parámetros del COVID-19 (Quito, DMQ) ',
                              bg=C['panel'], fg=C['acento'], font=('Consolas', 9, 'bold'),
                              labelanchor='n', bd=1)
        marco.pack(fill=tk.X, padx=4, pady=(12, 6))

        fila1 = tk.Frame(marco, bg=C['panel']); fila1.pack(pady=6)
        fila2 = tk.Frame(marco, bg=C['panel']); fila2.pack(pady=6)

        def cambiar(attr):
            def cb(v):
                setattr(self.estado, attr, float(v) if attr in ('beta', 'gamma') else int(float(v)))
            return cb

        var_b, esc_b = crear_slider(fila1, 'β  contagio', 0.01, 1.0, self.estado.beta, 0.005, cambiar('beta'), C['I'],
                     descripcion='Qué tan fácil se transmite el COVID-19 persona a persona (tasa de contagio)')
        var_g, esc_g = crear_slider(fila1, 'γ  recuperación', 0.01, 0.50, self.estado.gamma, 0.01, cambiar('gamma'), C['R'],
                     descripcion='Qué tan rápido se recupera una persona contagiada (1/γ = duración de la enfermedad)')
        var_i, esc_i = crear_slider(fila2, 'I0 infectados iniciales', 1, 2000, self.estado.I0, 1, cambiar('I0'), C['S'],
                     descripcion='Casos activos de COVID-19: casos nuevos confirmados SE44+SE45 en Quito (204+126=330)')
        var_n, esc_n = crear_slider(fila2, 'N  población total', N_MIN, N_MAX, self.estado.N, 500, cambiar('N'), C['txt2'],
                     descripcion='Población del DMQ; es casi una constante, solo varía ±10 000 hab.')

        self.sliders_maestros = {'beta': var_b, 'gamma': var_g, 'I0': var_i, 'N': var_n}

    def _construir_botones_accion(self, contenedor):
        marco = tk.Frame(contenedor, bg=C['bg'])
        marco.pack(fill=tk.X, padx=4, pady=(4, 14))
        tk.Button(marco, text='▶  2. Aplicar Simulación', bg=C['acento'], fg='#0D1117',
                  font=('Consolas', 11, 'bold'), relief=tk.FLAT, bd=0, padx=22, pady=12,
                  cursor='hand2', command=self.aplicar_simulacion).pack(side=tk.LEFT, padx=(0, 10))
        tk.Button(marco, text='🔄  Reiniciar', bg='#DA3633', fg='white',
                  activebackground='#F85149', activeforeground='white',
                  font=('Consolas', 11, 'bold'), relief=tk.FLAT, bd=0, padx=22, pady=12,
                  cursor='hand2', command=self.reiniciar_todo).pack(side=tk.LEFT, padx=(0, 10))
        self.btn_reporte_completo = tk.Button(
            marco, text='💾  Guardar reporte completo en PDF', bg=C['border'], fg=C['txt2'],
            font=('Consolas', 11, 'bold'), relief=tk.FLAT, bd=0, padx=22, pady=12,
            cursor='hand2', state=tk.DISABLED, command=self.guardar_reporte_completo)
        self.btn_reporte_completo.pack(side=tk.LEFT, padx=(0, 10))
        tk.Button(marco, text='📊  Historial y estadísticas', bg=C['fondo_f'], fg=C['txt'],
                  font=('Consolas', 11, 'bold'), relief=tk.FLAT, bd=0, padx=22, pady=12,
                  cursor='hand2', command=self.abrir_historial).pack(side=tk.LEFT)

    def _construir_vista_previa(self, contenedor):
        marco = tk.LabelFrame(contenedor, text=' Vista previa rápida — resumen y análisis de la simulación ',
                              bg=C['panel'], fg=C['acento'], font=('Consolas', 9, 'bold'), labelanchor='n', bd=1)
        marco.pack(fill=tk.X, padx=4, pady=6)
        self.vista_previa = VistaPrevia(marco, self.estado)

    def _construir_estado(self, contenedor):
        tk.Frame(contenedor, bg=C['bg'], height=8).pack()

    def _construir_selector_metodos(self, contenedor):
        self.frame_selector = tk.LabelFrame(contenedor, text=' 3. Elige qué resultado quieres ver ',
                                            bg=C['panel'], fg=C['acento'], font=('Consolas', 9, 'bold'),
                                            labelanchor='n', bd=1)
        cuadricula = tk.Frame(self.frame_selector, bg=C['panel'])
        cuadricula.pack(fill=tk.X, expand=True, padx=14, pady=14)
        for i, (clave, texto, titulo) in enumerate(TEMAS):
            fila, col = divmod(i, 3)
            b = tk.Button(cuadricula, text=f'{texto}\n{titulo.split("—")[0].strip()}',
                          wraplength=300, justify=tk.CENTER,
                          bg=C['fondo_f'], fg=C['txt'], activebackground=COLORES_TEMA[clave],
                          activeforeground='#0D1117', font=('Consolas', 9, 'bold'), relief=tk.FLAT, bd=0,
                          padx=10, pady=16, cursor='hand2', command=lambda c=clave: self.abrir_tema(c))
            b.grid(row=fila, column=col, padx=8, pady=8, sticky='nsew')
            self.botones_metodo[clave] = b
        for c in range(3):
            cuadricula.grid_columnconfigure(c, weight=1, uniform='sel')

    def abrir_historial(self):
        if self.ventana_historial is not None and self.ventana_historial.winfo_exists():
            self.ventana_historial.refrescar()
            self.ventana_historial.lift()
            return
        self.ventana_historial = VentanaHistorial(self, self.base_datos, on_cargar=self.cargar_parametros)

    def cargar_parametros(self, fila):
        self.estado.beta, self.estado.gamma = fila['beta'], fila['gamma']
        self.estado.N, self.estado.I0 = fila['n'], fila['i0']
        self.sliders_maestros['beta'].set(fila['beta'])
        self.sliders_maestros['gamma'].set(fila['gamma'])
        self.sliders_maestros['N'].set(fila['n'])
        self.sliders_maestros['I0'].set(fila['i0'])
        self.notebook.select(self.tab_simulacion)
        self.aplicar_simulacion()

    def aplicar_simulacion(self):
        self.actualizar_todo()
        try:
            self.base_datos.guardar_simulacion(self.estado)
            if self.ventana_historial is not None and self.ventana_historial.winfo_exists():
                self.ventana_historial.refrescar()
        except Exception as e:
            messagebox.showwarning('Historial', f'La simulación se calculó, pero no se pudo guardar en la base de datos:\n{e}')
        if not self.simulacion_aplicada:
            self.frame_selector.pack(fill=tk.X, padx=4, pady=6, before=self.frame_resultado)
            self.simulacion_aplicada = True
        self.btn_reporte_completo.config(state=tk.NORMAL, bg=C['acento'], fg='#0D1117')
        self.vista_previa.refrescar()

    def reiniciar_todo(self):
        if self.panel_actual is not None:
            self.panel_actual.cerrar()

        self.estado.restablecer()
        self.sliders_maestros['beta'].set(self.estado.beta)
        self.sliders_maestros['gamma'].set(self.estado.gamma)
        self.sliders_maestros['I0'].set(self.estado.I0)
        self.sliders_maestros['N'].set(self.estado.N)

        if self.simulacion_aplicada:
            self.frame_selector.pack_forget()
            self.simulacion_aplicada = False
        self.btn_reporte_completo.config(state=tk.DISABLED, bg=C['border'], fg=C['txt2'])

        self.actualizar_todo()

    def abrir_tema(self, clave):
        if self.panel_actual is not None:
            self.panel_actual.cerrar()

        cls = CLASES_TEMA[clave]
        self.panel_actual = cls(self.frame_resultado, self.estado, self._panel_cerrado)
        self.panel_actual.pack(fill=tk.BOTH, expand=True)
        self.clave_actual = clave

        for c, b in self.botones_metodo.items():
            b.config(bg=(COLORES_TEMA[c] if c == clave else C['fondo_f']),
                     fg=('#0D1117' if c == clave else C['txt']))

    def _panel_cerrado(self):
        self.panel_actual = None
        self.clave_actual = None
        for c, b in self.botones_metodo.items():
            b.config(bg=C['fondo_f'], fg=C['txt'])

    def cerrar_panel_actual(self):
        if self.panel_actual is not None:
            self.panel_actual.cerrar()

    def guardar_reporte_completo(self):
        ruta = filedialog.asksaveasfilename(
            defaultextension='.pdf', filetypes=[('Documento PDF', '*.pdf')],
            initialfile='PandemiaSimulador_Quito_reporte_completo.pdf')
        if not ruta:
            return

        ventana_oculta = tk.Toplevel(self)
        ventana_oculta.withdraw()
        ventana_oculta.geometry('1300x760')
        paneles = []
        self.config(cursor='watch')
        self.update_idletasks()
        try:
            modulos = [('previa', self.vista_previa)]
            for clave, _, _ in TEMAS:
                panel = CLASES_TEMA[clave](ventana_oculta, self.estado, lambda: None)
                panel.pack(fill=tk.BOTH, expand=True)
                if self.panel_actual is not None and clave == self.clave_actual:
                    panel.controles.update(self.panel_actual.controles)
                paneles.append(panel)
                modulos.append((clave, panel))
            ventana_oculta.update_idletasks()
            reporte.guardar_completo(ruta, modulos, self.estado)
            messagebox.showinfo('Reporte guardado', f'El reporte completo se guardó en:\n{ruta}')
        except Exception as e:
            messagebox.showerror('No se pudo guardar el reporte',
                                 f'Ocurrió un problema generando el PDF completo:\n{e}')
        finally:
            for panel in paneles:
                panel.estado.desuscribir(panel.actualizar)
            ventana_oculta.destroy()
            self.config(cursor='')

    def actualizar_todo(self):
        self.vista_previa.actualizar()
        self.estado.notificar()
