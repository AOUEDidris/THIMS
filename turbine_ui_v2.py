# -*- coding: utf-8 -*-
"""
=============================================================================
 TURBINE HEALTH INDEX & MAINTENANCE SCHEDULER  — v2.1 Algérie
 Logiciel de gestion préventive des turbines à gaz
 Marché algérien (Sonatrach / Sonelgaz / SKB / GTP)
=============================================================================
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import os
import datetime
import math

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.patches as mpatches

# ─────────────────────────────────────────────────────────────────────────────
#  COLOR PALETTE — Industrial Dark Theme
# ─────────────────────────────────────────────────────────────────────────────
BG_DARK    = "#0d1117"
BG_PANEL   = "#161b22"
BG_CARD    = "#1c2128"
ACCENT     = "#f78166"
ACCENT2    = "#58a6ff"
TEXT_PRI   = "#e6edf3"
TEXT_MUT   = "#8b949e"
GREEN      = "#3fb950"
YELLOW     = "#d29922"
RED        = "#f85149"
BORDER     = "#30363d"

# ─────────────────────────────────────────────────────────────────────────────
#  TURBINE FLEET — Algeria
# ─────────────────────────────────────────────────────────────────────────────
TURBINE_MODELS = {
    "GE Frame 6B (PG6581B)": {"eoh_limit": 32000, "fs": 15.0, "eta0": 0.330, "foul_max": 0.045},
    "GE Frame 9E (PG9171E)": {"eoh_limit": 25000, "fs": 20.0, "eta0": 0.345, "foul_max": 0.050},
    "GE LM2500+":            {"eoh_limit": 20000, "fs": 10.0, "eta0": 0.380, "foul_max": 0.040},
    "Siemens SGT-800":       {"eoh_limit": 30000, "fs": 18.0, "eta0": 0.375, "foul_max": 0.042},
    "Solar Centaur 50":      {"eoh_limit": 18000, "fs": 12.0, "eta0": 0.290, "foul_max": 0.035},
    "Rolls-Royce Avon":      {"eoh_limit": 20000, "fs": 10.0, "eta0": 0.300, "foul_max": 0.038},
}

OPERATORS = [
    "Sonatrach — Division Production",
    "Sonelgaz — Groupe Production",
    "GTP — Groupement Hassi R'Mel",
    "SKB — Groupement Berkine",
    "Groupement Bir Seba",
    "SHPG — Hassi Messaoud",
    "Autre",
]

COST_DZD = {
    "Fonctionnement Normal":          (0,          500_000),
    "Inspection Combustion / Mineure": (2_500_000,  8_000_000),
    "Grande Revision Requise":        (45_000_000, 180_000_000),
}

HISTORY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "turbine_history.json")


# ─────────────────────────────────────────────────────────────────────────────
#  CORE ENGINE
# ─────────────────────────────────────────────────────────────────────────────
class Engine:
    def __init__(self, p: dict):
        self.eoh_limit = p["eoh_limit"]
        self.fs        = p["fs"]
        self.eta0      = p["eta0"]
        self.foul_max  = p["foul_max"]

    def evaluate(self, oh: float, ns: int, eta: float, pr_drop: float = 0.0) -> dict:
        eoh       = oh + self.fs * ns
        fouling   = max(0.0, self.eta0 - eta)

        h_eoh  = max(0.0, 100.0 * (1.0 - eoh / self.eoh_limit))
        h_perf = max(0.0, 100.0 * (1.0 - fouling / self.foul_max))
        h_pr   = max(0.0, 100.0 * (1.0 - pr_drop / 0.10))

        thi       = 0.55 * h_eoh + 0.35 * h_perf + 0.10 * h_pr
        thi       = max(0.0, min(100.0, thi))
        remaining = max(0.0, self.eoh_limit - eoh)
        life_pct  = min(100.0, 100.0 * eoh / self.eoh_limit)

        if thi < 60 or eoh >= self.eoh_limit:
            urgency = "Grande Revision Requise"
            action  = "Programmer une Grande Revision (GR) immediatement."
            action2 = "Jdawla tasjil GR fi aqrab waqt / جدولة الإصلاح الكبير فوراً"
        elif thi <= 80:
            urgency = "Inspection Combustion / Mineure"
            action  = "Programmer Inspection Combustion + lavage compresseur."
            action2 = "Fas inspection + ghassil compresseur / فحص غرفة الاحتراق + غسيل الضاغط"
        else:
            urgency = "Fonctionnement Normal"
            action  = "Surveillance standard. Aucune intervention requise."
            action2 = "Tachghil adi, la tadakhol / تشغيل اعتيادي، لا يلزم تدخل"

        c_min, c_max = COST_DZD[urgency]

        return {
            "timestamp": datetime.datetime.now().isoformat(),
            "inputs":    {"oh": oh, "ns": ns, "eta": eta, "pr_drop": pr_drop},
            "metrics":   {
                "EOH":      round(eoh, 1),
                "h_eoh":    round(h_eoh, 1),
                "h_perf":   round(h_perf, 1),
                "h_pr":     round(h_pr, 1),
                "fouling":  round(fouling, 4),
                "THI":      round(thi, 1),
                "life_pct": round(life_pct, 1),
                "remaining":round(remaining, 0),
            },
            "rec": {
                "urgency": urgency,
                "action":  action,
                "action2": action2,
                "c_min":   c_min,
                "c_max":   c_max,
            }
        }


# ─────────────────────────────────────────────────────────────────────────────
#  HISTORY MANAGER
# ─────────────────────────────────────────────────────────────────────────────
class History:
    def __init__(self):
        self.recs = []
        if os.path.exists(HISTORY_FILE):
            try:
                with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                    self.recs = json.load(f)
            except Exception:
                self.recs = []

    def save(self, eq_id: str, model: str, operator: str, result: dict):
        self.recs.append({"eq_id": eq_id, "model": model, "operator": operator, **result})
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(self.recs, f, indent=2, ensure_ascii=False)

    def for_eq(self, eq_id: str):
        return [r for r in self.recs if r.get("eq_id") == eq_id]

    def all_ids(self):
        seen, out = set(), []
        for r in self.recs:
            e = r.get("eq_id", "")
            if e and e not in seen:
                seen.add(e); out.append(e)
        return out


# ─────────────────────────────────────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def thi_col(v):
    return GREEN if v >= 80 else (YELLOW if v >= 60 else RED)


def styled_entry(parent, default=""):
    e = tk.Entry(parent, bg=BG_DARK, fg=TEXT_PRI, insertbackground=TEXT_PRI,
                 relief="flat", font=("Segoe UI", 10), bd=4)
    e.insert(0, default)
    return e


def styled_label(parent, text, size=9, bold=False, color=TEXT_PRI):
    return tk.Label(parent, text=text, bg=parent["bg"],
                    fg=color, font=("Segoe UI", size, "bold" if bold else "normal"))


def action_button(parent, text, cmd, bg=ACCENT2, fg="white"):
    return tk.Button(parent, text=text, command=cmd, bg=bg, fg=fg,
                     activebackground=bg, activeforeground=fg,
                     font=("Segoe UI", 9, "bold"), relief="flat",
                     bd=0, padx=14, pady=7, cursor="hand2")


def draw_gauge(canvas, thi, w=240, h=150):
    canvas.delete("all")
    cx, cy, r = w // 2, h - 14, min(w, h * 2) // 2 - 12
    col = thi_col(thi)
    # background arc
    canvas.create_arc(cx-r, cy-r, cx+r, cy+r, start=0, extent=180,
                      style="arc", outline=BORDER, width=15)
    # value arc
    ext = 180.0 * thi / 100.0
    if ext > 0:
        canvas.create_arc(cx-r, cy-r, cx+r, cy+r, start=0, extent=ext,
                          style="arc", outline=col, width=15)
    # needle
    ang = math.radians(180.0 - ext)
    nx = cx + (r - 10) * math.cos(ang)
    ny = cy - (r - 10) * math.sin(ang)
    canvas.create_line(cx, cy, nx, ny, fill=TEXT_PRI, width=3)
    canvas.create_oval(cx-5, cy-5, cx+5, cy+5, fill=TEXT_PRI, outline="")
    # labels
    canvas.create_text(cx-r+2, cy+8,  text="0%",   fill=TEXT_MUT, font=("Segoe UI", 8))
    canvas.create_text(cx+r-2, cy+8,  text="100%",  fill=TEXT_MUT, font=("Segoe UI", 8))
    canvas.create_text(cx, cy+18, text=f"{thi:.1f}%", fill=col, font=("Segoe UI", 16, "bold"))
    canvas.create_text(cx, cy+34, text="Turbine Health Index", fill=TEXT_MUT, font=("Segoe UI", 8))


# ─────────────────────────────────────────────────────────────────────────────
#  METRIC CARD WIDGET
# ─────────────────────────────────────────────────────────────────────────────
class KpiCard(tk.Frame):
    def __init__(self, parent, title, unit="", accent=ACCENT2):
        super().__init__(parent, bg=BG_CARD, padx=14, pady=10)
        self._accent = accent
        tk.Label(self, text=title, bg=BG_CARD, fg=TEXT_MUT,
                 font=("Segoe UI", 8)).pack(anchor="w")
        self.val = tk.Label(self, text="—", bg=BG_CARD, fg=accent,
                            font=("Segoe UI", 20, "bold"))
        self.val.pack(anchor="w")
        tk.Label(self, text=unit, bg=BG_CARD, fg=TEXT_MUT,
                 font=("Segoe UI", 8)).pack(anchor="w")

    def set(self, value, color=None):
        self.val.config(text=str(value), fg=color or self._accent)


# ─────────────────────────────────────────────────────────────────────────────
#  HEALTH BAR WIDGET
# ─────────────────────────────────────────────────────────────────────────────
class HealthBar(tk.Frame):
    def __init__(self, parent, title):
        super().__init__(parent, bg=BG_CARD)
        tk.Label(self, text=title, bg=BG_CARD, fg=TEXT_MUT,
                 font=("Segoe UI", 8), width=26, anchor="w").pack(side="left")
        self.canvas = tk.Canvas(self, height=14, bg=BG_DARK,
                                highlightthickness=0)
        self.canvas.pack(side="left", fill="x", expand=True)
        self.pct = tk.Label(self, text=" 0%", bg=BG_CARD, fg=TEXT_PRI,
                            font=("Segoe UI", 8, "bold"), width=5)
        self.pct.pack(side="left")

    def update(self, value):
        self.canvas.update_idletasks()
        w = self.canvas.winfo_width() or 250
        col = thi_col(value)
        self.canvas.delete("all")
        self.canvas.create_rectangle(0, 1, w, 13, fill=BORDER, outline="")
        fw = int(w * value / 100)
        if fw > 0:
            self.canvas.create_rectangle(0, 1, fw, 13, fill=col, outline="")
        self.pct.config(text=f"{value:.0f}%", fg=col)


# ─────────────────────────────────────────────────────────────────────────────
#  MAIN APPLICATION
# ─────────────────────────────────────────────────────────────────────────────
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Turbine Health Index & Maintenance Scheduler — v2.1 Algerie")
        self.geometry("1060x730")
        self.configure(bg=BG_DARK)
        self.resizable(True, True)
        self.history     = History()
        self.last_result = None
        self.last_meta   = {}
        self._build_header()
        self._build_tabs()

    # ── HEADER ───────────────────────────────────────────────────────────────
    def _build_header(self):
        hdr = tk.Frame(self, bg=BG_PANEL, pady=9)
        hdr.pack(fill="x")
        tk.Label(hdr, text="  TURBINE HEALTH INDEX & MAINTENANCE SCHEDULER",
                 bg=BG_PANEL, fg=ACCENT, font=("Segoe UI", 13, "bold")).pack(side="left", padx=16)
        tk.Label(hdr, text="v2.1  |  Marche Algerien  |  Sonatrach / Sonelgaz",
                 bg=BG_PANEL, fg=TEXT_MUT, font=("Segoe UI", 9)).pack(side="left", padx=6)
        self._clk = tk.Label(hdr, text="", bg=BG_PANEL, fg=TEXT_MUT, font=("Segoe UI", 9))
        self._clk.pack(side="right", padx=20)
        self._tick()

    def _tick(self):
        self._clk.config(text=datetime.datetime.now().strftime("%d/%m/%Y   %H:%M:%S"))
        self.after(1000, self._tick)

    # ── TABS ─────────────────────────────────────────────────────────────────
    def _build_tabs(self):
        style = ttk.Style(self)
        style.theme_use("default")
        style.configure("TNotebook", background=BG_DARK, borderwidth=0)
        style.configure("TNotebook.Tab", background=BG_PANEL, foreground=TEXT_MUT,
                        padding=[16, 6], font=("Segoe UI", 9, "bold"))
        style.map("TNotebook.Tab",
                  background=[("selected", BG_CARD)],
                  foreground=[("selected", ACCENT2)])

        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=10, pady=(6, 10))

        self.t_dash  = tk.Frame(nb, bg=BG_DARK)
        self.t_input = tk.Frame(nb, bg=BG_PANEL)
        self.t_hist  = tk.Frame(nb, bg=BG_DARK)
        self.t_rep   = tk.Frame(nb, bg=BG_PANEL)

        nb.add(self.t_dash,  text="  Dashboard  ")
        nb.add(self.t_input, text="  Saisie des Donnees  ")
        nb.add(self.t_hist,  text="  Historique & Tendances  ")
        nb.add(self.t_rep,   text="  Rapport & Export  ")

        self._build_dash()
        self._build_input()
        self._build_hist()
        self._build_rep()

    # ═════════════════════════════════════════════════════════════════════════
    #  TAB 1 — DASHBOARD
    # ═════════════════════════════════════════════════════════════════════════
    def _build_dash(self):
        p = self.t_dash

        # ── KPI cards ──
        row = tk.Frame(p, bg=BG_DARK)
        row.pack(fill="x", padx=14, pady=(12, 6))
        self.kpi_thi  = KpiCard(row, "Turbine Health Index (THI)", "%",      ACCENT2)
        self.kpi_eoh  = KpiCard(row, "Equivalent Oper. Hours (EOH)", "h",    ACCENT)
        self.kpi_rem  = KpiCard(row, "Heures restantes avant MO", "h",       GREEN)
        self.kpi_life = KpiCard(row, "Vie consommee", "%",                   YELLOW)
        for c in (self.kpi_thi, self.kpi_eoh, self.kpi_rem, self.kpi_life):
            c.pack(side="left", expand=True, fill="both", padx=4, pady=2)

        # ── Middle: gauge + status ──
        mid = tk.Frame(p, bg=BG_DARK)
        mid.pack(fill="both", expand=True, padx=14, pady=4)

        # Gauge panel
        gf = tk.Frame(mid, bg=BG_CARD, padx=18, pady=14)
        gf.pack(side="left", fill="both", padx=(0, 8))
        tk.Label(gf, text="Jauge de Sante", bg=BG_CARD, fg=TEXT_MUT,
                 font=("Segoe UI", 9, "bold")).pack()
        self.gauge_c = tk.Canvas(gf, width=240, height=160, bg=BG_CARD, highlightthickness=0)
        self.gauge_c.pack(pady=8)
        draw_gauge(self.gauge_c, 0)

        # Status panel
        sf = tk.Frame(mid, bg=BG_CARD, padx=18, pady=14)
        sf.pack(side="left", fill="both", expand=True)
        tk.Label(sf, text="Etat du Systeme", bg=BG_CARD, fg=TEXT_MUT,
                 font=("Segoe UI", 9, "bold")).pack(anchor="w")
        ttk.Separator(sf).pack(fill="x", pady=6)

        self.lbl_urgency = tk.Label(sf, text="En attente d'evaluation...",
                                    bg=BG_CARD, fg=TEXT_MUT,
                                    font=("Segoe UI", 11, "bold"), anchor="w")
        self.lbl_urgency.pack(fill="x", pady=(4, 2))

        self.lbl_action = tk.Label(sf, text="", bg=BG_CARD, fg=TEXT_MUT,
                                   font=("Segoe UI", 9), anchor="w", wraplength=380, justify="left")
        self.lbl_action.pack(fill="x")

        self.lbl_action2 = tk.Label(sf, text="", bg=BG_CARD, fg=TEXT_MUT,
                                    font=("Segoe UI", 9), anchor="w", wraplength=380, justify="left")
        self.lbl_action2.pack(fill="x", pady=(2, 8))

        ttk.Separator(sf).pack(fill="x", pady=4)
        tk.Label(sf, text="Estimation cout d'intervention (DZD) :",
                 bg=BG_CARD, fg=TEXT_MUT, font=("Segoe UI", 8)).pack(anchor="w", pady=(6, 2))
        self.lbl_cost = tk.Label(sf, text="—", bg=BG_CARD, fg=ACCENT,
                                  font=("Segoe UI", 12, "bold"))
        self.lbl_cost.pack(anchor="w")

        # ── Sub-health bars ──
        bf = tk.Frame(p, bg=BG_CARD, padx=18, pady=12)
        bf.pack(fill="x", padx=14, pady=(4, 10))
        tk.Label(bf, text="Decomposition du THI", bg=BG_CARD, fg=TEXT_MUT,
                 font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(0, 6))
        self.bar_eoh  = HealthBar(bf, "Sante EOH  (55%)")
        self.bar_perf = HealthBar(bf, "Sante Performance  (35%)")
        self.bar_pr   = HealthBar(bf, "Sante Pression  (10%)")
        for b in (self.bar_eoh, self.bar_perf, self.bar_pr):
            b.pack(fill="x", pady=2)

    def _refresh_dash(self, r: dict):
        m   = r["metrics"]
        rec = r["rec"]
        thi = m["THI"]
        col = thi_col(thi)

        self.kpi_thi.set(f"{thi:.1f}", col)
        self.kpi_eoh.set(f"{m['EOH']:,.0f}")
        self.kpi_rem.set(f"{m['remaining']:,.0f}")
        self.kpi_life.set(f"{m['life_pct']:.1f}",
                          RED if m['life_pct'] > 85 else (YELLOW if m['life_pct'] > 60 else GREEN))

        draw_gauge(self.gauge_c, thi)

        self.lbl_urgency.config(text=f"  {rec['urgency']}", fg=col)
        self.lbl_action.config(text=rec['action'], fg=TEXT_PRI)
        self.lbl_action2.config(text=rec['action2'], fg=TEXT_MUT)

        c_min, c_max = rec['c_min'], rec['c_max']
        self.lbl_cost.config(text="Aucun cout prevu" if c_min == 0 and c_max == 0
                             else f"{c_min:,.0f}  —  {c_max:,.0f}  DZD")

        self.after(60, lambda: self.bar_eoh.update(m["h_eoh"]))
        self.after(60, lambda: self.bar_perf.update(m["h_perf"]))
        self.after(60, lambda: self.bar_pr.update(m["h_pr"]))

    # ═════════════════════════════════════════════════════════════════════════
    #  TAB 2 — INPUT FORM
    # ═════════════════════════════════════════════════════════════════════════
    def _build_input(self):
        p = self.t_input

        tk.Label(p, text="  Saisie des parametres operationnels  /  Idkhal al ma'ayir at-tashghiliya",
                 bg=BG_PANEL, fg=ACCENT, font=("Segoe UI", 11, "bold"), pady=10).pack(fill="x")

        form = tk.Frame(p, bg=BG_PANEL)
        form.pack(fill="both", expand=True, padx=20, pady=6)

        # ── Left: identification ──
        lf = tk.Frame(form, bg=BG_CARD, padx=16, pady=14)
        lf.pack(side="left", fill="both", expand=True, padx=(0, 8))
        tk.Label(lf, text="Identification de l'equipement", bg=BG_CARD,
                 fg=TEXT_MUT, font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 8))

        def lbl(parent, text):
            tk.Label(parent, text=text, bg=BG_CARD, fg=TEXT_MUT,
                     font=("Segoe UI", 9), anchor="w").pack(fill="x", padx=2, pady=(4, 0))

        lbl(lf, "ID Equipement :")
        self.e_id = styled_entry(lf, "GT-101")
        self.e_id.pack(fill="x", padx=2, pady=(0, 6))

        lbl(lf, "Operateur :")
        self.e_op = ttk.Combobox(lf, values=OPERATORS, state="readonly",
                                  font=("Segoe UI", 9))
        self.e_op.set(OPERATORS[0])
        self.e_op.pack(fill="x", padx=2, pady=(0, 6))

        lbl(lf, "Modele de turbine :")
        self.e_model = ttk.Combobox(lf, values=list(TURBINE_MODELS.keys()),
                                     state="readonly", font=("Segoe UI", 9))
        self.e_model.set(list(TURBINE_MODELS.keys())[0])
        self.e_model.pack(fill="x", padx=2, pady=(0, 6))
        self.e_model.bind("<<ComboboxSelected>>", self._on_model_change)

        self.lbl_model_info = tk.Label(lf, text="", bg=BG_CARD, fg=TEXT_MUT,
                                        font=("Segoe UI", 7), justify="left")
        self.lbl_model_info.pack(anchor="w", padx=2, pady=(2, 0))
        self._on_model_change()

        # ── Right: operational params ──
        rf = tk.Frame(form, bg=BG_CARD, padx=16, pady=14)
        rf.pack(side="left", fill="both", expand=True)
        tk.Label(rf, text="Parametres operationnels", bg=BG_CARD,
                 fg=TEXT_MUT, font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 8))

        def field(parent, txt, default, tip=""):
            tk.Label(parent, text=txt, bg=BG_CARD, fg=TEXT_MUT,
                     font=("Segoe UI", 9), anchor="w").pack(fill="x", padx=2, pady=(4, 0))
            e = styled_entry(parent, default)
            e.pack(fill="x", padx=2, pady=(0, 2))
            if tip:
                tk.Label(parent, text=tip, bg=BG_CARD, fg=TEXT_MUT,
                         font=("Segoe UI", 7)).pack(anchor="w", padx=2)
            return e

        self.e_oh  = field(rf, "Heures de fonctionnement (OH) :", "12000")
        self.e_ns  = field(rf, "Cycles demarrage/arret (Ns) :", "100")
        self.e_eta = field(rf, "Rendement thermique actuel (ex: 0.330) :", "0.325",
                           tip="Rendement nominal selon le modele selectionne")
        self.e_pr  = field(rf, "Chute taux de compression (0.02 = 2%) :", "0.01",
                           tip="Entrer 0 si non disponible")

        # ── Buttons ──
        brow = tk.Frame(p, bg=BG_PANEL)
        brow.pack(pady=14)
        action_button(brow, "  Evaluer la sante  ",
                      self._run_eval, bg=ACCENT).pack(side="left", padx=8)
        action_button(brow, "  Reinitialiser  ",
                      self._reset, bg=BG_CARD, fg=TEXT_MUT).pack(side="left", padx=8)

    def _on_model_change(self, event=None):
        m = self.e_model.get()
        if m in TURBINE_MODELS:
            p = TURBINE_MODELS[m]
            self.lbl_model_info.config(
                text=(f"EOH limit: {p['eoh_limit']:,} h  |  "
                      f"Start factor: {p['fs']} h/cycle  |  "
                      f"Rendement nominal: {p['eta0']*100:.1f}%"))

    def _reset(self):
        for e, v in [(self.e_oh, "0"), (self.e_ns, "0"),
                     (self.e_eta, "0.330"), (self.e_pr, "0.0")]:
            e.delete(0, tk.END); e.insert(0, v)

    def _run_eval(self):
        try:
            oh  = float(self.e_oh.get())
            ns  = int(self.e_ns.get())
            eta = float(self.e_eta.get())
            pr  = float(self.e_pr.get())
        except ValueError:
            messagebox.showerror("Erreur", "Veuillez entrer des valeurs numeriques valides.")
            return

        model_name = self.e_model.get()
        engine = Engine(TURBINE_MODELS.get(model_name, list(TURBINE_MODELS.values())[0]))
        result = engine.evaluate(oh, ns, eta, pr)
        self.last_result = result
        self.last_meta = {
            "eq_id": self.e_id.get().strip() or "GT-XXX",
            "model": model_name,
            "operator": self.e_op.get(),
        }
        self.history.save(self.last_meta["eq_id"], self.last_meta["model"],
                          self.last_meta["operator"], result)

        self._refresh_dash(result)
        self._refresh_rep(result)
        self._refresh_hist(self.last_meta["eq_id"])

        thi = result["metrics"]["THI"]
        messagebox.showinfo(
            "Evaluation terminee",
            f"THI = {thi:.1f}%\n{result['rec']['urgency']}")

    # ═════════════════════════════════════════════════════════════════════════
    #  TAB 3 — HISTORY CHART
    # ═════════════════════════════════════════════════════════════════════════
    def _build_hist(self):
        p = self.t_hist

        top = tk.Frame(p, bg=BG_DARK)
        top.pack(fill="x", padx=16, pady=(12, 4))
        tk.Label(top, text="Evolution du THI dans le temps", bg=BG_DARK,
                 fg=TEXT_PRI, font=("Segoe UI", 10, "bold")).pack(side="left")

        self.hist_id_var = tk.StringVar()
        self.hist_combo  = ttk.Combobox(top, textvariable=self.hist_id_var,
                                         state="readonly", width=16)
        self.hist_combo.pack(side="right", padx=6)
        action_button(top, " Charger ",
                      lambda: self._refresh_hist(self.hist_id_var.get()),
                      bg=ACCENT2).pack(side="right", padx=4)
        tk.Label(top, text="ID Equipement:", bg=BG_DARK, fg=TEXT_MUT,
                 font=("Segoe UI", 9)).pack(side="right")

        self.fig   = Figure(figsize=(9, 4.8), facecolor=BG_PANEL)
        self.ax    = self.fig.add_subplot(111)
        self._style_ax(self.ax)
        self.ax.set_title("Aucune donnee chargee", color=TEXT_MUT)

        self.canvas_fig = FigureCanvasTkAgg(self.fig, master=p)
        self.canvas_fig.get_tk_widget().pack(fill="both", expand=True, padx=16, pady=8)
        self._update_hist_combo()

    def _style_ax(self, ax):
        ax.set_facecolor(BG_DARK)
        for sp in ax.spines.values():
            sp.set_edgecolor(BORDER)
        ax.tick_params(colors=TEXT_MUT, labelsize=8)
        ax.yaxis.label.set_color(TEXT_MUT)
        ax.xaxis.label.set_color(TEXT_MUT)
        ax.title.set_color(TEXT_MUT)

    def _update_hist_combo(self):
        ids = self.history.all_ids()
        self.hist_combo["values"] = ids
        if ids:
            self.hist_combo.set(ids[-1])

    def _refresh_hist(self, eq_id: str):
        self._update_hist_combo()
        recs = self.history.for_eq(eq_id)
        self.ax.clear()
        self._style_ax(self.ax)
        if not recs:
            self.ax.set_title(f"Aucun historique pour : {eq_id}", color=TEXT_MUT)
            self.canvas_fig.draw()
            return

        dates = [r["timestamp"][:10] for r in recs]
        vals  = [r["metrics"]["THI"] for r in recs]
        xs    = list(range(len(dates)))

        self.ax.plot(xs, vals, color=ACCENT2, linewidth=2, zorder=2)
        for xi, yi in zip(xs, vals):
            self.ax.scatter(xi, yi, color=thi_col(yi), s=60, zorder=3)

        self.ax.axhline(80, color=GREEN,  linestyle="--", lw=0.9, alpha=0.6)
        self.ax.axhline(60, color=YELLOW, linestyle="--", lw=0.9, alpha=0.6)
        self.ax.fill_between(xs, 80, 100, alpha=0.05, color=GREEN)
        self.ax.fill_between(xs, 60,  80, alpha=0.05, color=YELLOW)
        self.ax.fill_between(xs,  0,  60, alpha=0.05, color=RED)

        self.ax.set_xticks(xs)
        self.ax.set_xticklabels(dates, rotation=30, ha="right", fontsize=7)
        self.ax.set_ylim(0, 105)
        self.ax.set_ylabel("THI (%)", color=TEXT_MUT, fontsize=9)
        self.ax.set_title(f"Evolution THI — {eq_id}", color=TEXT_PRI, fontsize=10)

        patches = [
            mpatches.Patch(color=GREEN,  label="Normal (>80%)"),
            mpatches.Patch(color=YELLOW, label="Inspection (60-80%)"),
            mpatches.Patch(color=RED,    label="Revision (<60%)"),
        ]
        self.ax.legend(handles=patches, loc="lower left",
                       facecolor=BG_CARD, edgecolor=BORDER,
                       labelcolor=TEXT_PRI, fontsize=8)

        self.fig.tight_layout()
        self.canvas_fig.draw()

    # ═════════════════════════════════════════════════════════════════════════
    #  TAB 4 — REPORT & EXPORT
    # ═════════════════════════════════════════════════════════════════════════
    def _build_rep(self):
        p = self.t_rep
        tk.Label(p, text="  Rapport d'evaluation & Export CMMS",
                 bg=BG_PANEL, fg=ACCENT, font=("Segoe UI", 11, "bold"),
                 pady=10).pack(fill="x")

        self.rep_txt = tk.Text(p, bg=BG_DARK, fg=TEXT_PRI, relief="flat",
                               font=("Courier New", 9), padx=12, pady=10,
                               state="disabled", wrap="word")
        self.rep_txt.pack(fill="both", expand=True, padx=16, pady=4)

        br = tk.Frame(p, bg=BG_PANEL, pady=10)
        br.pack(fill="x", padx=16)
        action_button(br, "  Exporter JSON (SAP PM / Maximo)",
                      self._exp_json, bg=ACCENT2).pack(side="left", padx=6)
        action_button(br, "  Exporter CSV",
                      self._exp_csv, bg=GREEN, fg="black").pack(side="left", padx=6)
        action_button(br, "  Sauvegarder Rapport (.txt)",
                      self._exp_txt, bg=ACCENT).pack(side="left", padx=6)

    def _refresh_rep(self, result: dict):
        m   = result["metrics"]
        rec = result["rec"]
        ts  = result["timestamp"]
        meta = self.last_meta

        lines = [
            "=" * 68,
            "  RAPPORT DE SANTE — TURBINE A GAZ",
            "=" * 68,
            f"  Date           : {ts[:10]}   {ts[11:19]}",
            f"  ID Equipement  : {meta.get('eq_id','')}",
            f"  Operateur      : {meta.get('operator','')}",
            f"  Modele         : {meta.get('model','')}",
            "-" * 68,
            "  METRIQUES DE SANTE",
            "-" * 68,
            f"  EOH                     : {m['EOH']:>12,.1f}  h",
            f"  Vie consommee           : {m['life_pct']:>12.1f}  %",
            f"  Heures restantes / MO   : {m['remaining']:>12,.0f}  h",
            f"  Chute rendement (fouling): {m['fouling']:>11.4f}",
            f"  Sante EOH               : {m['h_eoh']:>12.1f}  %",
            f"  Sante Performance       : {m['h_perf']:>12.1f}  %",
            f"  Sante Pression          : {m['h_pr']:>12.1f}  %",
            "",
            f"  >>> TURBINE HEALTH INDEX (THI) : {m['THI']:>8.1f} %",
            "-" * 68,
            "  RECOMMANDATION",
            "-" * 68,
            f"  Urgence  : {rec['urgency']}",
            f"  Action   : {rec['action']}",
            f"  Action2  : {rec['action2']}",
            "-" * 68,
            "  ESTIMATION DU COUT (DZD)",
            "-" * 68,
            f"  Minimum  : {rec['c_min']:>18,.0f}  DZD",
            f"  Maximum  : {rec['c_max']:>18,.0f}  DZD",
            "=" * 68,
        ]
        txt = "\n".join(lines)
        self._report_str = txt
        self.rep_txt.config(state="normal")
        self.rep_txt.delete("1.0", tk.END)
        self.rep_txt.insert(tk.END, txt)
        self.rep_txt.config(state="disabled")

    def _exp_json(self):
        if not self.last_result:
            messagebox.showwarning("Aucune donnee", "Effectuez d'abord une evaluation.")
            return
        m   = self.last_result["metrics"]
        rec = self.last_result["rec"]
        wo  = {
            "work_order_id":  f"WO-{int(datetime.datetime.now().timestamp())}",
            "equipment_id":   self.last_meta.get("eq_id"),
            "operator":       self.last_meta.get("operator"),
            "turbine_model":  self.last_meta.get("model"),
            "priority":       ("HAUTE" if "Grande" in rec["urgency"]
                               else "MOYENNE" if "Inspection" in rec["urgency"] else "BASSE"),
            "work_type":      "MP",
            "urgency":        rec["urgency"],
            "description":    rec["action"],
            "THI":            m["THI"],
            "EOH":            m["EOH"],
            "cout_DZD":       {"min": rec["c_min"], "max": rec["c_max"]},
            "creation_date":  self.last_result["timestamp"],
        }
        path = filedialog.asksaveasfilename(
            defaultextension=".json", filetypes=[("JSON", "*.json")],
            initialfile=f"WO_{self.last_meta.get('eq_id','GT')}.json")
        if path:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(wo, f, indent=4, ensure_ascii=False)
            messagebox.showinfo("Export JSON reussi", f"Fichier cree :\n{path}")

    def _exp_csv(self):
        if not self.last_result:
            messagebox.showwarning("Aucune donnee", "Effectuez d'abord une evaluation.")
            return
        m   = self.last_result["metrics"]
        rec = self.last_result["rec"]
        inp = self.last_result["inputs"]
        path = filedialog.asksaveasfilename(
            defaultextension=".csv", filetypes=[("CSV", "*.csv")],
            initialfile=f"THI_{self.last_meta.get('eq_id','GT')}.csv")
        if path:
            hdr = "Date,ID,Operateur,Modele,OH,Ns,Rendement,EOH,THI,ViePct,Urgence,CoutMin,CoutMax"
            row = (f"{self.last_result['timestamp'][:10]},"
                   f"{self.last_meta.get('eq_id','')},"
                   f"{self.last_meta.get('operator','')},"
                   f"{self.last_meta.get('model','')},"
                   f"{inp['oh']},{inp['ns']},{inp['eta']},"
                   f"{m['EOH']},{m['THI']},{m['life_pct']},"
                   f"{rec['urgency']},{rec['c_min']},{rec['c_max']}")
            with open(path, "w", encoding="utf-8") as f:
                f.write(hdr + "\n" + row + "\n")
            messagebox.showinfo("Export CSV reussi", f"Fichier cree :\n{path}")

    def _exp_txt(self):
        if not hasattr(self, "_report_str"):
            messagebox.showwarning("Aucun rapport", "Effectuez d'abord une evaluation.")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".txt", filetypes=[("Texte", "*.txt")],
            initialfile="Rapport_Turbine.txt")
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self._report_str)
            messagebox.showinfo("Sauvegarde reussie", f"Rapport sauvegarde :\n{path}")


# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = App()
    app.mainloop()
