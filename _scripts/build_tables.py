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
import argparse, json, subprocess, sys, shutil, tempfile, os, base64
from pathlib import Path
from weasyprint import HTML, CSS

# Icone ufficiali del cliente (PNG trasparenti) in _scripts/icons/
ICON_DIR = Path(__file__).resolve().parent / "icons"
def _icon_b64(fn):
    return base64.b64encode((ICON_DIR / fn).read_bytes()).decode()
def icon_img(fn, css):
    return f'<img src="data:image/png;base64,{_icon_b64(fn)}" style="{css}">'

MONTH_IT = {1:"Gennaio",2:"Febbraio",3:"Marzo",4:"Aprile",5:"Maggio",6:"Giugno",
            7:"Luglio",8:"Agosto",9:"Settembre",10:"Ottobre",11:"Novembre",12:"Dicembre"}
MONTH_EN = {1:"January",2:"February",3:"March",4:"April",5:"May",6:"June",7:"July",
            8:"August",9:"September",10:"October",11:"November",12:"December"}

# === Lingua slide (it default; en per clienti internazionali, es. Villa Ermellina) ===
ICON_DIR_EN = Path(__file__).resolve().parent / "icons_en"
def img_tag(dir_, fn, css):
    b64 = base64.b64encode((dir_ / fn).read_bytes()).decode()
    return f'<img src="data:image/png;base64,{b64}" style="{css}">'

LANG = "it"
TR = {
    "it": {"cur":"Periodo Attuale","prev":"Periodo Precedente","cmp":"Confronto","live":"1° mese live","na":"n/d",
           "b_annual":"BUDGET ANNUALE","b_months":"MESI","b_meta":"ADS META","b_tk":"ADS TIK TOK",
           "b_total":"TOTALE","b_spent":"BUDGET SPESO","b_remain":"BUDGET RIMANENTE",
           "lab":{"reach":"ACCOUNT RAGGIUNTI","views":"VISUALIZZAZIONI","interactions":"INTERAZIONI",
                  "clicks":"CLICKS","budget":"BUDGET","tk_clicks":"CLICK ALLA DESTINAZIONE"}},
    "en": {"cur":"Current Period","prev":"Previous Period","cmp":"Comparison","live":"1st month live","na":"n/a",
           "b_annual":"ANNUAL BUDGET","b_months":"MONTHS","b_meta":"META ADS","b_tk":"TIKTOK ADS",
           "b_total":"TOTAL","b_spent":"BUDGET SPENT","b_remain":"REMAINING BUDGET",
           "lab":{"reach":"ACCOUNTS REACHED","views":"IMPRESSIONS","interactions":"INTERACTIONS",
                  "clicks":"CLICKS","budget":"BUDGET","tk_clicks":"CLICKS TO DESTINATION"}},
}
def t(k): return TR[LANG][k]
def month_name(m): return MONTH_IT[m] if LANG == "it" else MONTH_EN[m]

CLIENTS = {
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
    "Puntebianche Resort":{"meta_id":"1528485957725509","filter":["Puntebianche"],"excl":[],"tk_id":None,"cm":"MoM","ct":None,"budget":0},
    "Terrazza Flavia":{"meta_id":"821188209852436","filter":["Terrazza"],"excl":[],"tk_id":None,"cm":"YoY","ct":None,"budget":7500},
    "Villa Ermellina":{"meta_id":"30233607946222961","filter":None,"excl":[],"tk_id":"7612666695502118929","cm":"MoM","ct":"MoM","budget":16400,"lang":"en"},  # report SEMPRE in inglese
    "Villa Giada":    {"meta_id":"1849759899186169","filter":None,"excl":[],"tk_id":"7626418949391351815","cm":"MoM","ct":"MoM","budget":21600},
    "Villa Miliani":  {"meta_id":"1353024533007038","filter":None,"excl":[],"tk_id":None,"cm":"MoM","ct":None,"budget":6600},
}

# === Loghi piattaforme (inline SVG) ===
# Loghi piattaforma dai PNG ufficiali forniti dal cliente (ritagliati al contenuto)
LOGO_IG = icon_img("ig.png", "height:52px")
LOGO_FB = icon_img("fb.png", "height:52px")
LOGO_TK = icon_img("tiktok.png", "height:56px")

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

# === Didascalie EN ===
CAP_REACH_EN = "Number of unique users who saw the sponsored content at least once, indicating the audience actually reached by the campaign."
CAP_VIEWS_EN = "Total number of ad views, including repeats per single user. It indicates the frequency and intensity of advertising exposure."
CAP_ENG_EN = "Includes all user interactions after seeing the ads (clicks, likes, comments, shares, saves, etc.)."
CAP_CLICKS_EN = "Includes all click actions taken by users after viewing the ad (link opening, click on the call-to-action button)."
CAP_TK_CLICKS_EN = "Number of clicks from the ads to the specified destination (e.g. website or landing page), net of purely social interactions."

CAPS = {
    "it": {"reach":CAP_REACH,"views":CAP_VIEWS,"interactions":CAP_ENG,"clicks":CAP_CLICKS,"tk_clicks":CAP_TK_CLICKS},
    "en": {"reach":CAP_REACH_EN,"views":CAP_VIEWS_EN,"interactions":CAP_ENG_EN,"clicks":CAP_CLICKS_EN,"tk_clicks":CAP_TK_CLICKS_EN},
}
ICON_FN = {
    "it": {"reach":"reach.png","views":"views.png","interactions":"interazioni.png","clicks":"clicks.png","budget":"budget.png","tk_clicks":"click_destinazione.png"},
    "en": {"reach":"reach.png","views":"views.png","interactions":"interactions.png","clicks":"clicks.png","budget":"budget.png","tk_clicks":"click_destination.png"},
}
# (campo dati, chiave metrica)
META_METRICS = [("reach","reach"),("impressions","views"),("actions_page_engagement","interactions"),("clicks","clicks")]
TK_METRICS = [("reach","reach"),("impressions","views"),("clicks","tk_clicks")]

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
    if x is None: return t("na")
    return f"{int(round(x)):,}".replace(",", ".")

def fmt_eur(x):
    if x is None: return t("na")
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

    # Meta "primo mese live": spesa corrente >0 ma periodo di confronto a zero (nessuno storico)
    _mcs = sum((meta_cur.get(p, {}).get("spend") or 0) for p in ("facebook", "instagram"))
    _mps = sum((meta_prev.get(p, {}).get("spend") or 0) for p in ("facebook", "instagram"))
    _mpi = sum((meta_prev.get(p, {}).get("impressions") or 0) for p in ("facebook", "instagram"))
    meta_launched = (_mcs > 0) and (_mps == 0) and (_mpi == 0)

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
        "has_tk": has_tk, "tk_launched": tk_launched, "meta_launched": meta_launched,
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

/* Colonna KPI (centro): icona metrica (PNG, nome incorporato) a sinistra di ogni tabella */
.tables-col { position: absolute; top: 44px; left: 438px; width: 952px; display: flex; flex-direction: column; gap: 9px; }
.kpi-block { display: flex; align-items: center; gap: 10px; }
.kpi-side { width: 174px; flex: 0 0 174px; display: flex; align-items: center; justify-content: center; }
.kpi-side img { display: block; }
.kpi-side-en { flex-direction: column; }
.kpi-side-en .ic-en { line-height: 0; }
.kpi-side-en .nm-en { margin-top: 7px; font-size: 14.5px; font-weight: 700; letter-spacing: 0.4px; color: #1F5C6E; line-height: 1.12; text-align: center; }
.kpi-main { flex: 1 1 auto; min-width: 0; }

table.kpi { border-collapse: collapse; width: 100%; }
table.kpi thead th { background: #1F5C6E; color: #fff; padding: 6px 12px; font-weight: 600; font-size: 12.5px; text-align: center; letter-spacing: 0.3px; border: 1px solid #1F5C6E; }
table.kpi thead th:first-child { background: #fff; border: none; width: 60px; }
table.kpi tbody td { padding: 7px 12px; text-align: center; font-size: 20px; font-weight: 700; border: 1px solid #E5E7EB; }
td.plat-cell { background: #fff; border: none; width: 60px; padding: 3px; }
td.plat-cell img { display: block; margin: 0 auto; }
td.cur-cell  { background: #E07B47; color: #fff; }      /* Periodo Attuale = arancione */
td.prev-cell { background: #fff;    color: #1F5C6E; }   /* Periodo Precedente = bianco */
.delta-pos { color: #1AA64B; }                          /* verde evidente per i + */
.delta-neg { color: #C0392B; }
.delta-launch { color: #2F5496; font-style: italic; font-size: 17px; }
.delta-na { color: #9CA3AF; font-style: italic; }
.kpi-caption { font-size: 12px; font-weight: 400; line-height: 1.26; color: #1F5C6E; margin-top: 3px; padding-right: 8px; }

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
    if p is None: return f'<td class="delta-na">{t("na")}</td>'
    cls = "delta-pos" if p >= 0 else "delta-neg"
    return f'<td class="{cls}">{fmt_pct(p)}</td>'


def kpi_block(metric_key, table_html, caption=None):
    cap = f'<div class="kpi-caption">{caption}</div>' if caption else ""
    if LANG == "en":
        glyph = img_tag(ICON_DIR_EN, ICON_FN["en"][metric_key], "height:86px")
        side = f'<div class="kpi-side kpi-side-en"><div class="ic-en">{glyph}</div><div class="nm-en">{t("lab")[metric_key]}</div></div>'
    else:
        full = img_tag(ICON_DIR, ICON_FN["it"][metric_key], "width:160px")
        side = f'<div class="kpi-side">{full}</div>'
    return f'<div class="kpi-block">{side}<div class="kpi-main">{table_html}{cap}</div></div>'


def meta_2row_table(field, ig_c, ig_p, fb_c, fb_p, fmt):
    return f"""<table class="kpi">
  <thead><tr><th></th><th>{t("cur")}</th><th>{t("prev")}</th><th>{t("cmp")}</th></tr></thead>
  <tbody>
    <tr><td class="plat-cell">{LOGO_IG}</td><td class="cur-cell">{fmt(ig_c.get(field) or 0)}</td><td class="prev-cell">{fmt(ig_p.get(field) or 0)}</td>{delta_cell(ig_c.get(field) or 0, ig_p.get(field) or 0)}</tr>
    <tr><td class="plat-cell">{LOGO_FB}</td><td class="cur-cell">{fmt(fb_c.get(field) or 0)}</td><td class="prev-cell">{fmt(fb_p.get(field) or 0)}</td>{delta_cell(fb_c.get(field) or 0, fb_p.get(field) or 0)}</tr>
  </tbody>
</table>"""


def meta_budget_table(sp_c, sp_p):
    return f"""<table class="kpi">
  <thead><tr><th></th><th>{t("cur")}</th><th>{t("prev")}</th><th>{t("cmp")}</th></tr></thead>
  <tbody>
    <tr><td class="plat-cell"></td><td class="cur-cell">{fmt_eur(sp_c)}</td><td class="prev-cell">{fmt_eur(sp_p)}</td>{delta_cell(sp_c, sp_p)}</tr>
  </tbody>
</table>"""


def tk_table(field, cur, prev, fmt, launched):
    override = t("live") if launched else None
    return f"""<table class="kpi">
  <thead><tr><th></th><th>{t("cur")}</th><th>{t("prev")}</th><th>{t("cmp")}</th></tr></thead>
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
        rows += f"""<tr><td class="mese">{month_name(m).upper()}</td><td>{fmt_eur(meta_v)}</td><td>{fmt_eur(tk_v)}</td><td>{fmt_eur(meta_v + tk_v)}</td></tr>"""
    speso = tot_meta + tot_tk; rimanente = budget - speso
    return f"""<table class="budget">
  <thead>
    <tr><th class="hdr-budget-annuale" colspan="3">{t("b_annual")}</th><th class="hdr-budget-val">{fmt_eur(budget)}</th></tr>
    <tr class="hdr-cols"><th>{t("b_months")}</th><th>{t("b_meta")}</th><th>{t("b_tk")}</th><th>{t("b_total")}</th></tr>
  </thead>
  <tbody>{rows}</tbody>
  <tfoot>
    <tr class="speso"><td>{t("b_spent")}</td><td>{fmt_eur(tot_meta)}</td><td>{fmt_eur(tot_tk)}</td><td>{fmt_eur(speso)}</td></tr>
    <tr class="rimanente"><td>{t("b_remain")}</td><td></td><td></td><td>{fmt_eur(rimanente)}</td></tr>
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
    if LANG == "en":
        return build_rational_en(v, focus)
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

    # META — primo mese live (debutto ads)
    if v.get("meta_launched"):
        impr_meta = (fb_c.get("impressions") or 0) + (ig_c.get("impressions") or 0)
        s = (f"{month_cap} {year} segna il debutto pubblicitario di {cn}: la prima campagna Meta va live e apre il "
             f"presidio con {fmt_int(reach_meta)} utenti unici raggiunti e {fmt_int(impr_meta)} visualizzazioni, "
             f"ponendo le fondamenta della brand awareness sul territorio. {driver} guida la copertura in questa fase "
             f"di lancio, a conferma di un mix ben calibrato sugli obiettivi di notorietà. L'investimento del mese "
             f"({fmt_eur(spend_cur)}) costruisce il primo bacino di pubblico qualificato da riattivare nelle finestre "
             f"stagionali a più alta intenzione di prenotazione. Da {next_low} (peso {next_w}% del piano annuo) "
             f"consolidiamo la pressione per trasformare la scoperta del brand in prenotazioni.")
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


def build_rational_en(v, focus):
    fb_c = v["meta_cur"]["facebook"]; fb_p = v["meta_prev"]["facebook"]
    ig_c = v["meta_cur"]["instagram"]; ig_p = v["meta_prev"]["instagram"]
    spend_cur = (fb_c.get("spend") or 0) + (ig_c.get("spend") or 0)
    spend_prev = (fb_p.get("spend") or 0) + (ig_p.get("spend") or 0)
    spend_delta = pct(spend_cur, spend_prev)
    fb_reach = fb_c.get("reach") or 0; ig_reach = ig_c.get("reach") or 0
    reach_meta = fb_reach + ig_reach
    fb_reach_delta = pct(fb_reach, fb_p.get("reach") or 0)
    tot_eng = (fb_c.get("actions_page_engagement") or 0) + (ig_c.get("actions_page_engagement") or 0)
    cn = v["client_name"]; mo = MONTH_EN[v["month"]]; year = v["year"]
    cur_w = BUDGET_WEIGHTS[v["month"]]
    next_m = (v["month"] % 12) + 1; next_mo = MONTH_EN[next_m]; next_w = BUDGET_WEIGHTS[next_m]
    driver = "Facebook" if fb_reach >= ig_reach else "Instagram"

    if focus == "tiktok":
        tk = v["tk_cur"] or empty_tk()
        if v["tk_launched"]:
            s = (f"{mo} {year} marks a new phase for {cn}: the first TikTok campaign goes live and debuts with "
                 f"{fmt_int(tk.get('impressions') or 0)} impressions and {fmt_int(tk.get('reach') or 0)} unique users "
                 f"reached, activating presence on a younger audience at the right moment of the calendar. From {next_mo}, "
                 f"{cn} works on two complementary levers — Meta for conversion, TikTok for brand discovery — ahead of the "
                 f"seasonal windows with the highest booking traffic.")
        elif (tk.get("impressions") or 0) > 0:
            s = (f"{mo} {year} confirms an efficient TikTok presence for {cn}, with {fmt_int(tk.get('impressions') or 0)} "
                 f"impressions and {fmt_int(tk.get('reach') or 0)} unique users reached: the channel expands coverage on a "
                 f"younger audience at competitive costs, confirming a well-balanced mix focused on awareness goals. "
                 f"Pressure continues strategically toward {next_mo} ({next_w}% of the annual plan).")
        else:
            s = (f"{mo} {year} sees TikTok on standby for {cn}: pressure stays focused on the main channels, while the "
                 f"dedicated budget remains intact and ready to reactivate on the higher-return seasonal windows toward {next_mo}.")
        return f"<p>{s}</p>"

    if v.get("meta_launched"):
        impr_meta = (fb_c.get("impressions") or 0) + (ig_c.get("impressions") or 0)
        s = (f"{mo} {year} marks the advertising debut of {cn}: the first Meta campaign goes live, opening presence with "
             f"{fmt_int(reach_meta)} unique users reached and {fmt_int(impr_meta)} impressions, laying the foundations of "
             f"brand awareness. {driver} leads coverage in this launch phase, confirming a well-balanced mix focused on "
             f"awareness goals. This month's investment ({fmt_eur(spend_cur)}) builds the first pool of qualified audience "
             f"to reactivate in the higher-intent seasonal booking windows. From {next_mo} ({next_w}% of the annual plan) "
             f"we consolidate pressure to turn brand discovery into bookings.")
        return f"<p>{s}</p>"

    if spend_cur == 0 and reach_meta == 0:
        s = (f"{mo} {year} represents a strategic pause for {cn}, consistent with the month's position within the annual "
             f"media plan ({cur_w}%). The budget stays intact and ready to focus on the higher-return seasonal windows. "
             f"From {next_mo} ({next_w}% of the annual plan) presence resumes "
             f"{'at the heart of the season' if next_w >= 12 else 'gradually'}, where we will concentrate pressure on the "
             f"windows with the highest booking intent.")
        return f"<p>{s}</p>"

    if spend_delta is not None and spend_delta > 8:
        s1 = (f"{mo} {year} opens with a strategic increase in the Meta ad budget ({fmt_pct(spend_delta)}), a choice "
              f"consistent with the month's position within the annual plan ({cur_w}%).")
    elif spend_delta is not None and spend_delta < -8:
        s1 = (f"{mo} {year} is the month of efficiency for {cn}: Meta investment is recalibrated ({fmt_pct(spend_delta)}) "
              f"in line with the month's position in the annual plan ({cur_w}%).")
    else:
        s1 = (f"{mo} {year} confirms a stable Meta presence for {cn}, in line with the month's position within the annual "
              f"plan ({cur_w}%).")

    if fb_reach_delta is not None and fb_reach_delta > 100:
        s2 = (f"{driver} becomes the driving channel and expands coverage to {fmt_int(reach_meta)} unique users, "
              f"confirming a well-balanced channel mix focused on awareness goals.")
    else:
        s2 = (f"{driver} expands coverage reaching {fmt_int(reach_meta)} unique users, confirming a well-balanced channel "
              f"mix focused on awareness goals.")

    if spend_delta is not None and spend_delta < -8 and reach_meta > 0:
        s3 = ("Cost per result stays efficient in a more selective auction context, a sign of a targeting strategy that "
              "keeps working.")
    elif tot_eng > 50000:
        s3 = (f"Total interactions reach {fmt_int(tot_eng)}, a sign of content that keeps generating qualified "
              f"conversations around the brand.")
    else:
        s3 = "Cost per result remains efficient in a more selective auction context, a sign of targeting that keeps working."

    if next_w >= 12:
        s4 = (f"The base built in {mo} {year} sets up {next_mo} ({next_w}% of the annual plan), where we will concentrate "
              f"pressure on the windows with the highest booking intent.")
    else:
        s4 = (f"The base built in {mo} {year} sets up {next_mo} ({next_w}% of the annual plan), keeping the audience warm "
              f"ahead of the most relevant windows.")
    return f"<p>{s1} {s2} {s3} {s4}</p>"


def _periods_meta(v):
    cy, cm = comparison_period(v["year"], v["month"], v["cfg"]["cm"])
    return f"{month_name(v['month'])} {v['year']}", f"{month_name(cm)} {cy}"

def _periods_tk(v):
    cy, cm = comparison_period(v["year"], v["month"], v["cfg"]["ct"])
    return f"{month_name(v['month'])} {v['year']}", f"{month_name(cm)} {cy}"

AG_LOGO = '<div class="ag-logo">AG</div>'

def meta_page_html(v):
    fb_c, fb_p = v["meta_cur"]["facebook"], v["meta_prev"]["facebook"]
    ig_c, ig_p = v["meta_cur"]["instagram"], v["meta_prev"]["instagram"]
    sp_c = (fb_c.get("spend") or 0) + (ig_c.get("spend") or 0)
    sp_p = (fb_p.get("spend") or 0) + (ig_p.get("spend") or 0)

    blocks = ""
    for field, mkey in META_METRICS:
        blocks += kpi_block(mkey, meta_2row_table(field, ig_c, ig_p, fb_c, fb_p, fmt_int), CAPS[LANG][mkey])
    blocks += kpi_block("budget", meta_budget_table(sp_c, sp_p), None)

    pa, pb = _periods_meta(v)
    return f"""<div class="page">
      <div class="page-header"><h1 class="page-title">Meta Advertising</h1>
        <p class="page-subtitle">{pa}<span class="vs">vs</span>{pb}</p></div>
      <div class="tables-col">{blocks}</div>
      <div class="rational-box">{build_rational(v, "meta")}</div>
    </div>"""


def tiktok_page_html(v):
    tk_c = v["tk_cur"] or empty_tk(); tk_p = v["tk_prev"] or empty_tk()
    launched = v["tk_launched"]
    blocks = ""
    for field, mkey in TK_METRICS:
        blocks += kpi_block(mkey, tk_table(field, tk_c.get(field) or 0, tk_p.get(field) or 0, fmt_int, launched), CAPS[LANG][mkey])
    blocks += kpi_block("budget", tk_table("spend", tk_c.get("spend") or 0, tk_p.get("spend") or 0, fmt_eur, launched), None)

    pa, pb = _periods_tk(v)
    return f"""<div class="page">
      <div class="page-header"><h1 class="page-title">Tik Tok Advertising</h1>
        <p class="page-subtitle">{pa}<span class="vs">vs</span>{pb}</p></div>
      <div class="tables-col">{blocks}</div>
      <div class="rational-box">{build_rational(v, "tiktok")}</div>
    </div>"""


def generate_client_tables(client_name, data, year, month, outdir, lang="it"):
    # lingua per-cliente dall'anagrafica (es. Villa Ermellina = en), altrimenti il default --lang
    global LANG; LANG = CLIENTS[client_name].get("lang", lang)
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
    p.add_argument("--lang", default="it", choices=["it", "en"], help="Lingua slide (default it)")
    args = p.parse_args()
    data = json.loads(Path(args.data).read_text(encoding="utf-8"))
    outdir = Path(args.output_dir); outdir.mkdir(parents=True, exist_ok=True)
    if args.client:
        if args.client not in CLIENTS:
            raise SystemExit(f"Cliente '{args.client}' non trovato.")
        generate_client_tables(args.client, data, args.year, args.month, outdir, args.lang)
    else:
        for cn in CLIENTS:
            generate_client_tables(cn, data, args.year, args.month, outdir, args.lang)


if __name__ == "__main__":
    main()
