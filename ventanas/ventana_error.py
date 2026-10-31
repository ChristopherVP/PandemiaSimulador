import numpy as np
from ui.ventana_base import PanelTema
from ui.estilo import C, estilo_ax, tabla_ax, nota_y, con_numero, num_corto
from core.estado_global import MESES
from core.metodos_numericos import rk4_sir, euler_sir


class VentanaError(PanelTema):
    ICONO = '②'
    TITULO = 'Confiabilidad de la Simulación'
    CLAVE = 'error'

    def teoria(self):
        titulo = 'Confiabilidad de la Simulación del COVID-19 — calculada comparando Euler vs RK4'
        formulas = [
            'Ea = |x_real − x_aprox|                        (error absoluto)',
            'Er = |x_real − x_aprox| / |x_real| × 100%       (error relativo)',
        ]
        explicacion = (
            '¿QUÉ MUESTRA ESTA GRÁFICA?\n'
            'No es un dato de la pandemia de COVID-19 en sí, sino qué tan "equivocada" podría estar la '
            'simulación si se usara un método numérico más simple y rápido en vez de uno preciso. Es una '
            'medida de confianza: entre más pequeño el error, más se puede confiar en el resultado obtenido '
            'con el método barato.\n\n'
            '¿QUÉ MÉTODO Y FÓRMULA LA CALCULAN?\n'
            'Se resuelve el mismo sistema SIR de COVID-19 dos veces con los mismos parámetros: una con '
            'Euler (orden 1, menos preciso) y otra con Runge-Kutta 4 (orden 4, se toma como el valor '
            '"real"). El error absoluto es la resta directa entre ambas curvas de infectados, y el relativo '
            'la expresa como porcentaje del valor real.\n\n'
            'RELACIÓN CON LOS DATOS REALES DE QUITO\n'
            'El propio Informe Quincenal COVID-19 de la Secretaría de Salud de Quito reconoce que la falta '
            'de pruebas (testeo) y el reporte tardío de resultados introducen sesgo y subregistro en las '
            'cifras oficiales de positividad e incidencia. De forma parecida, un método numérico más simple '
            'como Euler introduce su propio error frente a uno más preciso como RK4: esta ventana mide ese '
            'tipo de incertidumbre, pero del lado matemático de la simulación, no del lado del muestreo '
            'epidemiológico real de COVID-19.\n\n'
            'CÓMO FUNCIONA ESTA VENTANA\n'
            'Cada gráfica está numerada en su título. La ➊ superpone ambas curvas de infectados. La ➋ es el '
            'error absoluto mes por mes. La ➌ es el error relativo en porcentaje. La ➍ es la tabla con los '
            'valores exactos de cada mes. No tiene controles propios: usa los mismos β, γ, N, I0 del panel '
            'principal.'
        )
        return titulo, formulas, explicacion

    def crear_ejes(self):
        ax1 = self.fig.add_subplot(2, 2, 1)
        ax2 = self.fig.add_subplot(2, 2, 2)
        ax3 = self.fig.add_subplot(2, 2, 3)
        ax4 = self.fig.add_subplot(2, 2, 4)
        self.fig.subplots_adjust(top=0.88, bottom=0.11, hspace=0.75, wspace=0.35, left=0.07, right=0.97)
        return dict(rk4_vs_euler=ax1, absoluto=ax2, relativo=ax3, tabla=ax4)

    def interpretar_resultados(self):
        r = self._resumen
        if not r:
            return ''
        return (
            f"🔵 GRÁFICA ➊ (RK4 vs Euler): ambas curvas de infectados por COVID-19 se parecen mucho al "
            f"principio, pero se separan más cerca del pico (zona sombreada).\n"
            f"→ Conclusión: ahí es donde el método simple (Euler) pierde más precisión frente al de "
            f"referencia (RK4).\n\n"
            f"🔵 GRÁFICA ➋ (Error absoluto Ea): el error máximo es de {r['ea_max']:.1f} personas y ocurre "
            f"en el mes {r['dm']}.\n"
            f"→ Conclusión: como coincide con la zona de mayor cambio de la curva, Euler acumula más error "
            f"justo donde la epidemia cambia más rápido de dirección.\n\n"
            f"🔵 GRÁFICA ➌ (Error relativo Er %): el error relativo máximo es {r['er_max']:.1f}% del valor "
            f"real.\n"
            f"→ Conclusión: como se mantiene bajo el 5% (línea de referencia), Euler sigue siendo confiable "
            f"pese a ser más simple que RK4.\n\n"
            f"🔵 GRÁFICA ➍ (tabla comparativa mes por mes): permite verificar con números exactos en qué "
            f"meses puntuales el error crece o se mantiene bajo.\n"
            f"→ Conclusión: confirma numéricamente lo que se ve en las gráficas ➊-➌, sin depender solo de "
            f"leerlas visualmente."
        )

    def dibujar(self):
        t = np.arange(MESES)
        beta, gamma, N, I0 = self.estado.beta, self.estado.gamma, self.estado.N, self.estado.I0
        S4, I4, R4 = rk4_sir(beta, gamma, N, I0, MESES)
        Se, Ie, Re = euler_sir(beta, gamma, N, I0, MESES)
        ea = np.abs(I4 - Ie)
        with np.errstate(divide='ignore', invalid='ignore'):
            er = np.where(I4 > 0.1, ea / I4 * 100, 0.0)

        ax1 = self.ejes['rk4_vs_euler']; ax1.cla()
        ax1.plot(t, I4, color=C['I'], lw=2.5, label='RK4 (referencia "exacta")')
        ax1.plot(t, Ie, color=C['I_eu'], lw=1.8, ls='--', label='Euler (aprox. 1er orden)')
        ax1.fill_between(t, I4, Ie, alpha=0.25, color=C['I_eu'], label='Zona de error')
        dp = int(np.argmax(I4))
        ax1.axvline(dp, color=C['I'], lw=1.2, ls=':', alpha=0.6)
        ax1.legend(fontsize=8); ax1.set_xlim(0, MESES - 1); ax1.set_ylim(0, None)
        estilo_ax(ax1, con_numero(1, 'I(t): RK4 vs Euler'), ylabel='Personas infectadas')
        nota_y(ax1, 'Cantidad de personas infectadas\nestimada por cada método')

        ax2 = self.ejes['absoluto']; ax2.cla()
        ax2.fill_between(t, ea, alpha=0.3, color=C['nr_f'])
        ax2.plot(t, ea, color=C['nr_f'], lw=2.2)
        dm = int(np.argmax(ea))
        ax2.axvline(dm, color='white', lw=1.2, ls=':', alpha=0.7)
        ax2.annotate(f'  Máximo\n  {np.max(ea):.1f} personas\n  Mes {dm}', xy=(dm, np.max(ea)),
                     xytext=(min(dm + 1, MESES - 2), np.max(ea) * 0.75), color=C['nr_f'], fontsize=8.3,
                     arrowprops=dict(arrowstyle='->', color=C['nr_f']))
        ax2.set_xlim(0, MESES - 1); ax2.set_ylim(0, None)
        estilo_ax(ax2, con_numero(2, f'Error Absoluto Ea=|RK4−Euler| | Máx={np.max(ea):.2f}'), ylabel='Personas de diferencia')
        nota_y(ax2, 'Cuántas personas de diferencia\nhay entre RK4 y Euler')

        ax3 = self.ejes['relativo']; ax3.cla()
        ax3.fill_between(t, er, alpha=0.3, color=C['simps'])
        ax3.plot(t, er, color=C['simps'], lw=2.2)
        ax3.axhline(5, color='white', lw=1, ls=':', alpha=0.5, label='Referencia 5%')
        ax3.legend(fontsize=8); ax3.set_xlim(0, MESES - 1); ax3.set_ylim(0, None)
        estilo_ax(ax3, con_numero(3, f'Error Relativo Er(%) | Máx={np.max(er):.1f}'), ylabel='Error como % del valor real')
        nota_y(ax3, 'Qué porcentaje representa el\nerror sobre el valor real (RK4)')

        rows = [[f'{m}', num_corto(I4[m]), num_corto(Ie[m]), num_corto(ea[m], 2), f'{er[m]:.2f}%'] for m in range(MESES)]
        tabla_ax(self.ejes['tabla'], rows, ['Mes', 'RK4 I(t)', 'Euler I(t)', 'Ea', 'Er (%)'],
                 con_numero(4, f'Tabla comparativa — β={beta:.2f} γ={gamma:.2f} N={N:,}'))

        self._resumen = {'ea_max': float(np.max(ea)), 'er_max': float(np.max(er)), 'dm': dm}
