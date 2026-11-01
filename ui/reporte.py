"""Generador de reportes PDF: fondo blanco, tipografia Times New Roman, formato de documento
profesional (hoja de graficas en horizontal + hojas de resumen y analisis en vertical)."""
import datetime
import re
from matplotlib.figure import Figure
from matplotlib.gridspec import GridSpec
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.font_manager import FontProperties
from matplotlib.patches import Rectangle
from ui.estilo import tema_claro
from core.estado_global import FUENTE_PDF_NOMBRE, FUENTE_PDF_URL

A4_V = (8.27, 11.69)
A4_H = (11.69, 8.27)
NEGRO = '#111111'
GRIS = '#555555'
AZUL = '#1F3A6E'
LINEA = '#9AA3AE'
CAB = '#DDE3EA'
ZEBRA = '#F3F5F8'
NOMBRE_APP = 'PandemiaSimulador — COVID-19 en el Distrito Metropolitano de Quito (DMQ)'

MESES_ES = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto',
            'septiembre', 'octubre', 'noviembre', 'diciembre']

_REEMPLAZOS = {
    '➊': '(1)', '➋': '(2)', '➌': '(3)', '➍': '(4)',
    '①': '1', '②': '2', '③': '3', '④': '4', '⑤': '5', '⑥': '6',
    '🔵': '', '📖': '', '🔎': '', '🦠': '', '💾': '', '🎛': '', '✓': '', '⚠': '', '▶': '',
    '₀': '0', '₁': '1', '₂': '2', 'ₙ': 'n',
}


def limpiar(texto):
    for k, v in _REEMPLAZOS.items():
        texto = texto.replace(k, v)
    return re.sub(r'[ \t]{2,}', ' ', texto).strip()


def fecha_hoy():
    h = datetime.date.today()
    return f'{h.day} de {MESES_ES[h.month - 1]} de {h.year}'


def titulo_bonito(encabezado):
    """'¿QUÉ MUESTRA ESTA GRÁFICA?' -> '¿Qué muestra esta gráfica?'"""
    t = encabezado.strip().lower()
    for i, ch in enumerate(t):
        if ch.isalpha():
            t = t[:i] + ch.upper() + t[i + 1:]
            break
    return t.replace('quito', 'Quito').replace('ventana', 'sección').replace('dmq', 'DMQ')


def partir_explicacion(explicacion):
    """Divide el texto teorico en bloques (encabezado, parrafo)."""
    bloques = []
    for bloque in explicacion.strip().split('\n\n'):
        lineas = bloque.strip().split('\n', 1)
        if len(lineas) == 2 and lineas[0].strip() == lineas[0].strip().upper() and len(lineas[0]) < 80:
            bloques.append((titulo_bonito(lineas[0]), limpiar(lineas[1].replace('\n', ' '))))
        else:
            bloques.append(('', limpiar(bloque.replace('\n', ' '))))
    return bloques


class Maquetador:
    """Dibuja texto, tablas y encabezados sobre hojas blancas (coordenadas en pulgadas)."""

    def __init__(self, tam, cabecera, margen=0.85, sup=0.95, inf=0.95):
        self.tam = tam
        self.W, self.H = tam
        self.m = margen
        self.sup = sup
        self.inf = inf
        self.cabecera = cabecera
        self.paginas = []
        self._r = FigureCanvasAgg(Figure(dpi=100)).get_renderer()
        self.nueva()

    # ----------------------------------------------------------------- paginas
    def nueva(self):
        fig = Figure(figsize=self.tam, dpi=100, facecolor='white')
        ax = fig.add_axes([0, 0, 1, 1])
        ax.set_xlim(0, self.W)
        ax.set_ylim(self.H, 0)
        ax.axis('off')
        self.paginas.append(fig)
        self.fig, self.ax = fig, ax
        self.y = self.sup
        if self.cabecera:
            ax.text(self.m, 0.52, self.cabecera, fontsize=8.5, color=GRIS, ha='left', va='center',
                    fontproperties=self._fp(8.5, estilo='italic'))
            ax.text(self.W - self.m, 0.52, fecha_hoy(), fontsize=8.5, color=GRIS, ha='right', va='center',
                    fontproperties=self._fp(8.5, estilo='italic'))
            ax.plot([self.m, self.W - self.m], [0.68, 0.68], color=LINEA, lw=0.7)
        return fig

    @property
    def limite(self):
        return self.H - self.inf

    def asegurar(self, alto):
        if self.y + alto > self.limite:
            self.nueva()

    def espacio(self, pulgadas):
        self.y += pulgadas

    # ------------------------------------------------------------------ texto
    @staticmethod
    def _fp(tam, peso='normal', estilo='normal'):
        return FontProperties(family='serif', size=tam, weight=peso, style=estilo)

    def _w(self, s, fp):
        w, _, _ = self._r.get_text_width_height_descent(s, fp, False)
        return w / 100.0

    def _armar_lineas(self, segmentos, tam, ancho):
        """segmentos: [(texto, peso, estilo)] -> lista de lineas, cada una lista de (palabra, fp)."""
        espacio = self._w('i i', self._fp(tam)) - self._w('ii', self._fp(tam))
        lineas, actual, usado = [], [], 0.0
        for texto, peso, estilo in segmentos:
            fp = self._fp(tam, peso, estilo)
            piezas = []
            for palabra in texto.split():
                if self._w(palabra, fp) > ancho:
                    trozo = ''
                    for ch in palabra:
                        if self._w(trozo + ch, fp) > ancho * 0.97:
                            piezas.append(trozo)
                            trozo = ''
                        trozo += ch
                    piezas.append(trozo)
                else:
                    piezas.append(palabra)
            for palabra in piezas:
                w = self._w(palabra, fp)
                extra = espacio if actual else 0.0
                if actual and usado + extra + w > ancho:
                    lineas.append(actual)
                    actual, usado = [], 0.0
                    extra = 0.0
                actual.append((palabra, fp, w))
                usado += extra + w
        if actual:
            lineas.append(actual)
        return lineas, espacio

    def parrafo(self, segmentos, tam=10.5, color=NEGRO, justificar=True, sangria=0.0, despues=0.10,
                interlineado=1.32, ancho=None, x0=None):
        if isinstance(segmentos, str):
            segmentos = [(segmentos, 'normal', 'normal')]
        x0 = (self.m if x0 is None else x0) + sangria
        ancho = (self.W - 2 * self.m if ancho is None else ancho) - sangria
        lineas, esp = self._armar_lineas(segmentos, tam, ancho)
        lh = tam * interlineado / 72.0
        for k, linea in enumerate(lineas):
            self.asegurar(lh)
            base = self.y + tam * 0.86 / 72.0
            ultima = k == len(lineas) - 1
            suma = sum(w for _, _, w in linea)
            if justificar and not ultima and len(linea) > 1:
                esp_l = (ancho - suma) / (len(linea) - 1)
            else:
                esp_l = esp
            x = x0
            for palabra, fp, w in linea:
                self.ax.text(x, base, palabra, fontproperties=fp, color=color, ha='left', va='baseline')
                x += w + esp_l
            self.y += lh
        self.y += despues

    def centrado(self, texto, tam=11, peso='normal', estilo='normal', color=NEGRO, despues=0.08):
        lh = tam * 1.35 / 72.0
        self.asegurar(lh)
        self.ax.text(self.W / 2, self.y + tam * 0.86 / 72.0, texto, fontproperties=self._fp(tam, peso, estilo),
                     color=color, ha='center', va='baseline')
        self.y += lh + despues

    def titulo(self, texto, tam=20, color=AZUL, despues=0.06, regla=True):
        lineas, _ = self._armar_lineas([(texto, 'bold', 'normal')], tam, self.W - 2 * self.m)
        lh = tam * 1.25 / 72.0
        self.asegurar(lh * len(lineas) + 0.2)
        for linea in lineas:
            x = self.m
            for palabra, fp, w in linea:
                self.ax.text(x, self.y + tam * 0.86 / 72.0, palabra, fontproperties=fp, color=color, ha='left',
                             va='baseline')
                x += w + self._w('i i', fp) - self._w('ii', fp)
            self.y += lh
        if regla:
            self.ax.plot([self.m, self.W - self.m], [self.y + 0.03, self.y + 0.03], color=color, lw=1.4)
            self.y += 0.10
        self.y += despues

    def seccion(self, texto, tam=12.5):
        lh = tam * 1.3 / 72.0
        self.asegurar(lh + 0.55)
        self.y += 0.10
        self.ax.text(self.m, self.y + tam * 0.86 / 72.0, texto, fontproperties=self._fp(tam, 'bold'),
                     color=AZUL, ha='left', va='baseline')
        self.y += lh + 0.02
        self.ax.plot([self.m, self.W - self.m], [self.y, self.y], color=LINEA, lw=0.8)
        self.y += 0.10

    def subtitulo(self, texto, tam=11):
        lh = tam * 1.3 / 72.0
        self.asegurar(lh + 0.45)
        self.ax.text(self.m, self.y + tam * 0.86 / 72.0, texto, fontproperties=self._fp(tam, 'bold'),
                     color=NEGRO, ha='left', va='baseline')
        self.y += lh + 0.02

    # ----------------------------------------------------------------- tablas
    def tabla(self, cabecera, filas, anchos=None, alin=None, tam=9.6, despues=0.14, negrita_col0=False):
        n = len(cabecera)
        total = self.W - 2 * self.m
        anchos = anchos or [1.0 / n] * n
        suma = float(sum(anchos))
        cols = [total * a / suma for a in anchos]
        alin = alin or ['l'] + ['c'] * (n - 1)
        pad = 0.07
        lh = tam * 1.28 / 72.0

        def envolver(texto, ancho, peso='normal'):
            lin, _ = self._armar_lineas([(str(texto), peso, 'normal')], tam, ancho - 2 * pad)
            return [' '.join(p for p, _, _ in l) for l in lin] or ['']

        def dibujar_fila(celdas, y, alto, cab=False, zebra=False):
            if cab:
                self.ax.add_patch(Rectangle((self.m, y), total, alto, facecolor=CAB, edgecolor='none'))
            elif zebra:
                self.ax.add_patch(Rectangle((self.m, y), total, alto, facecolor=ZEBRA, edgecolor='none'))
            x = self.m
            for j, lineas in enumerate(celdas):
                ha = 'center' if cab else {'l': 'left', 'c': 'center', 'r': 'right'}[alin[j]]
                px = x + (cols[j] / 2 if ha == 'center' else pad if ha == 'left' else cols[j] - pad)
                peso = 'bold' if (cab or (negrita_col0 and j == 0)) else 'normal'
                for k, ln in enumerate(lineas):
                    self.ax.text(px, y + pad * 0.7 + k * lh + tam * 0.86 / 72.0, ln,
                                 fontproperties=self._fp(tam, peso), color=NEGRO, ha=ha, va='baseline')
                x += cols[j]

        def alto_fila(celdas):
            return max(len(c) for c in celdas) * lh + pad * 1.4

        cab_celdas = [envolver(c, cols[j], 'bold') for j, c in enumerate(cabecera)]
        h_cab = alto_fila(cab_celdas)
        self.asegurar(h_cab + 2 * lh + 0.3)
        self.ax.plot([self.m, self.m + total], [self.y, self.y], color=NEGRO, lw=1.2)
        dibujar_fila(cab_celdas, self.y, h_cab, cab=True)
        self.y += h_cab
        self.ax.plot([self.m, self.m + total], [self.y, self.y], color=NEGRO, lw=0.7)
        for i, fila in enumerate(filas):
            celdas = [envolver(c, cols[j]) for j, c in enumerate(fila)]
            h = alto_fila(celdas)
            if self.y + h > self.limite:
                self.ax.plot([self.m, self.m + total], [self.y, self.y], color=NEGRO, lw=1.0)
                self.nueva()
                self.ax.plot([self.m, self.m + total], [self.y, self.y], color=NEGRO, lw=1.2)
                dibujar_fila(cab_celdas, self.y, h_cab, cab=True)
                self.y += h_cab
                self.ax.plot([self.m, self.m + total], [self.y, self.y], color=NEGRO, lw=0.7)
            dibujar_fila(celdas, self.y, h, zebra=(i % 2 == 1))
            self.y += h
            self.ax.plot([self.m, self.m + total], [self.y, self.y], color='#C9CED6', lw=0.4)
        self.ax.plot([self.m, self.m + total], [self.y, self.y], color=NEGRO, lw=1.2)
        self.y += despues

    # ------------------------------------------------------------------ cierre
    def con_pie(self, texto_pie, numero_inicial=1, total=None):
        total = total or (numero_inicial + len(self.paginas) - 1)
        for k, fig in enumerate(self.paginas):
            _pie(fig, texto_pie, numero_inicial + k, total)
        return self.paginas


def _pie(fig, texto, n, total):
    ancho, alto = fig.get_size_inches()
    m = 0.85 if ancho < 10 else 0.6
    fig.add_artist(__import__('matplotlib.lines', fromlist=['Line2D']).Line2D(
        [m / ancho, 1 - m / ancho], [0.55 / alto, 0.55 / alto], color=LINEA, lw=0.7, transform=fig.transFigure))
    fp = FontProperties(family='serif', size=8.5, style='italic')
    fig.text(m / ancho, 0.38 / alto, texto, fontproperties=fp, color=GRIS, ha='left', va='center')
    fig.text(1 - m / ancho, 0.38 / alto, f'Página {n} de {total}', fontproperties=fp, color=GRIS,
             ha='right', va='center')


# ====================================================================== contenido
def _estado_r0(r0):
    if r0 > 1:
        return f'{r0:.3f}  (EPIDEMIA: R0 mayor a 1)'
    if r0 < 1:
        return f'{r0:.3f}  (CONTROLADO: R0 menor a 1)'
    return f'{r0:.3f}  (UMBRAL: R0 igual a 1)'


def filas_parametros(estado):
    return [
        ['β', 'Tasa de contagio (contagiosidad del COVID-19)', f'{estado.beta:.4f}'],
        ['γ', 'Tasa de recuperación (1/γ = duración de la enfermedad)', f'{estado.gamma:.4f}'],
        ['R0 = β/γ', 'Número reproductivo básico', _estado_r0(estado.R0)],
        ['N', 'Población total del DMQ', f'{estado.N:,}'],
        ['I0', 'Infectados iniciales', f'{estado.I0:,}'],
        ['Meses', 'Horizonte de simulación', f'{estado.meses}'],
    ]


def pagina_graficos(modulo, estado, cabecera, numero_seccion=None):
    """Hoja horizontal: titulo y descripcion arriba, graficas debajo."""
    mq = Maquetador(A4_H, cabecera, margen=0.6, sup=0.95, inf=0.75)
    nombre = modulo.TITULO if numero_seccion is None else f'{numero_seccion}. {modulo.TITULO}'
    mq.titulo(nombre, tam=19, despues=0.02)
    if getattr(modulo, 'SUBTITULO', ''):
        mq.parrafo([(limpiar(modulo.SUBTITULO), 'normal', 'italic')], tam=10.5, color=GRIS, justificar=False,
                   despues=0.04)
    mq.parrafo([('De qué trata. ', 'bold', 'normal'), (limpiar(modulo.DESCRIPCION), 'normal', 'normal')],
               tam=10, despues=0.03)
    mq.parrafo([('Parámetros. ', 'bold', 'normal'),
                (f'β = {estado.beta:.3f}   γ = {estado.gamma:.3f}   R0 = {estado.R0:.3f}   '
                 f'N = {estado.N:,}   I0 = {estado.I0}   Meses = {estado.meses}', 'normal', 'normal')],
               tam=10, justificar=False, despues=0.02)
    arriba = mq.y
    fig = mq.paginas[-1]
    W, H = A4_H
    alto_graf = H - arriba - 0.78
    gs = GridSpec(3, 3, figure=fig, width_ratios=[0.6, W - 1.2, 0.6], height_ratios=[arriba, alto_graf, 0.78],
                  hspace=0, wspace=0, left=0, right=1, top=1, bottom=0)
    sub = fig.add_subfigure(gs[1, 1])
    modulo.dibujar_en(sub)
    return mq.paginas[-1]


def paginas_resumen(modulo, estado, cabecera, numero_seccion=None, con_fuente=True):
    mq = Maquetador(A4_V, cabecera)
    nombre = modulo.TITULO if numero_seccion is None else f'{numero_seccion}. {modulo.TITULO}'
    mq.titulo(f'Resumen y análisis — {nombre}', tam=15, despues=0.02)

    mq.seccion('1. Parámetros de la simulación')
    mq.tabla(['Símbolo', 'Descripción', 'Valor'], filas_parametros(estado), anchos=[0.14, 0.46, 0.40],
             alin=['c', 'l', 'c'])

    datos = getattr(modulo, 'datos_resumen', None) or []
    if datos:
        mq.seccion('2. Resultados principales')
        ancho = [0.5, 0.5] if len(datos[0]) == 2 else [0.38, 0.32, 0.30]
        cab = ['Magnitud', 'Valor'] if len(datos[0]) == 2 else ['Magnitud', 'Valor', 'Observación']
        mq.tabla(cab, [[limpiar(str(c)) for c in f] for f in datos], anchos=ancho,
                 alin=['l', 'c', 'l'][:len(cab)])

    titulo_t, formulas, explicacion = modulo.teoria()
    mq.seccion('3. Fundamento teórico y fórmulas')
    mq.parrafo([(limpiar(titulo_t) + '.', 'bold', 'normal')], tam=10.3, justificar=False, despues=0.08)
    filas_f = []
    for f in formulas:
        partes = re.split(r'\s{2,}', f.strip(), maxsplit=1)
        filas_f.append([limpiar(partes[0]), limpiar(partes[1].strip('() ')) if len(partes) > 1 else ''])
    mq.tabla(['Expresión', 'Significado'], filas_f, anchos=[0.52, 0.48], alin=['l', 'l'], tam=9.6)
    for enc, texto in partir_explicacion(explicacion):
        if enc:
            mq.subtitulo(enc, tam=10.5)
        mq.parrafo(texto, tam=10.2, despues=0.10)

    mq.seccion('4. Análisis de cada gráfica')
    for it in modulo.analisis():
        mq.subtitulo(f'Gráfica {it["n"]} — {limpiar(it["titulo"])}', tam=10.8)
        mq.parrafo([('Observación. ', 'bold', 'normal'), (limpiar(it['texto']), 'normal', 'normal')],
                   tam=10.2, despues=0.04)
        mq.parrafo([('Conclusión. ', 'bold', 'italic'), (limpiar(it['conclusion']), 'normal', 'italic')],
                   tam=10.2, despues=0.12)

    if con_fuente:
        mq.seccion('Fuente de los datos de Quito')
        mq.parrafo(f'Secretaría de Salud del Municipio del Distrito Metropolitano de Quito, '
                   f'«{FUENTE_PDF_NOMBRE}». Disponible en: {FUENTE_PDF_URL}', tam=9.2, justificar=False)
    return mq.paginas


def figura_portada(estado, indice):
    """indice: lista de (nombre, pagina). Todo cabe en una sola hoja vertical."""
    mq = Maquetador(A4_V, '', margen=0.95, sup=1.0)
    mq.espacio(0.35)
    mq.centrado('PANDEMIA SIMULADOR', tam=30, peso='bold', color=AZUL, despues=0.06)
    mq.centrado('Reporte completo de resultados', tam=17, color=NEGRO, despues=0.04)
    mq.centrado('COVID-19 en el Distrito Metropolitano de Quito (DMQ)', tam=13, estilo='italic', color=GRIS,
                despues=0.06)
    mq.centrado('Modelo SIR y métodos numéricos', tam=12, estilo='italic', color=GRIS, despues=0.10)
    mq.ax.plot([mq.m, mq.W - mq.m], [mq.y, mq.y], color=AZUL, lw=1.6)
    mq.espacio(0.22)
    mq.centrado(f'Fecha de emisión: {fecha_hoy()}', tam=10.5, color=NEGRO, despues=0.12)

    mq.seccion('Parámetros de la simulación')
    mq.tabla(['Símbolo', 'Descripción', 'Valor'], filas_parametros(estado), anchos=[0.14, 0.46, 0.40],
             alin=['c', 'l', 'c'])

    mq.seccion('Contenido del reporte')
    mq.tabla(['Sección', 'Página'], [[n, str(p)] for n, p in indice], anchos=[0.85, 0.15], alin=['l', 'c'])

    mq.seccion('Fuente de los datos de Quito')
    mq.parrafo(f'Secretaría de Salud del Municipio del Distrito Metropolitano de Quito, '
               f'«{FUENTE_PDF_NOMBRE}». Disponible en: {FUENTE_PDF_URL}', tam=9.2, justificar=False)
    return mq.paginas


def _secciones_individuales(modulo, estado, numero=None):
    cabecera = f'{NOMBRE_APP}'
    gr = pagina_graficos(modulo, estado, cabecera, numero)
    res = paginas_resumen(modulo, estado, cabecera, numero, con_fuente=(numero is None))
    return [gr] + res


def guardar_modulo(ruta, modulo, estado):
    """PDF individual: hoja de graficas (con titulo y descripcion) + hojas de resumen y analisis."""
    with tema_claro():
        paginas = _secciones_individuales(modulo, estado)
        total = len(paginas)
        for k, fig in enumerate(paginas):
            _pie(fig, f'PandemiaSimulador — {modulo.TITULO}', k + 1, total)
        _escribir(ruta, paginas, modulo.TITULO)


def guardar_completo(ruta, modulos, estado):
    """PDF completo: portada con contenido + (resumen general) + cada modulo. `modulos` = lista de
    (nombre_seccion, objeto_modulo)."""
    with tema_claro():
        bloques = []
        for k, (nombre, mod) in enumerate(modulos, start=1):
            bloques.append((f'{k}. {mod.TITULO}', _secciones_individuales(mod, estado, k)))
        portada = figura_portada(estado, [(n, 0) for n, _ in bloques])
        pagina = 1 + len(portada)
        indice = []
        for nombre, pags in bloques:
            indice.append((nombre, pagina))
            pagina += len(pags)
        portada = figura_portada(estado, indice)
        paginas = list(portada)
        for _, pags in bloques:
            paginas += pags
        total = len(paginas)
        for k, fig in enumerate(paginas):
            if k > 0:
                _pie(fig, 'PandemiaSimulador — Reporte completo', k + 1, total)
        _escribir(ruta, paginas, 'PandemiaSimulador — Reporte completo')


def _escribir(ruta, paginas, titulo):
    with PdfPages(ruta, metadata={'Title': titulo, 'Author': 'PandemiaSimulador',
                                  'Subject': 'COVID-19 en el DMQ - Modelo SIR y métodos numéricos'}) as pdf:
        for fig in paginas:
            pdf.savefig(fig, facecolor='white')
