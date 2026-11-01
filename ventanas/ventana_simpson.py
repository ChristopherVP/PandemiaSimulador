import numpy as np
import matplotlib.gridspec as gridspec
from ui.ventana_base import PanelTema
from ui.estilo import C, estilo_ax, con_numero, num_corto, tabla_ax, dar_espacio, leyenda
from ui.componentes import crear_slider
from core.estado_global import MESES
from core.metodos_numericos import rk4_sir, simpson_compuesta

_trapz = getattr(np, 'trapezoid', None) or np.trapz


class VentanaSimpson(PanelTema):
    ICONO = '⑤'
    TITULO = 'Impacto en el Sistema de Salud'
    SUBTITULO = 'Integración numérica con la regla de Simpson compuesta'
    CLAVE = 'simpson'
    DESCRIPCION = ('Muestra la carga total de infectados-mes de COVID-19 sobre el sistema de salud, comparable '
                   'con la ocupación hospitalaria y de camas UCI que reporta el DMQ. Se calcula con la Regla de '
                   'Simpson (integración numérica).')

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
        gs = gridspec.GridSpec(2, 3, figure=self.fig, top=0.92, bottom=0.09,
                               hspace=0.62, wspace=0.42, left=0.075, right=0.97)
        return dict(main=self.fig.add_subplot(gs[0, :]), conv=self.fig.add_subplot(gs[1, 0]),
                    trap=self.fig.add_subplot(gs[1, 1]), info=self.fig.add_subplot(gs[1, 2]))

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

        a = int(self.controles.get('a', 0)); b = int(self.controles.get('b', min(MESES - 1, 7)))
        a = max(0, min(MESES - 3, a)); b = max(a + 2, min(MESES - 1, b))
        area = simpson_compuesta(I4, a, b)
        area_tr = float(_trapz(I4[a:b + 1], t[a:b + 1]))
        dif = abs(area - area_tr)
        pct = area / area_tot * 100 if area_tot > 0 else 0

        ax = self.ejes['main']; ax.cla()
        ax.plot(t, I4, color=C['I'], lw=2.3, marker='o', ms=3.5, label='I(t) — RK4')
        ax.fill_between(t[a:b + 1], I4[a:b + 1], alpha=0.40, color=C['simps'],
                        label=f'Área ∫I(t)dt (Simpson) = {area:,.0f} personas·mes')
        ax.axvline(a, color=C['simps'], lw=1.4, ls='--', alpha=0.9)
        ax.axvline(b, color=C['simps'], lw=1.4, ls='--', alpha=0.9)
        ax.set_xlim(0, MESES - 1); ax.set_ylim(bottom=0)
        dar_espacio(ax, 0.22)
        leyenda(ax, loc='upper right', ncol=2, fontsize=8)
        estilo_ax(ax, con_numero(1, f'Carga de infectados entre los meses {a} y {b}  ({pct:.1f} % del total)'),
                  ylabel='Personas infectadas')

        ax = self.ejes['conv']; ax.cla()
        # Referencia: solucion RK4 con paso 16 veces mas fino, integrada con Simpson (144 subintervalos)
        k = 16
        _, I_fino, _ = rk4_sir(beta, gamma, N, I0, (MESES - 1) * k + 1, h=30.0 / k)
        total_fino = (MESES - 1) * k
        ref = simpson_compuesta(I_fino, 0, total_fino, h=1.0 / k)
        subint = [m for m in (2, 4, 6, 8, 12, 16, 24, 36, 48) if total_fino % m == 0]
        e_sp, e_tr = [], []
        for m in subint:
            paso_idx = total_fino // m
            Is = I_fino[::paso_idx][:m + 1]
            h_ = (MESES - 1) / m
            e_sp.append(abs(simpson_compuesta(Is, 0, m, h=h_) - ref))
            e_tr.append(abs(float(_trapz(Is, dx=h_)) - ref))
        piso = 1e-9
        ax.semilogy(subint, [max(v, piso) for v in e_tr], 'o--', color=C['I_eu'], lw=1.8, ms=5, label='Trapecio  O(h²)')
        ax.semilogy(subint, [max(v, piso) for v in e_sp], 's-', color=C['simps'], lw=2.2, ms=5.5, label='Simpson  O(h⁴)')
        dar_espacio(ax, 0.38, log=True)
        leyenda(ax, loc='upper right', fontsize=7.6)
        estilo_ax(ax, con_numero(2, 'Convergencia: Trapecio vs Simpson'), xlabel='Número de subintervalos',
                  ylabel='Error absoluto (escala log)')

        ax = self.ejes['trap']; ax.cla()
        area_tr1 = float((I4[a] + I4[b]) / 2.0 * (b - a))
        nombres = ['Simpson\ncompuesta', 'Trapecio\ncompuesto', 'Trapecio\n(1 tramo)']
        valores = [area, area_tr, area_tr1]
        colores = [C['simps'], C['I_eu'], C['S']]
        barras = ax.bar(nombres, valores, color=colores, width=0.55, edgecolor=C['panel'], linewidth=0.8)
        for br, v in zip(barras, valores):
            ax.text(br.get_x() + br.get_width() / 2, v, f'{v:,.0f}', ha='center', va='bottom', fontsize=8.4,
                    color=C['txt'], fontweight='bold')
        ax.set_ylim(0, max(valores) * 1.25 if max(valores) > 0 else 1)
        estilo_ax(ax, con_numero(3, f'Área según cada método  (dif. = {dif:,.1f})'), xlabel='', ylabel='Personas·mes')
        ax.set_xticks(range(3))
        ax.set_xticklabels(nombres)
        ax.tick_params(axis='x', labelsize=8)

        prom = area / max(1, b - a)
        rows = [
            ['Intervalo', f'meses {a} a {b}'], ['Duración', f'{b - a} meses'],
            ['∫ Simpson', f'{num_corto(area)} pers·mes'], ['∫ Trapecio', f'{num_corto(area_tr)} pers·mes'],
            ['Diferencia', num_corto(dif, 2)], ['Promedio mensual', f'{num_corto(prom)} pers'],
            ['% del total', f'{pct:.1f} %'], ['Total epidemia', f'{num_corto(area_tot)} pers·mes'],
        ]
        tabla_ax(self.ejes['info'], rows, ['Concepto', 'Valor'], con_numero(4, 'Resumen del intervalo'),
                 alineacion=['l', 'c'])
        self.datos_resumen = [list(r) for r in rows]
        self._resumen = {'a': a, 'b': b, 'area': area, 'pct': pct, 'dif': dif, 'prom': prom,
                         'tr1': area_tr1, 'err_tr1': abs(area - area_tr1)}

    def analisis(self):
        r = self._resumen
        if not r:
            return []
        return [
            dict(n='1', titulo='Área bajo I(t)',
                 texto=(f"La zona sombreada entre los meses {r['a']} y {r['b']} representa {r['area']:,.0f} "
                        f"«infectados-mes» de COVID-19, el {r['pct']:.1f} % del total de la epidemia simulada."),
                 conclusion='Ese es el tramo de tiempo que más carga le pondría al sistema de salud del DMQ.'),
            dict(n='2', titulo='Convergencia Trapecio vs Simpson',
                 texto=('La línea de Simpson baja más rápido que la del trapecio al usar más puntos '
                        '(escala logarítmica).'),
                 conclusion='Simpson llega a la misma precisión con muchos menos puntos, porque ajusta parábolas en vez de rectas.'),
            dict(n='3', titulo='Área según cada método en el intervalo elegido',
                 texto=(f"Simpson y el trapecio compuesto difieren en {r['dif']:,.2f} personas·mes, mientras que un "
                        f"único trapecio sobre todo el intervalo se aleja {r['err_tr1']:,.1f} de Simpson."),
                 conclusion=('Cuando la curva cambia de forma rápida, un solo trapecio la aproxima mal; Simpson '
                             'recoge la curvatura y da un resultado más fiel.')),
            dict(n='4', titulo='Resumen del intervalo',
                 texto=f"Traduce el área calculada a un promedio de {r['prom']:,.1f} infectados por mes.",
                 conclusion='Es un dato útil para pensar en camas o personal necesarios por mes en ese tramo.'),
        ]
