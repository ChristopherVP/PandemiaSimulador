import numpy as np
import matplotlib.gridspec as gridspec
from ui.ventana_base import PanelTema
from ui.estilo import C, estilo_ax, tabla_ax, nota_y, con_numero, leyenda_combinada, num_corto
from ui.componentes import crear_slider
from core.estado_global import MESES
from core.metodos_numericos import rk4_sir, newton_raphson_beta


class VentanaNewtonRaphson(PanelTema):
    ICONO = '⑥'
    TITULO = 'Calibración del Contagio Real'
    CLAVE = 'nr'

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
        gs = gridspec.GridSpec(2, 3, figure=self.fig, top=0.88, bottom=0.10,
                                hspace=0.70, wspace=0.35, left=0.06, right=0.97)
        ax_main = self.fig.add_subplot(gs[0, :])
        ax_conv = self.fig.add_subplot(gs[1, 0])
        ax_convb = ax_conv.twinx()
        ax_f = self.fig.add_subplot(gs[1, 1])
        ax_tab = self.fig.add_subplot(gs[1, 2])
        return dict(main=ax_main, conv=ax_conv, convb=ax_convb, f=ax_f, tab=ax_tab)

    def construir_controles(self):
        _, I4, _ = rk4_sir(self.estado.beta, self.estado.gamma, self.estado.N, self.estado.I0, MESES)
        pico_ref = float(np.max(I4))
        self.controles['I_obs'] = pico_ref * 0.70
        self.controles['beta0'] = self.estado.beta * 0.5

        def on_iobs(v):
            self.controles['I_obs'] = float(v)
            self.actualizar()

        def on_b0(v):
            self.controles['beta0'] = float(v)
            self.actualizar()

        crear_slider(self.frame_controles, 'I_obs pico (observado)', 10, max(20, int(pico_ref * 1.8)),
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

        I_obs = float(self.controles.get('I_obs', pico_ref * 0.70))
        b0 = float(self.controles.get('beta0', beta * 0.5))
        beta_s, hist = newton_raphson_beta(I_obs, gamma, N, I0, b0, meses=MESES)
        _, I_cal, _ = rk4_sir(beta_s, gamma, N, I0, MESES)
        pico_cal = float(np.max(I_cal))
        R0_s = beta_s / gamma
        iters = [h['iter'] for h in hist]
        fb_abs = [h['ea'] for h in hist]
        betas_h = [h['beta'] for h in hist]

        ax_main = self.ejes['main']; ax_main.cla()
        ax_main.plot(t, I4, color=C['I'], lw=2.2, label=f'I(t) original (β={beta:.3f} R0={beta / gamma:.2f})')
        ax_main.plot(t, I_cal, color=C['nodo'], lw=2.4, ls='--', label=f'I(t) calibrada (β*={beta_s:.4f} R0*={R0_s:.2f})')
        ax_main.axhline(I_obs, color=C['simps'], lw=1.8, ls=':', label=f'I_observado={I_obs:.0f}')
        ax_main.legend(fontsize=8, loc='upper right')
        ax_main.set_xlim(0, MESES - 1); ax_main.set_ylim(bottom=0)
        estilo_ax(ax_main,
                  con_numero(1, f'Newton-Raphson: β0={b0:.3f}→β*={beta_s:.5f} | error={abs(pico_cal - I_obs):.2f} ({len(hist)} iter)'),
                  ylabel='Personas infectadas')
        nota_y(ax_main, 'Personas infectadas: curva original\nvs curva ya calibrada con β*')

        ax_conv = self.ejes['conv']; ax_conv.cla()
        ax_convb = self.ejes['convb']; ax_convb.cla()
        if len(fb_abs) > 1:
            ax_conv.semilogy(iters, fb_abs, 'o-', color=C['nr_f'], lw=2.2, ms=8, label='|f(β)|')
        ax_conv.axhline(1.0, color='white', lw=1.2, ls=':', alpha=0.55, label='Tolerancia')
        ax_convb.plot(iters, betas_h, 's--', color=C['nr_b'], lw=1.8, ms=6, alpha=0.85, label='β')
        ax_convb.set_ylabel('Valor de β en esa iteración', fontsize=8.5, color=C['nr_b'])
        ax_convb.tick_params(labelsize=8, colors=C['nr_b'])
        leyenda_combinada(ax_conv, ax_convb, fontsize=7.6, loc='center right')
        estilo_ax(ax_conv, con_numero(2, f'Convergencia | β*={beta_s:.5f} R0*={R0_s:.3f}'), xlabel='Iteración', ylabel='|f(β)| (escala log)')
        nota_y(ax_conv, 'Rojo=qué tan lejos del pico\nreal; Morado=valor de β', esquina='inferior_izquierda')

        ax_f = self.ejes['f']; ax_f.cla()
        betas_scan = np.linspace(0.05, min(1.5, beta * 3 + 0.3), 50)
        fvals = []
        for bv in betas_scan:
            _, Iv, _ = rk4_sir(bv, gamma, N, I0, MESES)
            fvals.append(float(np.max(Iv)) - I_obs)
        ax_f.plot(betas_scan, fvals, color=C['nr_b'], lw=2.2, label='f(β)')
        ax_f.axhline(0, color='white', lw=1.2, ls='--', alpha=0.5)
        ax_f.axvline(beta_s, color=C['nodo'], lw=1.8, ls=':', label=f'Raíz β*={beta_s:.4f}')
        ax_f.plot(beta_s, 0, 'o', color=C['nodo'], ms=9, zorder=6)
        for h_ in hist:
            ax_f.plot(h_['beta'], h_['fb'], 's', color=C['nr_f'], ms=6, zorder=5)
        ax_f.legend(fontsize=8)
        estilo_ax(ax_f, con_numero(3, 'Curva f(β) y raíz encontrada'), xlabel='β (contagiosidad)', ylabel='f(β) = pico simulado − observado')
        nota_y(ax_f, 'Diferencia entre el pico simulado\ncon ese β y el pico observado')

        rows = []
        for i, h_ in enumerate(hist):
            prev = betas_h[i - 1] if i > 0 else b0
            paso = abs(h_['beta'] - prev)
            rows.append([f"{h_['iter']}", f"{h_['beta']:.5f}", f"{'+' if h_['fb'] >= 0 else '-'}{num_corto(abs(h_['fb']))}",
                        num_corto(h_['ea']), num_corto(paso) if i > 0 else "—"])
        tabla_ax(self.ejes['tab'], rows, ['Iter', 'β_n', 'f(β_n)', '|f(β_n)|', '|Δβ|'],
                 con_numero(4, f'Iteraciones | β*={beta_s:.5f} R0*={R0_s:.3f}'))

        self._resumen = {'b0': b0, 'beta_s': beta_s, 'R0_s': R0_s, 'n_iter': len(hist), 'I_obs': I_obs}

    def interpretar_resultados(self):
        r = self._resumen
        if not r:
            return ''
        return (
            f"🔵 GRÁFICA ➊ (curva original vs calibrada): partiendo de β0={r['b0']:.3f}, Newton-Raphson "
            f"encontró β*={r['beta_s']:.4f} (línea verde punteada) para que el pico simulado de COVID-19 "
            f"coincida con el dato observado de {r['I_obs']:.0f} infectados (línea horizontal).\n"
            f"→ Conclusión: así es como se recalibra el modelo cuando se tiene un dato real de un pico de "
            f"contagios.\n\n"
            f"🔵 GRÁFICA ➋ (convergencia de |f(β)| y de β): |f(β)| baja hacia cero en pocas iteraciones "
            f"({r['n_iter']}).\n"
            f"→ Conclusión: el método converge rápido porque parte de una buena estimación inicial y la "
            f"función es suave.\n\n"
            f"🔵 GRÁFICA ➌ (curva f(β) y su raíz): el punto verde marca dónde f(β)=0, es decir, el valor "
            f"exacto de β que hace que el pico simulado sea igual al observado.\n"
            f"→ Conclusión: los cuadrados rojos muestran por dónde fue pasando el algoritmo hasta llegar "
            f"ahí, iteración tras iteración.\n\n"
            f"🔵 GRÁFICA ➍ (tabla iteración por iteración): permite verificar a mano cada paso del "
            f"método.\n"
            f"→ Conclusión: |Δβ| se hace cada vez más pequeño conforme el algoritmo se acerca a la raíz, "
            f"confirmando que converge."
        )
