import numpy as np
from ui.ventana_base import PanelTema
from ui.estilo import C, estilo_ax, tabla_ax, con_numero, num_corto, dar_espacio, leyenda, eje_derecho
from core.estado_global import MESES
from core.metodos_numericos import rk4_sir, derivacion_numerica


class VentanaDerivacion(PanelTema):
    ICONO = '④'
    TITULO = 'Velocidad de Propagación'
    SUBTITULO = 'Diferenciación numérica de 3 puntos sobre la curva de infectados'
    CLAVE = 'derivacion'
    DESCRIPCION = ('Muestra qué tan rápido crece o baja el contagio de COVID-19 cada mes (la velocidad de '
                   'cambio de la incidencia, no el número de infectados en sí). Se calcula con '
                   'Diferenciación Numérica de 3 puntos.')

    def teoria(self):
        titulo = 'Velocidad de Propagación del COVID-19 — calculada con Diferenciación Numérica'
        formulas = [
            'Interior:  dI/dt ≈ [I(t+h) − I(t−h)] / 2h        (3 puntos, centrada)',
            'Inicio:    dI/dt ≈ [-3I0 + 4I1 − I2] / 2h         (progresiva)',
            'Final:     dI/dt ≈ [In-2 − 4In-1 + 3In] / 2h      (regresiva)',
        ]
        explicacion = (
            '¿QUÉ MUESTRA ESTA GRÁFICA?\n'
            'No muestra cuántos infectados de COVID-19 hay, sino qué tan rápido está subiendo o bajando ese '
            'número cada mes: la "aceleración" del contagio, muy parecida a la tasa de incidencia que '
            'reporta la vigilancia epidemiológica. Permite ver el momento exacto en que la epidemia deja de '
            'crecer y empieza a bajar (el pico), sin tener que leerlo directamente de la curva de '
            'infectados.\n\n'
            '¿QUÉ MÉTODO Y FÓRMULA LA CALCULAN?\n'
            'Se parte únicamente de los valores discretos de I(t) que ya generó RK4, sin usar la ecuación '
            'diferencial original, y se aproxima su derivada con fórmulas de diferencias finitas de 3 '
            'puntos. Cuando esta velocidad cruza por cero, ahí está exactamente el pico de la epidemia.\n\n'
            'RELACIÓN CON LOS DATOS REALES DE QUITO\n'
            'El informe de la Secretaría de Salud reporta la incidencia de COVID-19 semana a semana; por '
            'ejemplo, los casos nuevos confirmados bajaron de 204 en la SE44 a 126 en la SE45. Esa '
            'comparación entre periodos es, en esencia, una derivada discreta de los contagios. Esta '
            'ventana calcula lo mismo pero de forma numérica y continua, mes a mes, sobre toda la curva '
            'simulada, mostrando exactamente cuándo cambia la tendencia de crecimiento a decrecimiento '
            '(justo lo que el informe describe como "tendencia sostenida a la baja").\n\n'
            'CÓMO FUNCIONA ESTA VENTANA\n'
            'No tiene controles propios, usa los parámetros del panel principal. Cada gráfica está numerada '
            'en su título. La ➊ muestra dI/dt coloreada según si la epidemia crece o decrece. La ➋ superpone '
            'I(t) y su derivada. La ➌ compara la derivada numérica contra la analítica, para verificar la '
            'precisión del método. La ➍ es la tabla que resume las velocidades máximas.'
        )
        return titulo, formulas, explicacion

    def crear_ejes(self):
        gs = self.fig.add_gridspec(2, 2, top=0.92, bottom=0.10, hspace=0.62, wspace=0.40, left=0.085, right=0.925)
        ax1 = self.fig.add_subplot(gs[0, 0])
        ax2 = self.fig.add_subplot(gs[0, 1])
        ax2b = ax2.twinx()
        ax3 = self.fig.add_subplot(gs[1, 0])
        ax4 = self.fig.add_subplot(gs[1, 1])
        return dict(dIdt=ax1, superpuesta=ax2, superpuesta2=ax2b, error=ax3, tabla=ax4)

    def dibujar(self):
        t = np.arange(MESES)
        beta, gamma, N, I0 = self.estado.beta, self.estado.gamma, self.estado.N, self.estado.I0
        S4, I4, _ = rk4_sir(beta, gamma, N, I0, MESES)
        dIdt = derivacion_numerica(I4)
        dIdt_anal = 30 * (beta * S4 * I4 / N - gamma * I4)
        dp = int(np.argmax(I4))
        cruces = np.where((dIdt[:-1] > 0) & (dIdt[1:] <= 0))[0]
        cero = int(cruces[0]) + 1 if len(cruces) > 0 else dp

        ax = self.ejes['dIdt']; ax.cla()
        ax.fill_between(t, dIdt, 0, where=(dIdt > 0), interpolate=True, alpha=0.30, color=C['I'], label='Crece (dI/dt > 0)')
        ax.fill_between(t, dIdt, 0, where=(dIdt < 0), interpolate=True, alpha=0.30, color=C['R'], label='Decrece (dI/dt < 0)')
        ax.plot(t, dIdt, color=C['deriv'], lw=2.3, marker='o', ms=3.5, label='dI/dt (3 puntos)')
        ax.plot(t, dIdt_anal, color=C['ref'], lw=1.2, ls='--', alpha=0.8, label='dI/dt analítica')
        ax.axhline(0, color=C['ref'], lw=0.9, alpha=0.6)
        ax.axvline(cero, color=C['I'], lw=1.2, ls=':', alpha=0.9)
        ax.set_xlim(0, MESES - 1)
        dar_espacio(ax, 0.40)
        leyenda(ax, loc='upper right', ncol=2, fontsize=7.4)
        estilo_ax(ax, con_numero(1, f'Velocidad de contagio dI/dt  (pico en el mes {cero})'),
                  ylabel='Cambio de infectados por mes')

        ax = self.ejes['superpuesta']; ax.cla()
        ax2 = self.ejes['superpuesta2']; ax2.cla()
        ax.plot(t, I4, color=C['I'], lw=2.4, label='I(t) infectados')
        ax.axvline(cero, color=C['ref'], lw=1.0, ls=':', alpha=0.7)
        ax2.plot(t, dIdt, color=C['deriv'], lw=1.9, ls='--', label='dI/dt (eje derecho)')
        ax2.axhline(0, color=C['deriv'], lw=0.8, ls=':', alpha=0.45)
        ax.set_xlim(0, MESES - 1); ax.set_ylim(0, None)
        dar_espacio(ax, 0.34)
        lo, hi = ax2.get_ylim(); ax2.set_ylim(lo, lo + (hi - lo) / 0.66)
        estilo_ax(ax, con_numero(2, f'I(t) y dI/dt superpuestas'), ylabel='Personas infectadas')
        ax.yaxis.label.set_color(C['I'])
        eje_derecho(ax2, 'Velocidad dI/dt', C['deriv'])
        leyenda(ax, loc='upper right', fontsize=7.6, ejes_extra=(ax2,))

        ax = self.ejes['error']; ax.cla()
        err_d = np.abs(dIdt - dIdt_anal)
        ax.fill_between(t, err_d, alpha=0.25, color=C['simps'])
        ax.plot(t, err_d, color=C['simps'], lw=2.0, marker='o', ms=3.5, label='|numérica − analítica|')
        ax.set_xlim(0, MESES - 1); ax.set_ylim(bottom=0)
        dar_espacio(ax, 0.30)
        leyenda(ax, loc='upper right', fontsize=7.6)
        estilo_ax(ax, con_numero(3, f'Error vs derivada analítica  (máx = {np.max(err_d):,.2f})'),
                  ylabel='Error absoluto')

        rows = [
            ['Vel. máx. de contagio', f'{num_corto(np.max(dIdt))} pers/mes', f'mes {int(np.argmax(dIdt))}'],
            ['Vel. máx. de recuperación', f'{num_corto(np.min(dIdt))} pers/mes', f'mes {int(np.argmin(dIdt))}'],
            ['dI/dt = 0 (pico)', f'mes {cero}', 'máx. de infectados'],
            ['Infectados en el pico (RK4)', num_corto(np.max(I4)), f'mes {dp}'],
            ['S en el pico', num_corto(S4[cero]), 'S ≈ N/R0'],
            ['N/R0 (teórico)', num_corto(N / (beta / gamma)), 'referencia'],
            ['Error máx. vs analítica', num_corto(np.max(err_d), 4), 'ver gráfica 3'],
        ]
        tabla_ax(self.ejes['tabla'], rows, ['Magnitud', 'Valor', 'Nota'], con_numero(4, 'Análisis de dI/dt'),
                 alineacion=['l', 'c', 'c'])
        self.datos_resumen = [list(r) for r in rows]
        self._resumen = {'cero': cero, 'err_max': float(np.max(err_d)), 'R0': beta / gamma,
                         'vmax': float(np.max(dIdt)), 'vmin': float(np.min(dIdt))}

    def analisis(self):
        r = self._resumen
        if not r:
            return []
        crece = r['R0'] > 1
        return [
            dict(n='1', titulo='Velocidad de contagio dI/dt',
                 texto=(f"La zona roja (dI/dt > 0) es cuando el COVID-19 sigue creciendo en Quito y la verde "
                        f"(dI/dt < 0) cuando ya está bajando; "
                        + (f"ambas se separan en el mes {r['cero']}." if crece else
                           "como R0 es menor a 1, la velocidad es negativa desde el inicio y no hay fase de crecimiento.")),
                 conclusion=('El cruce por cero marca exactamente el pico de contagios.' if crece else
                             'No existe un cruce por cero: el pico coincide con el mes inicial (I0).')),
            dict(n='2', titulo='I(t) y dI/dt superpuestas',
                 texto=('Permite ver al mismo tiempo cuántos infectados hay (curva roja, eje izquierdo) y qué tan rápido '
                        'cambia ese número (curva morada, eje derecho).'),
                 conclusion='Cuando la curva morada llega a cero, la roja está en su punto más alto.' if crece else
                            'Mientras la curva morada permanece bajo cero, los infectados solo disminuyen.'),
            dict(n='3', titulo='Error frente a la derivada analítica',
                 texto=f"El error máximo es de {r['err_max']:,.4f} personas por mes.",
                 conclusion=('La fórmula de 3 puntos aproxima la velocidad real de contagio sin necesidad de conocer '
                             'la ecuación diferencial original; el error crece donde la curva tiene más curvatura.')),
            dict(n='4', titulo='Tabla de velocidades máximas',
                 texto=(f"La máxima velocidad de contagio es {r['vmax']:,.1f} personas/mes y la máxima de "
                        f"recuperación {r['vmin']:,.1f} personas/mes."),
                 conclusion='Confirma que el punto dI/dt = 0 coincide con el pico visto en la gráfica de Evolución de la Epidemia.'),
        ]
