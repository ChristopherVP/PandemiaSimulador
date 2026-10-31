import numpy as np
from core.modelo_sir import sir_derivadas


def euler_sir(beta, gamma, N, I0, meses, h=30.0, subpasos=10):
    S = np.zeros(meses); I = np.zeros(meses); R = np.zeros(meses)
    S[0] = N - I0; I[0] = I0; R[0] = 0.0
    hs = h / subpasos
    for n in range(meses - 1):
        s, i, r = S[n], I[n], R[n]
        for _ in range(subpasos):
            dS, dI, dR = sir_derivadas(s, i, r, beta, gamma, N)
            s = max(0.0, s + hs * dS)
            i = max(0.0, i + hs * dI)
            r = max(0.0, r + hs * dR)
        S[n + 1], I[n + 1], R[n + 1] = s, i, r
    return S, I, R


def rk4_sir(beta, gamma, N, I0, meses, h=30.0, subpasos=10):
    S = np.zeros(meses); I = np.zeros(meses); R = np.zeros(meses)
    S[0] = N - I0; I[0] = I0; R[0] = 0.0
    hs = h / subpasos
    for n in range(meses - 1):
        s, i, r = S[n], I[n], R[n]
        for _ in range(subpasos):
            k1S, k1I, k1R = sir_derivadas(s, i, r, beta, gamma, N)
            k2S, k2I, k2R = sir_derivadas(s + hs / 2 * k1S, i + hs / 2 * k1I, r + hs / 2 * k1R, beta, gamma, N)
            k3S, k3I, k3R = sir_derivadas(s + hs / 2 * k2S, i + hs / 2 * k2I, r + hs / 2 * k2R, beta, gamma, N)
            k4S, k4I, k4R = sir_derivadas(s + hs * k3S, i + hs * k3I, r + hs * k3R, beta, gamma, N)
            s = max(0.0, s + hs / 6 * (k1S + 2 * k2S + 2 * k3S + k4S))
            i = max(0.0, i + hs / 6 * (k1I + 2 * k2I + 2 * k3I + k4I))
            r = max(0.0, r + hs / 6 * (k1R + 2 * k2R + 2 * k3R + k4R))
        S[n + 1], I[n + 1], R[n + 1] = s, i, r
    return S, I, R


def derivacion_numerica(I, h=1.0):
    n = len(I)
    dIdt = np.zeros(n)
    dIdt[0] = (-3 * I[0] + 4 * I[1] - I[2]) / (2 * h)
    for i in range(1, n - 1):
        dIdt[i] = (I[i + 1] - I[i - 1]) / (2 * h)
    dIdt[-1] = (I[-3] - 4 * I[-2] + 3 * I[-1]) / (2 * h)
    return dIdt


def simpson_compuesta(I, a, b, h=1.0):
    seg = I[a:b + 1].copy()
    n = len(seg) - 1
    if n % 2 != 0:
        n -= 1
        seg = seg[:n + 1]
    if n < 2:
        return 0.0
    area = seg[0] + seg[n]
    for i in range(1, n):
        area += (4 if i % 2 == 1 else 2) * seg[i]
    return area * h / 3.0


def newton_raphson_beta(I_obs, gamma, N, I0, b0, meses=10, tol=1.0, max_iter=15):
    def pico(b):
        _, Iv, _ = rk4_sir(b, gamma, N, I0, meses)
        return float(np.max(Iv))

    def f(b):
        return pico(b) - I_obs

    def df(b):
        d = 0.001
        return (f(b + d) - f(b - d)) / (2 * d)

    b = float(b0)
    hist = []
    for it in range(max_iter):
        fv = f(b)
        dfv = df(b)
        hist.append({'iter': it, 'beta': b, 'fb': fv, 'ea': abs(fv)})
        if abs(fv) < tol or abs(dfv) < 1e-10:
            break
        b = np.clip(b - fv / dfv, 0.001, 2.0)
    return b, hist
