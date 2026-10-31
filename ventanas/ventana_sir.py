import numpy as np
import matplotlib.gridspec as gridspec
from ui.ventana_base import PanelTema
from ui.estilo import C, estilo_ax, badge, nota_y, con_numero, num_corto
from core.estado_global import MESES
from core.metodos_numericos import rk4_sir, euler_sir


class VentanaSIR(PanelTema):
    ICONO = '①'
    TITULO = 'Evolución de la Epidemia'
    CLAVE = 'sir'

    def teoria(self):
        titulo = 'Evolución del COVID-19 en Quito — calculada con el Modelo SIR (EDO), calibrado con datos del DMQ'
        formulas = [
            'dS/dt = -β·S·I/N        (susceptibles que se contagian de COVID-19)',
            'dI/dt =  β·S·I/N - γ·I  (infectados: entran y se recuperan)',
            'dR/dt =  γ·I             (recuperados que ya no contagian)',
            'R0 = β/γ                 (número reproductivo básico del COVID-19)',
        ]
        explicacion = (
            '¿QUÉ MUESTRA ESTA GRÁFICA?\n'
            'Es la fotografía completa de un brote de COVID-19 mes a mes: cuántas personas del Distrito '
            'Metropolitano de Quito (DMQ) siguen sanas pero en riesgo de contagio (Susceptibles), cuántas '
            'están contagiadas del virus en ese momento (Infectados) y cuántas ya pasaron la enfermedad y '
            'quedaron inmunizadas (Recuperados). De esta curva epidémica de infectados dependen las otras '
            'cinco gráficas del software: todas parten de estos mismos datos.\n\n'
            '¿QUÉ MÉTODO Y FÓRMULA LA CALCULAN?\n'
            'Las tres ecuaciones diferenciales de arriba describen cómo se mueve la población entre esos '
            'tres grupos durante la pandemia, pero no se pueden resolver a mano de forma exacta, así que se '
            'resuelven numéricamente, mes a mes, con dos métodos: Euler (usa solo la pendiente actual, '
            'acumula más error) y Runge-Kutta 4 o RK4 (promedia cuatro pendientes por paso, mucho más '
            'preciso). Internamente cada mes se subdivide en pasos más finos para que el cálculo sea '
            'estable y preciso, y solo se muestra el resultado al final de cada mes. RK4 es el que se usa '
            'como referencia en el resto del software.\n\n'
            'RELACIÓN CON LOS DATOS REALES DE QUITO\n'
            'La población N y los infectados iniciales I0 están calibrados con el Informe Quincenal '
            'COVID-19 de la Secretaría de Salud del Municipio de Quito (semana epidemiológica 45, corte '
            '13-nov-2021): N es la población del DMQ mayor a 5 años (base del cálculo de cobertura de '
            'vacunación) e I0 aproxima los casos activos de COVID-19 sumando los casos nuevos confirmados '
            'de las dos últimas semanas del informe (SE44=204 + SE45=126 ≈ 330), un rango cercano a los '
            '10-14 días que dura una persona siendo infecciosa. β y γ están ajustados para reflejar el '
            'nivel de alerta "Medio" y la epidemia controlada (R0<1) que describía ese informe, propio de '
            'una sexta ola de COVID-19 en descenso gracias a la cobertura de vacunación e inmunidad de '
            'rebaño.\n\n'
            'CÓMO FUNCIONA ESTA VENTANA\n'
            'Cada gráfica está numerada en su título. La ➊ muestra S(t), I(t) y R(t) con RK4 y también I(t) '
            'con Euler. La ➋ aísla la curva de Susceptibles. La ➌ muestra Infectados junto con Recuperados. '
            'La ➍ es la tabla resumen.'
        )
        return titulo, formulas, explicacion

    def crear_ejes(self):
        gs = gridspec.GridSpec(2, 3, figure=self.fig, top=0.88, bottom=0.10,
                                hspace=0.70, wspace=0.35, left=0.06, right=0.97)
        ax_main = self.fig.add_subplot(gs[0, :])
        ax_S = self.fig.add_subplot(gs[1, 0])
        ax_I = self.fig.add_subplot(gs[1, 1])
        ax_info = self.fig.add_subplot(gs[1, 2])
        ax_I2 = ax_I.twinx()
        return dict(main=ax_main, S=ax_S, I=ax_I, I2=ax_I2, info=ax_info)

    def interpretar_resultados(self):
        r = self._resumen
        if not r:
            return ''
        return (
            f"🔵 GRÁFICA ➊ (S, I, R con RK4 y Euler): con β={r['beta']:.2f} y γ={r['gamma']:.2f} el número "
            f"reproductivo es R0={r['R0']:.2f}. Como R0 {'es mayor a 1' if r['R0'] > 1 else 'es menor a 1'}, "
            f"la curva roja de infectados por COVID-19 {'crece hasta un pico y luego baja' if r['R0'] > 1 else 'desciende desde el inicio'}. "
            f"El pico ocurre en el mes {r['dp']} con {r['pico']:.0f} infectados.\n"
            f"→ Conclusión: con estos parámetros, el brote en Quito "
            f"{'se propagaría de forma sostenida' if r['R0'] > 1 else 'estaría controlado y se apagaría solo'}.\n\n"
            f"🔵 GRÁFICA ➋ (Susceptibles S(t)): la curva azul siempre baja o se mantiene, nunca sube, "
            f"porque una persona Susceptible al COVID-19 solo puede pasar a Infectada, nunca al revés.\n"
            f"→ Conclusión: representa a cuánta gente de Quito le queda todavía por exponerse al virus; "
            f"terminó en {r['S_final']:.0f} personas.\n\n"
            f"🔵 GRÁFICA ➌ (I(t) y R(t) superpuestas): mientras la curva roja de infectados sube y baja, la "
            f"verde de recuperados solo puede subir, porque una vez que alguien se recupera del COVID-19 no "
            f"vuelve a infectarse en este modelo.\n"
            f"→ Conclusión: la distancia entre ambas curvas al final indica cuánta gente ya pasó la "
            f"enfermedad y cuánta sigue contagiada.\n\n"
            f"🔵 GRÁFICA ➍ (tabla resumen): confirma en cifras exactas el pico, el estado epidémico y la "
            f"duración de la enfermedad (1/γ).\n"
            f"→ Conclusión: son los mismos datos que se ven en las gráficas ➊-➌, listos para citar en un "
            f"informe."
        )

    def dibujar(self):
        t = np.arange(MESES)
        beta, gamma, N, I0 = self.estado.beta, self.estado.gamma, self.estado.N, self.estado.I0
        R0 = beta / gamma

        S4, I4, R4 = rk4_sir(beta, gamma, N, I0, MESES)
        Se, Ie, Re = euler_sir(beta, gamma, N, I0, MESES)
        pico = np.max(I4)
        dp = int(np.argmax(I4))

        ax_main = self.ejes['main']; ax_main.cla()
        ax_main.plot(t, S4, color=C['S'], lw=2.2, label='S — Susceptibles (RK4)')
        ax_main.plot(t, I4, color=C['I'], lw=2.5, label='I — Infectados   (RK4)')
        ax_main.plot(t, R4, color=C['R'], lw=2.2, label='R — Recuperados  (RK4)')
        ax_main.plot(t, Ie, color=C['I_eu'], lw=1.6, ls='--', alpha=0.75, label='I — Infectados (Euler, aprox.)')
        ax_main.fill_between(t, I4, Ie, alpha=0.12, color=C['I_eu'], label='Diferencia Euler−RK4')
        ax_main.axvline(dp, color=C['I'], lw=1.2, ls=':', alpha=0.6)
        ax_main.annotate(f'  Pico RK4\n  {pico:.0f} infectados\n  Mes {dp}',
                          xy=(dp, pico), xytext=(min(dp + 1, MESES - 2), pico * 0.82), color=C['I'], fontsize=9,
                          arrowprops=dict(arrowstyle='->', color=C['I'], lw=1.3))
        ax_main.set_xlim(0, MESES - 1); ax_main.set_ylim(0, N * 1.09)
        ax_main.legend(fontsize=8, loc='lower right', ncol=2, framealpha=0.85)
        estilo_ax(ax_main, con_numero(1, f'Modelo SIR COVID-19 — β={beta:.2f}  γ={gamma:.2f}  I0={I0}  N={N:,}  |  R0=β/γ={R0:.3f}'),
                  ylabel='Personas (S, I o R)')
        badge(ax_main, 0.30, 0.97, f'R0={R0:.2f}  {"⚠ EPIDEMIA" if R0 > 1 else "✓ CONTROLADO"}',
              '#DA3633' if R0 > 1 else '#238636')
        nota_y(ax_main, 'Eje Y = cantidad de personas en\ncada grupo (S, I o R) ese mes')

        ax_S = self.ejes['S']; ax_S.cla()
        ax_S.plot(t, S4, color=C['S'], lw=2.2)
        ax_S.fill_between(t, S4, alpha=0.15, color=C['S'])
        ax_S.axvline(dp, color=C['S'], lw=1, ls=':', alpha=0.5)
        estilo_ax(ax_S, con_numero(2, 'Susceptibles S(t)'), ylabel='Personas susceptibles')
        ax_S.set_xlim(0, MESES - 1); ax_S.set_ylim(0, N * 1.05)
        ax_S.text(0.98, 0.95, f'S final\n{S4[-1]:.0f}', transform=ax_S.transAxes, ha='right', fontsize=8, color=C['S'])
        nota_y(ax_S, 'Personas que aún NO se\nhan contagiado del COVID-19')

        ax_I = self.ejes['I']; ax_I.cla()
        ax_I2 = self.ejes['I2']; ax_I2.cla()
        ax_I.plot(t, I4, color=C['I'], lw=2.2, label='RK4')
        ax_I.plot(t, Ie, color=C['I_eu'], lw=1.6, ls='--', alpha=0.8, label='Euler')
        ax_I.fill_between(t, I4, Ie, alpha=0.2, color=C['I_eu'])
        ax_I2.plot(t, R4, color=C['R'], lw=1.6, alpha=0.7)
        ax_I2.set_ylabel('Personas recuperadas', fontsize=8.5, color=C['R'])
        ax_I2.tick_params(labelsize=8, colors=C['R'])
        ax_I.legend(fontsize=8, loc='upper right')
        ax_I.set_xlim(0, MESES - 1); ax_I.set_ylim(0, None)
        estilo_ax(ax_I, con_numero(3, f'Infectados I(t) y Recuperados R(t) | Pico={pico:.0f} (mes {dp})'), ylabel='Personas infectadas')
        nota_y(ax_I, 'Rojo=infectados ahora (eje izq.)\nVerde=recuperados en total (eje der.)')

        ax_info = self.ejes['info']; ax_info.cla(); ax_info.axis('off')
        pico_eu = np.max(Ie); mes_eu = int(np.argmax(Ie))
        rows = [
            ['R0 = β/γ', f'{R0:.4f}'],
            ['Estado', '⚠ EPIDEMIA' if R0 > 1 else '✓ CONTROLADO'],
            ['Pico RK4', f'{num_corto(pico)} (mes {dp})'],
            ['Pico Euler', f'{num_corto(pico_eu)} (mes {mes_eu})'],
            ['Error pico |RK4-Eu|', f'{num_corto(abs(pico - pico_eu))} pers.'],
            ['S final (RK4)', num_corto(S4[-1])],
            ['R final (RK4)', num_corto(R4[-1])],
            ['β / γ', f'{beta:.3f} / {gamma:.3f}'],
            ['N / I0', f'{N:,} / {I0}'],
            ['1/γ (duración enfermedad)', f'{1 / gamma:.1f} días (≈{1 / gamma / 30:.2f} meses)'],
        ]
        t_tab = ax_info.table(cellText=rows, colLabels=['Métrica', 'Valor'], cellLoc='left', loc='center',
                              bbox=[0.0, 0.01, 1.0, 0.82])
        t_tab.auto_set_font_size(False); t_tab.set_fontsize(8.4)
        for (rr, cc), cell in t_tab.get_celld().items():
            cell.set_facecolor(C['fondo_f'] if rr == 0 else C['panel'])
            cell.set_edgecolor(C['border'])
            cell.set_text_props(color=C['txt'])
        ax_info.set_title(con_numero(4, 'Resumen'), fontsize=9.6, color=C['txt'], pad=10, fontweight='bold')

        self._resumen = {'beta': beta, 'gamma': gamma, 'R0': R0, 'pico': pico, 'dp': dp, 'S_final': S4[-1]}
