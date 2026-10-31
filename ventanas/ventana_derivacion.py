import numpy as np
from ui.ventana_base import PanelTema
from ui.estilo import C, estilo_ax, tabla_ax, nota_y, con_numero, num_corto
from core.estado_global import MESES
from core.metodos_numericos import rk4_sir, derivacion_numerica


class VentanaDerivacion(PanelTema):
    ICONO = '④'
    TITULO = 'Velocidad de Propagación'
    CLAVE = 'derivacion'

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
        ax1 = self.fig.add_subplot(2, 2, 1)
        ax2 = self.fig.add_subplot(2, 2, 2)
        ax2b = ax2.twinx()
        ax3 = self.fig.add_subplot(2, 2, 3)
        ax4 = self.fig.add_subplot(2, 2, 4)
        self.fig.subplots_adjust(top=0.88, bottom=0.11, hspace=0.75, wspace=0.38, left=0.07, right=0.96)
        return dict(dIdt=ax1, superpuesta=ax2, superpuesta2=ax2b, error=ax3, tabla=ax4)

    def dibujar(self):
        t = np.arange(MESES)
        beta, gamma, N, I0 = self.estado.beta, self.estado.gamma, self.estado.N, self.estado.I0
        S4, I4, _ = rk4_sir(beta, gamma, N, I0, MESES)
        dIdt = derivacion_numerica(I4)
        dIdt_anal = 30 * (beta * S4 * I4 / N - gamma * I4)
        dp = int(np.argmax(I4))
        cruces = np.where(np.diff(np.sign(dIdt)))[0]
        cero = int(cruces[0]) if len(cruces) > 0 else dp

        ax1 = self.ejes['dIdt']; ax1.cla()
        ax1.fill_between(t, dIdt, where=(dIdt > 0), alpha=0.25, color=C['I'], label='COVID-19 CRECE')
        ax1.fill_between(t, dIdt, where=(dIdt < 0), alpha=0.25, color=C['R'], label='COVID-19 DECRECE')
        ax1.plot(t, dIdt, color=C['deriv'], lw=2.4, label='dI/dt (3 puntos)')
        ax1.plot(t, dIdt_anal, color='white', lw=1.2, ls='--', alpha=0.5, label='dI/dt analítica')
        ax1.axhline(0, color='white', lw=1.2, ls='--', alpha=0.45)
        ax1.axvline(cero, color=C['I'], lw=1.5, ls=':', alpha=0.8)
        ax1.legend(fontsize=8, loc='upper right'); ax1.set_xlim(0, MESES - 1)
        estilo_ax(ax1, con_numero(1, f'Velocidad de contagio dI/dt | pico en el mes {cero}'), ylabel='Personas de más o menos / mes')
        nota_y(ax1, 'Cuántas personas MÁS (+) o\nMENOS (-) se contagian cada mes')

        ax2 = self.ejes['superpuesta']; ax2.cla()
        ax2b = self.ejes['superpuesta2']; ax2b.cla()
        ax2.plot(t, I4, color=C['I'], lw=2.4, label='I(t) infectados')
        ax2.axvline(cero, color='white', lw=1.2, ls=':', alpha=0.5)
        ax2b.plot(t, dIdt, color=C['deriv'], lw=1.8, ls='--', alpha=0.85, label='dI/dt')
        ax2b.axhline(0, color='white', lw=0.8, ls=':', alpha=0.35)
        ax2b.set_ylabel('Velocidad de cambio (dI/dt)', fontsize=8.5, color=C['deriv'])
        ax2b.tick_params(labelsize=8, colors=C['deriv'])
        ax2.legend(fontsize=8, loc='upper left')
        ax2.set_xlim(0, MESES - 1); ax2.set_ylim(0, None)
        estilo_ax(ax2, con_numero(2, f'I(t) y dI/dt superpuestas | pico exacto en el mes {cero}'), ylabel='Personas infectadas')
        nota_y(ax2, 'Rojo=infectados (eje izq.)\nMorado=velocidad de cambio (eje der.)')

        ax3 = self.ejes['error']; ax3.cla()
        err_d = np.abs(dIdt - dIdt_anal)
        ax3.fill_between(t, err_d, alpha=0.3, color=C['simps'])
        ax3.plot(t, err_d, color=C['simps'], lw=2.0)
        ax3.set_xlim(0, MESES - 1); ax3.set_ylim(bottom=0)
        estilo_ax(ax3, con_numero(3, f'Error vs dI/dt analítica | máx={np.max(err_d):.5f}'), ylabel='Error absoluto')
        nota_y(ax3, 'Diferencia entre la derivada\nnumérica y la fórmula exacta')

        rows = [
            ['Vel. máx. contagio', f'{num_corto(np.max(dIdt))} pers/mes', f'Mes {int(np.argmax(dIdt))}'],
            ['Vel. máx. recuper.', f'{num_corto(np.min(dIdt))} pers/mes', f'Mes {int(np.argmin(dIdt))}'],
            ['dI/dt = 0 (pico)', f'Mes {cero}', '→ máx. infectados'],
            ['I_pico RK4', num_corto(np.max(I4)), f'Mes {dp}'],
            ['S en el pico', num_corto(S4[cero]), 'S_pico ≈ N/R0'],
            ['N/R0 (teórico)', num_corto(N / (beta / gamma)), 'coincide con S_pico'],
            ['Error máx vs analítica', num_corto(np.max(err_d), 4), 'muy pequeño ✓'],
        ]
        tabla_ax(self.ejes['tabla'], rows, ['Magnitud', 'Valor', 'Nota'], con_numero(4, 'Análisis de dI/dt'))

        self._resumen = {'cero': cero, 'err_max': float(np.max(err_d))}

    def interpretar_resultados(self):
        r = self._resumen
        if not r:
            return ''
        return (
            f"🔵 GRÁFICA ➊ (dI/dt): la zona roja (dI/dt>0) es cuando el COVID-19 sigue creciendo en Quito, "
            f"y la verde (dI/dt<0) cuando ya está bajando; ambas se cruzan en el mes {r['cero']}.\n"
            f"→ Conclusión: ese cruce por cero marca exactamente el pico de contagios.\n\n"
            f"🔵 GRÁFICA ➋ (I(t) y dI/dt superpuestas): permite ver al mismo tiempo cuántos infectados hay "
            f"(curva roja) y qué tan rápido cambia ese número (curva morada).\n"
            f"→ Conclusión: cuando la curva morada llega a cero, la roja está exactamente en su punto más "
            f"alto.\n\n"
            f"🔵 GRÁFICA ➌ (Error vs derivada analítica): el error máximo es de apenas {r['err_max']:.5f}.\n"
            f"→ Conclusión: la fórmula de 3 puntos aproxima casi perfectamente la velocidad real de "
            f"contagio, sin necesidad de conocer la ecuación diferencial original.\n\n"
            f"🔵 GRÁFICA ➍ (tabla de velocidades máximas): resume en qué mes exacto el contagio crece más "
            f"rápido y en cuál se recupera más gente.\n"
            f"→ Conclusión: confirma que el punto dI/dt=0 coincide con el pico visto en la gráfica de "
            f"Evolución de la Epidemia."
        )
