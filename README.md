# 🦠 PandemiaSimulador

**An educational COVID-19 simulator for the Metropolitan District of Quito (DMQ), Ecuador — built on the SIR epidemic model and six numerical methods.**

PandemiaSimulador is a desktop application (Python + Tkinter + Matplotlib) created for a **Numerical Methods** course. It solves a SIR (Susceptible – Infected – Recovered) epidemic model calibrated with real data from Quito's health authorities, and then applies **six different numerical methods to that same simulated epidemic**, so each technique can be seen working on the same data instead of on isolated textbook exercises. Every simulation is stored in a local SQLite database, and everything can be exported to **PDF**, **Excel** and **CSV**.

> All analysis is presented **per month** over a **10-month horizon**.

---

## Table of Contents

1. [Features at a Glance](#-features-at-a-glance)
2. [Project Requirements](#-project-requirements)
3. [Installation](#-installation)
4. [Running the Application](#-running-the-application)
5. [How to Use It (Step by Step)](#-how-to-use-it-step-by-step)
6. [The Mathematical Model](#-the-mathematical-model)
7. [Default Parameters and Data Source](#-default-parameters-and-data-source)
8. [The Six Results (Numerical Methods)](#-the-six-results-numerical-methods)
9. [Simulation History, Trash Bin and Statistics](#-simulation-history-trash-bin-and-statistics)
10. [Exports: PDF, Excel and CSV](#-exports-pdf-excel-and-csv)
11. [Database Schema](#-database-schema)
12. [Project Structure](#-project-structure)
13. [Architecture and Design Notes](#-architecture-and-design-notes)
14. [Model Assumptions and Limitations](#-model-assumptions-and-limitations)
15. [Troubleshooting](#-troubleshooting)
16. [Author, Repository and License](#-author-repository-and-license)

---

## ✨ Features at a Glance

- **SIR epidemic model** solved numerically with **Euler** and **Runge-Kutta 4 (RK4)**, calibrated with real Quito (DMQ) COVID-19 data.
- **Six numerical-method modules**, each with 4 numbered charts, a theory/formula panel and an automatic written analysis of every chart:
  1. Epidemic evolution — SIR with Euler and RK4
  2. Reliability — absolute and relative numerical error
  3. Estimation of months without data — natural cubic spline interpolation
  4. Speed of spread — 3-point numerical differentiation
  5. Health-system impact — composite Simpson integration (vs. trapezoid)
  6. Calibration of real contagion — Newton-Raphson on β
- **Interactive sliders** for β, γ, I0 and N, plus module-specific controls (spline nodes, integration limits, observed peak, initial β…).
- **Quick preview panel** with a summary and analysis of the current simulation.
- **Built-in user guide tab** explaining the SIR model, the workflow, the data source and all six modules.
- **Automatic history** of every simulation in a local **SQLite** file, with KPIs, an aggregate chart, **load-back of parameters**, and a **trash bin** (restore deleted simulations within 7 days).
- **PDF reports**: one per module, or a **complete report** (cover page with index + all modules) in A4 format with a print-friendly light theme.
- **Excel export** (4 formatted sheets with native charts) and **CSV export**.
- Dark-themed UI with a splash screen, scrollable panels and embedded Matplotlib toolbars (zoom/pan).

---

## 📋 Project Requirements

### Functional requirements

| ID | Requirement |
|----|-------------|
| FR-01 | Simulate an epidemic with the SIR model (S, I, R compartments) over 10 monthly points. |
| FR-02 | Allow the user to set β (transmission rate), γ (recovery rate), I0 (initial infected) and N (total population) through sliders. |
| FR-03 | Compute nothing until the user explicitly presses **“Aplicar Simulación” (Apply Simulation)**. |
| FR-04 | Solve the SIR system with both **Euler** and **RK4**, using finer internal sub-steps for numerical stability. |
| FR-05 | Compute and display the basic reproduction number **R0 = β/γ** and classify the state as `EPIDEMIA` (R0 > 1) or `CONTROLADO` (R0 ≤ 1). |
| FR-06 | Provide six result modules: SIR evolution, numerical error, cubic spline, numerical differentiation, Simpson integration and Newton-Raphson calibration. |
| FR-07 | Each module must show 4 numbered charts, a theory/formula panel and a written analysis (what is seen, why, conclusion) for every chart. |
| FR-08 | Only one module panel is open at a time; opening another closes the previous one. |
| FR-09 | Provide a **Reset** action that restores all parameters and results to their initial state. |
| FR-10 | Persist every applied simulation (parameters, key indicators and full monthly series for RK4 and Euler) in SQLite, avoiding duplicates of the most recent identical simulation. |
| FR-11 | Provide a history window with KPIs, an aggregate chart, parameter reload (button or double-click), single delete, and clear-all. |
| FR-12 | Deleted simulations go to a **trash bin** and are restorable for **7 days**, after which they are purged permanently. |
| FR-13 | Export a **PDF report** per module and a **complete PDF report** (cover + index + all modules). |
| FR-14 | Export the history to **Excel (.xlsx)** and **CSV**. |
| FR-15 | Include an in-app user guide that cites the data source (with a clickable link). |

### Non-functional requirements

| ID | Requirement |
|----|-------------|
| NFR-01 | **Offline & serverless**: a single-file SQLite database (`pandemia.db`), no server or internet needed (internet only to open the source link). |
| NFR-02 | **Desktop GUI** built with the Python standard library toolkit (Tkinter) — no web stack. |
| NFR-03 | **Numerical stability**: state variables are clamped to ≥ 0 and each month is subdivided into 10 sub-steps. |
| NFR-04 | **Responsiveness**: charts redraw live when sliders move; heavy exports run with a busy cursor. |
| NFR-05 | **Print-ready reports**: PDF output uses a light theme, serif fonts when available, and A4 portrait/landscape pages. |
| NFR-06 | **Robust persistence**: transactional access (commit / rollback), foreign keys enabled, automatic schema creation and lightweight migration of older databases (adds the `eliminada_en` column if missing). |
| NFR-07 | **Language**: user interface, theory and analysis texts are written in **Spanish**. |

### Software requirements

| Requirement | Details |
|-------------|---------|
| **Python** | 3.10 or newer recommended (development artifacts show CPython 3.11 and 3.14). |
| **Tkinter** | Bundled with the official Python installers for Windows/macOS. On Debian/Ubuntu: `sudo apt install python3-tk`. |
| **numpy** | Numerical arrays and math. |
| **matplotlib** | All charts (embedded via `FigureCanvasTkAgg`) and PDF generation (`PdfPages`). |
| **scipy** | `CubicSpline` for the spline module. |
| **openpyxl** | Excel workbook creation with formatting and native charts. |
| **sqlite3** | Python standard library (no install needed). |
| **OS** | Designed and tested on **Windows** (uses the *Consolas* font and emoji icons). Works on Linux/macOS if Tkinter and a monospace font are available. |
| **Display** | Recommended ≥ 1300 × 900 px; minimum window size is 1080 × 700. |

### Python dependencies (`requirements.txt`)

```text
numpy
matplotlib
scipy
openpyxl
```

---

## 🔧 Installation

```bash
# 1. Clone the repository
git clone https://github.com/ChristopherVP/PandemiaSimulador.git
cd PandemiaSimulador

# 2. (Recommended) create and activate a virtual environment
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux / macOS:
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt
```

---

## ▶️ Running the Application

```bash
python main.py
```

A splash screen appears for about 1.6 seconds, then the main window opens (1300 × 900). The SQLite database `pandemia.db` is created automatically next to the project the first time you run it.

---

## 🧭 How to Use It (Step by Step)

1. Open the **“🎛 Panel de Simulación”** tab and adjust **β, γ, I0 and N** with the sliders. *Nothing is recalculated yet — you are only choosing the data.*
2. Press **“▶ 2. Aplicar Simulación”**. The simulation is computed and saved to the history, the six result buttons appear, and the **“💾 Guardar reporte completo en PDF”** button is enabled.
3. Click any of the six result buttons (e.g. *Evolución*). The module opens right below, inside the same screen, with its 4 numbered charts.
4. Above the charts you will find **theory and formulas** (collapsible); below them, a **written analysis of each chart** — what is shown, why, and a conclusion.
5. Each module has its own **“💾 Guardar reporte de [module]”** button that exports just that module (charts + parameters + formulas + analysis) to PDF.
6. **“💾 Guardar reporte completo en PDF”** exports all six modules plus the quick preview in a single file.
7. Opening another module automatically closes the previous one.
8. **“🔄 Reiniciar”** restores parameters and results to the state at first launch.
9. **“📊 Historial y estadísticas”** opens the history window; **“📗 Generar Excel”** exports the history to a workbook.

The first tab, **“📘 Guía de Uso”**, contains the same explanation inside the app, together with the data-source link.

---

## 📐 The Mathematical Model

### SIR equations

The population *N* is split into Susceptible (S), Infected (I) and Recovered (R):

```text
dS/dt = -β · S · I / N
dI/dt =  β · S · I / N - γ · I
dR/dt =  γ · I

R0 = β / γ
```

- **β (beta)** — transmission rate (how easily the virus spreads).
- **γ (gamma)** — recovery rate (`1/γ` = average duration of the infectious period, in days).
- **R0** — basic reproduction number. `R0 > 1` → the epidemic grows (state **EPIDEMIA**); `R0 ≤ 1` → it fades out (state **CONTROLADO**).
- **Attack rate** = `(N − S_final) / N × 100 %`.

### Numerical solvers (`core/metodos_numericos.py`)

| Function | Description |
|----------|-------------|
| `euler_sir(...)` | Explicit Euler (order 1). Each month (`h = 30` days) is split into `subpasos = 10` internal sub-steps; values are clamped to ≥ 0. |
| `rk4_sir(...)` | Classical Runge-Kutta of order 4, same sub-stepping. Used as the **reference solution** in the rest of the software. |
| `derivacion_numerica(I, h)` | 3-point finite differences: forward at the start, centered in the interior, backward at the end. |
| `simpson_compuesta(I, a, b, h)` | Composite Simpson 1/3 rule; if the interval has an odd number of subintervals, the last one is dropped. |
| `newton_raphson_beta(...)` | Newton-Raphson on `f(β) = peak_simulated(β) − I_observed`, with a central-difference derivative (δ = 0.001), tolerance 1 person, max 15 iterations and β clipped to [0.001, 2.0]. |

Only one data point per month is shown on screen; internally each month is integrated with finer steps for accuracy.

---

## 📍 Default Parameters and Data Source

The simulator starts with values calibrated for the **Metropolitan District of Quito (DMQ)** at **epidemiological week 45 (cut-off 13 November 2021)**:

| Parameter | Default | Meaning / slider range |
|-----------|---------|------------------------|
| **N** | 2,584,622 | DMQ population older than 5 years (basis of the vaccination-coverage calculation). Slider allows only **±10,000** (2,574,622 – 2,594,622, step 500), since the population is practically constant over the simulated period. |
| **I0** | 330 | Approximation of active cases = new confirmed cases of the last two weeks (SE44 = 204 + SE45 = 126). Range 1 – 2000. |
| **β** | 0.085 | Transmission rate. Range 0.01 – 1.00 (step 0.005). |
| **γ** | 0.10 | Recovery rate (≈ 10-day infectious period). Range 0.01 – 0.50 (step 0.01). |
| **R0** | 0.85 | `β/γ` — a *controlled* epidemic (“Medio” alert level), consistent with the report. |
| **Months** | 10 | Simulation horizon. |

**Source:** Secretaría de Salud, Municipio del Distrito Metropolitano de Quito — *Informe Quincenal COVID-19 – Mes Noviembre 2021*.
Link: <https://www7.quito.gob.ec/mdmq_Ordenanzas/Administraci%C3%B3n%202019-2023/Comisiones%20del%20Concejo%20Metropolitano/Salud/2021/2021-11-29/Documentos%20para%20tratamiento/Punto%202/informe_quincenal_covid_19_mes_de_noviembre_2021.pdf>

The report is also used to relate each numerical method to a real epidemiological concept (e.g., hospital occupancy 56 % and ICU occupancy 59 % ↔ Simpson integration; weekly new cases 204 → 126 ↔ numerical derivative; biweekly reporting ↔ spline interpolation; test under-reporting bias ↔ numerical error).

---

## 🔬 The Six Results (Numerical Methods)

Every module follows the same template (`PanelTema`): a title bar with its own PDF export button, a collapsible **theory & formulas** panel, a Matplotlib figure with **4 numbered charts** (with zoom/pan toolbar), optional **module controls**, and an automatic **chart-by-chart analysis**.

### ① Evolution of the Epidemic — *SIR with Euler and RK4*
- Chart 1: S(t), I(t), R(t) with RK4 plus I(t) with Euler, peak annotation and an R0 / state badge.
- Chart 2: Susceptibles S(t). Chart 3: Infected and Recovered (dual axis). Chart 4: summary table (R0, state, RK4/Euler peak, peak error, S and R final, β/γ, N/I0, duration 1/γ).

### ② Reliability of the Simulation — *Numerical error*
- Compares Euler against RK4 (taken as the “true” value).
- **Absolute error** `Ea = |x_real − x_approx|` and **relative error** `Er = |x_real − x_approx| / |x_real| × 100 %`, with a 5 % reliability reference line.
- Charts: RK4 vs Euler, absolute error, relative error, and a month-by-month comparison table.

### ③ Estimation of Months Without Data — *Natural cubic spline*
- Builds a natural cubic spline (`scipy.interpolate.CubicSpline`) from “known” nodes of the RK4 curve to estimate the months in between, like filling gaps between biweekly reports.
- **Controls:** *Nodes (every N months)* (1–4) and *Month to estimate*.
- Charts: spline vs real curve, zoom around the chosen month, spline error over the whole range, and a table of precision vs. number of nodes.

### ④ Speed of Spread — *3-point numerical differentiation*
- Approximates `dI/dt` from the discrete I(t) values only; the zero crossing marks the epidemic peak.
- Charts: dI/dt coloured by growth/decline (plus the analytic derivative), I(t) and dI/dt superposed, error vs the analytic derivative, and a table of maximum speeds (infection/recovery speed, `S ≈ N/R0` at the peak).

### ⑤ Health-System Impact — *Composite Simpson integration*
- Area under I(t) between two months = cumulative “person-months” of load on the health system.
- **Controls:** *Start month (a)* and *End month (b)*.
- Charts: shaded area, convergence of **Trapezoid O(h²) vs Simpson O(h⁴)** on a log scale (against a 16×-finer RK4 reference), bar comparison of Simpson / composite trapezoid / single trapezoid, and an interval summary (average monthly load, % of total epidemic).

### ⑥ Calibration of Real Contagion — *Newton-Raphson*
- Finds the β that makes the simulated peak match an observed peak: `f(β) = peak(β) − I_obs`, `β_{n+1} = β_n − f(β_n)/f'(β_n)`.
- **Controls:** *I_obs peak (observed)* and *β0 initial estimate*.
- Charts: original vs calibrated curve, convergence of |f(β)| and β, the curve f(β) with the root marked, and an iteration table (β_n, f(β_n), |f(β_n)|, |Δβ|).
- Handles edge cases explicitly: if R0 ≤ 1 the peak is always I0 (derivative ≈ 0), and an observed peak below I0 is unreachable — the app explains why it did not converge and suggests what to change.

### Quick Preview
A summary panel on the simulation tab shows R0, the epidemic state and an overview of S/I/R with an automatic analysis, before opening any module.

---

## 🗂 Simulation History, Trash Bin and Statistics

Pressing **Apply Simulation** saves the run to SQLite (unless it is identical to the latest active one). The **Historial y estadísticas** window offers:

- **KPI cards:** total simulations, controlled, in epidemic, average R0, average peak, average attack rate (%).
- **Aggregate chart:** average infected per month across all saved simulations, with a min–max band.
- **Table of simulations** with all parameters and indicators; **double-click** or **“↩ Cargar parámetros”** reloads a simulation’s parameters into the panel and re-applies it.
- **Delete selection** / **Clear history** → items go to the **🗑 Trash bin**.
- **Trash bin tab:** shows deleted simulations with the time remaining; **restore selection** or **restore all**. After **7 days** they are permanently purged (also checked at startup).
- **Export** buttons for Excel and CSV.

---

## 📤 Exports: PDF, Excel and CSV

### PDF (Matplotlib `PdfPages`, A4)
- **Per-module report:** charts page (landscape) + summary pages (portrait) with parameters, formulas, explanation and chart-by-chart analysis.
- **Complete report:** cover page with an automatic **table of contents with page numbers**, quick-preview section, and the six modules, with page footers (“Página n de total”). Uses a light, print-friendly theme and serif fonts when available. PDF metadata includes title and author.

### Excel (`.xlsx`, via openpyxl)
Four formatted sheets (hidden gridlines, styled headers, zebra rows, frozen panes and auto-filters). Derived values are written as **live Excel formulas** (R0 = β/γ, epidemic state, attack rate, averages, `MINIFS`/`MAXIFS`, error columns), so the workbook recalculates when opened.

| Sheet | Content |
|-------|---------|
| **Resumen** | KPIs (saved simulations, controlled vs. epidemic, average R0, average/maximum peak, average attack rate), a comparison by epidemic state, a **bar chart** of the peak per simulation, and the data-source note. |
| **Simulaciones** | One row per simulation with all parameters and indicators; the state column is colour-coded (red = `EPIDEMIA`, green = `CONTROLADO`). |
| **Series mensuales** | Month-by-month S, I, R (RK4) and I (Euler) for every simulation, with absolute and relative Euler-vs-RK4 error. |
| **Estadísticas por mes** | Average/min/max infected, average S and R, and average Euler error per month, with a **line chart**. |

### CSV
Semicolon-separated, UTF-8 with BOM (`utf-8-sig`) so Excel opens it correctly. Columns: `id, fecha, beta, gamma, n, i0, meses, r0, estado, pico, mes_pico, s_final, r_final, tasa_ataque, error_euler_max`.

---

## 🗄 Database Schema

SQLite file: `pandemia.db` (auto-created, ignored by Git).

```sql
CREATE TABLE simulaciones (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha           TEXT    NOT NULL,   -- 'YYYY-MM-DD HH:MM:SS'
    beta            REAL    NOT NULL,
    gamma           REAL    NOT NULL,
    n               INTEGER NOT NULL,
    i0              INTEGER NOT NULL,
    meses           INTEGER NOT NULL,
    r0              REAL    NOT NULL,
    estado          TEXT    NOT NULL,   -- 'EPIDEMIA' | 'CONTROLADO'
    pico            REAL    NOT NULL,   -- peak of infected (RK4)
    mes_pico        INTEGER NOT NULL,
    s_final         REAL    NOT NULL,
    r_final         REAL    NOT NULL,
    tasa_ataque     REAL    NOT NULL,   -- attack rate (%)
    error_euler_max REAL    NOT NULL,   -- max |I_RK4 - I_Euler|
    eliminada_en    TEXT                -- NULL = active; date = in trash bin
);

CREATE TABLE serie_mensual (
    simulacion_id INTEGER NOT NULL REFERENCES simulaciones(id) ON DELETE CASCADE,
    mes           INTEGER NOT NULL,
    s REAL NOT NULL, i REAL NOT NULL, r REAL NOT NULL,
    s_euler REAL NOT NULL, i_euler REAL NOT NULL, r_euler REAL NOT NULL,
    PRIMARY KEY (simulacion_id, mes)
);
CREATE INDEX idx_serie_mes ON serie_mensual(mes);
```

---

## 🧱 Project Structure

```text
PandemiaSimulador/
├── main.py                     # Entry point: theme + splash screen + main window
├── requirements.txt            # numpy, matplotlib, scipy, openpyxl
├── .gitignore                  # venv, caches, build output, *.db, *.xlsx, *.csv
├── pandemia.db                 # SQLite history (auto-generated, not versioned)
│
├── core/                       # Logic (no GUI)
│   ├── modelo_sir.py           # SIR derivatives dS/dt, dI/dt, dR/dt
│   ├── metodos_numericos.py    # Euler, RK4, differentiation, Simpson, Newton-Raphson
│   ├── estado_global.py        # Shared state (β, γ, N, I0, months) + observer pattern
│   └── base_datos.py           # SQLite persistence, trash bin, statistics queries
│
├── ui/                         # Reusable interface pieces
│   ├── estilo.py               # Dark/light themes, Matplotlib styling, table/legend helpers
│   ├── componentes.py          # Sliders and the collapsible theory/formula panel
│   ├── ventana_base.py         # PanelTema base class + ModuloReporte (screen + PDF)
│   ├── splash.py               # Animated splash screen
│   ├── reporte.py              # PDF layout engine (cover, index, chart and summary pages)
│   └── exportar_excel.py       # Excel (4 sheets + charts) and CSV export
│
└── ventanas/                   # Screens and result modules
    ├── ventana_principal.py    # Main window: guide tab + simulation panel
    ├── registro.py             # List of the six result modules (TEMAS)
    ├── vista_previa.py         # Quick preview / summary of the simulation
    ├── ventana_sir.py          # ① SIR evolution
    ├── ventana_error.py        # ② Numerical error
    ├── ventana_spline.py       # ③ Cubic spline
    ├── ventana_derivacion.py   # ④ Numerical differentiation
    ├── ventana_simpson.py      # ⑤ Simpson integration
    ├── ventana_nr.py           # ⑥ Newton-Raphson
    └── ventana_historial.py    # History, statistics and trash bin
```

---

## 🏗 Architecture and Design Notes

- **Separation of concerns:** `core/` contains pure math and persistence with no GUI dependency; `ui/` holds reusable widgets, styling and report generation; `ventanas/` contains the screens.
- **Observer pattern:** `EstadoGlobal` keeps β, γ, N, I0 and the months, and notifies subscribed panels (`suscribir` / `notificar`) so charts update live. Dead Tk widgets are handled safely (`TclError` is ignored).
- **Template-method modules:** each result inherits from `PanelTema` and implements `teoria()`, `crear_ejes()`, `dibujar()` and `analisis()`. The same code draws on screen **and** into PDF pages (`dibujar_en`), so screen and report always match.
- **Module registry:** adding a seventh result only needs a new `PanelTema` subclass and one entry in `registro.TEMAS` / `CLASES_TEMA`.
- **Safe persistence:** a context-managed connection with commit/rollback, `PRAGMA foreign_keys = ON`, soft deletion through `eliminada_en`, and an automatic purge of expired trash entries.
- **Dynamic analysis text:** every module generates its analysis text dynamically from the current numbers (e.g., different conclusions for R0 > 1 vs R0 ≤ 1).

---

## ⚠️ Model Assumptions and Limitations

This is an **educational tool**, not a forecasting or public-health decision tool.

- Classic SIR assumptions: homogeneous mixing, constant β and γ, **no latent (exposed) stage, no vaccination, no births/deaths, no reinfection**.
- The “observed” peak in the Newton-Raphson module and the “known” nodes in the spline module are **simulated** from the model itself to demonstrate the methods, not real measured series.
- β and γ were **adjusted** to reproduce a controlled-epidemic scenario (R0 < 1); they are not statistically fitted to the full official time series.
- I0 is an approximation of active cases from two weeks of new confirmed cases, and official figures are subject to under-reporting.
- With R0 ≤ 1 the infected curve decreases from the start (the peak is I0); use β > γ to explore growth scenarios and the Newton-Raphson calibration.

---

## 🛠 Troubleshooting

| Problem | Solution |
|---------|----------|
| `ModuleNotFoundError: tkinter` | Install Tkinter (`sudo apt install python3-tk` on Debian/Ubuntu; reinstall Python with “tcl/tk” on Windows/macOS). |
| `ModuleNotFoundError: numpy / scipy / matplotlib / openpyxl` | Run `pip install -r requirements.txt` inside your virtual environment. |
| “Could not save: close the file if it is open in Excel” | The target `.xlsx` is open in Excel; close it and export again. |
| “Historial: could not save in database” | Check write permissions in the project folder (`pandemia.db`). |
| Fonts/emojis look different on Linux or macOS | The UI is designed around *Consolas*; install a similar monospace font or accept the fallback. |
| Newton-Raphson “NO CONVERGIÓ” | Use a larger β0, or an observed peak larger than I0 (and consider R0 > 1 settings). |

---

## 👤 Author, Repository and License

- **Author:** Christopher Josué Villón Peralta
- **Repository:** <https://github.com/ChristopherVP/PandemiaSimulador>
- **Context:** university project for a Numerical Methods course.
- **License:** *not specified yet* — add a `LICENSE` file (e.g., MIT) if you want others to reuse the code.

---

*Data source: Secretaría de Salud del DMQ — Informe Quincenal COVID-19, November 2021. This software is for educational purposes only.*
