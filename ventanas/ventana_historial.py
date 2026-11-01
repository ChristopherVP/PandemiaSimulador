import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from ui.estilo import C, estilo_ax, dar_espacio, leyenda
from ui.exportar_excel import exportar_excel, exportar_csv
from core.base_datos import DIAS_PAPELERA

COLUMNAS = [
    ('id', 'ID', 45), ('fecha', 'Fecha', 140), ('beta', 'β', 60), ('gamma', 'γ', 60), ('n', 'N', 85),
    ('i0', 'I0', 55), ('r0', 'R0', 60), ('estado', 'Estado', 95), ('pico', 'Pico', 95),
    ('mes_pico', 'Mes pico', 70), ('tasa_ataque', 'Ataque %', 75),
]
COLUMNAS_PAPELERA = [
    ('id', 'ID', 45), ('beta', 'β', 60), ('gamma', 'γ', 60), ('n', 'N', 85), ('i0', 'I0', 55), ('r0', 'R0', 60),
    ('estado', 'Estado', 95), ('pico', 'Pico', 95), ('eliminada', 'Eliminada el', 140),
    ('restante', 'Se borra en', 90),
]


class VentanaHistorial(tk.Toplevel):
    """Historial de simulaciones (SQLite). Los datos son de solo lectura: solo se pueden eliminar
    (van a una papelera, se pueden restaurar y se borran definitivamente a los 7 dias) y exportar."""

    def __init__(self, parent, base, on_cargar=None):
        super().__init__(parent)
        self.base = base
        self.on_cargar = on_cargar
        self.title('Historial y estadísticas — PandemiaSimulador')
        ancho = min(1180, self.winfo_screenwidth() - 60)
        alto = min(760, self.winfo_screenheight() - 110)
        self.geometry(f'{ancho}x{alto}+20+10')
        self.minsize(900, 520)
        self.configure(bg=C['bg'])
        self._estilo_tabla()
        self._construir()
        self.refrescar()

    # ------------------------------------------------------------------ estilo
    def _estilo_tabla(self):
        st = ttk.Style(self)
        st.configure('Hist.Treeview', background=C['panel'], fieldbackground=C['panel'], foreground=C['txt'],
                     rowheight=26, font=('Consolas', 9), borderwidth=0)
        st.configure('Hist.Treeview.Heading', background=C['cab'], foreground=C['txt'],
                     font=('Consolas', 9, 'bold'), relief='flat')
        st.map('Hist.Treeview', background=[('selected', C['acento'])], foreground=[('selected', '#0D1117')])

    def _boton(self, padre, texto, comando, color=None):
        return tk.Button(padre, text=texto, command=comando, bg=color or C['fondo_f'],
                         fg=C['txt'] if not color else '#0D1117', font=('Consolas', 10, 'bold'),
                         relief=tk.FLAT, bd=0, padx=14, pady=8, cursor='hand2')

    def _tabla(self, padre, columnas):
        marco = tk.Frame(padre, bg=C['bg'])
        tabla = ttk.Treeview(marco, columns=[c[0] for c in columnas], show='headings', style='Hist.Treeview',
                             selectmode='browse', height=8)
        for clave, titulo, ancho in columnas:
            tabla.heading(clave, text=titulo)
            tabla.column(clave, width=ancho, anchor='center')
        tabla.tag_configure('EPIDEMIA', foreground='#FF7B72')
        tabla.tag_configure('CONTROLADO', foreground='#3FB950')
        barra = ttk.Scrollbar(marco, orient=tk.VERTICAL, command=tabla.yview)
        tabla.configure(yscrollcommand=barra.set)
        tabla.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        barra.pack(side=tk.LEFT, fill=tk.Y)
        return marco, tabla

    # --------------------------------------------------------------- estructura
    def _construir(self):
        cab = tk.Frame(self, bg=C['fondo_f'])
        cab.pack(fill=tk.X)
        tk.Label(cab, text='📊  Historial y estadísticas de simulaciones', bg=C['fondo_f'], fg=C['txt'],
                 font=('Consolas', 13, 'bold')).pack(side=tk.LEFT, padx=14, pady=12)
        tk.Label(cab, text='Datos de solo lectura · Base de datos SQLite: pandemia.db', bg=C['fondo_f'],
                 fg=C['txt2'], font=('Consolas', 9)).pack(side=tk.RIGHT, padx=14)
        tk.Frame(self, bg=C['border'], height=2).pack(fill=tk.X)

        self.pestanas = ttk.Notebook(self)
        self.pestanas.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        self.tab_hist = tk.Frame(self.pestanas, bg=C['bg'])
        self.tab_pap = tk.Frame(self.pestanas, bg=C['bg'])
        self.pestanas.add(self.tab_hist, text='  📊 Historial  ')
        self.pestanas.add(self.tab_pap, text='  🗑 Papelera  ')
        self._construir_historial(self.tab_hist)
        self._construir_papelera(self.tab_pap)

    def _construir_historial(self, tab):
        botones = tk.Frame(tab, bg=C['bg'])
        botones.pack(side=tk.BOTTOM, fill=tk.X, padx=6, pady=(4, 8))
        self._boton(botones, '📗  GENERAR EXCEL', self.exportar_xlsx, C['R']).pack(side=tk.LEFT, padx=(0, 8))
        self._boton(botones, '📄  Exportar a CSV', self.exportar_csv).pack(side=tk.LEFT, padx=(0, 8))
        if self.on_cargar:
            self._boton(botones, '↩  Cargar parámetros', self.cargar_seleccion, C['acento']).pack(side=tk.LEFT)
        self._boton(botones, '🗑  Eliminar selección', self.eliminar).pack(side=tk.RIGHT, padx=(8, 0))
        self._boton(botones, '🧹  Vaciar historial', self.vaciar).pack(side=tk.RIGHT, padx=(8, 0))
        self._boton(botones, '🔄  Actualizar', self.refrescar).pack(side=tk.RIGHT)

        self.fig = Figure(figsize=(11, 2.6), dpi=100, facecolor=C['bg'])
        self.ax = self.fig.add_subplot(111)
        self.fig.subplots_adjust(left=0.08, right=0.98, top=0.86, bottom=0.2)
        self.canvas = FigureCanvasTkAgg(self.fig, master=tab)
        self.canvas.get_tk_widget().pack(side=tk.BOTTOM, fill=tk.X, padx=6, pady=4)

        frame_kpi = tk.Frame(tab, bg=C['bg'])
        frame_kpi.pack(fill=tk.X, padx=6, pady=(8, 4))
        self.kpis = {}
        for clave, titulo in [('total', 'Simulaciones'), ('controladas', 'Controladas'), ('epidemias', 'En epidemia'),
                              ('r0_prom', 'R0 promedio'), ('pico_prom', 'Pico promedio'), ('ataque_prom', 'Ataque prom. %')]:
            tarjeta = tk.Frame(frame_kpi, bg=C['panel'], highlightbackground=C['border'], highlightthickness=1)
            tarjeta.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=4)
            tk.Label(tarjeta, text=titulo, bg=C['panel'], fg=C['txt2'], font=('Consolas', 8)).pack(pady=(6, 0))
            lbl = tk.Label(tarjeta, text='—', bg=C['panel'], fg=C['acento'], font=('Consolas', 14, 'bold'))
            lbl.pack(pady=(0, 6))
            self.kpis[clave] = lbl

        marco, self.tabla = self._tabla(tab, COLUMNAS)
        marco.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)
        self.tabla.bind('<Double-1>', lambda e: self.cargar_seleccion())

    def _construir_papelera(self, tab):
        botones = tk.Frame(tab, bg=C['bg'])
        botones.pack(side=tk.BOTTOM, fill=tk.X, padx=6, pady=(4, 8))
        self._boton(botones, '♻  Restaurar selección', self.restaurar, C['R']).pack(side=tk.LEFT, padx=(0, 8))
        self._boton(botones, '♻  Restaurar todo', self.restaurar_todo).pack(side=tk.LEFT)
        self._boton(botones, '🔄  Actualizar', self.refrescar).pack(side=tk.RIGHT)

        self.lbl_info_pap = tk.Label(
            tab, bg=C['fondo_f'], fg=C['txt'], font=('Consolas', 10), justify=tk.LEFT, anchor='w', padx=12, pady=10,
            text=f'Aquí aparecen las simulaciones que eliminaste. Puedes restaurarlas durante {DIAS_PAPELERA} días; '
                 f'pasado ese tiempo se borran definitivamente.')
        self.lbl_info_pap.pack(fill=tk.X, padx=6, pady=(8, 4))
        tab.bind('<Configure>', lambda e: self.lbl_info_pap.config(wraplength=max(300, e.width - 40)))
        marco, self.tabla_pap = self._tabla(tab, COLUMNAS_PAPELERA)
        marco.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)
        self.lbl_vacia = tk.Label(tab, text='La papelera está vacía.', bg=C['bg'], fg=C['txt2'], font=('Consolas', 10))

    # --------------------------------------------------------------- contenido
    def refrescar(self):
        self.base.purgar_vencidas()
        for fila in self.tabla.get_children():
            self.tabla.delete(fila)
        for s in self.base.listar_simulaciones():
            self.tabla.insert('', tk.END, iid=str(s['id']), tags=(s['estado'],), values=(
                s['id'], s['fecha'], f"{s['beta']:.3f}", f"{s['gamma']:.3f}", f"{s['n']:,}", s['i0'],
                f"{s['r0']:.3f}", s['estado'], f"{s['pico']:,.1f}", s['mes_pico'], f"{s['tasa_ataque']:.2f}"))
        est = self.base.estadisticas_generales()
        self.kpis['total'].config(text=f"{est['total']}")
        self.kpis['controladas'].config(text=f"{int(est['controladas'])}")
        self.kpis['epidemias'].config(text=f"{int(est['epidemias'])}")
        self.kpis['r0_prom'].config(text=f"{est['r0_prom']:.3f}")
        self.kpis['pico_prom'].config(text=f"{est['pico_prom']:,.0f}")
        self.kpis['ataque_prom'].config(text=f"{est['ataque_prom']:.2f}")

        for fila in self.tabla_pap.get_children():
            self.tabla_pap.delete(fila)
        papelera = self.base.listar_papelera()
        for s in papelera:
            self.tabla_pap.insert('', tk.END, iid=str(s['id']), tags=(s['estado'],), values=(
                s['id'], f"{s['beta']:.3f}", f"{s['gamma']:.3f}", f"{s['n']:,}", s['i0'], f"{s['r0']:.3f}",
                s['estado'], f"{s['pico']:,.1f}", s['eliminada_en'], s['restante']))
        self.pestanas.tab(self.tab_pap, text=f'  🗑 Papelera ({len(papelera)})  ')
        self._dibujar()

    def _dibujar(self):
        ax = self.ax
        ax.cla()
        datos = self.base.promedio_por_mes()
        if datos:
            meses = [d['mes'] for d in datos]
            ax.fill_between(meses, [d['i_min'] for d in datos], [d['i_max'] for d in datos],
                            color=C['I'], alpha=0.18, label='Rango (mín – máx)')
            ax.plot(meses, [d['i_prom'] for d in datos], color=C['I'], lw=2.4, marker='o', ms=4,
                    label='Promedio de infectados')
            ax.set_xlim(0, max(meses)); ax.set_ylim(bottom=0)
            dar_espacio(ax, 0.22)
            leyenda(ax, loc='upper right', ncol=2, fontsize=8)
        else:
            ax.text(0.5, 0.5, 'Aún no hay simulaciones guardadas.\nPulsa «Aplicar Simulación» para registrar la primera.',
                    transform=ax.transAxes, ha='center', va='center', color=C['txt2'], fontsize=10)
        estilo_ax(ax, 'Infectados por mes en todas las simulaciones guardadas', ylabel='Personas infectadas')
        self.canvas.draw()

    # ----------------------------------------------------------------- acciones
    def _seleccion(self, tabla):
        sel = tabla.selection()
        return int(sel[0]) if sel else None

    def cargar_seleccion(self):
        sim_id = self._seleccion(self.tabla)
        if sim_id is None or not self.on_cargar:
            return
        fila = next((s for s in self.base.listar_simulaciones() if s['id'] == sim_id), None)
        if fila:
            self.on_cargar(fila)

    def eliminar(self):
        sim_id = self._seleccion(self.tabla)
        if sim_id is None:
            messagebox.showinfo('Eliminar', 'Selecciona primero una simulación de la tabla.', parent=self)
            return
        if messagebox.askyesno('Eliminar', f'¿Eliminar la simulación {sim_id}?\n\nIrá a la Papelera y podrás '
                               f'restaurarla durante {DIAS_PAPELERA} días.', parent=self):
            self.base.eliminar(sim_id)
            self.refrescar()

    def vaciar(self):
        n = self.base.total()
        if n and messagebox.askyesno('Vaciar historial', f'¿Enviar las {n} simulaciones a la Papelera?\n\n'
                                     f'Podrás restaurarlas durante {DIAS_PAPELERA} días.', parent=self):
            self.base.vaciar()
            self.refrescar()

    def restaurar(self):
        sim_id = self._seleccion(self.tabla_pap)
        if sim_id is None:
            messagebox.showinfo('Restaurar', 'Selecciona primero una simulación de la papelera.', parent=self)
            return
        self.base.restaurar(sim_id)
        self.refrescar()

    def restaurar_todo(self):
        if not self.base.total_papelera():
            messagebox.showinfo('Restaurar', 'La papelera está vacía.', parent=self)
            return
        for s in self.base.listar_papelera():
            self.base.restaurar(s['id'])
        self.refrescar()

    def exportar_xlsx(self):
        if not self.base.total():
            messagebox.showinfo('Exportar', 'No hay simulaciones para exportar.', parent=self)
            return
        ruta = filedialog.asksaveasfilename(parent=self, defaultextension='.xlsx', filetypes=[('Libro de Excel', '*.xlsx')],
                                            initialfile='PandemiaSimulador_historial.xlsx')
        if not ruta:
            return
        try:
            exportar_excel(self.base, ruta)
            messagebox.showinfo('Exportar', f'Archivo de Excel guardado en:\n{ruta}', parent=self)
        except PermissionError:
            messagebox.showerror('Exportar', 'No se pudo guardar: cierra el archivo si lo tienes abierto en Excel.', parent=self)
        except Exception as e:
            messagebox.showerror('Exportar', f'No se pudo generar el Excel:\n{e}', parent=self)

    def exportar_csv(self):
        if not self.base.total():
            messagebox.showinfo('Exportar', 'No hay simulaciones para exportar.', parent=self)
            return
        ruta = filedialog.asksaveasfilename(parent=self, defaultextension='.csv', filetypes=[('CSV', '*.csv')],
                                            initialfile='PandemiaSimulador_historial.csv')
        if ruta:
            try:
                exportar_csv(self.base, ruta)
                messagebox.showinfo('Exportar', f'CSV guardado en:\n{ruta}', parent=self)
            except Exception as e:
                messagebox.showerror('Exportar', f'No se pudo generar el CSV:\n{e}', parent=self)
