import tkinter as tk
from ui.estilo import C


def crear_slider(parent, etiqueta, minimo, maximo, valor_inicial, resolucion, comando, color=C['acento'], descripcion=None):
    frame = tk.Frame(parent, bg=C['panel'])
    frame.pack(side=tk.LEFT, padx=12, pady=4)
    tk.Label(frame, text=etiqueta, bg=C['panel'], fg=C['txt2'], font=('Consolas', 8, 'bold')).pack(anchor='w')
    var = tk.DoubleVar(value=valor_inicial)
    esc = tk.Scale(frame, from_=minimo, to=maximo, resolution=resolucion, orient=tk.HORIZONTAL,
                   length=210, variable=var, bg=C['panel'], fg=C['txt'], troughcolor=C['border'],
                   highlightthickness=0, bd=0, font=('Consolas', 8), command=comando,
                   activebackground=color)
    esc.pack()
    if descripcion:
        tk.Label(frame, text=descripcion, bg=C['panel'], fg=C['txt2'], font=('Consolas', 7),
                 wraplength=210, justify=tk.LEFT, anchor='w').pack(fill=tk.X, pady=(2, 0))
    return var, esc


def crear_panel_teoria(parent, titulo, formulas, explicacion, wraplength=1250):
    contenedor = tk.Frame(parent, bg=C['fondo_f'], highlightbackground=C['acento'], highlightthickness=1)

    cabecera = tk.Frame(contenedor, bg=C['fondo_f'])
    cabecera.pack(fill=tk.X)

    tk.Label(cabecera, text=f'📖  {titulo}', bg=C['fondo_f'], fg=C['acento'],
             font=('Consolas', 10, 'bold'), anchor='w').pack(side=tk.LEFT, padx=12, pady=8)

    cuerpo = tk.Frame(contenedor, bg=C['fondo_f'])
    cuerpo.pack(fill=tk.X, padx=16, pady=(0, 12))

    marco_formulas = tk.Frame(cuerpo, bg=C['panel'])
    marco_formulas.pack(fill=tk.X, pady=(0, 8))
    tk.Label(marco_formulas, text='FÓRMULAS UTILIZADAS PARA GENERAR ESTOS DATOS', bg=C['panel'], fg=C['txt2'],
              font=('Consolas', 7, 'bold'), anchor='w').pack(fill=tk.X, padx=10, pady=(6, 0))
    for f in formulas:
        tk.Label(marco_formulas, text=f'   {f}', bg=C['panel'], fg=C['nodo'],
                 font=('Consolas', 10, 'bold'), anchor='w', justify=tk.LEFT).pack(fill=tk.X, padx=8, pady=2)
    tk.Frame(marco_formulas, bg=C['panel'], height=4).pack()

    tk.Label(cuerpo, text=explicacion, bg=C['fondo_f'], fg=C['txt'], font=('Consolas', 9),
             wraplength=wraplength, justify=tk.LEFT, anchor='w').pack(fill=tk.X)

    def alternar():
        if cuerpo.winfo_ismapped():
            cuerpo.pack_forget()
            btn_toggle.config(text='▼  Mostrar teoría y fórmulas')
        else:
            cuerpo.pack(fill=tk.X, padx=16, pady=(0, 12))
            btn_toggle.config(text='▲  Ocultar teoría y fórmulas')

    btn_toggle = tk.Button(cabecera, text='▲  Ocultar teoría y fórmulas', bg=C['fondo_f'], fg=C['txt2'],
                           font=('Consolas', 8), relief=tk.FLAT, bd=0, cursor='hand2', command=alternar)
    btn_toggle.pack(side=tk.RIGHT, padx=12)

    return contenedor
