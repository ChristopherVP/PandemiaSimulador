import tkinter as tk
import numpy as np
import matplotlib.gridspec as gridspec
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from ui.ventana_base import ModuloReporte
from ui.estilo import C, estilo_ax, badge_figura, con_numero, num_corto, tabla_ax, dar_espacio, leyenda, anotar
from core.estado_global import MESES
from core.metodos_numericos import rk4_sir


class VistaPrevia(ModuloReporte):
    """Vista previa rápida: se dibuja dentro del panel de simulación y también entra al reporte completo."""
    ICONO = '◉'
    TITULO = 'Resumen General de la Simulación'
    SUBTITULO = 'Vista previa rápida: evolución de S, I y R, estado epidémico (R0) y cifras clave'
    CLAVE = 'previa'
    DESCRIPCION = ('Resume de un vistazo la simulación con los parámetros elegidos: las curvas de Susceptibles, '
                   'Infectados y Recuperados, el pico de contagios, y si la epidemia está controlada (R0 menor a 1) '
                   'o en expansión (R0 mayor a 1). Se calcula con el Modelo SIR resuelto con Runge-Kutta 4.')

    def __init__(self, parent, estado):
        self.estado = estado
        self._resumen = {}
        self.controles = {}
        self.fig = Figure(figsize=(12, 3.9), dpi=100, facecolor=C['bg'])
        self.canvas = FigureCanvasTkAgg(self.fig, master=parent)
        self.widget = self.canvas.get_tk_widget()
        self.widget.config(height=390, bg=C['bg'], highlightthickness=0)
        self.widget.pack(side=tk.TOP, fill=tk.X, expand=False, padx=6, pady=(6, 2))

        self.lbl_estado = tk.Label(parent, text='', bg=C['panel'], fg=C['txt'], font=('Consolas', 11, 'bold'))
        self.lbl_estado.pack(side=tk.TOP, fill=tk.X, pady=(2, 4))

        self.lbl_analisis = tk.Label(parent, bg=C['fondo_f'], fg=C['txt'], font=('Consolas', 9),
                                     justify=tk.LEFT, anchor='w', wraplength=1100)
        self.lbl_analisis.pack(side=tk.TOP, fill=tk.X, padx=8, pady=(4, 10))
        parent.bind('<Configure>', lambda e: self.lbl_analisis.config(wraplength=max(400, e.width - 40)))

        self.ejes = self.crear_ejes()

    # --------------------------------------------------------------- reporte
    def teoria(self):
        titulo = 'Resumen de la simulación del COVID-19 — Modelo SIR resuelto con Runge-Kutta 4'
        formulas = [
            'R0 = β/γ                       (número reproductivo básico)',
            'Criterio: R0 < 1 controlada, R0 > 1 en expansión   (estado de la epidemia)',
            'Tasa de ataque = (N − S_final)/N × 100 %   (porcentaje de la población que se contagió)',
        ]
        explicacion = (
            '¿QUÉ MUESTRA ESTA SECCIÓN?\n'
            'Es la vista general de la simulación con los parámetros elegidos antes de entrar al detalle de '
            'cada método numérico: cómo evolucionan los Susceptibles, Infectados y Recuperados de COVID-19 en el '
            'DMQ, cuándo ocurre el pico de contagios y si la epidemia se apaga sola (R0 < 1) o se expande (R0 > 1).\n\n'
            '¿QUÉ MÉTODO Y FÓRMULA LA CALCULAN?\n'
            'Se resuelve el sistema de ecuaciones diferenciales del Modelo SIR con Runge-Kutta 4, que promedia '
            'cuatro pendientes por paso. El número reproductivo básico R0 = β/γ resume la dinámica: indica a '
            'cuántas personas contagia, en promedio, cada infectado cuando casi toda la población es susceptible.\n\n'
            'CÓMO SE INTERPRETA\n'
            'Si R0 es menor a 1, la curva de infectados desciende desde el inicio. Si R0 es mayor a 1, la curva '
            'crece hasta un pico y luego baja a medida que se agotan los susceptibles.'
        )
        return titulo, formulas, explicacion

    def crear_ejes(self):
        gs = gridspec.GridSpec(1, 3, figure=self.fig, width_ratios=[1.3, 1.3, 1.0], top=0.83, bottom=0.17,
                               left=0.075, right=0.97, wspace=0.40)
        return dict(sir=self.fig.add_subplot(gs[0, 0]), inf=self.fig.add_subplot(gs[0, 1]),
                    tabla=self.fig.add_subplot(gs[0, 2]))

    def dibujar(self):
        beta, gamma, N, I0 = self.estado.beta, self.estado.gamma, self.estado.N, self.estado.I0
        R0 = beta / gamma
        t = np.arange(MESES)
        S4, I4, R4 = rk4_sir(beta, gamma, N, I0, MESES)
        pico = float(np.max(I4)); dp = int(np.argmax(I4))
        ataque = (N - S4[-1]) / N * 100

        ax = self.ejes['sir']; ax.cla()
        ax.plot(t, S4, color=C['S'], lw=2.2, label='S  Susceptibles')
        ax.plot(t, I4, color=C['I'], lw=2.4, label='I  Infectados')
        ax.plot(t, R4, color=C['R'], lw=2.2, label='R  Recuperados')
        ax.set_xlim(0, MESES - 1); ax.set_ylim(0, N)
        dar_espacio(ax, 0.26)
        leyenda(ax, loc='upper center', ncol=3, fontsize=7.6)
        estilo_ax(ax, con_numero(1, 'Curvas S, I y R'), ylabel='Personas')

        ax = self.ejes['inf']; ax.cla()
        ax.fill_between(t, I4, alpha=0.20, color=C['I'])
        ax.plot(t, I4, color=C['I'], lw=2.4, marker='o', ms=3.5, label='I(t) infectados')
        ax.axhline(I0, color=C['ref'], lw=1.0, ls=':', alpha=0.8, label=f'I0 = {I0:,}')
        ax.set_xlim(0, MESES - 1); ax.set_ylim(0, None)
        dar_espacio(ax, 0.42)
        if dp > 0 or R0 > 1:
            anotar(ax, dp, pico, f'Pico: {pico:,.0f} (mes {dp})', C['I'], MESES - 1, fs=8)
        leyenda(ax, loc='upper right', fontsize=7.6)
        estilo_ax(ax, con_numero(2, 'Infectados I(t) ampliado'), ylabel='Personas infectadas')

        ax = self.ejes['tabla']
        rows = [
            ['R0 = β/γ', f'{R0:.3f}'],
            ['Estado', 'EPIDEMIA' if R0 > 1 else 'CONTROLADO'],
            ['Pico de infectados', f'{num_corto(pico)}'],
            ['Mes del pico', f'{dp}'],
            ['Infectados al final', num_corto(I4[-1])],
            ['S final', num_corto(S4[-1])],
            ['R final', num_corto(R4[-1])],
            ['Tasa de ataque', f'{ataque:.2f} %'],
        ]
        tabla_ax(ax, rows, ['Indicador', 'Valor'], con_numero(3, 'Resumen'), alineacion=['l', 'c'],
                 resaltar={(1, 1): C['mal'] if R0 > 1 else C['ok']})
        badge_figura(self.fig, f'R0 = {R0:.2f}   {"EPIDEMIA (R0 > 1)" if R0 > 1 else "CONTROLADO (R0 < 1)"}',
                     C['mal'] if R0 > 1 else C['ok'])
        self.datos_resumen = [list(r) for r in rows]
        self._resumen = {'R0': R0, 'beta': beta, 'gamma': gamma, 'pico': pico, 'dp': dp, 'N': N, 'I0': I0,
                         'S_final': float(S4[-1]), 'R_final': float(R4[-1]), 'I_final': float(I4[-1]),
                         'ataque': float(ataque)}

    def analisis(self):
        r = self._resumen
        if not r:
            return []
        exp = r['R0'] > 1
        return [
            dict(n='1', titulo='Curvas S, I y R',
                 texto=(f"Con β = {r['beta']:.2f} y γ = {r['gamma']:.2f} el número reproductivo es R0 = {r['R0']:.2f}. "
                        f"La curva de susceptibles baja de {r['N']:,} a {r['S_final']:,.0f} personas y la de "
                        f"recuperados sube hasta {r['R_final']:,.0f}."),
                 conclusion=('R0 es mayor a 1: la epidemia está en EXPANSIÓN y cada infectado contagia en promedio a '
                             f"{r['R0']:.2f} personas." if exp else
                             'R0 es menor a 1: la epidemia está CONTROLADA y se apaga sola, porque cada infectado '
                             f"contagia en promedio a menos de una persona ({r['R0']:.2f}).")),
            dict(n='2', titulo='Infectados I(t) ampliado',
                 texto=(f"Partiendo de {r['I0']:,} infectados, " +
                        (f"la curva crece hasta un pico de {r['pico']:,.0f} infectados en el mes {r['dp']} y luego desciende."
                         if exp and r['dp'] > 0 else
                         f"la curva desciende desde el primer mes y termina en {r['I_final']:,.1f} infectados.")),
                 conclusion=('El pico marca el momento de mayor presión sobre el sistema de salud.' if exp and r['dp'] > 0
                             else 'No hay pico posterior: el mayor número de infectados es el inicial.')),
            dict(n='3', titulo='Tabla de indicadores',
                 texto=(f"Resume el estado ({'EPIDEMIA' if exp else 'CONTROLADO'}), el pico, los valores finales de S y R y "
                        f"la tasa de ataque, que alcanza {r['ataque']:.2f} % de la población."),
                 conclusion=('Una tasa de ataque baja indica que la población casi no se vio afectada; una alta, que '
                             'la epidemia recorrió buena parte de los susceptibles.')),
        ]

    # ------------------------------------------------------------ pantalla
    def actualizar(self):
        self.dibujar()
        self.canvas.draw()
        R0 = self.estado.R0
        self.lbl_estado.config(
            text=f'R0 = {R0:.2f}   {"⚠ EPIDEMIA (R0 > 1)" if R0 > 1 else "✓ CONTROLADO (R0 < 1)"}',
            fg=(C['I'] if R0 > 1 else C['R']))
        self.lbl_analisis.config(text='🔎 ANÁLISIS DE LA VISTA PREVIA\n\n' + self.interpretar_resultados())

    def refrescar(self):
        try:
            self.canvas.draw()
        except tk.TclError:
            pass
