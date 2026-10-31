import tkinter as tk
from ui.estilo import aplicar_tema_matplotlib
from ui.splash import Splash
from ventanas.ventana_principal import VentanaPrincipal

aplicar_tema_matplotlib()


def iniciar_app():
    raiz.destroy()
    app = VentanaPrincipal()
    app.mainloop()


raiz = tk.Tk()
raiz.withdraw()
Splash(raiz, al_terminar=iniciar_app)
raiz.mainloop()
