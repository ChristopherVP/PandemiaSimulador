import numpy as np
import matplotlib.gridspec as gridspec
from ui.ventana_base import PanelTema
from ui.estilo import (C, estilo_ax, badge, con_numero, num_corto, tabla_ax, eje_derecho,
                       dar_espacio, leyenda, anotar)
from core.estado_global import MESES
from core.metodos_numericos import rk4_sir, euler_sir


class VentanaSIR(PanelTema):
    ICONO = '①'
    TITULO = 'Evolución de la Epidemia'
    SUBTITULO = 'Modelo SIR (Susceptibles – Infectados – Recuperados) resuelto con Euler y Runge-Kutta 4'
    CLAVE = 'sir'
    DESCRIPCION = ('Muestra cómo evoluciona el COVID-19 mes a mes en el DMQ (Susceptibles, Infectados, '
                   'Recuperados), la curva epidémica y el número reproductivo básico R0. Se calcula resolviendo '
                   'el Modelo SIR (ecuaciones diferenciales) con Euler y Runge-Kutta 4.')

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
        gs = gridspec.GridSpec(2, 3, figure=self.fig, top=0.92, bottom=0.09,
                               hspace=0.62, wspace=0.50, left=0.075, right=0.955)
        ax_main = self.fig.add_subplot(gs[0, :])
        ax_S = self.fig.add_subplot(gs[1, 0])
        ax_I = self.fig.add_subplot(gs[1, 1])
        ax_info = self.fig.add_subplot(gs[1, 2])
        ax_I2 = ax_I.twinx()
        return dict(main=ax_main, S=ax_S, I=ax_I, I2=ax_I2, info=ax_info)

    def analisis(self):
        r = self._resumen
        if not r:
            return []
        ctrl = r['R0'] <= 1
        return [
            dict(n='1', titulo='Curvas S, I y R con RK4 y Euler',
                 texto=(f"Con β={r['beta']:.2f} y γ={r['gamma']:.2f} el número reproductivo es R0={r['R0']:.2f}. "
                        f"Como R0 {'es mayor a 1' if r['R0'] > 1 else 'es menor o igual a 1'}, la curva de infectados "
                        f"por COVID-19 {'crece hasta un pico y luego baja' if r['R0'] > 1 else 'desciende desde el inicio'}. "
                        f"El pico ocurre en el mes {r['dp']} con {r['pico']:.0f} infectados."),
                 conclusion=(f"Con estos parámetros, el brote en Quito "
                             f"{'se propagaría de forma sostenida hasta alcanzar su pico' if not ctrl else 'estaría controlado y se apagaría solo'}.")),
            dict(n='2', titulo='Susceptibles S(t)',
                 texto=("La curva de susceptibles siempre baja o se mantiene, nunca sube, porque una persona "
                        "susceptible al COVID-19 solo puede pasar a infectada, nunca al revés."),
                 conclusion=(f"Representa a cuánta gente de Quito le queda por exponerse al virus; al final de la "
                             f"simulación quedan {r['S_final']:,.0f} personas susceptibles.")),
            dict(n='3', titulo='Infectados I(t) y Recuperados R(t)',
                 texto=("Mientras la curva de infectados sube y baja, la de recuperados solo puede subir, porque "
                        "una vez que alguien se recupera del COVID-19 no vuelve a infectarse en este modelo."),
                 conclusion=(f"La distancia entre ambas curvas al final indica cuánta gente ya pasó la "
                             f"enfermedad ({r['R_final']:,.0f}) y cuánta sigue contagiada.")),
            dict(n='4', titulo='Tabla resumen',
                 texto=("Confirma en cifras exactas el pico, el estado epidémico, el error entre Euler y RK4 y la "
                        "duración de la enfermedad (1/γ)."),
                 conclusion="Son los mismos datos de las gráficas 1 a 3, listos para citar en un informe."),
        ]

    def dibujar(self):
        t = np.arange(MESES)
        beta, gamma, N, I0 = self.estado.beta, self.estado.gamma, self.estado.N, self.estado.I0
        R0 = beta / gamma

        S4, I4, R4 = rk4_sir(beta, gamma, N, I0, MESES)
        Se, Ie, Re = euler_sir(beta, gamma, N, I0, MESES)
        pico = float(np.max(I4))
        dp = int(np.argmax(I4))

        # ---------------------------------------------------------------- 1
        ax = self.ejes['main']; ax.cla()
        ax.plot(t, S4, color=C['S'], lw=2.2, label='S  Susceptibles (RK4)')
        ax.plot(t, I4, color=C['I'], lw=2.4, label='I  Infectados (RK4)')
        ax.plot(t, R4, color=C['R'], lw=2.2, label='R  Recuperados (RK4)')
        ax.plot(t, Ie, color=C['I_eu'], lw=1.5, ls='--', label='I  Infectados (Euler)')
        ax.fill_between(t, I4, Ie, alpha=0.18, color=C['I_eu'], label='Diferencia Euler − RK4')
        ax.axvline(dp, color=C['I'], lw=1.0, ls=':', alpha=0.7)
        ax.set_xlim(0, MESES - 1); ax.set_ylim(0, N * 1.0)
        dar_espacio(ax, 0.24)
        anotar(ax, dp, pico, f'Pico: {pico:,.0f} infectados (mes {dp})', C['I'], MESES - 1)
        leyenda(ax, loc='upper center', ncol=5, fontsize=8)
        estilo_ax(ax, con_numero(1, 'Modelo SIR del COVID-19: Susceptibles, Infectados y Recuperados'),
                  ylabel='Personas')
        badge(ax, f'R0 = {R0:.2f}   {"EPIDEMIA" if R0 > 1 else "CONTROLADO"}', C['mal'] if R0 > 1 else C['ok'])

        # ---------------------------------------------------------------- 2
        ax = self.ejes['S']; ax.cla()
        rango = max(N - S4.min(), 0.002 * N)
        ax.plot(t, S4, color=C['S'], lw=2.2, marker='o', ms=3.5, label=f'S(t)  final = {S4[-1]:,.0f}')
        ax.axhline(N, color=C['ref'], lw=1.0, ls='--', alpha=0.7, label=f'N = {N:,}')
        ax.fill_between(t, S4, S4.min() - 0.25 * rango, alpha=0.15, color=C['S'])
        ax.set_xlim(0, MESES - 1)
        ax.set_ylim(S4.min() - 0.25 * rango, N + 0.55 * rango)
        leyenda(ax, loc='upper right', fontsize=7.8)
        estilo_ax(ax, con_numero(2, 'Susceptibles S(t)'), ylabel='Personas susceptibles')

        # ---------------------------------------------------------------- 3
        ax_I = self.ejes['I']; ax_I.cla()
        ax_I2 = self.ejes['I2']; ax_I2.cla()
        ax_I.plot(t, I4, color=C['I'], lw=2.2, label='I  Infectados (RK4)')
        ax_I.plot(t, Ie, color=C['I_eu'], lw=1.5, ls='--', label='I  Infectados (Euler)')
        ax_I.fill_between(t, I4, Ie, alpha=0.2, color=C['I_eu'])
        ax_I2.plot(t, R4, color=C['R'], lw=2.0, label='R  Recuperados (RK4)')
        ax_I.set_xlim(0, MESES - 1); ax_I.set_ylim(0, None)
        ax_I2.set_ylim(0, None)
        dar_espacio(ax_I, 0.34); dar_espacio(ax_I2, 0.34)
        estilo_ax(ax_I, con_numero(3, 'Infectados I(t) y Recuperados R(t)'), ylabel='Personas infectadas')
        ax_I.yaxis.label.set_color(C['I'])
        eje_derecho(ax_I2, 'Personas recuperadas', C['R'])
        leyenda(ax_I, loc='upper right', fontsize=7.4, ejes_extra=(ax_I2,))

        # ---------------------------------------------------------------- 4
        pico_eu = float(np.max(Ie)); mes_eu = int(np.argmax(Ie))
        rows = [
            ['R0 = β/γ', f'{R0:.4f}'],
            ['Estado', 'EPIDEMIA' if R0 > 1 else 'CONTROLADO'],
            ['Pico RK4', f'{num_corto(pico)} (mes {dp})'],
            ['Pico Euler', f'{num_corto(pico_eu)} (mes {mes_eu})'],
            ['Error del pico', f'{num_corto(abs(pico - pico_eu))} pers.'],
            ['S final (RK4)', num_corto(S4[-1])],
            ['R final (RK4)', num_corto(R4[-1])],
            ['β / γ', f'{beta:.3f} / {gamma:.3f}'],
            ['N / I0', f'{N:,} / {I0}'],
            ['Duración 1/γ', f'{1 / gamma:.1f} días ({1 / gamma / 30:.2f} meses)'],
        ]
        tabla_ax(self.ejes['info'], rows, ['Métrica', 'Valor'], con_numero(4, 'Resumen'),
                 alineacion=['l', 'c'], resaltar={(1, 1): C['mal'] if R0 > 1 else C['ok']})
        self.datos_resumen = [list(r) for r in rows]

        self._resumen = {'beta': beta, 'gamma': gamma, 'R0': R0, 'pico': pico, 'dp': dp,
                         'S_final': float(S4[-1]), 'R_final': float(R4[-1])}
