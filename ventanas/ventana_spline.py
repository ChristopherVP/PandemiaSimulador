import numpy as np
import matplotlib.gridspec as gridspec
from scipy.interpolate import CubicSpline
from ui.ventana_base import PanelTema
from ui.estilo import C, estilo_ax, nota_y, con_numero, num_corto
from ui.componentes import crear_slider
from core.estado_global import MESES
from core.metodos_numericos import rk4_sir


class VentanaSpline(PanelTema):
    ICONO = '③'
    TITULO = 'Estimación de Meses sin Datos'
    CLAVE = 'spline'

    def crear_ejes(self):
        gs = gridspec.GridSpec(2, 3, figure=self.fig, top=0.88, bottom=0.10,
                                hspace=0.70, wspace=0.35, left=0.06, right=0.97)
        ax_main = self.fig.add_subplot(gs[0, :])
        ax_zoom = self.fig.add_subplot(gs[1, 0])
        ax_err = self.fig.add_subplot(gs[1, 1])
        ax_info = self.fig.add_subplot(gs[1, 2])
        return dict(main=ax_main, zoom=ax_zoom, err=ax_err, info=ax_info)

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
        dq = int(self.controles.get('dia', 5))
        dq = max(1, min(MESES - 2, dq))

        idx = np.arange(0, MESES, paso)
        if idx[-1] != MESES - 1:
            idx = np.append(idx, MESES - 1)
        tn = t[idx].astype(float); In = I4[idx]
        cs = CubicSpline(tn, In, bc_type='natural')
        Isp = np.maximum(0, cs(t.astype(float)))
        Iest = float(np.maximum(0, cs(float(dq))))
        Ireal = float(I4[dq])
        ea_pt = abs(Ireal - Iest)

        ax_main = self.ejes['main']; ax_main.cla()
        ax_main.plot(t, I4, color=C['I'], lw=1.8, ls='--', alpha=0.55, label='RK4 (real)')
        ax_main.plot(t, Isp, color=C['spline'], lw=2.6, label=f'Spline cúbico ({len(tn)} nodos)')
        ax_main.scatter(tn, In, color=C['nodo'], s=55, zorder=6, label='Nodos conocidos')
        ax_main.axvline(dq, color='white', lw=1.2, ls=':', alpha=0.6)
        ax_main.plot(dq, Iest, 'D', color=C['spline'], ms=10, zorder=8, label=f'Estimado mes {dq}: {Iest:.1f}')
        ax_main.plot(dq, Ireal, 'o', color=C['I'], ms=8, zorder=8, label=f'Real mes {dq}: {Ireal:.1f}')
        ax_main.set_xlim(0, MESES - 1); ax_main.set_ylim(bottom=0)
        ax_main.legend(fontsize=8, ncol=3, loc='upper right')
        estilo_ax(ax_main, con_numero(1, f'Spline cúbico — {len(tn)} nodos cada {paso} meses | mes {dq}: est={Iest:.1f} real={Ireal:.1f}'),
                  ylabel='Personas infectadas')
        nota_y(ax_main, 'Personas infectadas: reales (RK4)\nvs estimadas por el spline')

        ax_zoom = self.ejes['zoom']; ax_zoom.cla()
        m = 2; ta = max(0, dq - m); tb = min(MESES, dq + m)
        ax_zoom.plot(t[ta:tb], I4[ta:tb], color=C['I'], lw=1.8, ls='--', alpha=0.7, label='Real (RK4)')
        ax_zoom.plot(t[ta:tb], Isp[ta:tb], color=C['spline'], lw=2.3, label='Spline')
        ax_zoom.axvline(dq, color='white', lw=1.2, ls=':')
        ax_zoom.plot(dq, Iest, 'D', color=C['spline'], ms=11, zorder=7)
        ax_zoom.plot(dq, Ireal, 'o', color=C['I'], ms=9, zorder=7)
        ax_zoom.legend(fontsize=8)
        estilo_ax(ax_zoom, con_numero(2, f'Zoom mes {dq} | Ea={ea_pt:.3f}'), ylabel='Personas infectadas')
        nota_y(ax_zoom, 'Acercamiento al mes\nconsultado con el slider')

        ax_err = self.ejes['err']; ax_err.cla()
        err_sp = np.abs(I4 - Isp)
        ax_err.fill_between(t, err_sp, alpha=0.3, color=C['spline'])
        ax_err.plot(t, err_sp, color=C['spline'], lw=2)
        ax_err.scatter(tn, np.zeros(len(tn)), color=C['nodo'], s=32, zorder=5, label='Nodos (error=0)')
        ax_err.legend(fontsize=8); ax_err.set_xlim(0, MESES - 1); ax_err.set_ylim(bottom=0)
        estilo_ax(ax_err, con_numero(3, f'Error spline vs RK4 | máx={np.max(err_sp):.2f}'), ylabel='Error absoluto')
        nota_y(ax_err, 'Qué tan lejos está el spline\ndel valor real en cada mes')

        ax_info = self.ejes['info']; ax_info.cla(); ax_info.axis('off')
        pasos_test = [1, 2, 3, 4]
        info_rows = []
        for ps in pasos_test:
            idxT = np.arange(0, MESES, ps)
            if idxT[-1] != MESES - 1:
                idxT = np.append(idxT, MESES - 1)
            csT = CubicSpline(t[idxT].astype(float), I4[idxT], bc_type='natural')
            IspT = np.maximum(0, csT(t.astype(float)))
            eT = np.abs(I4 - IspT)
            info_rows.append([f'{ps} mes(es)', f'{len(idxT)}', num_corto(np.max(eT), 2), num_corto(np.mean(eT), 2)])
        t_tab = ax_info.table(cellText=info_rows, colLabels=['Paso', 'Nodos', 'Ea máx', 'Ea prom'],
                              cellLoc='center', loc='center', bbox=[0.0, 0.38, 1.0, 0.46])
        t_tab.auto_set_font_size(False); t_tab.set_fontsize(8.2)
        for (rr, cc), cell in t_tab.get_celld().items():
            cell.set_facecolor(C['fondo_f'] if rr == 0 else C['panel'])
            cell.set_edgecolor(C['border'])
            cell.set_text_props(color=C['txt'])
        ax_info.set_title(con_numero(4, 'Precisión vs nodos'), fontsize=9.6, color=C['txt'], pad=10, fontweight='bold')
        ax_info.text(0.5, 0.30,
            'Evita el fenómeno de Runge.\nÚtil para estimar infectados\nde COVID-19 en meses sin datos.',
            ha='center', va='top', transform=ax_info.transAxes, fontsize=8.4, color=C['txt2'],
            bbox=dict(boxstyle='round', facecolor=C['fondo_f'], edgecolor=C['acento'], lw=1.1))

        self._resumen = {'paso': paso, 'dq': dq, 'Iest': Iest, 'Ireal': Ireal, 'ea_pt': ea_pt}

    def interpretar_resultados(self):
        r = self._resumen
        if not r:
            return ''
        return (
            f"🔵 GRÁFICA ➊ (spline vs curva real): con nodos cada {r['paso']} mes(es), el spline estima "
            f"{r['Iest']:.1f} infectados por COVID-19 en el mes {r['dq']} (rombo), mientras el valor real "
            f"(RK4) es {r['Ireal']:.1f} (círculo).\n"
            f"→ Conclusión: la diferencia de {r['ea_pt']:.2f} personas indica qué tan bien se puede "
            f"\"adivinar\" un mes sin informe oficial.\n\n"
            f"🔵 GRÁFICA ➋ (zoom al mes consultado): acerca la vista justo alrededor del mes {r['dq']}.\n"
            f"→ Conclusión: permite comparar visualmente el punto estimado contra el real sin la "
            f"distracción del resto de la curva.\n\n"
            f"🔵 GRÁFICA ➌ (error del spline en todo el rango): el error llega a cero exactamente en los "
            f"nodos (porque ahí el spline sí conoce el dato real) y crece en los meses intermedios.\n"
            f"→ Conclusión: la estimación es más confiable cerca de un dato real y menos a mitad de camino "
            f"entre dos.\n\n"
            f"🔵 GRÁFICA ➍ (precisión según nº de nodos): compara el error usando distintos espaciados de "
            f"nodos.\n"
            f"→ Conclusión: entre más seguido se tenga un dato real (menos meses de espaciado), menor es el "
            f"error al estimar los meses sin dato."
        )
