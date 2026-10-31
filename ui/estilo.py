import warnings
import matplotlib
from matplotlib.ticker import ScalarFormatter

warnings.filterwarnings('ignore')

C = {
    'bg': '#0D1117', 'panel': '#161B22', 'border': '#30363D',
    'S': '#58A6FF', 'I': '#FF7B72', 'I_eu': '#FFA657', 'R': '#3FB950',
    'spline': '#F0C040', 'nodo': '#56D364', 'deriv': '#BC8CFF',
    'simps': '#E3B341', 'nr_f': '#FF7B72', 'nr_b': '#BC8CFF',
    'txt': '#E6EDF3', 'txt2': '#8B949E', 'fondo_f': '#1C2128', 'acento': '#388BFD',
}


def con_numero(n, titulo):
    return f'{n}.  {titulo}'


def aplicar_tema_matplotlib():
    matplotlib.rcParams.update({
        'figure.facecolor': C['bg'], 'axes.facecolor': C['panel'], 'axes.edgecolor': C['border'],
        'axes.labelcolor': C['txt'], 'xtick.color': C['txt'], 'ytick.color': C['txt'],
        'text.color': C['txt'], 'grid.color': C['border'], 'grid.alpha': 0.6,
        'legend.facecolor': C['panel'], 'legend.edgecolor': C['border'], 'legend.labelcolor': C['txt'],
        'font.family': 'monospace', 'axes.grid': True, 'axes.titlecolor': C['txt'], 'axes.titlesize': 9.8,
    })


def sin_notacion_cientifica(ax):
    if ax.get_xscale() == 'linear':
        fmt_x = ScalarFormatter(useOffset=False)
        fmt_x.set_scientific(False)
        ax.xaxis.set_major_formatter(fmt_x)
        ax.xaxis.offsetText.set_visible(False)
    if ax.get_yscale() == 'linear':
        fmt_y = ScalarFormatter(useOffset=False)
        fmt_y.set_scientific(False)
        ax.yaxis.set_major_formatter(fmt_y)
        ax.yaxis.offsetText.set_visible(False)


def num_corto(x, decimales=1):
    ax_ = abs(x)
    if ax_ >= 1000:
        return f'{x:,.0f}'
    if ax_ >= 1:
        return f'{x:,.{decimales}f}'
    return f'{x:.4f}'.rstrip('0').rstrip('.') or '0'


def estilo_ax(ax, titulo, xlabel='Mes', ylabel=''):
    ax.set_title(titulo, fontsize=9.6, fontweight='bold', color=C['txt'], pad=10)
    ax.set_xlabel(xlabel, fontsize=9.8, color=C['txt'], fontweight='bold', labelpad=6)
    if ylabel:
        ax.set_ylabel(ylabel, fontsize=9.8, color=C['txt'], fontweight='bold', labelpad=6)
    ax.tick_params(labelsize=8.6, colors=C['txt'])
    for spine in ax.spines.values():
        spine.set_color(C['border'])
    sin_notacion_cientifica(ax)


def caja(ax, x, y, titulo, lineas, fs=7.6):
    cuerpo = f"  {titulo}\n" + "\n".join(f"  {l}" for l in lineas)
    ax.text(x, y, cuerpo, transform=ax.transAxes, fontsize=fs, color=C['txt'],
            verticalalignment='top',
            bbox=dict(boxstyle='round,pad=0.5', facecolor=C['fondo_f'],
                      edgecolor=C['acento'], linewidth=1.2, alpha=0.96),
            family='monospace', zorder=10)


def badge(ax, x, y, txt, bg):
    ax.text(x, y, f'  {txt}  ', transform=ax.transAxes, fontsize=9.5,
            color='#0D1117', fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.3', facecolor=bg, edgecolor='none'), zorder=11)


def nota_y(ax, texto, esquina='inferior_derecha'):
    posiciones = {
        'inferior_derecha': dict(x=0.985, y=0.03, ha='right', va='bottom'),
        'inferior_izquierda': dict(x=0.015, y=0.03, ha='left', va='bottom'),
        'superior_izquierda': dict(x=0.015, y=0.97, ha='left', va='top'),
    }
    p = posiciones.get(esquina, posiciones['inferior_derecha'])
    ax.text(p['x'], p['y'], texto, transform=ax.transAxes, ha=p['ha'], va=p['va'],
            fontsize=6.8, color=C['txt2'], style='italic', wrap=True, zorder=12,
            bbox=dict(boxstyle='round,pad=0.32', facecolor=C['fondo_f'], edgecolor=C['border'], alpha=0.92))


def leyenda_combinada(*ejes, fontsize=7.6, loc='best', ncol=1):
    lineas, etiquetas = [], []
    for ax in ejes:
        l, e = ax.get_legend_handles_labels()
        lineas += l; etiquetas += e
    if lineas:
        ejes[0].legend(lineas, etiquetas, fontsize=fontsize, loc=loc, ncol=ncol, framealpha=0.9)


def tabla_ax(ax, rows, cabecera, titulo=''):
    ax.cla()
    ax.axis('off')
    if titulo:
        ax.set_title(titulo, fontsize=9.4, color=C['txt'], fontweight='bold', pad=10)
    t = ax.table(cellText=rows, colLabels=cabecera, cellLoc='center', loc='center',
                 bbox=[0.0, 0.04, 1.0, 0.84])
    t.auto_set_font_size(False)
    t.set_fontsize(8.2)
    for (r, c), cell in t.get_celld().items():
        cell.set_facecolor(C['fondo_f'] if r == 0 else C['panel'])
        cell.set_edgecolor(C['border'])
        cell.set_text_props(color=C['txt'])
        cell.PAD = 0.04
    return t
