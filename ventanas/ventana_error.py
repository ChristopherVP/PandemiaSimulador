import numpy as np
from ui.ventana_base import PanelTema
from ui.estilo import C, estilo_ax, tabla_ax, con_numero, num_corto, dar_espacio, leyenda, anotar
from core.estado_global import MESES
from core.metodos_numericos import rk4_sir, euler_sir


class VentanaError(PanelTema):
    ICONO = '②'
    TITULO = 'Confiabilidad de la Simulación'
    SUBTITULO = 'Error numérico: comparación entre el método de Euler y Runge-Kutta 4'
    CLAVE = 'error'
    DESCRIPCION = ('Muestra qué tan confiable es la simulación del COVID-19 al comparar un método numérico '
                   'rápido (Euler) contra uno preciso (RK4), algo parecido a los sesgos por falta de pruebas y '
                   'subregistro que reconoce el propio informe de Quito. Se calcula con las fórmulas de error '
                   'absoluto y relativo.')

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
        gs = self.fig.add_gridspec(2, 2, top=0.92, bottom=0.10, hspace=0.62, wspace=0.28, left=0.08, right=0.97)
        return dict(rk4_vs_euler=self.fig.add_subplot(gs[0, 0]), absoluto=self.fig.add_subplot(gs[0, 1]),
                    relativo=self.fig.add_subplot(gs[1, 0]), tabla=self.fig.add_subplot(gs[1, 1]))

    def analisis(self):
        r = self._resumen
        if not r:
            return []
        bajo = r['er_max'] < 5
        return [
            dict(n='1', titulo='Infectados I(t): RK4 frente a Euler',
                 texto=('Ambas curvas de infectados por COVID-19 se parecen mucho al principio, pero se separan '
                        'más cerca del pico (zona sombreada).'),
                 conclusion='Ahí es donde el método simple (Euler) pierde más precisión frente al de referencia (RK4).'),
            dict(n='2', titulo='Error absoluto Ea',
                 texto=f"El error máximo es de {r['ea_max']:.1f} personas y ocurre en el mes {r['dm']}.",
                 conclusion=('Coincide con la zona de mayor cambio de la curva: Euler acumula más error justo '
                             'donde la epidemia cambia más rápido de dirección.')),
            dict(n='3', titulo='Error relativo Er (%)',
                 texto=f"El error relativo máximo es {r['er_max']:.1f}% del valor real.",
                 conclusion=('Se mantiene bajo el 5% (línea de referencia), por lo que Euler sigue siendo confiable '
                             'pese a ser más simple que RK4.') if bajo else
                            ('Supera el 5% de referencia en algún mes: para estos parámetros conviene usar RK4 o '
                             'reducir el paso de Euler.')),
            dict(n='4', titulo='Tabla comparativa mes por mes',
                 texto='Permite verificar con números exactos en qué meses puntuales el error crece o se mantiene bajo.',
                 conclusion='Confirma numéricamente lo que se ve en las gráficas 1 a 3, sin depender solo de leerlas.'),
        ]

    def dibujar(self):
        t = np.arange(MESES)
        beta, gamma, N, I0 = self.estado.beta, self.estado.gamma, self.estado.N, self.estado.I0
        S4, I4, R4 = rk4_sir(beta, gamma, N, I0, MESES)
        Se, Ie, Re = euler_sir(beta, gamma, N, I0, MESES)
        ea = np.abs(I4 - Ie)
        with np.errstate(divide='ignore', invalid='ignore'):
            er = np.where(I4 > 0.1, ea / I4 * 100, 0.0)
        dm = int(np.argmax(ea))

        ax = self.ejes['rk4_vs_euler']; ax.cla()
        ax.plot(t, I4, color=C['I'], lw=2.4, label='RK4 (referencia)')
        ax.plot(t, Ie, color=C['I_eu'], lw=1.7, ls='--', label='Euler (1er orden)')
        ax.fill_between(t, I4, Ie, alpha=0.25, color=C['I_eu'], label='Zona de error')
        ax.set_xlim(0, MESES - 1); ax.set_ylim(0, None)
        dar_espacio(ax, 0.40)
        leyenda(ax, loc='upper right', fontsize=7.8)
        estilo_ax(ax, con_numero(1, 'Infectados I(t): RK4 vs Euler'), ylabel='Personas infectadas')

        ax = self.ejes['absoluto']; ax.cla()
        ax.fill_between(t, ea, alpha=0.25, color=C['nr_f'])
        ax.plot(t, ea, color=C['nr_f'], lw=2.2, marker='o', ms=3.5)
        ax.set_xlim(0, MESES - 1); ax.set_ylim(0, max(float(np.max(ea)), 1e-9) * 1.0)
        dar_espacio(ax, 0.38)
        if np.max(ea) > 0:
            anotar(ax, dm, float(np.max(ea)), f'Máximo: {np.max(ea):,.1f} pers. (mes {dm})', C['nr_f'], MESES - 1)
        estilo_ax(ax, con_numero(2, 'Error absoluto  Ea = |RK4 − Euler|'), ylabel='Diferencia (personas)')

        ax = self.ejes['relativo']; ax.cla()
        ax.fill_between(t, er, alpha=0.25, color=C['simps'])
        ax.plot(t, er, color=C['simps'], lw=2.2, marker='o', ms=3.5, label='Error relativo Er')
        ax.axhline(5, color=C['ref'], lw=1.1, ls='--', alpha=0.8, label='Referencia 5 %')
        ax.set_xlim(0, MESES - 1); ax.set_ylim(0, max(float(np.max(er)) * 1.0, 6.0))
        dar_espacio(ax, 0.30)
        leyenda(ax, loc='upper right', fontsize=7.8)
        estilo_ax(ax, con_numero(3, 'Error relativo  Er (%)'), ylabel='Error (% del valor real)')

        rows = [[f'{m}', num_corto(I4[m]), num_corto(Ie[m]), num_corto(ea[m], 2), f'{er[m]:.2f}'] for m in range(MESES)]
        tabla_ax(self.ejes['tabla'], rows, ['Mes', 'RK4 I(t)', 'Euler I(t)', 'Ea', 'Er (%)'],
                 con_numero(4, 'Tabla comparativa mes por mes'))
        self.datos_resumen = [
            ['Error absoluto máximo', f'{np.max(ea):.2f} personas (mes {dm})'],
            ['Error absoluto promedio', f'{np.mean(ea):.2f} personas'],
            ['Error relativo máximo', f'{np.max(er):.2f} %'],
            ['Error relativo promedio', f'{np.mean(er):.2f} %'],
            ['Referencia de confiabilidad', 'Er < 5 %  —  ' + ('CUMPLE' if np.max(er) < 5 else 'NO CUMPLE')],
        ]
        self._resumen = {'ea_max': float(np.max(ea)), 'er_max': float(np.max(er)), 'dm': dm}
