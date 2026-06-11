#!/usr/bin/env python3
"""build_tables.py — Genera PNG delle slide KPI per ogni cliente AGHC.

Output: una cartella per cliente con i PNG (Meta + TikTok + Budget Annuale).

Estetica replicata 1:1 col TEMPLATE ORIGINALE Canva AGHC:
  - Header teal #1F5C6E con testo bianco bold
  - Colonna "Periodo Attuale" ARANCIONE #E07B47 testo bianco  (= il dato del mese)
  - Colonna "Periodo Precedente" BIANCA testo teal
  - Confronto colorato verde positivo / rosso negativo
  - Per ogni KPI: ICONA + NOME METRICA (voce insight) a sinistra
  - DIDASCALIA descrittiva sotto ogni tabella
  - Box RATIONAL teal a destra: paragrafo unico, TOV advisor (~580 caratteri)
  - Disclaimer attribuzione in basso a sinistra

Uso:
  python3 build_tables.py --year 2026 --month 5 \\
    --data _data/data-2026-05.json --output-dir /tmp/all_tables/
"""
import argparse, json, subprocess, sys, shutil, tempfile, os
from pathlib import Path
from weasyprint import HTML, CSS

MONTH_IT = {1:"Gennaio",2:"Febbraio",3:"Marzo",4:"Aprile",5:"Maggio",6:"Giugno",
            7:"Luglio",8:"Agosto",9:"Settembre",10:"Ottobre",11:"Novembre",12:"Dicembre"}

CLIENTS = {
    "Accentodì":      {"meta_id":"1312718426033158","filter":["Accentodì"],"excl":[],"tk_id":None,"cm":"YoY","ct":None,"budget":2400},
    "Adèsso":         {"meta_id":"1312718426033158","filter":["Adèsso","MICE"],"excl":[],"tk_id":None,"cm":"YoY","ct":None,"budget":2400},
    "Altafiumara":    {"meta_id":"1201395876543423","filter":None,"excl":[],"tk_id":None,"cm":"MoM","ct":None,"budget":23000},
    "Castello":       {"meta_id":"1489903155429629","filter":None,"excl":[],"tk_id":None,"cm":"MoM","ct":None,"budget":14400},
    "Della Piana":    {"meta_id":"911357333863123","filter":None,"excl":[],"tk_id":"7504967007843319824","cm":"YoY","ct":"MoM","budget":14000},
    "Hannah":         {"meta_id":"1528485957725509","filter":["Hannah"],"excl":["Terraces"],"tk_id":None,"cm":"YoY","ct":None,"budget":9000},
    "Hannah Terraces":{"meta_id":"1528485957725509","filter":["Terraces"],"excl":[],"tk_id":None,"cm":"MoM","ct":None,"budget":7200},
    "Hemanaire":      {"meta_id":"217115315497718","filter":None,"excl":[],"tk_id":None,"cm":"MoM","ct":None,"budget":15000},
    "Livata":         {"meta_id":"4666471140299701","filter":None,"excl":[],"tk_id":None,"cm":"MoM","ct":None,"budget":15000},
    "Lunetta":        {"meta_id":"687349689221880","filter":None,"excl":[],"tk_id":"7498330316248203280","cm":"YoY","ct":"MoM","budget":18000},
    "Magari Estates": {"meta_id":"1372615496521110","filter":None,"excl":[],"tk_id":None,"cm":"MoM","ct":None,"budget":24600},
    "Marcella Royal": {"meta_id":"821188209852436","filter":["Marcella"],"excl":[],"tk_id":"7499093699838607377","cm":"YoY","ct":"MoM","budget":14400},
    "Mare":           {"meta_id":"1432341844596179","filter":None,"excl":[],"tk_id":"7498679494010667009","cm":"MoM","ct":"MoM","budget":15000},
    "Montemagno":     {"meta_id":"752450855779035","filter":None,"excl":[],"tk_id":None,"cm":"MoM","ct":None,"budget":0},
    "Terrazza Flavia":{"meta_id":"821188209852436","filter":["Terrazza"],"excl":[],"tk_id":None,"cm":"YoY","ct":None,"budget":7500},
    "Villa Ermellina":{"meta_id":"30233607946222961","filter":None,"excl":[],"tk_id":"7612666695502118929","cm":"MoM","ct":"MoM","budget":16400},
    "Villa Giada":    {"meta_id":"1849759899186169","filter":None,"excl":[],"tk_id":None,"cm":"MoM","ct":None,"budget":21600},
    "Villa Miliani":  {"meta_id":"1353024533007038","filter":None,"excl":[],"tk_id":None,"cm":"MoM","ct":None,"budget":6600},
}

# === Loghi piattaforme (inline SVG) ===
# IG a tinta piena (WeasyPrint non renderizza i gradienti url(#...) → il logo spariva)
LOGO_IG = """<svg viewBox="0 0 24 24" width="40" height="40" xmlns="http://www.w3.org/2000/svg"><rect x="2" y="2" width="20" height="20" rx="5.5" ry="5.5" fill="#E1306C"/><rect x="6" y="6" width="12" height="12" rx="3.6" ry="3.6" fill="none" stroke="#fff" stroke-width="1.7"/><circle cx="12" cy="12" r="3.1" fill="none" stroke="#fff" stroke-width="1.7"/><circle cx="16.4" cy="7.6" r="1.15" fill="#fff"/></svg>"""
LOGO_FB = """<svg viewBox="0 0 24 24" width="40" height="40" xmlns="http://www.w3.org/2000/svg"><path d="M24 12.073C24 5.405 18.627 0 12 0S0 5.405 0 12.073C0 18.1 4.388 23.094 10.125 24v-8.437H7.078v-3.49h3.047V9.41c0-3.007 1.792-4.668 4.533-4.668 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.927-1.956 1.876v2.25h3.328l-.532 3.49h-2.796V24C19.612 23.094 24 18.1 24 12.073z" fill="#1877F2"/></svg>"""
LOGO_TK = """<svg viewBox="0 0 24 24" width="40" height="40" xmlns="http://www.w3.org/2000/svg"><path d="M19.59 6.69a4.83 4.83 0 0 1-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 0 1-5.2 1.74 2.89 2.89 0 0 1 2.31-4.64 2.93 2.93 0 0 1 .88.13V9.4a6.84 6.84 0 0 0-1-.05A6.33 6.33 0 0 0 5.6 20.1a6.34 6.34 0 0 0 10.86-4.43V8.61a8.16 8.16 0 0 0 4.77 1.52v-3.4a4.85 4.85 0 0 1-1.64-.04Z" fill="#010101"/></svg>"""

# === Icone metrica (voci insight) — palette AGHC teal/arancio ===
IC_REACH = """<svg viewBox="0 0 64 64" width="50" height="50" xmlns="http://www.w3.org/2000/svg"><path d="M6 26v12h9l21 11V15L15 26H6z" fill="#1F5C6E"/><path d="M44 23c5 4 5 14 0 18" fill="none" stroke="#E07B47" stroke-width="4" stroke-linecap="round"/><path d="M50 17c8 7 8 23 0 30" fill="none" stroke="#E07B47" stroke-width="4" stroke-linecap="round"/></svg>"""
IC_VIEWS = """<svg viewBox="0 0 64 64" width="50" height="50" xmlns="http://www.w3.org/2000/svg"><path d="M4 32s12-17 28-17 28 17 28 17-12 17-28 17S4 32 4 32z" fill="none" stroke="#1F5C6E" stroke-width="4"/><circle cx="32" cy="32" r="9" fill="#E07B47"/></svg>"""
IC_ENG = """<svg viewBox="0 0 64 64" width="50" height="50" xmlns="http://www.w3.org/2000/svg"><rect x="6" y="12" width="34" height="25" rx="5" fill="#1F5C6E"/><path d="M14 37v8l10-8z" fill="#1F5C6E"/><rect x="28" y="27" width="30" height="22" rx="5" fill="#E07B47"/><path d="M50 49v7l-9-7z" fill="#E07B47"/></svg>"""
IC_CLICK = """<svg viewBox="0 0 64 64" width="50" height="50" xmlns="http://www.w3.org/2000/svg"><path d="M30 30V18a4 4 0 0 1 8 0v10" fill="none" stroke="#1F5C6E" stroke-width="4" stroke-linecap="round"/><path d="M38 28a4 4 0 0 1 8 0v4" fill="none" stroke="#1F5C6E" stroke-width="4" stroke-linecap="round"/><path d="M46 30a4 4 0 0 1 8 0v10c0 9-6 16-15 16-6 0-10-3-13-8l-5-9c-2-4 3-7 6-4l5 5V22a4 4 0 0 1 8 0v8" fill="#1F5C6E"/><path d="M12 12l2 5 5 2-5 2-2 5-2-5-5-2 5-2z" fill="#E07B47"/></svg>"""
IC_BUDGET = """<svg viewBox="0 0 64 64" width="50" height="50" xmlns="http://www.w3.org/2000/svg"><path d="M10 20v12c0 4 7 7 16 7s16-3 16-7V20" fill="#1F5C6E"/><ellipse cx="26" cy="20" rx="16" ry="7" fill="#E07B47"/><path d="M22 38v8c0 4 7 7 16 7s16-3 16-7v-8" fill="#1F5C6E"/><ellipse cx="38" cy="38" rx="16" ry="7" fill="#E07B47"/></svg>"""

# === Didascalie fisse (uguali ogni mese) ===
CAP_REACH = "Numero di utenti unici che hanno visto almeno una volta i contenuti sponsorizzati, indicativo del pubblico realmente raggiunto dalla campagna."
CAP_VIEWS = "Numero complessivo di visualizzazioni degli annunci, incluse le ripetizioni per singolo utente. Indica la frequenza e l'intensità dell'esposizione pubblicitaria."
CAP_ENG = "Include tutte le interazioni degli utenti dopo aver visto gli annunci (clic, like, commenti, condivisioni, salvataggi, ecc.)."
CAP_CLICKS = "Include tutte le azioni di clic effettuate dagli utenti dopo aver visualizzato l'annuncio (apertura del link, clic sul pulsante call to action)."
CAP_TK_CLICKS = "Numero di clic dagli annunci verso la destinazione specificata (es. sito o landing page), al netto delle interazioni puramente social."

META_METRICS = [
    ("reach",                    "ACCOUNT RAGGIUNTI", IC_REACH, CAP_REACH),
    ("impressions",              "VISUALIZZAZIONI",   IC_VIEWS, CAP_VIEWS),
    ("actions_page_engagement",  "INTERAZIONI",       IC_ENG,   CAP_ENG),
    ("clicks",                   "CLICKS",            IC_CLICK, CAP_CLICKS),
]
TK_METRICS = [
    ("reach",        "ACCOUNT RAGGIUNTI", IC_REACH, CAP_REACH),
    ("impressions",  "VISUALIZZAZIONI",   IC_VIEWS, CAP_VIEWS),
    ("clicks",       "CLICKS",            IC_CLICK, CAP_TK_CLICKS),
]

DISCLAIMER_HTML = (
    "<p>Le metriche riportate nel presente report relative a Copertura, Visualizzazioni, "
    "Interazioni e Budget potrebbero essere soggette a variazioni in quanto influenzate dalla "
    "finestra di attribuzione, che può estendersi oltre la data di chiusura della reportistica.</p>"
    "<p>*Nel report è stato presentato il confronto tra click nel periodo attuale e il mese "
    "precedente. Tuttavia questa metrica risulta parzialmente non comparabile, in quanto Meta ha "
    "aggiornato nel corso degli ultimi 12 mesi le regole e i modelli di attribuzione dei click e "
    "delle conversioni (inclusi i criteri di attribuzione standard e le finestre di attribuzione). "
    "Questi adeguamenti sistemici modificano il modo in cui Facebook/Instagram contabilizzano i "
    "click rispetto ai periodi precedenti, rendendo il confronto diretto potenzialmente fuorviante.</p>"
)

# === Formattazione IT ===
def fmt_int(x):
    if x is None: return "n/d"
    return f"{int(round(x)):,}".replace(",", ".")

def fmt_eur(x):
    if x is None: return "n/d"
    return f"{x:,.2f}€".replace(",", "X").replace(".", ",").replace("X", ".")

def pct(c, p):
    if p is None or p == 0 or c is None: return None
    return (c - p) / p * 100

def fmt_pct(p):
    if p is None: return "n/d"
    sign = "+" if p > 0 else ""
    return f"{sign}{int(round(p))}%"

def comparison_period(year, month, tipo):
    if tipo == "YoY": return (year - 1, month)
    if month == 1: return (year - 1, 12)
    return (year, month - 1)


# === Build view ===
def empty_meta(): return {"reach":0,"impressions":0,"actions_page_engagement":0,"clicks":0,"spend":0}
def empty_tk(): return {"reach":0,"impressions":0,"engagements":0,"clicks":0,"spend":0}

def build_view(client_name, data, year, month):
    cfg = CLIENTS[client_name]
    if cfg["filter"]:
        f = data.get("meta_filtered", {}).get(client_name, {})
        meta_cur = f.get("current") or {"facebook":empty_meta(),"instagram":empty_meta()}
        meta_prev = f.get("prev_yoy" if cfg["cm"]=="YoY" else "prev_mom") or {"facebook":empty_meta(),"instagram":empty_meta()}
    else:
        meta_cur = data["meta_by_account"]["current"].get(cfg["meta_id"]) or {"facebook":empty_meta(),"instagram":empty_meta()}
        meta_prev = data["meta_by_account"]["prev_yoy" if cfg["cm"]=="YoY" else "prev_mom"].get(cfg["meta_id"]) or {"facebook":empty_meta(),"instagram":empty_meta()}
    for d in (meta_cur, meta_prev):
        for plat in ("facebook","instagram"):
            if not d.get(plat): d[plat] = empty_meta()

    has_tk = bool(cfg["tk_id"])
    tk_cur = tk_prev = None; tk_launched = False
    if has_tk:
        tk_cur = data["tiktok"]["current"].get(cfg["tk_id"]) or empty_tk()
        ck = "prev_yoy" if cfg["ct"]=="YoY" else "prev_mom"
        tk_prev = data["tiktok"].get(ck, {}).get(cfg["tk_id"]) or empty_tk()
        if (tk_cur.get("spend") or 0) > 0 and (tk_prev.get("spend") or 0) == 0 and (tk_prev.get("impressions") or 0) == 0:
            tk_launched = True

    ytd_root = data.get("ytd_spend", {})
    ytd_months = ytd_root.get("months", list(range(1, month+1)))
    ytd_client = ytd_root.get("by_client", {}).get(client_name, {})

    return {
        "client_name": client_name, "cfg": cfg, "year": year, "month": month,
        "has_tk": has_tk, "tk_launched": tk_launched,
        "meta_cur": meta_cur, "meta_prev": meta_prev,
        "tk_cur": tk_cur, "tk_prev": tk_prev,
        "ytd_months": ytd_months, "ytd_client": ytd_client,
    }


# === CSS pagina intera (Meta/TikTok) — replica layout template originale ===
CSS_FULL_PAGE = """
@page { size: 1920px 1080px; margin: 0; }
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: "Lato", "Open Sans", "DejaVu Sans", sans-serif; color: #1F5C6E; background: #fff; }
.page { width: 1920px; height: 1080px; position: relative; }

/* Colonna sinistra: solo titolo + periodo (niente disclaimer) */
.page-header { position: absolute; top: 80px; left: 70px; width: 360px; }
.page-title { font-size: 52px; font-weight: 700; color: #1F5C6E; letter-spacing: -0.5px; line-height: 1.05; margin: 0 0 14px 0; }
.page-subtitle { font-size: 24px; font-weight: 700; color: #1F5C6E; letter-spacing: 0.3px; margin: 0; }
.page-subtitle .vs { font-size: 15px; font-weight: 400; color: #1F5C6E; text-transform: lowercase; display: block; margin: 4px 0; }

/* Colonna KPI (centro): icona + nome metrica a sinistra di ogni tabella */
.tables-col { position: absolute; top: 70px; left: 470px; width: 900px; display: flex; flex-direction: column; gap: 16px; }
.kpi-block { display: flex; align-items: center; gap: 14px; }
.kpi-side { width: 128px; flex: 0 0 128px; display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; }
.kpi-side .ic { line-height: 0; }
.kpi-side .nm { margin-top: 6px; font-size: 15px; font-weight: 700; letter-spacing: 0.4px; color: #1F5C6E; line-height: 1.12; }
.kpi-main { flex: 1 1 auto; min-width: 0; }

table.kpi { border-collapse: collapse; width: 100%; }
table.kpi thead th { background: #1F5C6E; color: #fff; padding: 8px 12px; font-weight: 600; font-size: 13px; text-align: center; letter-spacing: 0.3px; border: 1px solid #1F5C6E; }
table.kpi thead th:first-child { background: #fff; border: none; width: 58px; }
table.kpi tbody td { padding: 9px 12px; text-align: center; font-size: 21px; font-weight: 700; border: 1px solid #E5E7EB; }
td.plat-cell { background: #fff; border: none; width: 58px; padding: 3px; }
td.plat-cell svg { display: block; margin: 0 auto; }
td.cur-cell  { background: #E07B47; color: #fff; }      /* Periodo Attuale = arancione */
td.prev-cell { background: #fff;    color: #1F5C6E; }   /* Periodo Precedente = bianco */
.delta-pos { color: #1AA64B; }                          /* verde evidente per i + */
.delta-neg { color: #C0392B; }
.delta-launch { color: #2F5496; font-style: italic; font-size: 17px; }
.delta-na { color: #9CA3AF; font-style: italic; }
.kpi-caption { font-size: 12.5px; font-weight: 400; line-height: 1.32; color: #1F5C6E; margin-top: 5px; padding-right: 8px; }

/* Box RATIONAL (destra) — separato dalle tabelle, nessuna sovrapposizione */
.rational-box { position: absolute; top: 150px; right: 55px; width: 415px; min-height: 600px; background: #1F5C6E; color: #fff; padding: 36px 36px; display: flex; flex-direction: column; justify-content: center; }
.rational-box p { font-size: 17px; line-height: 1.62; }

/* Footer (solo confidenzialità a destra) */
.footer-r { position: absolute; bottom: 26px; right: 55px; font-size: 12px; font-style: italic; color: #9AA7AD; }
"""

CSS_BUDGET_TABLE = """
@page { size: 1400px 720px; margin: 0; }
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: "Lato", "Open Sans", "DejaVu Sans", sans-serif; color: #1F5C6E; padding: 12px; }
table.budget { border-collapse: collapse; width: 100%; font-size: 22px; }
th.hdr-budget-annuale { background: #1F5C6E; color: #fff; padding: 16px 24px; text-align: left; font-size: 22px; font-weight: 700; letter-spacing: 1.5px; border: 1px solid #1F5C6E; }
th.hdr-budget-val { background: #1F5C6E; color: #fff; padding: 16px 24px; text-align: right; font-size: 22px; font-weight: 700; border: 1px solid #1F5C6E; }
tr.hdr-cols th { background: #E07B47; color: #fff; padding: 11px 24px; font-size: 14px; font-weight: 700; letter-spacing: 1px; border: 1px solid #fff; }
tr.hdr-cols th:first-child { text-align: left; }
tr.hdr-cols th:nth-child(n+2) { text-align: center; }
.budget tbody td { padding: 11px 24px; font-size: 18px; font-weight: 600; border: 1px solid #E5E7EB; }
.budget tbody td.mese { text-align: left; font-weight: 700; color: #1F5C6E; }
.budget tbody td:nth-child(n+2) { text-align: right; }
.budget tfoot td { background: #fff; padding: 13px 24px; font-size: 18px; font-weight: 700; color: #1F5C6E; border-top: 2px solid #1F5C6E; }
.budget tfoot td:nth-child(n+2) { text-align: right; }
.budget tfoot tr.speso td { border-bottom: 1px solid #E5E7EB; }
.budget tfoot tr.rimanente td { border-top: none; }
"""

def render_html(table_inner_html, css):
    return f"""<!DOCTYPE html><html><head><meta charset="UTF-8"></head><body>{table_inner_html}</body></html>"""


def delta_cell(cur, prev, override=None):
    if override:
        return f'<td class="delta-launch">{override}</td>'
    p = pct(cur, prev)
    if p is None: return '<td class="delta-na">n/d</td>'
    cls = "delta-pos" if p >= 0 else "delta-neg"
    return f'<td class="{cls}">{fmt_pct(p)}</td>'


def kpi_block(icon, name, table_html, caption=None):
    cap = f'<div class="kpi-caption">{caption}</div>' if caption else ""
    side = f'<div class="kpi-side"><div class="ic">{icon}</div><div class="nm">{name}</div></div>'
    return f'<div class="kpi-block">{side}<div class="kpi-main">{table_html}{cap}</div></div>'


def meta_2row_table(field, ig_c, ig_p, fb_c, fb_p, fmt):
    return f"""<table class="kpi">
  <thead><tr><th></th><th>Periodo Attuale</th><th>Periodo Precedente</th><th>Confronto</th></tr></thead>
  <tbody>
    <tr><td class="plat-cell">{LOGO_IG}</td><td class="cur-cell">{fmt(ig_c.get(field) or 0)}</td><td class="prev-cell">{fmt(ig_p.get(field) or 0)}</td>{delta_cell(ig_c.get(field) or 0, ig_p.get(field) or 0)}</tr>
    <tr><td class="plat-cell">{LOGO_FB}</td><td class="cur-cell">{fmt(fb_c.get(field) or 0)}</td><td class="prev-cell">{fmt(fb_p.get(field) or 0)}</td>{delta_cell(fb_c.get(field) or 0, fb_p.get(field) or 0)}</tr>
  </tbody>
</table>"""


def meta_budget_table(sp_c, sp_p):
    return f"""<table class="kpi">
  <thead><tr><th></th><th>Periodo Attuale</th><th>Periodo Precedente</th><th>Confronto</th></tr></thead>
  <tbody>
    <tr><td class="plat-cell"></td><td class="cur-cell">{fmt_eur(sp_c)}</td><td class="prev-cell">{fmt_eur(sp_p)}</td>{delta_cell(sp_c, sp_p)}</tr>
  </tbody>
</table>"""


def tk_table(field, cur, prev, fmt, launched):
    override = "1° mese live" if launched else None
    return f"""<table class="kpi">
  <thead><tr><th></th><th>Periodo Attuale</th><th>Periodo Precedente</th><th>Confronto</th></tr></thead>
  <tbody>
    <tr><td class="plat-cell">{LOGO_TK}</td><td class="cur-cell">{fmt(cur)}</td><td class="prev-cell">{fmt(prev)}</td>{delta_cell(cur, prev, override)}</tr>
  </tbody>
</table>"""


def budget_annuale_table(v):
    budget = v["cfg"]["budget"] or 0
    ytd_months = v["ytd_months"]; ytd_client = v["ytd_client"]
    rows = ""; tot_meta = tot_tk = 0
    for m in range(1, 13):
        md = ytd_client.get(str(m), {"meta":0, "tiktok":0}) if m in ytd_months else {"meta":0, "tiktok":0}
        meta_v = md.get("meta") or 0; tk_v = md.get("tiktok") or 0
        tot_meta += meta_v; tot_tk += tk_v
        rows += f"""<tr><td class="mese">{MONTH_IT[m].upper()}</td><td>{fmt_eur(meta_v)}</td><td>{fmt_eur(tk_v)}</td><td>{fmt_eur(meta_v + tk_v)}</td></tr>"""
    speso = tot_meta + tot_tk; rimanente = budget - speso
    return f"""<table class="budget">
  <thead>
    <tr><th class="hdr-budget-annuale" colspan="3">BUDGET ANNUALE</th><th class="hdr-budget-val">{fmt_eur(budget)}</th></tr>
    <tr class="hdr-cols"><th>MESI</th><th>ADS META</th><th>ADS TIK TOK</th><th>TOTALE</th></tr>
  </thead>
  <tbody>{rows}</tbody>
  <tfoot>
    <tr class="speso"><td>BUDGET SPESO</td><td>{fmt_eur(tot_meta)}</td><td>{fmt_eur(tot_tk)}</td><td>{fmt_eur(speso)}</td></tr>
    <tr class="rimanente"><td>BUDGET RIMANENTE</td><td></td><td></td><td>{fmt_eur(rimanente)}</td></tr>
  </tfoot>
</table>"""


def render_table(html_inner, css, out_png, dpi=200):
    out_png.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="aghc_tables_") as td:
        td_path = Path(td); pdf_path = td_path / "page.pdf"
        html = render_html(html_inner, css)
        HTML(string=html).write_pdf(str(pdf_path), stylesheets=[CSS(string=css)])
        prefix = td_path / "page"
        subprocess.run(["pdftoppm", "-png", "-r", str(dpi), str(pdf_path), str(prefix)], check=True)
        generated = td_path / "page-1.png"
        if not generated.exists():
            raise RuntimeError(f"pdftoppm non ha prodotto PNG attesa: {generated}")
        shutil.copy(generated, out_png)


# === RATIONAL — paragrafo unico, TOV advisor, ~580 caratteri (replica template) ===
BUDGET_WEIGHTS = {1:3,2:3,3:5,4:10,5:15,6:15,7:12,8:12,9:5,10:5,11:5,12:10}

def build_rational(v, focus):
    fb_c = v["meta_cur"]["facebook"]; fb_p = v["meta_prev"]["facebook"]
    ig_c = v["meta_cur"]["instagram"]; ig_p = v["meta_prev"]["instagram"]
    spend_cur = (fb_c.get("spend") or 0) + (ig_c.get("spend") or 0)
    spend_prev = (fb_p.get("spend") or 0) + (ig_p.get("spend") or 0)
    spend_delta = pct(spend_cur, spend_prev)
    fb_reach = fb_c.get("reach") or 0; ig_reach = ig_c.get("reach") or 0
    reach_meta = fb_reach + ig_reach
    fb_reach_delta = pct(fb_reach, fb_p.get("reach") or 0)
    tot_eng = (fb_c.get("actions_page_engagement") or 0) + (ig_c.get("actions_page_engagement") or 0)

    cn = v["client_name"]
    month_cap = MONTH_IT[v["month"]]; year = v["year"]
    cur_w = BUDGET_WEIGHTS[v["month"]]
    next_m = (v["month"] % 12) + 1
    next_cap = MONTH_IT[next_m]; next_low = next_cap.lower(); next_w = BUDGET_WEIGHTS[next_m]
    driver = "Facebook" if fb_reach >= ig_reach else "Instagram"

    if focus == "tiktok":
        tk = v["tk_cur"] or empty_tk()
        if v["tk_launched"]:
            s = (f"{month_cap} {year} inaugura una nuova fase per {cn}: la prima campagna TikTok va live e "
                 f"debutta con {fmt_int(tk.get('impressions') or 0)} visualizzazioni e {fmt_int(tk.get('reach') or 0)} "
                 f"utenti unici raggiunti, attivando il presidio sul pubblico più giovane nel momento giusto del "
                 f"calendario. Da {next_low} {cn} lavora su due leve complementari — Meta per la conversione, "
                 f"TikTok per la scoperta del brand — in vista delle finestre stagionali a più alto traffico di prenotazione.")
        elif (tk.get("impressions") or 0) > 0:
            s = (f"{month_cap} {year} conferma su TikTok un presidio efficiente per {cn}, con "
                 f"{fmt_int(tk.get('impressions') or 0)} visualizzazioni e {fmt_int(tk.get('reach') or 0)} utenti unici "
                 f"raggiunti: il canale amplia la copertura sul pubblico più giovane a costi competitivi, a conferma "
                 f"di un mix ben bilanciato sugli obiettivi di awareness. La pressione prosegue strategica verso "
                 f"{next_cap} (peso {next_w}% del piano annuo).")
        else:
            s = (f"{month_cap} {year} vede TikTok in stand-by per {cn}: la pressione resta concentrata sui canali "
                 f"principali, mentre il budget dedicato resta integro e pronto a riattivarsi sulle finestre "
                 f"stagionali a più alto ritorno verso {next_cap}.")
        return f"<p>{s}</p>"

    # META — pausa strategica
    if spend_cur == 0 and reach_meta == 0:
        s = (f"{month_cap} {year} rappresenta una pausa strategica per {cn}, coerente con il posizionamento del "
             f"mese all'interno del piano media annuo (peso {cur_w}%). Il budget resta integro e pronto a "
             f"concentrarsi sulle finestre stagionali a più alto ritorno. Da {next_low} (peso {next_w}% del piano "
             f"annuo) il presidio riprende {'nel cuore della stagione' if next_w >= 12 else 'in modo progressivo'}, "
             f"dove concentreremo la pressione sulle finestre a più alta intenzione di prenotazione.")
        return f"<p>{s}</p>"

    # Frase 1 — apertura su budget/posizionamento
    if spend_delta is not None and spend_delta > 8:
        s1 = (f"{month_cap} {year} si apre con un incremento strategico del budget pubblicitario Meta "
              f"({fmt_pct(spend_delta)}), scelta coerente con il posizionamento del mese all'interno del piano "
              f"annuo (peso {cur_w}%).")
    elif spend_delta is not None and spend_delta < -8:
        s1 = (f"{month_cap} {year} è il mese dell'efficienza per {cn}: l'investimento Meta viene rimodulato "
              f"({fmt_pct(spend_delta)}) in coerenza con il posizionamento del mese nel piano annuo (peso {cur_w}%).")
    else:
        s1 = (f"{month_cap} {year} conferma per {cn} un presidio Meta stabile, in linea con il posizionamento del "
              f"mese all'interno del piano annuo (peso {cur_w}%).")

    # Frase 2 — copertura / canale di traino
    if fb_reach_delta is not None and fb_reach_delta > 100:
        s2 = (f"{driver} diventa il canale di traino e amplia la copertura fino a {fmt_int(reach_meta)} utenti unici, "
              f"a conferma di un mix canali ben bilanciato sugli obiettivi di awareness.")
    else:
        s2 = (f"{driver} amplia la copertura raggiungendo {fmt_int(reach_meta)} utenti unici, a conferma di un mix "
              f"canali ben bilanciato sugli obiettivi di awareness.")

    # Frase 3 — efficienza / interazioni
    if spend_delta is not None and spend_delta < -8 and reach_meta > 0:
        s3 = ("Il costo per risultato si mantiene efficiente in un contesto d'asta più selettivo, segno di una "
              "strategia di targeting che continua a funzionare.")
    elif tot_eng > 50000:
        s3 = (f"Le interazioni complessive toccano {fmt_int(tot_eng)}, segno di contenuti che continuano a generare "
              f"conversazioni qualificate intorno al brand.")
    else:
        s3 = ("Il costo per risultato resta efficiente in un contesto d'asta più selettivo, segno di un targeting "
              "che continua a funzionare.")

    # Frase 4 — prossimo mese
    if next_w >= 12:
        s4 = (f"La base costruita in {month_cap} {year} prepara {next_cap} (peso {next_w}% del piano annuo), dove "
              f"concentreremo la pressione sulle finestre a più alta intenzione di prenotazione.")
    else:
        s4 = (f"La base costruita in {month_cap} {year} prepara {next_cap} (peso {next_w}% del piano annuo), "
              f"mantenendo il pubblico caldo in vista delle finestre più rilevanti.")

    return f"<p>{s1} {s2} {s3} {s4}</p>"


def _periods_meta(v):
    cy, cm = comparison_period(v["year"], v["month"], v["cfg"]["cm"])
    return f"{MONTH_IT[v['month']]} {v['year']}", f"{MONTH_IT[cm]} {cy}"

def _periods_tk(v):
    cy, cm = comparison_period(v["year"], v["month"], v["cfg"]["ct"])
    return f"{MONTH_IT[v['month']]} {v['year']}", f"{MONTH_IT[cm]} {cy}"

AG_LOGO = '<div class="ag-logo">AG</div>'

def meta_page_html(v):
    fb_c, fb_p = v["meta_cur"]["facebook"], v["meta_prev"]["facebook"]
    ig_c, ig_p = v["meta_cur"]["instagram"], v["meta_prev"]["instagram"]
    sp_c = (fb_c.get("spend") or 0) + (ig_c.get("spend") or 0)
    sp_p = (fb_p.get("spend") or 0) + (ig_p.get("spend") or 0)

    blocks = ""
    for field, name, icon, cap in META_METRICS:
        blocks += kpi_block(icon, name, meta_2row_table(field, ig_c, ig_p, fb_c, fb_p, fmt_int), cap)
    blocks += kpi_block(IC_BUDGET, "BUDGET", meta_budget_table(sp_c, sp_p), None)

    pa, pb = _periods_meta(v)
    return f"""<div class="page">
      <div class="page-header"><h1 class="page-title">Meta Advertising</h1>
        <p class="page-subtitle">{pa}<span class="vs">vs</span>{pb}</p></div>
      <div class="tables-col">{blocks}</div>
      <div class="rational-box">{build_rational(v, "meta")}</div>
      <div class="footer-r">Confidential&amp;proprietary | &reg; {v['year']-1} AG Hotel Consulting</div>
    </div>"""


def tiktok_page_html(v):
    tk_c = v["tk_cur"] or empty_tk(); tk_p = v["tk_prev"] or empty_tk()
    launched = v["tk_launched"]
    blocks = ""
    for field, name, icon, cap in TK_METRICS:
        blocks += kpi_block(icon, name, tk_table(field, tk_c.get(field) or 0, tk_p.get(field) or 0, fmt_int, launched), cap)
    blocks += kpi_block(IC_BUDGET, "BUDGET", tk_table("spend", tk_c.get("spend") or 0, tk_p.get("spend") or 0, fmt_eur, launched), None)

    pa, pb = _periods_tk(v)
    return f"""<div class="page">
      <div class="page-header"><h1 class="page-title">Tik Tok Advertising</h1>
        <p class="page-subtitle">{pa}<span class="vs">vs</span>{pb}</p></div>
      <div class="tables-col">{blocks}</div>
      <div class="rational-box">{build_rational(v, "tiktok")}</div>
      <div class="footer-r">Confidential&amp;proprietary | &reg; {v['year']-1} AG Hotel Consulting</div>
    </div>"""


def generate_client_tables(client_name, data, year, month, outdir):
    v = build_view(client_name, data, year, month)
    client_dir = outdir / client_name
    client_dir.mkdir(parents=True, exist_ok=True)
    render_table(meta_page_html(v), CSS_FULL_PAGE, client_dir / "01_meta.png", dpi=96)
    if v["has_tk"]:
        render_table(tiktok_page_html(v), CSS_FULL_PAGE, client_dir / "02_tiktok.png", dpi=96)
    render_table(budget_annuale_table(v), CSS_BUDGET_TABLE, client_dir / "03_budget.png", dpi=120)
    n_pages = len(list(client_dir.glob("*.png")))
    print(f"✔ {client_name}: {n_pages} PNG (Meta+TikTok+Budget) in {client_dir}")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--year", type=int, required=True)
    p.add_argument("--month", type=int, required=True)
    p.add_argument("--client", help="Cliente singolo. Omettere per generare tutti i 18.")
    p.add_argument("--data", required=True)
    p.add_argument("--output-dir", required=True)
    args = p.parse_args()
    data = json.loads(Path(args.data).read_text(encoding="utf-8"))
    outdir = Path(args.output_dir); outdir.mkdir(parents=True, exist_ok=True)
    if args.client:
        if args.client not in CLIENTS:
            raise SystemExit(f"Cliente '{args.client}' non trovato.")
        generate_client_tables(args.client, data, args.year, args.month, outdir)
    else:
        for cn in CLIENTS:
            generate_client_tables(cn, data, args.year, args.month, outdir)


if __name__ == "__main__":
    main()
