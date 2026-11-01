import numpy as np
import matplotlib.gridspec as gridspec
from scipy.interpolate import CubicSpline
from ui.ventana_base import PanelTema
from ui.estilo import C, estilo_ax, con_numero, num_corto, dar_espacio, leyenda, tabla_ax
from ui.componentes import crear_slider
from core.estado_global import MESES
from core.metodos_numericos import rk4_sir


class VentanaSpline(PanelTema):
    ICONO = '③'
    TITULO = 'Estimación de Meses sin Datos'
    SUBTITULO = 'Interpolación mediante Spline Cúbico natural'
    CLAVE = 'spline'
    DESCRIPCION = ('Muestra qué tan bien se puede estimar el número de infectados de COVID-19 en meses sin '
                   'datos —igual que entre dos informes quincenales de la Secretaría de Salud—, usando solo '
                   'algunos puntos conocidos. Se calcula con Interpolación por Spline Cúbico.')

    def crear_ejes(self):
        gs = gridspec.GridSpec(2, 3, figure=self.fig, top=0.92, bottom=0.09,
                               hspace=0.62, wspace=0.42, left=0.075, right=0.97)
        return dict(main=self.fig.add_subplot(gs[0, :]), zoom=self.fig.add_subplot(gs[1, 0]),
                    err=self.fig.add_subplot(gs[1, 1]), info=self.fig.add_subplot(gs[1, 2]))

    def teoria(self):
        titulo = 'Estimación de Meses de COVID-19 sin Datos — calculada con Spline Cúbico'
        formulas = [
            'Sk(x) = ak + bk(x−xk) + ck(x−xk)² + dk(x−xk)³   (polinomio por tramo)',
            "Condición: Sk, Sk', Sk''  continuas entre tramos consecutivos",
        ]
        explicacion = (
            '¿QUÉ MUESTRA ESTA GRÁFICA?\n'
            'Simula una situación real de la pandemia: si solo tuvieras reportes de infectados de COVID-19 '
            'cada cierto número de meses (no todos los meses), esta gráfica muestra qué tan bien se puede '
            '"rellenar" o adivinar los meses sin dato, sin necesidad de volver a correr el modelo '
            'completo.\n\n'
            '¿QUÉ MÉTODO Y FÓRMULA LA CALCULAN?\n'
            'Se toman solo algunos "nodos" (puntos conocidos) de la curva real de infectados y se construye '
            'un polinomio cúbico distinto entre cada par de nodos, exigiendo que la unión entre tramos sea '
            'suave (misma pendiente y curvatura). Con eso se estima el valor en cualquier mes intermedio.\n\n'
            'RELACIÓN CON LOS DATOS REALES DE QUITO\n'
            'La Secretaría de Salud publica sus informes de COVID-19 de forma quincenal (cada dos semanas), '
            'no todos los meses completos: exactamente el mismo problema que resuelve el spline cúbico, '
            'estimar los valores en los periodos intermedios sin dato reportado, usando solo los puntos que '
            'sí se conocen.\n\n'
            'CÓMO FUNCIONA ESTA VENTANA\n'
            'El slider "Nodos (cada N meses)" controla cada cuántos meses se toma un punto conocido; con '
            'menos nodos la estimación es menos precisa. El slider "Mes a estimar" mueve la línea vertical '
            'hasta el mes que quieras consultar. La gráfica ➊ compara el valor estimado (rombo) contra el '
            'real (círculo). La ➋ es un acercamiento a esa zona. La ➌ es el error del spline en todo el '
            'rango. La ➍ es una tabla que compara distintos números de nodos.'
        )
        return titulo, formulas, explicacion

    def construir_controles(self):
        self.controles['paso'] = 2
        self.controles['dia'] = min(MESES - 2, 5)

        def on_paso(v):
            self.controles['paso'] = int(float(v))
            self.actualizar()

        def on_dia(v):
            self.controles['dia'] = int(float(v))
            self.actualizar()

        crear_slider(self.frame_controles, 'Nodos (cada N meses)', 1, 4, self.controles['paso'], 1, on_paso, C['nodo'],
                     descripcion='Cada cuántos meses se toma un dato real conocido')
        crear_slider(self.frame_controles, 'Mes a estimar', 1, MESES - 2, self.controles['dia'], 1, on_dia, C['spline'],
                     descripcion='Mes intermedio sin dato real que quieres estimar con el spline')

    def dibujar(self):
        t = np.arange(MESES)
        beta, gamma, N, I0 = self.estado.beta, self.estado.gamma, self.estado.N, self.estado.I0
        _, I4, _ = rk4_sir(beta, gamma, N, I0, MESES)
        paso = int(self.controles.get('paso', 2))
        dq = int(self.controles.get('dia', min(MESES - 2, 5)))
        dq = max(1, min(MESES - 2, dq))

        idx = np.arange(0, MESES, paso)
        if idx[-1] != MESES - 1:
            idx = np.append(idx, MESES - 1)
        tn = t[idx].astype(float); In = I4[idx]
        cs = CubicSpline(tn, In, bc_type='natural')
        tf = np.linspace(0, MESES - 1, 200)
        Isp_f = np.maximum(0, cs(tf))
        Isp = np.maximum(0, cs(t.astype(float)))
        Iest = float(np.maximum(0, cs(float(dq))))
        Ireal = float(I4[dq])
        ea_pt = abs(Ireal - Iest)

        ax = self.ejes['main']; ax.cla()
        ax.plot(t, I4, color=C['I'], lw=1.8, ls='--', alpha=0.8, label='RK4 (real)')
        ax.plot(tf, Isp_f, color=C['spline'], lw=2.6, label=f'Spline cúbico ({len(tn)} nodos)')
        ax.scatter(tn, In, color=C['nodo'], s=50, zorder=6, edgecolor=C['panel'], linewidth=0.8,
                   label='Nodos conocidos')
        ax.axvline(dq, color=C['ref'], lw=1.0, ls=':', alpha=0.7)
        ax.plot(dq, Iest, 'D', color=C['spline'], ms=9, zorder=8, markeredgecolor=C['panel'],
                label=f'Estimado mes {dq}: {Iest:,.1f}')
        ax.plot(dq, Ireal, 'o', color=C['I'], ms=7, zorder=9, markeredgecolor=C['panel'],
                label=f'Real mes {dq}: {Ireal:,.1f}')
        ax.set_xlim(0, MESES - 1); ax.set_ylim(bottom=0)
        dar_espacio(ax, 0.22)
        leyenda(ax, loc='upper center', ncol=5, fontsize=8)
        estilo_ax(ax, con_numero(1, f'Spline cúbico con nodos cada {paso} mes(es) frente a la curva real'),
                  ylabel='Personas infectadas')

        ax = self.ejes['zoom']; ax.cla()
        ta = max(0, dq - 2); tb = min(MESES - 1, dq + 2)
        m = (tf >= ta) & (tf <= tb)
        ax.plot(t[ta:tb + 1], I4[ta:tb + 1], color=C['I'], lw=1.8, ls='--', marker='o', ms=3.5, label='Real (RK4)')
        ax.plot(tf[m], Isp_f[m], color=C['spline'], lw=2.3, label='Spline')
        ax.axvline(dq, color=C['ref'], lw=1.0, ls=':')
        ax.plot(dq, Iest, 'D', color=C['spline'], ms=9, zorder=7, markeredgecolor=C['panel'], label='Estimado')
        ax.plot(dq, Ireal, 'o', color=C['I'], ms=7, zorder=8, markeredgecolor=C['panel'])
        ax.set_xlim(ta, tb)
        dar_espacio(ax, 0.38)
        leyenda(ax, loc='upper right', fontsize=7.6)
        estilo_ax(ax, con_numero(2, f'Zoom en el mes {dq}  (Ea = {ea_pt:,.2f})'), ylabel='Personas infectadas')
        ax.xaxis.set_major_locator(__import__('matplotlib.ticker', fromlist=['MaxNLocator']).MaxNLocator(integer=True))

        ax = self.ejes['err']; ax.cla()
        err_sp = np.abs(I4 - Isp)
        ax.fill_between(t, err_sp, alpha=0.25, color=C['spline'])
        ax.plot(t, err_sp, color=C['spline'], lw=2, marker='o', ms=3.5, label='Error del spline')
        ax.scatter(tn, np.zeros(len(tn)), color=C['nodo'], s=34, zorder=5, label='Nodos (error 0)')
        ax.set_xlim(0, MESES - 1); ax.set_ylim(bottom=0)
        dar_espacio(ax, 0.38)
        leyenda(ax, loc='upper right', fontsize=7.6)
        estilo_ax(ax, con_numero(3, f'Error spline vs RK4  (máx = {np.max(err_sp):,.1f})'), ylabel='Error absoluto')

        ax = self.ejes['info']
        info_rows = []
        for ps in [1, 2, 3, 4]:
            idxT = np.arange(0, MESES, ps)
            if idxT[-1] != MESES - 1:
                idxT = np.append(idxT, MESES - 1)
            csT = CubicSpline(t[idxT].astype(float), I4[idxT], bc_type='natural')
            eT = np.abs(I4 - np.maximum(0, csT(t.astype(float))))
            info_rows.append([f'{ps}', f'{len(idxT)}', num_corto(np.max(eT), 2), num_corto(np.mean(eT), 2)])
        tabla_ax(ax, info_rows, ['Paso', 'Nodos', 'Ea máx', 'Ea prom'], con_numero(4, 'Precisión según nodos'))
        self.datos_resumen = [
            ['Nodos usados', f'{len(tn)} (cada {paso} mes(es))'],
            ['Mes consultado', f'{dq}'],
            ['Valor estimado (spline)', f'{Iest:,.2f} personas'],
            ['Valor real (RK4)', f'{Ireal:,.2f} personas'],
            ['Error absoluto en ese mes', f'{ea_pt:,.3f} personas'],
            ['Error máximo del spline', f'{np.max(err_sp):,.2f} personas'],
        ]
        self._resumen = {'paso': paso, 'dq': dq, 'Iest': Iest, 'Ireal': Ireal, 'ea_pt': ea_pt,
                         'err_max': float(np.max(err_sp))}

    def analisis(self):
        r = self._resumen
        if not r:
            return []
        return [
            dict(n='1', titulo='Spline frente a la curva real',
                 texto=(f"Con nodos cada {r['paso']} mes(es), el spline estima {r['Iest']:,.1f} infectados por "
                        f"COVID-19 en el mes {r['dq']} (rombo), mientras el valor real (RK4) es {r['Ireal']:,.1f} (círculo)."),
                 conclusion=(f"La diferencia de {r['ea_pt']:,.2f} personas indica qué tan bien se puede «adivinar» "
                             f"un mes sin informe oficial.")),
            dict(n='2', titulo='Zoom al mes consultado',
                 texto=f"Acerca la vista justo alrededor del mes {r['dq']}.",
                 conclusion='Permite comparar visualmente el punto estimado contra el real sin la distracción del resto de la curva.'),
            dict(n='3', titulo='Error del spline en todo el rango',
                 texto=(f"El error llega a cero exactamente en los nodos (ahí el spline sí conoce el dato real) y "
                        f"crece en los meses intermedios, hasta un máximo de {r['err_max']:,.1f} personas."),
                 conclusion='La estimación es más confiable cerca de un dato real y menos a mitad de camino entre dos.'),
            dict(n='4', titulo='Precisión según el número de nodos',
                 texto='Compara el error usando distintos espaciados de nodos (cada 1, 2, 3 y 4 meses).',
                 conclusion=('Entre más seguido se tenga un dato real (menos meses de espaciado), menor es el error al '
                             'estimar los meses sin dato.')),
        ]
