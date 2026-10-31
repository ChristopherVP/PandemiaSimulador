import numpy as np
import matplotlib.gridspec as gridspec
from ui.ventana_base import PanelTema
from ui.estilo import C, estilo_ax, nota_y, con_numero, num_corto
from ui.componentes import crear_slider
from core.estado_global import MESES
from core.metodos_numericos import rk4_sir, simpson_compuesta

_trapz = getattr(np, 'trapezoid', None) or np.trapz


class VentanaSimpson(PanelTema):
    ICONO = '⑤'
    TITULO = 'Impacto en el Sistema de Salud'
    CLAVE = 'simpson'

    def teoria(self):
        titulo = 'Impacto del COVID-19 en el Sistema de Salud — calculado con Integración de Simpson'
        formulas = [
            '∫I(t)dt ≈ (h/3)·[I0 + 4I1 + 2I2 + 4I3 + ... + In]   (Simpson compuesta)',
        ]
        explicacion = (
            '¿QUÉ MUESTRA ESTA GRÁFICA?\n'
            'El área bajo la curva de infectados de COVID-19 entre dos meses, que representa la carga '
            'acumulada de "personas-mes" enfermas que tuvo que atender el sistema de salud en ese periodo. '
            'Es útil para dimensionar recursos: camas, personal, insumos, en un tramo específico de la '
            'epidemia.\n\n'
            '¿QUÉ MÉTODO Y FÓRMULA LA CALCULAN?\n'
            'Se integra numéricamente la curva de infectados I(t) generada por RK4 usando la regla de '
            'Simpson, que ajusta una parábola a cada par de intervalos en vez de una línea recta (como '
            'haría el método del trapecio), obteniendo una aproximación más exacta del área.\n\n'
            'RELACIÓN CON LOS DATOS REALES DE QUITO\n'
            'El informe de la Secretaría de Salud reporta la ocupación hospitalaria y de camas UCI '
            'destinadas a COVID-19 en el DMQ (56% y 59% respectivamente, al corte del informe). Esa carga '
            'sobre el sistema de salud es, matemáticamente, el área bajo la curva de infectados en un '
            'periodo. Esta ventana calcula exactamente esa área con la Regla de Simpson, para dimensionar '
            'cuántas "personas-mes" de atención habría que cubrir entre dos fechas cualquiera.\n\n'
            'CÓMO FUNCIONA ESTA VENTANA\n'
            'Los sliders "Mes inicio (a)" y "Mes fin (b)" definen el intervalo a integrar; la zona '
            'sombreada en la gráfica ➊ es exactamente esa área. La gráfica ➋ compara qué tan rápido '
            'converge Simpson contra el trapecio al usar más puntos. La gráfica ➌ muestra ambos métodos '
            'superpuestos sobre el mismo intervalo. La ➍ es el resumen numérico con la interpretación del '
            'resultado.'
        )
        return titulo, formulas, explicacion

    def crear_ejes(self):
        gs = gridspec.GridSpec(2, 3, figure=self.fig, top=0.88, bottom=0.10,
                                hspace=0.70, wspace=0.35, left=0.06, right=0.97)
        ax_main = self.fig.add_subplot(gs[0, :])
        ax_conv = self.fig.add_subplot(gs[1, 0])
        ax_trap = self.fig.add_subplot(gs[1, 1])
        ax_info = self.fig.add_subplot(gs[1, 2])
        return dict(main=ax_main, conv=ax_conv, trap=ax_trap, info=ax_info)

    def construir_controles(self):
        self.controles['a'] = 0
        self.controles['b'] = min(MESES - 1, 7)

        def on_a(v):
            self.controles['a'] = int(float(v))
            self.actualizar()

        def on_b(v):
            self.controles['b'] = int(float(v))
            self.actualizar()

        crear_slider(self.frame_controles, 'Mes inicio (a)', 0, MESES - 4, 0, 1, on_a, C['simps'],
                     descripcion='Desde qué mes empieza a sumarse la carga sobre el sistema de salud')
        crear_slider(self.frame_controles, 'Mes fin (b)', 3, MESES - 1, self.controles['b'], 1, on_b, C['simps'],
                     descripcion='Hasta qué mes se acumula la carga sobre el sistema de salud')

    def dibujar(self):
        t = np.arange(MESES)
        beta, gamma, N, I0 = self.estado.beta, self.estado.gamma, self.estado.N, self.estado.I0
        _, I4, _ = rk4_sir(beta, gamma, N, I0, MESES)
        area_tot = simpson_compuesta(I4, 0, MESES - 1)

        a = int(self.controles.get('a', 0)); b = int(self.controles.get('b', MESES - 3))
        a = max(0, min(MESES - 3, a)); b = max(a + 2, min(MESES - 1, b))
        area = simpson_compuesta(I4, a, b)
        area_tr = float(_trapz(I4[a:b + 1], t[a:b + 1]))
        dif = abs(area - area_tr)
        pct = area / area_tot * 100 if area_tot > 0 else 0

        ax_main = self.ejes['main']; ax_main.cla()
        ax_main.plot(t, I4, color=C['I'], lw=2.2, label='I(t) — RK4')
        ax_main.fill_between(t[:a + 1], I4[:a + 1], alpha=0.08, color=C['I'])
        ax_main.fill_between(t[a:b + 1], I4[a:b + 1], alpha=0.45, color=C['simps'],
                             label=f'∫I(t)dt Simpson ≈ {area:,.0f}')
        ax_main.fill_between(t[b:], I4[b:], alpha=0.08, color=C['I'])
        ax_main.axvline(a, color=C['simps'], lw=1.8, ls='--', alpha=0.8)
        ax_main.axvline(b, color=C['simps'], lw=1.8, ls='--', alpha=0.8)
        ax_main.set_xlim(0, MESES - 1); ax_main.set_ylim(bottom=0)
        ax_main.legend(fontsize=8.3)
        estilo_ax(ax_main, con_numero(1, f'∫I(t)dt mes {a}→{b} | Simpson={area:,.0f} Trapecio={area_tr:,.0f} ({pct:.1f}% del total)'),
                  ylabel='Personas infectadas')
        nota_y(ax_main, 'Personas infectadas activas cada\nmes; el área sombreada es la carga total')

        ax_conv = self.ejes['conv']; ax_conv.cla()
        npts = list(range(4, MESES + 1))
        e_sp, e_tr = [], []
        ref = area_tot
        for np_ in npts:
            idx = np.round(np.linspace(0, MESES - 1, np_)).astype(int)
            Is = I4[idx]; ts = t[idx].astype(float); h_ = ts[1] - ts[0]
            ar_s = Is[0] + Is[-1]
            for ii in range(1, len(Is) - 1):
                ar_s += (4 if ii % 2 == 1 else 2) * Is[ii]
            e_sp.append(abs(ar_s * h_ / 3 - ref))
            e_tr.append(abs(_trapz(Is, ts) - ref))
        ax_conv.semilogy(npts, [max(v, 1e-6) for v in e_tr], 'o--', color=C['I_eu'], lw=1.8, ms=5, label='Trapecio O(h²)')
        ax_conv.semilogy(npts, [max(v, 1e-6) for v in e_sp], 's-', color=C['simps'], lw=2.2, ms=6, label='Simpson O(h⁴)')
        ax_conv.legend(fontsize=8)
        estilo_ax(ax_conv, con_numero(2, 'Convergencia Trapecio vs Simpson'), xlabel='Nº de puntos usados', ylabel='Error abs. (escala log)')
        nota_y(ax_conv, 'Qué tan lejos está cada método\ndel área real, en escala logarítmica')

        ax_trap = self.ejes['trap']; ax_trap.cla()
        seg = t[a:b + 1]; Iseg = I4[a:b + 1]
        ax_trap.plot(seg, Iseg, color=C['I'], lw=2.2)
        ax_trap.fill_between(seg, Iseg, alpha=0.20, color=C['simps'], label=f'Simpson: {area:,.0f}')
        ax_trap.fill_between([a, b], [I4[a], I4[b]], alpha=0.15, color=C['I_eu'])
        ax_trap.plot([a, b], [I4[a], I4[b]], color=C['I_eu'], lw=1.5, ls='--', label=f'Trapecio: {area_tr:,.0f}')
        ax_trap.legend(fontsize=8)
        estilo_ax(ax_trap, con_numero(3, f'Trapecio vs Simpson | diferencia={dif:.2f}'), ylabel='Personas infectadas')
        nota_y(ax_trap, 'Comparación del área (carga de\ninfectados) según cada método')

        ax_info = self.ejes['info']; ax_info.cla(); ax_info.axis('off')
        prom = area / max(1, b - a)
        rows = [
            ['Intervalo', f'Meses {a}→{b}'], ['Duración', f'{b - a} meses'],
            ['∫Simpson', num_corto(area)], ['∫Trapecio', num_corto(area_tr)],
            ['Diferencia', num_corto(dif, 2)], ['Promedio mensual', num_corto(prom)],
            ['% del total', f'{pct:.1f}%'], ['Total epidemia', num_corto(area_tot)],
        ]
        t_t = ax_info.table(cellText=rows, colLabels=['Concepto', 'Valor'], cellLoc='left', loc='upper center',
                            bbox=[0.0, 0.42, 1.0, 0.40])
        t_t.auto_set_font_size(False); t_t.set_fontsize(8.0)
        for (rr, cc), cell in t_t.get_celld().items():
            cell.set_facecolor(C['fondo_f'] if rr == 0 else C['panel'])
            cell.set_edgecolor(C['border'])
            cell.set_text_props(color=C['txt'])
        ax_info.text(0.5, 0.36,
            '∫I(t)dt = carga total de\nCOVID-19 sobre el sistema\nde salud (personas·mes).',
            ha='center', va='top', transform=ax_info.transAxes, fontsize=8.4, color=C['txt2'],
            bbox=dict(boxstyle='round', facecolor=C['fondo_f'], edgecolor=C['acento'], lw=1.1))
        ax_info.set_title(con_numero(4, 'Interpretación'), fontsize=9.6, color=C['txt'], pad=10, fontweight='bold')

        self._resumen = {'a': a, 'b': b, 'area': area, 'pct': pct, 'dif': dif}

    def interpretar_resultados(self):
        r = self._resumen
        if not r:
            return ''
        return (
            f"🔵 GRÁFICA ➊ (área bajo I(t)): la zona amarilla sombreada entre los meses {r['a']} y {r['b']} "
            f"representa {r['area']:,.0f} \"infectados-mes\" de COVID-19, el {r['pct']:.1f}% del total de "
            f"la epidemia simulada.\n"
            f"→ Conclusión: ese es el tramo de tiempo que más carga le pondría al sistema de salud del "
            f"DMQ.\n\n"
            f"🔵 GRÁFICA ➋ (Convergencia Trapecio vs Simpson): la línea de Simpson baja más rápido que la "
            f"del trapecio al usar más puntos (escala logarítmica).\n"
            f"→ Conclusión: Simpson llega a la misma precisión con muchos menos puntos, porque ajusta "
            f"parábolas en vez de líneas rectas.\n\n"
            f"🔵 GRÁFICA ➌ (Trapecio vs Simpson en el intervalo elegido): la diferencia entre ambos métodos "
            f"es de solo {r['dif']:.2f}.\n"
            f"→ Conclusión: para esta curva relativamente suave, incluso el trapecio (más simple) da un "
            f"resultado cercano al de Simpson.\n\n"
            f"🔵 GRÁFICA ➍ (resumen del intervalo): traduce el área calculada a un promedio mensual de "
            f"infectados.\n"
            f"→ Conclusión: es un dato útil para pensar en camas o personal necesarios por mes en ese "
            f"tramo."
        )
