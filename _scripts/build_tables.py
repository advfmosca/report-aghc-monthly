#!/usr/bin/env python3
"""build_tables.py — Genera PNG delle tabelle KPI per ogni cliente AGHC.

Output: una cartella per cliente con i PNG delle tabelle (Meta + TikTok + Budget Annuale).
Francesco apre il template Canva del cliente, seleziona la tabella vuota, e la sostituisce
con il PNG corrispondente (drag&drop o Inserisci → Immagine).

Estetica replicata 1:1 col TEMPLATE ORIGINALE Canva AGHC:
  - Header teal #1F5C6E con testo bianco bold
  - Cella "Periodo Precedente" (colonna media) arancione #E07B47 testo bianco
  - Cella "Periodo Attuale" bianca testo teal bold
  - Confronto colorato verde positivo / rosso negativo
  - Loghi IG/FB/TikTok nella prima colonna (fuori griglia)

Tabelle generate per cliente:
  Meta (sempre):    01_meta_account_raggiunti, 02_meta_visualizzazioni,
                    03_meta_interazioni, 04_meta_clicks, 05_meta_budget
  TikTok (se attivo): 06_tk_account_raggiunti, 07_tk_visualizzazioni,
                      08_tk_click_destinazione, 09_tk_budget
  Budget annuale:   10_budget_annuale

Uso:
  # Singolo cliente
  python3 build_tables.py --year 2026 --month 4 --client Lunetta \\
    --data _data/data-2026-04.json --output-dir /tmp/lunetta_tables/

  # Tutti i 18 clienti
  python3 build_tables.py --year 2026 --month 4 \\
    --data _data/data-2026-04.json --output-dir /tmp/all_tables/
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
LOGO_IG = """<svg viewBox="0 0 24 24" width="46" height="46" xmlns="http://www.w3.org/2000/svg"><defs><linearGradient id="igG" x1="0%" y1="100%" x2="100%" y2="0%"><stop offset="0%" stop-color="#FED576"/><stop offset="26%" stop-color="#F47133"/><stop offset="61%" stop-color="#BC3081"/><stop offset="100%" stop-color="#4C63D2"/></linearGradient></defs><rect x="2" y="2" width="20" height="20" rx="5.5" ry="5.5" fill="url(#igG)"/><path d="M12 7.4a4.6 4.6 0 1 0 0 9.2 4.6 4.6 0 0 0 0-9.2zm0 7.6a3 3 0 1 1 0-6 3 3 0 0 1 0 6zm5.8-7.85a1.1 1.1 0 1 1-2.2 0 1.1 1.1 0 0 1 2.2 0z" fill="#fff"/></svg>"""
LOGO_FB = """<svg viewBox="0 0 24 24" width="46" height="46" xmlns="http://www.w3.org/2000/svg"><path d="M24 12.073C24 5.405 18.627 0 12 0S0 5.405 0 12.073C0 18.1 4.388 23.094 10.125 24v-8.437H7.078v-3.49h3.047V9.41c0-3.007 1.792-4.668 4.533-4.668 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.927-1.956 1.876v2.25h3.328l-.532 3.49h-2.796V24C19.612 23.094 24 18.1 24 12.073z" fill="#1877F2"/></svg>"""
LOGO_TK = """<svg viewBox="0 0 24 24" width="46" height="46" xmlns="http://www.w3.org/2000/svg"><path d="M19.59 6.69a4.83 4.83 0 0 1-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 0 1-5.2 1.74 2.89 2.89 0 0 1 2.31-4.64 2.93 2.93 0 0 1 .88.13V9.4a6.84 6.84 0 0 0-1-.05A6.33 6.33 0 0 0 5.6 20.1a6.34 6.34 0 0 0 10.86-4.43V8.61a8.16 8.16 0 0 0 4.77 1.52v-3.4a4.85 4.85 0 0 1-1.64-.04Z" fill="#010101"/></svg>"""

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


# === CSS ===
CSS_KPI_TABLE = """
@page { size: 1200px 220px; margin: 0; }
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: "Lato", "Open Sans", -apple-system, sans-serif; color: #1F5C6E; padding: 8px; }
table.kpi {
  border-collapse: collapse;
  width: 100%;
  font-size: 28px;
}
table.kpi thead th {
  background: #1F5C6E; color: #fff;
  padding: 13px 16px;
  font-weight: 600; font-size: 17px;
  text-align: center; letter-spacing: 0.3px;
  border: 1px solid #1F5C6E;
}
table.kpi thead th:first-child { background: #fff; border: none; width: 70px; }
table.kpi tbody td {
  padding: 16px 16px;
  text-align: center;
  font-size: 28px; font-weight: 700;
  border: 1px solid #E5E7EB;
}
td.plat-cell { background: #fff; border: none; width: 70px; padding: 4px; }
td.plat-cell svg { display: block; margin: 0 auto; }
td.cur-cell { background: #fff; color: #1F5C6E; }
td.prev-cell { background: #E07B47; color: #fff; }
.delta-pos { color: #4F8C3F; }
.delta-neg { color: #C04A3D; }
.delta-launch { color: #2F5496; font-style: italic; font-size: 22px; }
.delta-na { color: #9CA3AF; font-style: italic; }
"""

# === CSS pagina intera (Meta/TikTok) — replica layout template originale ===
CSS_FULL_PAGE = """
@page { size: 1920px 1080px; margin: 0; }
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: "Lato", "Open Sans", -apple-system, sans-serif; color: #1F5C6E; background: #fff; }
.page {
  width: 1920px; height: 1080px;
  position: relative;
}
/* Header slide (titolo + sottotitolo periodo) */
.page-header {
  position: absolute;
  top: 60px; left: 70px;
  width: 400px;
}
.page-title {
  font-size: 52px; font-weight: 700;
  color: #1F5C6E;
  letter-spacing: -0.5px;
  line-height: 1.05;
  margin: 0 0 12px 0;
}
.page-subtitle {
  font-size: 22px; font-weight: 600;
  color: #1F5C6E;
  letter-spacing: 0.3px;
  margin: 0;
}
.page-subtitle .vs {
  font-size: 14px; font-weight: 400;
  color: #1F5C6E;
  text-transform: lowercase;
  display: block;
  margin: 4px 0;
}

/* Colonna tabelle (centro pagina) */
.tables-col {
  position: absolute;
  top: 90px; left: 500px;
  width: 1000px;
  display: flex; flex-direction: column;
  gap: 30px;
}
.tables-col table.kpi {
  border-collapse: collapse;
  width: 100%;
  font-size: 22px;
}
.tables-col table.kpi thead th {
  background: #1F5C6E; color: #fff;
  padding: 10px 14px;
  font-weight: 600; font-size: 14px;
  text-align: center; letter-spacing: 0.3px;
  border: 1px solid #1F5C6E;
}
.tables-col table.kpi thead th:first-child { background: #fff; border: none; width: 60px; }
.tables-col table.kpi tbody td {
  padding: 12px 14px;
  text-align: center;
  font-size: 22px; font-weight: 700;
  border: 1px solid #E5E7EB;
}
.tables-col td.plat-cell { background: #fff; border: none; width: 60px; padding: 4px; }
.tables-col td.plat-cell svg { display: block; margin: 0 auto; }
.tables-col td.cur-cell { background: #fff; color: #1F5C6E; }
.tables-col td.prev-cell { background: #E07B47; color: #fff; }
.tables-col .delta-pos { color: #4F8C3F; }
.tables-col .delta-neg { color: #C04A3D; }
.tables-col .delta-launch { color: #2F5496; font-style: italic; font-size: 18px; }
.tables-col .delta-na { color: #9CA3AF; font-style: italic; }

/* Box RATIONAL (destra) */
.rational-box {
  position: absolute;
  top: 130px; right: 50px;
  width: 360px;
  background: #1F5C6E;
  color: #fff;
  padding: 26px 28px;
  font-size: 16px;
  line-height: 1.55;
  min-height: 800px;
}
.rational-box .rational-header {
  font-size: 18px; font-weight: 700; letter-spacing: 1.5px;
  margin-bottom: 18px;
}
.rational-box p { margin-bottom: 14px; }
.rational-box p:last-child { margin-bottom: 0; }
"""

CSS_BUDGET_TABLE = """
@page { size: 1400px 720px; margin: 0; }
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: "Lato", "Open Sans", -apple-system, sans-serif; color: #1F5C6E; padding: 12px; }
table.budget {
  border-collapse: collapse;
  width: 100%;
  font-size: 22px;
}
th.hdr-budget-annuale {
  background: #1F5C6E; color: #fff;
  padding: 16px 24px;
  text-align: left; font-size: 22px; font-weight: 700; letter-spacing: 1.5px;
  border: 1px solid #1F5C6E;
}
th.hdr-budget-val {
  background: #1F5C6E; color: #fff;
  padding: 16px 24px;
  text-align: right; font-size: 22px; font-weight: 700;
  border: 1px solid #1F5C6E;
}
tr.hdr-cols th {
  background: #E07B47; color: #fff;
  padding: 11px 24px; font-size: 14px; font-weight: 700; letter-spacing: 1px;
  border: 1px solid #fff;
}
tr.hdr-cols th:first-child { text-align: left; }
tr.hdr-cols th:nth-child(n+2) { text-align: center; }
.budget tbody td {
  padding: 11px 24px;
  font-size: 18px; font-weight: 600;
  border: 1px solid #E5E7EB;
}
.budget tbody td.mese { text-align: left; font-weight: 700; color: #1F5C6E; }
.budget tbody td:nth-child(n+2) { text-align: right; }
.budget tfoot td {
  background: #fff;
  padding: 13px 24px;
  font-size: 18px; font-weight: 700;
  color: #1F5C6E;
  border-top: 2px solid #1F5C6E;
}
.budget tfoot td:nth-child(n+2) { text-align: right; }
.budget tfoot tr.speso td { border-bottom: 1px solid #E5E7EB; }
.budget tfoot tr.rimanente td { border-top: none; }
"""

# === Generazione tabelle ===
def render_html(table_inner_html, css):
    return f"""<!DOCTYPE html><html><head><meta charset="UTF-8"></head><body>{table_inner_html}</body></html>"""


def delta_cell(cur, prev, override=None):
    if override:
        return f'<td class="delta-launch">{override}</td>'
    p = pct(cur, prev)
    if p is None: return '<td class="delta-na">n/d</td>'
    cls = "delta-pos" if p >= 0 else "delta-neg"
    return f'<td class="{cls}">{fmt_pct(p)}</td>'


def kpi_meta_2row_table(ig_logo, fb_logo, field, ig_c, ig_p, fb_c, fb_p, fmt):
    return f"""
<table class="kpi">
  <thead><tr><th></th><th>Periodo Attuale</th><th>Periodo Precedente</th><th>Confronto</th></tr></thead>
  <tbody>
    <tr><td class="plat-cell">{ig_logo}</td><td class="cur-cell">{fmt(ig_c.get(field) or 0)}</td><td class="prev-cell">{fmt(ig_p.get(field) or 0)}</td>{delta_cell(ig_c.get(field) or 0, ig_p.get(field) or 0)}</tr>
    <tr><td class="plat-cell">{fb_logo}</td><td class="cur-cell">{fmt(fb_c.get(field) or 0)}</td><td class="prev-cell">{fmt(fb_p.get(field) or 0)}</td>{delta_cell(fb_c.get(field) or 0, fb_p.get(field) or 0)}</tr>
  </tbody>
</table>"""


def kpi_meta_budget_table(sp_c, sp_p):
    return f"""
<table class="kpi">
  <thead><tr><th></th><th>Periodo Attuale</th><th>Periodo Precedente</th><th>Confronto</th></tr></thead>
  <tbody>
    <tr><td class="plat-cell"></td><td class="cur-cell">{fmt_eur(sp_c)}</td><td class="prev-cell">{fmt_eur(sp_p)}</td>{delta_cell(sp_c, sp_p)}</tr>
  </tbody>
</table>"""


def kpi_tk_table(tk_logo, field, cur, prev, fmt, launched):
    override = "1° mese live" if launched else None
    return f"""
<table class="kpi">
  <thead><tr><th></th><th>Periodo Attuale</th><th>Periodo Precedente</th><th>Confronto</th></tr></thead>
  <tbody>
    <tr><td class="plat-cell">{tk_logo}</td><td class="cur-cell">{fmt(cur)}</td><td class="prev-cell">{fmt(prev)}</td>{delta_cell(cur, prev, override)}</tr>
  </tbody>
</table>"""


def budget_annuale_table(v):
    budget = v["cfg"]["budget"] or 0
    ytd_months = v["ytd_months"]
    ytd_client = v["ytd_client"]
    rows = ""
    tot_meta = tot_tk = 0
    for m in range(1, 13):
        md = ytd_client.get(str(m), {"meta":0, "tiktok":0}) if m in ytd_months else {"meta":0, "tiktok":0}
        meta_v = md.get("meta") or 0
        tk_v = md.get("tiktok") or 0
        tot_meta += meta_v
        tot_tk += tk_v
        rows += f"""<tr><td class="mese">{MONTH_IT[m].upper()}</td><td>{fmt_eur(meta_v)}</td><td>{fmt_eur(tk_v)}</td><td>{fmt_eur(meta_v + tk_v)}</td></tr>"""
    speso = tot_meta + tot_tk
    rimanente = budget - speso
    return f"""
<table class="budget">
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
    """HTML → PDF (WeasyPrint) → PNG (pdftoppm).
    Lavora in /tmp per evitare problemi di permessi su FUSE mount."""
    out_png.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="aghc_tables_") as td:
        td_path = Path(td)
        pdf_path = td_path / "page.pdf"
        html = render_html(html_inner, css)
        HTML(string=html).write_pdf(str(pdf_path), stylesheets=[CSS(string=css)])
        # pdftoppm → PNG (pagina singola → page-1.png)
        prefix = td_path / "page"
        subprocess.run([
            "pdftoppm", "-png", "-r", str(dpi),
            str(pdf_path), str(prefix)
        ], check=True)
        generated = td_path / "page-1.png"
        if not generated.exists():
            raise RuntimeError(f"pdftoppm non ha prodotto PNG attesa: {generated}")
        # Copia su destinazione finale (no rename, può attraversare filesystem)
        shutil.copy(generated, out_png)


# === BUDGET_WEIGHTS for rational ===
BUDGET_WEIGHTS = {1:3,2:3,3:5,4:10,5:15,6:15,7:12,8:12,9:5,10:5,11:5,12:10}


def build_rational(v, focus):
    """Rational 3-paragrafi adatto al box laterale, TOV positivo-strategico."""
    fb_c = v["meta_cur"]["facebook"]; fb_p = v["meta_prev"]["facebook"]
    ig_c = v["meta_cur"]["instagram"]; ig_p = v["meta_prev"]["instagram"]
    spend_cur = (fb_c.get("spend") or 0) + (ig_c.get("spend") or 0)
    spend_prev = (fb_p.get("spend") or 0) + (ig_p.get("spend") or 0)
    spend_delta = pct(spend_cur, spend_prev)
    fb_reach_cur = fb_c.get("reach") or 0
    fb_reach_delta = pct(fb_reach_cur, fb_p.get("reach") or 0)
    reach_meta = fb_reach_cur + (ig_c.get("reach") or 0)
    fb_eng_cur = fb_c.get("actions_page_engagement") or 0
    fb_eng_delta = pct(fb_eng_cur, fb_p.get("actions_page_engagement") or 0)
    tot_eng = fb_eng_cur + (ig_c.get("actions_page_engagement") or 0)

    cn = v["client_name"]; pa = f"{MONTH_IT[v['month']]} {v['year']}"
    month_cap = MONTH_IT[v["month"]]
    next_m = (v["month"] % 12) + 1
    next_low = MONTH_IT[next_m].lower()
    next_w = BUDGET_WEIGHTS[next_m]

    if focus == "tiktok":
        if v["tk_launched"]:
            tk = v["tk_cur"]
            p1 = (f"{month_cap} inaugura una nuova fase per {cn}: la prima campagna TikTok va live e debutta "
                  f"con {fmt_int(tk.get('impressions') or 0)} visualizzazioni e {fmt_int(tk.get('reach') or 0)} "
                  f"utenti unici raggiunti.")
            p2 = ("Il presidio sul pubblico più giovane si attiva nel momento giusto, anticipando le finestre "
                  "stagionali a più alto traffico di prenotazione.")
            p3 = (f"Da {next_low} {cn} opera su due leve complementari: Meta per la conversione, TikTok per la "
                  f"scoperta del brand.")
            return f"<p>{p1}</p><p>{p2}</p><p>{p3}</p>"
        if v["tk_cur"] and (v["tk_cur"].get("impressions") or 0) > 0:
            return (f"<p>In {pa} TikTok mantiene un presidio efficiente con {fmt_int(v['tk_cur'].get('impressions') or 0)} "
                    f"impression generate, a conferma di un mix canali ben bilanciato sugli obiettivi di awareness.</p>")
        return f"<p>TikTok in stand-by per {cn} in {pa}; la pressione resta concentrata sui canali principali.</p>"

    # META
    if spend_cur == 0 and reach_meta == 0:
        p1 = f"{month_cap} rappresenta una pausa strategica per {cn}, coerente con il calendario annuo del piano media."
        p2 = "Il budget residuo resta integro e pronto a concentrarsi sulle finestre stagionali a più alto ritorno."
        p3 = f"Da {next_low} (peso {next_w}% del piano annuo) il presidio riprende {'nel cuore della stagione' if next_w >= 12 else 'in modo progressivo'}."
        return f"<p>{p1}</p><p>{p2}</p><p>{p3}</p>"

    if fb_reach_delta is not None and fb_reach_delta > 100:
        mul = f"{(1 + fb_reach_delta/100):.1f}".replace('.', ',')
        p1 = (f"{month_cap} segna un cambio di passo per {cn}: Facebook diventa il canale di traino e amplia "
              f"la copertura di {mul} volte, raggiungendo {fmt_int(fb_reach_cur)} utenti unici.")
    elif spend_delta is not None and spend_delta < -8 and reach_meta > 0:
        p1 = (f"{month_cap} è il mese dell'efficienza per {cn}: la copertura Meta resta solida con "
              f"{fmt_int(reach_meta)} utenti unici raggiunti, con un investimento ridotto del {abs(int(spend_delta))}%. "
              f"Ogni euro speso ha lavorato meglio.")
    else:
        p1 = (f"{month_cap} mantiene il presidio di {cn} su base solida: {fmt_int(reach_meta)} utenti unici "
              f"raggiunti su Meta, in linea con il posizionamento strategico del mese.")

    if fb_eng_delta is not None and fb_eng_delta > 100 and fb_eng_cur > 5000:
        p2 = (f"Le interazioni sui contenuti Facebook salgono a {fmt_int(fb_eng_cur)}, una scala completamente "
              f"diversa rispetto al periodo di confronto.")
    elif tot_eng > 50000:
        p2 = (f"Il pubblico interagisce attivamente con i contenuti, con {fmt_int(tot_eng)} interazioni totali "
              f"generate nel mese.")
    else:
        p2 = (f"Il presidio del marchio resta attivo: i contenuti pubblicati continuano a generare conversazioni "
              f"qualificate intorno a {cn}.")

    if next_w >= 12:
        p3 = (f"{MONTH_IT[next_m]} entra nel cuore della stagione ({next_w}% del budget annuo): saliamo sulla "
              f"pressione per intercettare la domanda attiva.")
    else:
        p3 = (f"A {next_low} (peso {next_w}% del piano annuo) il presidio prosegue strategico, mantenendo il "
              f"pubblico caldo in vista delle finestre più rilevanti.")
    return f"<p>{p1}</p><p>{p2}</p><p>{p3}</p>"


def _periods_meta(v):
    comp_y, comp_m = comparison_period(v["year"], v["month"], v["cfg"]["cm"])
    return f"{MONTH_IT[v['month']]} {v['year']}", f"{MONTH_IT[comp_m]} {comp_y}"

def _periods_tk(v):
    comp_y, comp_m = comparison_period(v["year"], v["month"], v["cfg"]["ct"])
    return f"{MONTH_IT[v['month']]} {v['year']}", f"{MONTH_IT[comp_m]} {comp_y}"


def meta_page_html(v):
    fb_c, fb_p = v["meta_cur"]["facebook"], v["meta_prev"]["facebook"]
    ig_c, ig_p = v["meta_cur"]["instagram"], v["meta_prev"]["instagram"]
    sp_c = (fb_c.get("spend") or 0) + (ig_c.get("spend") or 0)
    sp_p = (fb_p.get("spend") or 0) + (ig_p.get("spend") or 0)

    tables = ""
    for field in ["reach", "impressions", "actions_page_engagement", "clicks"]:
        tables += kpi_meta_2row_table(LOGO_IG, LOGO_FB, field, ig_c, ig_p, fb_c, fb_p, fmt_int)
    tables += kpi_meta_budget_table(sp_c, sp_p)

    pa, pb = _periods_meta(v)
    rational_html = build_rational(v, "meta")
    return f"""<div class="page">
      <div class="page-header">
        <h1 class="page-title">Meta Advertising</h1>
        <p class="page-subtitle">{pa}<span class="vs">vs</span>{pb}</p>
      </div>
      <div class="tables-col">{tables}</div>
      <div class="rational-box"><div class="rational-header">RATIONAL</div>{rational_html}</div>
    </div>"""


def tiktok_page_html(v):
    tk_c = v["tk_cur"] or empty_tk()
    tk_p = v["tk_prev"] or empty_tk()
    launched = v["tk_launched"]

    tables = ""
    tables += kpi_tk_table(LOGO_TK, "reach",       tk_c.get("reach") or 0, tk_p.get("reach") or 0, fmt_int, launched)
    tables += kpi_tk_table(LOGO_TK, "impressions", tk_c.get("impressions") or 0, tk_p.get("impressions") or 0, fmt_int, launched)
    tables += kpi_tk_table(LOGO_TK, "clicks",      tk_c.get("clicks") or 0, tk_p.get("clicks") or 0, fmt_int, launched)
    tables += kpi_tk_table(LOGO_TK, "spend",       tk_c.get("spend") or 0, tk_p.get("spend") or 0, fmt_eur, launched)

    pa, pb = _periods_tk(v)
    rational_html = build_rational(v, "tiktok")
    return f"""<div class="page">
      <div class="page-header">
        <h1 class="page-title">Tik Tok Advertising</h1>
        <p class="page-subtitle">{pa}<span class="vs">vs</span>{pb}</p>
      </div>
      <div class="tables-col">{tables}</div>
      <div class="rational-box"><div class="rational-header">RATIONAL</div>{rational_html}</div>
    </div>"""


def generate_client_tables(client_name, data, year, month, outdir):
    v = build_view(client_name, data, year, month)
    client_dir = outdir / client_name
    client_dir.mkdir(parents=True, exist_ok=True)

    # 1. Meta page (5 tabelle + rational a destra)
    render_table(meta_page_html(v), CSS_FULL_PAGE, client_dir / "01_meta.png", dpi=150)

    # 2. TikTok page (se attivo, 4 tabelle + rational)
    if v["has_tk"]:
        render_table(tiktok_page_html(v), CSS_FULL_PAGE, client_dir / "02_tiktok.png", dpi=150)

    # 3. Budget annuale
    render_table(budget_annuale_table(v), CSS_BUDGET_TABLE, client_dir / "03_budget.png", dpi=200)

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
    outdir = Path(args.output_dir)
    outdir.mkdir(parents=True, exist_ok=True)
    if args.client:
        if args.client not in CLIENTS:
            raise SystemExit(f"Cliente '{args.client}' non trovato.")
        generate_client_tables(args.client, data, args.year, args.month, outdir)
    else:
        for cn in CLIENTS:
            generate_client_tables(cn, data, args.year, args.month, outdir)


if __name__ == "__main__":
    main()
