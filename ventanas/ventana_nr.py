import numpy as np
import matplotlib.gridspec as gridspec
from ui.ventana_base import PanelTema
from ui.estilo import (C, estilo_ax, tabla_ax, con_numero, num_corto, dar_espacio, leyenda, eje_derecho)
from ui.componentes import crear_slider
from core.estado_global import MESES
from core.metodos_numericos import rk4_sir, newton_raphson_beta

TOLERANCIA = 1.0


class VentanaNewtonRaphson(PanelTema):
    ICONO = '⑥'
    TITULO = 'Calibración del Contagio Real'
    SUBTITULO = 'Ajuste del parámetro β con el método de Newton-Raphson'
    CLAVE = 'nr'
    DESCRIPCION = ('Muestra cómo se ajusta β (contagiosidad del COVID-19) para que el modelo coincida con un pico '
                   'de contagios observado en la vigilancia epidemiológica real, igual que hace el MSP para '
                   'calibrar sus propios modelos. Se calcula con el método de Newton-Raphson.')

    def teoria(self):
        titulo = 'Calibración del Contagio Real de COVID-19 — calculada con Newton-Raphson'
        formulas = [
            'f(β) = pico_simulado(β) − I_observado             (qué tan lejos está β)',
            "f'(β) ≈ [f(β+δ) − f(β−δ)] / 2δ                     (pendiente de f)",
            "β_(n+1) = β_n − f(β_n) / f'(β_n)                    (nueva estimación de β)",
        ]
        explicacion = (
            '¿QUÉ MUESTRA ESTA GRÁFICA?\n'
            'Cómo se ajusta el parámetro β (qué tan contagioso es el COVID-19) para que el modelo coincida '
            'con un dato real observado, por ejemplo, un pico de contagios reportado oficialmente en una '
            'ola epidemiológica real. Es un ejercicio de calibración: partir de datos reales y encontrar '
            'qué β los explica.\n\n'
            '¿QUÉ MÉTODO Y FÓRMULA LA CALCULAN?\n'
            'Newton-Raphson encuentra la raíz de f(β) por iteración: en cada paso simula la epidemia '
            'completa con RK4 usando el β actual, compara el pico resultante contra el observado, estima la '
            'pendiente de ese error con una derivada numérica, y corrige β para acercarse a f(β)=0.\n\n'
            'RELACIÓN CON LOS DATOS REALES DE QUITO\n'
            'Así calibran los epidemiólogos del MSP y la Secretaría de Salud sus propios modelos de '
            'COVID-19: parten de un dato real observado —por ejemplo, un pico de contagios reportado por la '
            'vigilancia epidemiológica de la Coordinación Zonal 9 (CZS9)— y ajustan matemáticamente los '
            'parámetros del modelo (como β) hasta que la simulación reproduzca ese dato real. '
            'Newton-Raphson automatiza exactamente ese proceso de calibración.\n\n'
            'CÓMO FUNCIONA ESTA VENTANA\n'
            'El slider "I_obs pico (observado)" simula un dato real: cuántos infectados hubo en el pico. El '
            'slider "β0 estimación inicial" es desde qué valor arranca la búsqueda. La gráfica ➊ compara la '
            'curva original contra la calibrada. La ➋ muestra la convergencia de |f(β)| hacia cero. La ➌ es '
            'la curva f(β) con la raíz marcada. La ➍ es la tabla iteración por iteración.'
        )
        return titulo, formulas, explicacion

    def crear_ejes(self):
        gs = gridspec.GridSpec(2, 3, figure=self.fig, top=0.92, bottom=0.09,
                               hspace=0.62, wspace=0.60, left=0.075, right=0.955)
        ax_main = self.fig.add_subplot(gs[0, :])
        ax_conv = self.fig.add_subplot(gs[1, 0])
        ax_convb = ax_conv.twinx()
        ax_f = self.fig.add_subplot(gs[1, 1])
        ax_tab = self.fig.add_subplot(gs[1, 2])
        return dict(main=ax_main, conv=ax_conv, convb=ax_convb, f=ax_f, tab=ax_tab)

    def construir_controles(self):
        e = self.estado
        _, I4, _ = rk4_sir(e.beta, e.gamma, e.N, e.I0, MESES)
        pico_ref = float(np.max(I4))
        # Si la epidemia esta controlada (R0<1) el pico siempre es I0 y la derivada de f es 0: se propone
        # un pico observado mayor y un beta0 por encima del umbral de contagio para que el metodo pueda iterar.
        if e.R0 <= 1:
            self.controles['I_obs'] = float(round(pico_ref * 3 / 5) * 5)
            self.controles['beta0'] = round(max(0.05, e.gamma * 1.5) / 0.05) * 0.05
        else:
            self.controles['I_obs'] = float(round(pico_ref * 0.70 / 5) * 5)
            self.controles['beta0'] = round(max(0.05, e.beta * 0.5) / 0.05) * 0.05

        def on_iobs(v):
            self.controles['I_obs'] = float(v)
            self.actualizar()

        def on_b0(v):
            self.controles['beta0'] = float(v)
            self.actualizar()

        crear_slider(self.frame_controles, 'I_obs pico (observado)', 10, max(20, int(pico_ref * 4)),
                     self.controles['I_obs'], 5, on_iobs, C['nr_f'],
                     descripcion='Dato real simulado: cuántos infectados de COVID-19 hubo en el pico de una ola')
        crear_slider(self.frame_controles, 'β0 estimación inicial', 0.05, 1.5,
                     self.controles['beta0'], 0.05, on_b0, C['nr_b'],
                     descripcion='Valor inicial desde el que arranca la búsqueda de Newton-Raphson')

    def dibujar(self):
        t = np.arange(MESES)
        beta, gamma, N, I0 = self.estado.beta, self.estado.gamma, self.estado.N, self.estado.I0
        _, I4, _ = rk4_sir(beta, gamma, N, I0, MESES)
        pico_ref = float(np.max(I4))

        I_obs = float(self.controles.get('I_obs', pico_ref * 3 if beta <= gamma else pico_ref * 0.7))
        b0 = float(self.controles.get('beta0', max(0.05, gamma * 1.5) if beta <= gamma else beta * 0.5))
        beta_s, hist = newton_raphson_beta(I_obs, gamma, N, I0, b0, meses=MESES, tol=TOLERANCIA)
        _, I_cal, _ = rk4_sir(beta_s, gamma, N, I0, MESES)
        pico_cal = float(np.max(I_cal))
        R0_s = beta_s / gamma
        convergio = abs(pico_cal - I_obs) < TOLERANCIA
        iters = [h['iter'] for h in hist]
        fb_abs = [max(h['ea'], 1e-3) for h in hist]
        betas_h = [h['beta'] for h in hist]

        # ---------------------------------------------------------------- 1
        ax = self.ejes['main']; ax.cla()
        ax.plot(t, I4, color=C['I'], lw=2.3, marker='o', ms=3.5, label=f'I(t) original  (β = {beta:.3f},  R0 = {beta / gamma:.2f})')
        ax.plot(t, I_cal, color=C['nodo'], lw=2.4, ls='--', marker='s', ms=3.5,
                label=f'I(t) calibrada  (β* = {beta_s:.4f},  R0* = {R0_s:.2f})')
        ax.axhline(I_obs, color=C['simps'], lw=1.6, ls=':', label=f'Pico observado = {I_obs:,.0f}')
        ax.set_xlim(0, MESES - 1); ax.set_ylim(bottom=0)
        dar_espacio(ax, 0.20)
        leyenda(ax, loc='upper center', ncol=3, fontsize=8)
        estilo_ax(ax, con_numero(1, 'Curva original frente a curva calibrada con β*'), ylabel='Personas infectadas')

        # ---------------------------------------------------------------- 2
        ax = self.ejes['conv']; ax.cla()
        axb = self.ejes['convb']; axb.cla()
        ax.semilogy(iters, fb_abs, 'o-', color=C['nr_f'], lw=2.2, ms=6, label='|f(β)|')
        ax.axhline(TOLERANCIA, color=C['ref'], lw=1.1, ls=':', alpha=0.8, label='Tolerancia')
        axb.plot(iters, betas_h, 's--', color=C['nr_b'], lw=1.8, ms=5, alpha=0.9, label='β')
        if len(iters) == 1:
            ax.set_xlim(-0.6, 0.6)
        ax.xaxis.set_major_locator(__import__('matplotlib.ticker', fromlist=['MaxNLocator']).MaxNLocator(integer=True))
        dar_espacio(ax, 0.40, log=True)
        lo, hi = axb.get_ylim(); pad = max((hi - lo), 1e-3)
        axb.set_ylim(lo - 0.05 * pad, lo + (hi - lo) / 0.60 + 0.05 * pad)
        estilo_ax(ax, con_numero(2, 'Convergencia de Newton-Raphson'), xlabel='Iteración', ylabel='|f(β)|  (escala log)')
        ax.yaxis.label.set_color(C['nr_f'])
        eje_derecho(axb, 'Valor de β', C['nr_b'])
        leyenda(ax, loc='upper right', fontsize=7.4, ejes_extra=(axb,))

        # ---------------------------------------------------------------- 3
        ax = self.ejes['f']; ax.cla()
        betas_scan = np.linspace(0.01, min(1.5, gamma * 3.5), 60)
        fvals = []
        for bv in betas_scan:
            _, Iv, _ = rk4_sir(bv, gamma, N, I0, MESES)
            fvals.append(float(np.max(Iv)) - I_obs)
        ax.plot(betas_scan, fvals, color=C['nr_b'], lw=2.2, label='f(β)')
        ax.axhline(0, color=C['ref'], lw=1.0, ls='--', alpha=0.7)
        ax.axvline(beta_s, color=C['nodo'], lw=1.5, ls=':', label=f'β* = {beta_s:.4f}')
        ax.plot(beta_s, 0, 'o', color=C['nodo'], ms=8, zorder=6, markeredgecolor=C['panel'])
        ax.plot([h_['beta'] for h_ in hist], [h_['fb'] for h_ in hist], 's', color=C['nr_f'], ms=5, zorder=5,
                label='Iteraciones')
        dar_espacio(ax, 0.40)
        leyenda(ax, loc='upper left', fontsize=7.4)
        estilo_ax(ax, con_numero(3, 'Curva f(β) y raíz encontrada'), xlabel='β (contagiosidad)',
                  ylabel='f(β)')

        # ---------------------------------------------------------------- 4
        rows = []
        for i, h_ in enumerate(hist):
            prev = betas_h[i - 1] if i > 0 else b0
            paso = abs(h_['beta'] - prev)
            rows.append([f"{h_['iter']}", f"{h_['beta']:.5f}",
                         f"{'+' if h_['fb'] >= 0 else '−'}{num_corto(abs(h_['fb']))}",
                         num_corto(h_['ea']), f'{paso:.5f}' if i > 0 else '—'])
        tabla_ax(self.ejes['tab'], rows, ['Iter', 'β_n', 'f(β_n)', '|f(β_n)|', '|Δβ|'],
                 con_numero(4, 'Tabla de iteraciones'))
        self.datos_resumen = [
            ['Pico observado (I_obs)', f'{I_obs:,.0f} personas'],
            ['β inicial (β0)', f'{b0:.4f}'],
            ['β calibrado (β*)', f'{beta_s:.5f}'],
            ['R0* = β*/γ', f'{R0_s:.4f}'],
            ['Pico simulado con β*', f'{pico_cal:,.1f} personas'],
            ['Error final |f(β*)|', f'{abs(pico_cal - I_obs):,.3f}'],
            ['Iteraciones realizadas', f'{len(hist)}'],
            ['Resultado', 'CONVERGIÓ (|f| < 1)' if convergio else 'NO CONVERGIÓ'],
        ]
        self._resumen = {'b0': b0, 'beta_s': beta_s, 'R0_s': R0_s, 'n_iter': len(hist), 'I_obs': I_obs,
                         'convergio': convergio, 'I0': I0, 'pico_cal': pico_cal}

    def analisis(self):
        r = self._resumen
        if not r:
            return []
        ok = r['convergio']
        if ok:
            c1 = 'Así se recalibra el modelo cuando se tiene un dato real de un pico de contagios.'
            c2 = (f"El método converge rápido ({r['n_iter']} iteraciones) porque parte de una buena estimación inicial "
                  f"y la función es suave.")
        else:
            motivo = ('el pico observado es menor que I0: como la curva parte de I0, ningún β puede producir un pico '
                      'menor') if r['I_obs'] < r['I0'] else \
                     ('la pendiente de f(β) es casi cero en ese punto de partida (mientras R0 < 1 el pico siempre es I0), '
                      'así que el método no tiene hacia dónde corregir')
            c1 = f'No se alcanzó el pico observado: {motivo}. Prueba con un β0 mayor o con otro pico observado.'
            c2 = 'El método se detuvo sin llegar a la tolerancia; la causa está descrita en la gráfica 1.'
        return [
            dict(n='1', titulo='Curva original frente a curva calibrada',
                 texto=(f"Partiendo de β0 = {r['b0']:.3f}, Newton-Raphson llegó a β* = {r['beta_s']:.4f} "
                        f"(R0* = {r['R0_s']:.2f}); con él el pico simulado de COVID-19 es {r['pico_cal']:,.1f} "
                        f"frente al dato observado de {r['I_obs']:,.0f} infectados (línea horizontal)."),
                 conclusion=c1),
            dict(n='2', titulo='Convergencia de |f(β)| y de β',
                 texto=f"|f(β)| se evaluó en {r['n_iter']} iteración(es) y se compara con la tolerancia de 1 persona.",
                 conclusion=c2),
            dict(n='3', titulo='Curva f(β) y su raíz',
                 texto=('El punto verde marca dónde f(β) = 0, es decir, el valor de β que haría que el pico simulado '
                        'sea igual al observado; los cuadrados rojos son los β visitados por el algoritmo.'),
                 conclusion='Si los cuadrados se acercan al punto verde, el método está convergiendo hacia la raíz.'),
            dict(n='4', titulo='Tabla iteración por iteración',
                 texto='Permite verificar a mano cada paso del método: valor de β, f(β), |f(β)| y tamaño del paso |Δβ|.',
                 conclusion='|Δβ| se hace cada vez más pequeño conforme el algoritmo se acerca a la raíz, confirmando que converge.'),
        ]
