import tkinter as tk
from tkinter import filedialog, messagebox
import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.backends.backend_pdf import PdfPages
from ui.estilo import C
from ui.componentes import crear_panel_teoria


class BarraHerramientas(NavigationToolbar2Tk):
    toolitems = [t for t in NavigationToolbar2Tk.toolitems if t[0] not in ('Save', 'Subplots')]


def construir_figura_texto(icono, titulo, formulas, interpretacion, estado, ancho_pulgadas=12.0):
    parametros = (f"β={estado.beta:.3f}   γ={estado.gamma:.3f}   "
                  f"N={estado.N:,}   I0={estado.I0}   R0={estado.R0:.3f}   "
                  f"Meses simulados={estado.meses}")
    fig = Figure(figsize=(ancho_pulgadas, 6.4), dpi=100, facecolor=C['bg'])
    ax = fig.add_axes([0.03, 0.03, 0.94, 0.94])
    ax.axis('off')
    cuerpo_formulas = '\n'.join(formulas)
    cuerpo = (
        f'PandemiaSimulador — Distrito Metropolitano de Quito (DMQ) — COVID-19\n'
        f'{icono}  {titulo}\n\n'
        f'PARAMETROS DE LA SIMULACION:\n{parametros}\n\n'
        f'FORMULAS:\n{cuerpo_formulas}\n\n'
        f'ANALISIS DE CADA GRAFICA:\n{interpretacion}'
    )
    ax.text(0.0, 1.0, cuerpo, transform=ax.transAxes, va='top', ha='left',
            fontsize=9.2, color=C['txt'], family='monospace', wrap=True)
    return fig


class PanelTema(tk.Frame):
    ICONO = ''
    TITULO = 'Tema'
    CLAVE = ''

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

    def teoria(self):
        raise NotImplementedError

    def interpretar_resultados(self):
        return ''

    def cerrar(self):
        self.estado.desuscribir(self.actualizar)
        self.on_volver()
        self.destroy()

    def crear_ejes(self):
        raise NotImplementedError

    def construir_controles(self):
        pass

    def dibujar(self):
        raise NotImplementedError

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

        self.canvas.draw()
        titulo, formulas, _ = self.teoria()
        interpretacion = self.interpretar_resultados()
        fig_txt = construir_figura_texto(self.ICONO, titulo, formulas, interpretacion, self.estado)

        try:
            with PdfPages(ruta) as pdf:
                pdf.savefig(self.fig, facecolor=C['bg'])
                pdf.savefig(fig_txt, facecolor=C['bg'])
        except Exception as e:
            messagebox.showerror('No se pudo guardar el reporte',
                                 f'Ocurrió un problema generando el PDF:\n{e}')
