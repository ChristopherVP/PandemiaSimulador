import tkinter as tk
from ui.estilo import C


class Splash(tk.Toplevel):
    def __init__(self, master, al_terminar, duracion_ms=1600):
        super().__init__(master)
        self.al_terminar = al_terminar
        self.overrideredirect(True)
        self.configure(bg=C['bg'])
        ancho, alto = 480, 260
        x = (self.winfo_screenwidth() - ancho) // 2
        y = (self.winfo_screenheight() - alto) // 2
        self.geometry(f'{ancho}x{alto}+{x}+{y}')

        marco = tk.Frame(self, bg=C['bg'], highlightbackground=C['acento'], highlightthickness=2)
        marco.pack(fill=tk.BOTH, expand=True)

        tk.Label(marco, text='🦠', bg=C['bg'], fg=C['txt'], font=('Consolas', 40)).pack(pady=(30, 4))
        tk.Label(marco, text='SIMULADOR DE PANDEMIA', bg=C['bg'], fg=C['txt'],
                 font=('Consolas', 15, 'bold')).pack()
        tk.Label(marco, text='Modelo SIR + Métodos Numéricos', bg=C['bg'], fg=C['txt2'],
                 font=('Consolas', 9)).pack(pady=(2, 16))

        self.barra = tk.Canvas(marco, width=380, height=8, bg=C['border'], highlightthickness=0)
        self.barra.pack(pady=6)
        self.relleno = self.barra.create_rectangle(0, 0, 0, 8, fill=C['acento'], width=0)

        self.duracion_ms = duracion_ms
        self.pasos = 40
        self.paso_actual = 0
        self.after(20, self._animar)

    def _animar(self):
        self.paso_actual += 1
        ancho = int(380 * self.paso_actual / self.pasos)
        self.barra.coords(self.relleno, 0, 0, ancho, 8)
        if self.paso_actual < self.pasos:
            self.after(self.duracion_ms // self.pasos, self._animar)
        else:
            self.destroy()
            self.al_terminar()
