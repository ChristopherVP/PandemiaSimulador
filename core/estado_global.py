import tkinter as tk

MESES = 10

N_QUITO = 2584622
N_MIN = N_QUITO - 10000
N_MAX = N_QUITO + 10000

I0_QUITO = 330
BETA_QUITO = 0.085
GAMMA_QUITO = 0.10

FUENTE_PDF_NOMBRE = 'Informe Quincenal COVID-19 - Mes Noviembre 2021 (Secretaría de Salud, DMQ)'
FUENTE_PDF_URL = ('https://www7.quito.gob.ec/mdmq_Ordenanzas/Administraci%C3%B3n%202019-2023/'
                   'Comisiones%20del%20Concejo%20Metropolitano/Salud/2021/2021-11-29/Documentos'
                   '%20para%20tratamiento/Punto%202/informe_quincenal_covid_19_mes_de_noviembre_2021.pdf')


class EstadoGlobal:
    def __init__(self):
        self.beta = BETA_QUITO
        self.gamma = GAMMA_QUITO
        self.N = N_QUITO
        self.I0 = I0_QUITO
        self.meses = MESES
        self._listeners = []

    def restablecer(self):
        self.beta = BETA_QUITO
        self.gamma = GAMMA_QUITO
        self.N = N_QUITO
        self.I0 = I0_QUITO
        self.notificar()

    def suscribir(self, callback):
        if callback not in self._listeners:
            self._listeners.append(callback)

    def desuscribir(self, callback):
        if callback in self._listeners:
            self._listeners.remove(callback)

    def notificar(self):
        for cb in list(self._listeners):
            try:
                cb()
            except tk.TclError:
                pass

    @property
    def R0(self):
        return self.beta / self.gamma
