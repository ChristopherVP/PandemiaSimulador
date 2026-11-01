import warnings
from contextlib import contextmanager
import matplotlib
from matplotlib.ticker import ScalarFormatter, FuncFormatter

warnings.filterwarnings('ignore')

TEMA_OSCURO = {
    'bg': '#0D1117', 'panel': '#161B22', 'border': '#30363D',
    'S': '#58A6FF', 'I': '#FF7B72', 'I_eu': '#FFA657', 'R': '#3FB950',
    'spline': '#F0C040', 'nodo': '#56D364', 'deriv': '#BC8CFF',
    'simps': '#E3B341', 'nr_f': '#FF7B72', 'nr_b': '#BC8CFF',
    'txt': '#E6EDF3', 'txt2': '#8B949E', 'fondo_f': '#1C2128', 'acento': '#388BFD',
    'ref': '#C9D1D9', 'ok': '#2EA043', 'mal': '#DA3633', 'grid': '#30363D',
    'fila_a': '#161B22', 'fila_b': '#1C2128', 'cab': '#2D333B',
    'sobre_color': '#0D1117',
}

TEMA_CLARO = {
    'bg': '#FFFFFF', 'panel': '#FFFFFF', 'border': '#8C959F',
    'S': '#1F5FBF', 'I': '#C62828', 'I_eu': '#E67E22', 'R': '#2E7D32',
    'spline': '#B07D00', 'nodo': '#2E7D32', 'deriv': '#6A32B8',
    'simps': '#B07D00', 'nr_f': '#C62828', 'nr_b': '#6A32B8',
    'txt': '#111111', 'txt2': '#4A4F55', 'fondo_f': '#F3F5F8', 'acento': '#1F4E9C',
    'ref': '#444444', 'ok': '#1B7F37', 'mal': '#B3261E', 'grid': '#D0D5DB',
    'fila_a': '#FFFFFF', 'fila_b': '#F3F5F8', 'cab': '#DDE3EA',
    'sobre_color': '#FFFFFF',
}

C = dict(TEMA_OSCURO)

FUENTES_SERIF = ['Times New Roman', 'Times', 'Liberation Serif', 'Nimbus Roman',
                 'TeX Gyre Termes', 'DejaVu Serif']


def _rc(tema, serif):
    base = {
        'figure.facecolor': tema['bg'], 'axes.facecolor': tema['panel'], 'axes.edgecolor': tema['border'],
        'axes.labelcolor': tema['txt'], 'xtick.color': tema['txt'], 'ytick.color': tema['txt'],
        'text.color': tema['txt'], 'grid.color': tema['grid'], 'grid.alpha': 0.55, 'grid.linewidth': 0.6,
        'legend.facecolor': tema['panel'], 'legend.edgecolor': tema['border'], 'legend.labelcolor': tema['txt'],
        'axes.grid': True, 'axes.titlecolor': tema['txt'], 'axes.titlesize': 10,
        'axes.spines.top': False, 'axes.spines.right': False,
        'savefig.facecolor': tema['bg'], 'axes.unicode_minus': True,
        'mathtext.default': 'regular', 'pdf.fonttype': 42,
    }
    if serif:
        base.update({'font.family': 'serif', 'font.serif': FUENTES_SERIF, 'mathtext.fontset': 'stix'})
    else:
        base.update({'font.family': 'sans-serif',
                     'font.sans-serif': ['Segoe UI', 'DejaVu Sans', 'Arial']})
    return base


def aplicar_tema_matplotlib():
    C.clear()
    C.update(TEMA_OSCURO)
    matplotlib.rcParams.update(_rc(TEMA_OSCURO, serif=False))


@contextmanager
def tema_claro():
    """Dentro del bloque todo se dibuja con fondo blanco y Times New Roman (para los PDF)."""
    copia = dict(C)
    C.clear()
    C.update(TEMA_CLARO)
    try:
        with matplotlib.rc_context(_rc(TEMA_CLARO, serif=True)):
            yield
    finally:
        C.clear()
        C.update(copia)


def con_numero(n, titulo):
    return f'{n}.  {titulo}'


def sin_notacion_cientifica(ax):
    sep = FuncFormatter(lambda v, _: f'{v:,.0f}' if abs(v) >= 1000 else (f'{v:.0f}' if float(v).is_integer() else f'{v:g}'))
    if ax.get_xscale() == 'linear':
        fmt_x = ScalarFormatter(useOffset=False)
        fmt_x.set_scientific(False)
        ax.xaxis.set_major_formatter(fmt_x)
        ax.xaxis.offsetText.set_visible(False)
    if ax.get_yscale() == 'linear':
        ax.yaxis.set_major_formatter(sep)
        ax.yaxis.offsetText.set_visible(False)


def num_corto(x, decimales=1):
    ax_ = abs(x)
    if ax_ >= 1000:
        return f'{x:,.0f}'
    if ax_ >= 1:
        return f'{x:,.{decimales}f}'
    return f'{x:.4f}'.rstrip('0').rstrip('.') or '0'


def estilo_ax(ax, titulo, xlabel='Mes', ylabel='', tam_titulo=10):
    ax.set_title(titulo, fontsize=tam_titulo, fontweight='bold', color=C['txt'], pad=9, loc='left')
    ax.set_xlabel(xlabel, fontsize=9, color=C['txt'], labelpad=4)
    if ylabel:
        ax.set_ylabel(ylabel, fontsize=9, color=C['txt'], labelpad=5)
    ax.tick_params(labelsize=8.4, colors=C['txt'], length=3)
    for nombre in ('left', 'bottom'):
        ax.spines[nombre].set_color(C['border'])
    ax.grid(True, color=C['grid'], alpha=0.55, lw=0.6)
    ax.set_axisbelow(True)
    sin_notacion_cientifica(ax)


def eje_derecho(ax2, ylabel, color):
    """cla() en un eje gemelo reinicia la posicion de la etiqueta: se vuelve a poner a la derecha."""
    ax2.yaxis.tick_right()
    ax2.yaxis.set_label_position('right')
    ax2.spines['right'].set_visible(True)
    ax2.spines['right'].set_color(color)
    ax2.spines['top'].set_visible(False)
    ax2.grid(False)
    ax2.set_ylabel(ylabel, fontsize=9, color=color, labelpad=6)
    ax2.tick_params(axis='y', labelsize=8.4, colors=color, length=3)
    sin_notacion_cientifica(ax2)


def dar_espacio(ax, frac=0.26, log=False):
    """Agrega espacio libre arriba del grafico para que la leyenda no tape las curvas."""
    lo, hi = ax.get_ylim()
    if log or ax.get_yscale() == 'log':
        ax.set_ylim(lo, hi * (hi / lo) ** (frac / (1 - frac)))
    else:
        ax.set_ylim(lo, lo + (hi - lo) / (1 - frac))


def leyenda(ax, loc='upper right', ncol=1, fontsize=8, ejes_extra=()):
    lineas, etiquetas = [], []
    for a in (ax, *ejes_extra):
        l, e = a.get_legend_handles_labels()
        lineas += l
        etiquetas += e
    if not lineas:
        return None
    lg = ax.legend(lineas, etiquetas, loc=loc, ncol=ncol, fontsize=fontsize, frameon=True,
                   framealpha=0.95, borderpad=0.5, handlelength=2.0, columnspacing=1.4, labelspacing=0.4)
    lg.get_frame().set_edgecolor(C['border'])
    lg.get_frame().set_linewidth(0.8)
    lg.set_zorder(20)
    return lg


def leyenda_combinada(*ejes, fontsize=8, loc='best', ncol=1):
    return leyenda(ejes[0], loc=loc, ncol=ncol, fontsize=fontsize, ejes_extra=ejes[1:])


def badge_figura(fig, txt, bg):
    """Etiqueta de estado en la esquina superior derecha de toda la figura."""
    for tx in list(fig.texts):
        tx.remove()
    fig.text(0.97, 0.985, f' {txt} ', fontsize=9.5, color='#FFFFFF', fontweight='bold', ha='right', va='top',
             bbox=dict(boxstyle='round,pad=0.3', facecolor=bg, edgecolor='none'), zorder=11)


def badge(ax, txt, bg, x=1.0, y=1.03):
    """Etiqueta de estado fuera del area de datos (alineada con el titulo), sin tapar nada."""
    ax.text(x, y, f' {txt} ', transform=ax.transAxes, fontsize=9, color='#FFFFFF', fontweight='bold',
            ha='right', va='bottom', zorder=11,
            bbox=dict(boxstyle='round,pad=0.28', facecolor=bg, edgecolor='none'))


def anotar(ax, x, y, texto, color, xmax, dy=0.0, fs=8.6):
    """Anotacion con flecha que se coloca hacia el lado con mas espacio."""
    lado = -1 if x > 0.6 * xmax else 1
    ax.annotate(texto, xy=(x, y), xytext=(34 * lado, 30 + dy), textcoords='offset points',
                ha='left' if lado > 0 else 'right', va='bottom', fontsize=fs, color=color, fontweight='bold',
                arrowprops=dict(arrowstyle='-|>', color=color, lw=1.2, shrinkA=2, shrinkB=3),
                bbox=dict(boxstyle='round,pad=0.3', facecolor=C['panel'], edgecolor=color, lw=0.9), zorder=15)


def nota_y(ax, texto, esquina='inferior_derecha'):
    """Se mantiene por compatibilidad: las notas ya no se dibujan encima del grafico (la explicacion
    esta en la teoria y en el analisis), asi no se encima con curvas ni leyendas."""
    return None


def caja(ax, x, y, titulo, lineas, fs=7.6):
    cuerpo = f"{titulo}\n" + "\n".join(lineas)
    ax.text(x, y, cuerpo, transform=ax.transAxes, fontsize=fs, color=C['txt'], va='top',
            bbox=dict(boxstyle='round,pad=0.5', facecolor=C['fondo_f'], edgecolor=C['acento'], lw=1.0),
            zorder=10)


def tabla_ax(ax, rows, cabecera, titulo='', alineacion=None, resaltar=None, bbox=None, fs_max=9.6):
    """Tabla legible: ancho de columna segun su contenido, tamano de letra segun el espacio disponible,
    filas alternadas y encabezado marcado. `alineacion`: lista 'l'/'c'/'r' por columna.
    `resaltar`: {(fila, col): color} para colorear texto de celdas (fila 0 = primera fila de datos)."""
    ax.cla()
    ax.axis('off')
    if titulo:
        ax.set_title(titulo, fontsize=10, color=C['txt'], fontweight='bold', pad=9, loc='left')
    ncol = len(cabecera)
    nfil = len(rows)
    pesos = []
    for j in range(ncol):
        largo = max([len(str(cabecera[j]))] + [len(str(r[j])) for r in rows])
        if resaltar and any(c == j for (_, c) in resaltar):
            largo *= 1.25
        pesos.append(max(largo, 4) + 2.2)
    tot = float(sum(pesos))
    anchos = [p / tot for p in pesos]

    ext = ax.get_window_extent()
    dpi = ax.figure.dpi
    ancho_pt = ext.width * 72.0 / dpi
    alto_pt = ext.height * 72.0 / dpi
    fs_ancho = ancho_pt / (tot * (0.44 if C['bg'] == '#FFFFFF' else 0.52))
    alto_tabla = alto_pt * (0.92 if bbox is None else bbox[3])
    fs_alto = (alto_tabla / (nfil + 1)) / 1.5
    fs = max(5.6, min(fs_max, fs_ancho, fs_alto))

    if bbox is None:
        alto_rel = min(0.94, ((nfil + 1) * fs * 1.5) / alto_pt)
        bbox = [0.0, 0.94 - alto_rel, 1.0, alto_rel]
    t = ax.table(cellText=[[str(v) for v in r] for r in rows], colLabels=cabecera, colWidths=anchos,
                 cellLoc='center', loc='center', bbox=bbox)
    t.auto_set_font_size(False)
    t.set_fontsize(fs)
    alineacion = alineacion or ['c'] * ncol
    mapa = {'l': 'left', 'c': 'center', 'r': 'right'}
    resaltar = resaltar or {}
    for (r, c), cell in t.get_celld().items():
        cell.set_edgecolor(C['border'])
        cell.set_linewidth(0.5)
        if r == 0:
            cell.set_facecolor(C['cab'])
            cell.set_text_props(color=C['txt'], fontweight='bold')
            cell.get_text().set_ha('center')
        else:
            cell.set_facecolor(C['fila_a'] if r % 2 else C['fila_b'])
            color = resaltar.get((r - 1, c), C['txt'])
            cell.set_text_props(color=color, fontweight='bold' if (r - 1, c) in resaltar else 'normal')
            ha = mapa[alineacion[c]]
            cell.get_text().set_ha(ha)
            if ha == 'left':
                cell.get_text().set_x(0.04)
            elif ha == 'right':
                cell.get_text().set_x(0.96)
        cell.PAD = 0.04
    t.bbox_usado = bbox
    return t
