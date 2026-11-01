"""Exporta el historial de simulaciones a Excel (con formulas y graficos) o a CSV."""
import csv
from datetime import datetime
from openpyxl import Workbook
from openpyxl.chart import BarChart, LineChart, Reference
from openpyxl.formatting.rule import CellIsRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

FUENTE = 'Times New Roman'
AZUL = '1F3A6E'
GRIS = 'F3F5F8'
BORDE = Side(style='thin', color='9AA3AE')
CAJA = Border(left=BORDE, right=BORDE, top=BORDE, bottom=BORDE)


def _f(negrita=False, tam=11, color='111111', cursiva=False):
    return Font(name=FUENTE, bold=negrita, size=tam, color=color, italic=cursiva)


def _cabecera(ws, fila, titulos, col0=1):
    for j, t in enumerate(titulos):
        c = ws.cell(row=fila, column=col0 + j, value=t)
        c.font = _f(True, 11, 'FFFFFF')
        c.fill = PatternFill('solid', fgColor=AZUL)
        c.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
        c.border = CAJA
    ws.row_dimensions[fila].height = 32


def _celda(ws, fila, col, valor, formato=None, centro=True, zebra=False, negrita=False):
    c = ws.cell(row=fila, column=col, value=valor)
    c.font = _f(negrita)
    c.border = CAJA
    c.alignment = Alignment(horizontal='center' if centro else 'left', vertical='center')
    if formato:
        c.number_format = formato
    if zebra:
        c.fill = PatternFill('solid', fgColor=GRIS)
    return c


def _titulo(ws, texto, subtitulo, ancho_cols):
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=ancho_cols)
    ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=ancho_cols)
    ws['A1'] = texto
    ws['A1'].font = _f(True, 16, AZUL)
    ws['A2'] = subtitulo
    ws['A2'].font = _f(False, 10, '555555', True)
    ws.row_dimensions[1].height = 26


def _anchos(ws, anchos):
    for i, a in enumerate(anchos, start=1):
        ws.column_dimensions[get_column_letter(i)].width = a


def exportar_excel(base, ruta):
    sims = base.listar_simulaciones()
    serie = base.serie_completa()
    por_mes = base.promedio_por_mes()
    ahora = datetime.now().strftime('%d/%m/%Y %H:%M')
    sub = f'PandemiaSimulador — COVID-19 en el DMQ (Quito, Ecuador) · Generado el {ahora}'

    wb = Workbook()
    ws_res = wb.active
    ws_res.title = 'Resumen'
    ws_sim = wb.create_sheet('Simulaciones')
    ws_ser = wb.create_sheet('Series mensuales')
    ws_est = wb.create_sheet('Estadísticas por mes')
    for ws in (ws_res, ws_sim, ws_ser, ws_est):
        ws.sheet_view.showGridLines = False

    # ------------------------------------------------------------ Simulaciones
    _titulo(ws_sim, 'Historial de simulaciones', sub, 14)
    cab = ['ID', 'Fecha', 'β', 'γ', 'N', 'I0', 'Meses', 'R0', 'Estado', 'Pico de infectados', 'Mes del pico',
           'S final', 'R final', 'Tasa de ataque (%)']
    _cabecera(ws_sim, 4, cab)
    for k, s in enumerate(sims):
        r = 5 + k
        z = k % 2 == 1
        vals = [(s['id'], '0'), (s['fecha'], None), (s['beta'], '0.000'), (s['gamma'], '0.000'),
                (s['n'], '#,##0'), (s['i0'], '#,##0'), (s['meses'], '0')]
        for j, (v, fmt) in enumerate(vals, start=1):
            _celda(ws_sim, r, j, v, fmt, zebra=z)
        _celda(ws_sim, r, 8, f'=C{r}/D{r}', '0.000', zebra=z)                      # R0 = β/γ
        _celda(ws_sim, r, 9, f'=IF(H{r}>1,"EPIDEMIA","CONTROLADO")', None, zebra=z, negrita=True)
        _celda(ws_sim, r, 10, s['pico'], '#,##0.0', zebra=z)
        _celda(ws_sim, r, 11, s['mes_pico'], '0', zebra=z)
        _celda(ws_sim, r, 12, s['s_final'], '#,##0', zebra=z)
        _celda(ws_sim, r, 13, s['r_final'], '#,##0', zebra=z)
        _celda(ws_sim, r, 14, f'=(E{r}-L{r})/E{r}*100', '0.00', zebra=z)           # tasa de ataque
    ult = 4 + len(sims)
    if sims:
        ws_sim.auto_filter.ref = f'A4:N{ult}'
        rng = f'I5:I{ult}'
        ws_sim.conditional_formatting.add(rng, CellIsRule(operator='equal', formula=['"EPIDEMIA"'],
                                          font=Font(name=FUENTE, bold=True, color='9C0006'),
                                          fill=PatternFill('solid', bgColor='FFC7CE')))
        ws_sim.conditional_formatting.add(rng, CellIsRule(operator='equal', formula=['"CONTROLADO"'],
                                          font=Font(name=FUENTE, bold=True, color='006100'),
                                          fill=PatternFill('solid', bgColor='C6EFCE')))
    ws_sim.freeze_panes = 'C5'
    _anchos(ws_sim, [6, 20, 9, 9, 12, 9, 8, 9, 14, 16, 12, 13, 12, 16])

    # --------------------------------------------------------- Series mensuales
    _titulo(ws_ser, 'Series mensuales de cada simulación', sub, 9)
    _cabecera(ws_ser, 4, ['ID simulación', 'Mes', 'S (RK4)', 'I (RK4)', 'R (RK4)', 'I (Euler)',
                          'Error absoluto |RK4 − Euler|', 'Error relativo (%)'])
    for k, f in enumerate(serie):
        r = 5 + k
        z = k % 2 == 1
        _celda(ws_ser, r, 1, f['simulacion_id'], '0', zebra=z)
        _celda(ws_ser, r, 2, f['mes'], '0', zebra=z)
        _celda(ws_ser, r, 3, f['s'], '#,##0', zebra=z)
        _celda(ws_ser, r, 4, f['i'], '#,##0.00', zebra=z)
        _celda(ws_ser, r, 5, f['r'], '#,##0', zebra=z)
        _celda(ws_ser, r, 6, f['i_euler'], '#,##0.00', zebra=z)
        _celda(ws_ser, r, 7, f'=ABS(D{r}-F{r})', '#,##0.00', zebra=z)
        _celda(ws_ser, r, 8, f'=IF(D{r}>0.1,G{r}/D{r}*100,0)', '0.00', zebra=z)
    ult_s = 4 + len(serie)
    if serie:
        ws_ser.auto_filter.ref = f'A4:H{ult_s}'
    ws_ser.freeze_panes = 'A5'
    _anchos(ws_ser, [14, 8, 14, 12, 12, 12, 22, 18])

    # ------------------------------------------------- Estadísticas por mes
    _titulo(ws_est, 'Estadísticas por mes (todas las simulaciones)', sub, 8)
    _cabecera(ws_est, 4, ['Mes', 'Infectados promedio', 'Infectados mínimo', 'Infectados máximo',
                          'S promedio', 'R promedio', 'Error Euler promedio'])
    sh = "'Series mensuales'"
    for k, m in enumerate(por_mes):
        r = 5 + k
        z = k % 2 == 1
        _celda(ws_est, r, 1, m['mes'], '0', zebra=z)
        _celda(ws_est, r, 2, f'=AVERAGEIF({sh}!$B$5:$B${ult_s},A{r},{sh}!$D$5:$D${ult_s})', '#,##0.00', zebra=z)
        _celda(ws_est, r, 3, f'=_xlfn.MINIFS({sh}!$D$5:$D${ult_s},{sh}!$B$5:$B${ult_s},A{r})', '#,##0.00', zebra=z)
        _celda(ws_est, r, 4, f'=_xlfn.MAXIFS({sh}!$D$5:$D${ult_s},{sh}!$B$5:$B${ult_s},A{r})', '#,##0.00', zebra=z)
        _celda(ws_est, r, 5, f'=AVERAGEIF({sh}!$B$5:$B${ult_s},A{r},{sh}!$C$5:$C${ult_s})', '#,##0', zebra=z)
        _celda(ws_est, r, 6, f'=AVERAGEIF({sh}!$B$5:$B${ult_s},A{r},{sh}!$E$5:$E${ult_s})', '#,##0', zebra=z)
        _celda(ws_est, r, 7, f'=AVERAGEIF({sh}!$B$5:$B${ult_s},A{r},{sh}!$G$5:$G${ult_s})', '#,##0.00', zebra=z)
    ult_m = 4 + len(por_mes)
    _anchos(ws_est, [8, 20, 18, 18, 16, 16, 20])
    if por_mes:
        g = LineChart()
        g.title = 'Infectados por mes: promedio, mínimo y máximo'
        g.y_axis.title = 'Personas infectadas'
        g.x_axis.title = 'Mes'
        g.height, g.width = 9, 20
        g.add_data(Reference(ws_est, min_col=2, max_col=4, min_row=4, max_row=ult_m), titles_from_data=True)
        g.set_categories(Reference(ws_est, min_col=1, min_row=5, max_row=ult_m))
        g.x_axis.delete = False
        g.y_axis.delete = False
        ws_est.add_chart(g, f'I4')

    # ------------------------------------------------------------------ Resumen
    _titulo(ws_res, 'Resumen del historial de simulaciones', sub, 6)
    _cabecera(ws_res, 4, ['Indicador', 'Valor'])
    n = len(sims)
    sim = "Simulaciones"
    kpis = [
        ('Simulaciones guardadas', f'=COUNT({sim}!A5:A{max(ult, 5)})', '0'),
        ('Simulaciones controladas (R0 < 1)', f'=COUNTIF({sim}!I5:I{max(ult, 5)},"CONTROLADO")', '0'),
        ('Simulaciones en epidemia (R0 > 1)', f'=COUNTIF({sim}!I5:I{max(ult, 5)},"EPIDEMIA")', '0'),
        ('R0 promedio', f'=IFERROR(AVERAGE({sim}!H5:H{max(ult, 5)}),0)', '0.000'),
        ('Pico promedio de infectados', f'=IFERROR(AVERAGE({sim}!J5:J{max(ult, 5)}),0)', '#,##0.0'),
        ('Pico máximo de infectados', f'=IFERROR(MAX({sim}!J5:J{max(ult, 5)}),0)', '#,##0.0'),
        ('Tasa de ataque promedio (%)', f'=IFERROR(AVERAGE({sim}!N5:N{max(ult, 5)}),0)', '0.00'),
    ]
    for k, (nombre, formula, fmt) in enumerate(kpis):
        r = 5 + k
        _celda(ws_res, r, 1, nombre, None, centro=False, zebra=k % 2 == 1)
        _celda(ws_res, r, 2, formula, fmt, zebra=k % 2 == 1, negrita=True)
    fila = 5 + len(kpis) + 2
    ws_res.cell(row=fila - 1, column=1, value='Comparación por estado de la epidemia').font = _f(True, 12, AZUL)
    _cabecera(ws_res, fila, ['Estado', 'Simulaciones', 'R0 promedio', 'Pico promedio', 'Tasa de ataque prom. (%)'])
    for k, est in enumerate(('CONTROLADO', 'EPIDEMIA')):
        r = fila + 1 + k
        rg = lambda col: f'{sim}!{col}5:{col}{max(ult, 5)}'
        _celda(ws_res, r, 1, est, None, zebra=k % 2 == 1, negrita=True)
        _celda(ws_res, r, 2, f'=COUNTIF({rg("I")},A{r})', '0', zebra=k % 2 == 1)
        _celda(ws_res, r, 3, f'=IFERROR(AVERAGEIF({rg("I")},A{r},{rg("H")}),0)', '0.000', zebra=k % 2 == 1)
        _celda(ws_res, r, 4, f'=IFERROR(AVERAGEIF({rg("I")},A{r},{rg("J")}),0)', '#,##0.0', zebra=k % 2 == 1)
        _celda(ws_res, r, 5, f'=IFERROR(AVERAGEIF({rg("I")},A{r},{rg("N")}),0)', '0.00', zebra=k % 2 == 1)
    _anchos(ws_res, [38, 18, 16, 18, 24, 4])
    if n:
        b = BarChart()
        b.type = 'col'
        b.title = 'Pico de infectados por simulación'
        b.y_axis.title = 'Personas infectadas'
        b.x_axis.title = 'ID de simulación'
        b.height, b.width = 9, 18
        b.add_data(Reference(ws_sim, min_col=10, min_row=4, max_row=ult), titles_from_data=True)
        b.set_categories(Reference(ws_sim, min_col=1, min_row=5, max_row=ult))
        b.legend = None
        b.x_axis.delete = False
        b.y_axis.delete = False
        ws_res.add_chart(b, f'A{fila + 5}')
    nota = ws_res.cell(row=fila + 4, column=1,
                       value='Fuente de datos base: Informe Quincenal COVID-19, Secretaría de Salud del DMQ (noviembre 2021).')
    nota.font = _f(False, 9, '555555', True)

    wb.calculation.fullCalcOnLoad = True
    wb.save(ruta)


def exportar_csv(base, ruta):
    sims = base.listar_simulaciones()
    with open(ruta, 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.writer(f, delimiter=';')
        w.writerow(['id', 'fecha', 'beta', 'gamma', 'n', 'i0', 'meses', 'r0', 'estado', 'pico', 'mes_pico',
                    's_final', 'r_final', 'tasa_ataque', 'error_euler_max'])
        for s in sims:
            w.writerow([s['id'], s['fecha'], s['beta'], s['gamma'], s['n'], s['i0'], s['meses'], round(s['r0'], 4),
                        s['estado'], round(s['pico'], 2), s['mes_pico'], round(s['s_final'], 2),
                        round(s['r_final'], 2), round(s['tasa_ataque'], 4), round(s['error_euler_max'], 4)])
