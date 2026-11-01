import tkinter as tk
from tkinter import filedialog, messagebox
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from ui.estilo import C, tema_claro
from ui.componentes import crear_panel_teoria
from ui import reporte


class BarraHerramientas(NavigationToolbar2Tk):
    toolitems = [t for t in NavigationToolbar2Tk.toolitems if t[0] not in ('Save', 'Subplots')]


class ModuloReporte:
    """Comportamiento comun de todo resultado que se puede dibujar en pantalla y exportar a PDF.
    Las subclases definen teoria(), crear_ejes(), dibujar() y analisis()."""
    ICONO = ''
    TITULO = 'Tema'
    CLAVE = ''
    DESCRIPCION = ''
    SUBTITULO = ''

    datos_resumen = ()

    def teoria(self):
        raise NotImplementedError

    def crear_ejes(self):
        raise NotImplementedError

    def dibujar(self):
        raise NotImplementedError

    def analisis(self):
        """Lista de dicts: {'n': '1', 'titulo': ..., 'texto': ..., 'conclusion': ...}"""
        return []

    def interpretar_resultados(self):
        """Texto del analisis para mostrar en pantalla."""
        items = self.analisis()
        if not items:
            return ''
        bloques = []
        for it in items:
            bloques.append(f"🔵 GRÁFICA {it['n']} ({it['titulo']}): {it['texto']}\n→ Conclusión: {it['conclusion']}")
        return '\n\n'.join(bloques)

    def dibujar_en(self, figura):
        """Redibuja este resultado en otra figura (p. ej. la hoja del PDF) sin tocar la de pantalla."""
        fig_ant, ejes_ant, resumen_ant = self.fig, self.ejes, dict(getattr(self, '_resumen', {}))
        try:
            self.fig = figura
            self.ejes = self.crear_ejes()
            self.dibujar()
        finally:
            self.fig, self.ejes = fig_ant, ejes_ant
            self._resumen = resumen_ant
        return figura


class PanelTema(tk.Frame, ModuloReporte):
    def __init__(self, parent, estado, on_volver):
        super().__init__(parent, bg=C['bg'], highlightbackground=C['border'], highlightthickness=1)
        self.estado = estado
        self.on_volver = on_volver
        self.controles = {}
        self._resumen = {}

        self._construir_barra_superior()
        self._construir_panel_teoria()

        frame_fig = tk.Frame(self, bg=C['bg'])
        frame_fig.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.fig = Figure(figsize=(12, 6.9), dpi=100, facecolor=C['bg'])
        self.canvas = FigureCanvasTkAgg(self.fig, master=frame_fig)
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        barra_zoom = BarraHerramientas(self.canvas, frame_fig)
        barra_zoom.config(bg=C['panel'])
        barra_zoom.update()

        self.frame_controles = tk.Frame(self, bg=C['panel'])
        self.frame_controles.pack(side=tk.TOP, fill=tk.X)

        self.lbl_interpretacion = tk.Label(self, bg=C['fondo_f'], fg=C['txt'], font=('Consolas', 9),
                                            justify=tk.LEFT, anchor='w', wraplength=950)
        self.lbl_interpretacion.pack(side=tk.TOP, fill=tk.X, padx=12, pady=(10, 18))

        self.ejes = self.crear_ejes()
        self.construir_controles()
        estado.suscribir(self.actualizar)
        self.actualizar()

    def _construir_barra_superior(self):
        barra = tk.Frame(self, bg=C['fondo_f'])
        barra.pack(side=tk.TOP, fill=tk.X)
        fila = tk.Frame(barra, bg=C['fondo_f'])
        fila.pack(fill=tk.X, padx=12, pady=10)
        tk.Label(fila, text=f'{self.ICONO}  {self.TITULO}', bg=C['fondo_f'], fg=C['txt'],
                 font=('Consolas', 13, 'bold')).pack(side=tk.LEFT)
        tk.Button(fila, text=f'💾  Guardar reporte de {self.TITULO}', bg=C['acento'], fg='#0D1117',
                  activebackground='#58A6FF', activeforeground='#0D1117',
                  font=('Consolas', 10, 'bold'), relief=tk.FLAT, bd=0, padx=16, pady=8,
                  cursor='hand2', command=self.guardar_reporte).pack(side=tk.RIGHT)
        tk.Frame(barra, bg=C['border'], height=2).pack(fill=tk.X)

    def _construir_panel_teoria(self):
        titulo, formulas, explicacion = self.teoria()
        panel = crear_panel_teoria(self, titulo, formulas, explicacion, wraplength=950)
        panel.pack(side=tk.TOP, fill=tk.X, padx=12, pady=10)

    def cerrar(self):
        self.estado.desuscribir(self.actualizar)
        self.on_volver()
        self.destroy()

    def construir_controles(self):
        pass

    def actualizar(self, *_):
        self.dibujar()
        self.canvas.draw_idle()
        texto = self.interpretar_resultados()
        self.lbl_interpretacion.config(
            text=('🔎 ANÁLISIS DE CADA GRÁFICA DE ESTE RESULTADO\n\n' + texto) if texto else '')

    def guardar_reporte(self):
        nombre_defecto = self.TITULO.replace(' ', '_').replace('/', '-')
        ruta = filedialog.asksaveasfilename(
            defaultextension='.pdf', filetypes=[('Documento PDF', '*.pdf')],
            initialfile=f'{nombre_defecto}.pdf')
        if not ruta:
            return
        try:
            reporte.guardar_modulo(ruta, self, self.estado)
        except Exception as e:
            messagebox.showerror('No se pudo guardar el reporte',
                                 f'Ocurrió un problema generando el PDF:\n{e}')
