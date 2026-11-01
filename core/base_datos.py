"""Persistencia de las simulaciones en SQLite (un solo archivo: pandemia.db, sin servidor)."""
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime

import numpy as np

from core.metodos_numericos import rk4_sir, euler_sir

RUTA_DEFECTO = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'pandemia.db')

ESQUEMA = """
CREATE TABLE IF NOT EXISTS simulaciones (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha           TEXT    NOT NULL,
    beta            REAL    NOT NULL,
    gamma           REAL    NOT NULL,
    n               INTEGER NOT NULL,
    i0              INTEGER NOT NULL,
    meses           INTEGER NOT NULL,
    r0              REAL    NOT NULL,
    estado          TEXT    NOT NULL,
    pico            REAL    NOT NULL,
    mes_pico        INTEGER NOT NULL,
    s_final         REAL    NOT NULL,
    r_final         REAL    NOT NULL,
    tasa_ataque     REAL    NOT NULL,
    error_euler_max REAL    NOT NULL
);
CREATE TABLE IF NOT EXISTS serie_mensual (
    simulacion_id INTEGER NOT NULL REFERENCES simulaciones(id) ON DELETE CASCADE,
    mes           INTEGER NOT NULL,
    s             REAL NOT NULL,
    i             REAL NOT NULL,
    r             REAL NOT NULL,
    s_euler       REAL NOT NULL,
    i_euler       REAL NOT NULL,
    r_euler       REAL NOT NULL,
    PRIMARY KEY (simulacion_id, mes)
);
CREATE INDEX IF NOT EXISTS idx_serie_mes ON serie_mensual(mes);
"""


class BaseDatos:
    def __init__(self, ruta=None):
        self.ruta = ruta or RUTA_DEFECTO
        with self._conexion() as con:
            con.executescript(ESQUEMA)

    @contextmanager
    def _conexion(self):
        con = sqlite3.connect(self.ruta)
        con.row_factory = sqlite3.Row
        con.execute('PRAGMA foreign_keys = ON')
        try:
            yield con
            con.commit()
        except Exception:
            con.rollback()
            raise
        finally:
            con.close()

    # ---------------------------------------------------------------- escritura
    def guardar_simulacion(self, estado):
        """Guarda la simulacion actual con su serie mensual. Si es identica a la ultima guardada,
        no la duplica y devuelve el id existente."""
        beta, gamma, N, I0, meses = estado.beta, estado.gamma, int(estado.N), int(estado.I0), int(estado.meses)
        with self._conexion() as con:
            ultima = con.execute('SELECT * FROM simulaciones ORDER BY id DESC LIMIT 1').fetchone()
            if ultima and (abs(ultima['beta'] - beta) < 1e-9 and abs(ultima['gamma'] - gamma) < 1e-9
                           and ultima['n'] == N and ultima['i0'] == I0 and ultima['meses'] == meses):
                return ultima['id']

            S4, I4, R4 = rk4_sir(beta, gamma, N, I0, meses)
            Se, Ie, Re = euler_sir(beta, gamma, N, I0, meses)
            r0 = beta / gamma
            cur = con.execute(
                'INSERT INTO simulaciones (fecha, beta, gamma, n, i0, meses, r0, estado, pico, mes_pico, '
                's_final, r_final, tasa_ataque, error_euler_max) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
                (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), beta, gamma, N, I0, meses, r0,
                 'EPIDEMIA' if r0 > 1 else 'CONTROLADO', float(np.max(I4)), int(np.argmax(I4)),
                 float(S4[-1]), float(R4[-1]), float((N - S4[-1]) / N * 100),
                 float(np.max(np.abs(I4 - Ie)))))
            sim_id = cur.lastrowid
            con.executemany(
                'INSERT INTO serie_mensual VALUES (?,?,?,?,?,?,?,?)',
                [(sim_id, m, float(S4[m]), float(I4[m]), float(R4[m]), float(Se[m]), float(Ie[m]), float(Re[m]))
                 for m in range(len(I4))])
            return sim_id

    def eliminar(self, sim_id):
        with self._conexion() as con:
            con.execute('DELETE FROM simulaciones WHERE id = ?', (sim_id,))

    def vaciar(self):
        with self._conexion() as con:
            con.execute('DELETE FROM simulaciones')
            con.execute("DELETE FROM sqlite_sequence WHERE name = 'simulaciones'")

    # ----------------------------------------------------------------- lectura
    def listar_simulaciones(self):
        with self._conexion() as con:
            return [dict(f) for f in con.execute('SELECT * FROM simulaciones ORDER BY id')]

    def serie_completa(self):
        with self._conexion() as con:
            return [dict(f) for f in con.execute('SELECT * FROM serie_mensual ORDER BY simulacion_id, mes')]

    def total(self):
        with self._conexion() as con:
            return con.execute('SELECT COUNT(*) FROM simulaciones').fetchone()[0]

    def estadisticas_generales(self):
        with self._conexion() as con:
            f = con.execute(
                'SELECT COUNT(*) AS total, AVG(r0) AS r0_prom, AVG(pico) AS pico_prom, MAX(pico) AS pico_max, '
                'AVG(tasa_ataque) AS ataque_prom, AVG(error_euler_max) AS error_prom, '
                "SUM(estado = 'CONTROLADO') AS controladas, SUM(estado = 'EPIDEMIA') AS epidemias "
                'FROM simulaciones').fetchone()
        return {k: (f[k] if f[k] is not None else 0) for k in f.keys()}

    def resumen_por_estado(self):
        with self._conexion() as con:
            return [dict(f) for f in con.execute(
                'SELECT estado, COUNT(*) AS simulaciones, AVG(r0) AS r0_prom, AVG(pico) AS pico_prom, '
                'AVG(tasa_ataque) AS ataque_prom FROM simulaciones GROUP BY estado ORDER BY estado')]

    def promedio_por_mes(self):
        with self._conexion() as con:
            return [dict(f) for f in con.execute(
                'SELECT mes, AVG(i) AS i_prom, MIN(i) AS i_min, MAX(i) AS i_max, AVG(s) AS s_prom, '
                'AVG(r) AS r_prom, AVG(ABS(i - i_euler)) AS error_euler_prom '
                'FROM serie_mensual GROUP BY mes ORDER BY mes')]
