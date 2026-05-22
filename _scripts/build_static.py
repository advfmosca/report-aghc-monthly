#!/usr/bin/env python3
"""build_static.py — Genera la pagina HTML statica self-contained del report mensile AGHC.

Style: Executive Minimal — typography pulita, palette mono nero/grigio, numeri grandi,
sparkline inline sui trend YTD. Niente colori corporate, niente gradient pesanti.

Input:
  --year 2026 --month 4 --data _data/data-2026-04.json

Output:
  - <slug>.html (es. aprile-2026.html) nella root del repo
  - index.html ricostruito con la lista di tutti i mesi disponibili
"""
import argparse, json, sys, re, os
from pathlib import Path
from datetime import datetime

MONTH_IT = {1:"gennaio",2:"febbraio",3:"marzo",4:"aprile",5:"maggio",6:"giugno",
            7:"luglio",8:"agosto",9:"settembre",10:"ottobre",11:"novembre",12:"dicembre"}

ROOT = Path(__file__).resolve().parent.parent

CLIENTS = [
    {"nome":"Accentodì","meta_id":"1312718426033158","filter":["Accentodì"],"excl":[],"tk_id":None,"cm":"YoY","ct":None,"budget":2400,"note":"Cadenza TRIMESTRALE (incluso per consultazione)"},
    {"nome":"Adèsso","meta_id":"1312718426033158","filter":["Adèsso","MICE"],"excl":[],"tk_id":None,"cm":"YoY","ct":None,"budget":2400,"note":"Cadenza TRIMESTRALE (incluso per consultazione)"},
    {"nome":"Altafiumara","meta_id":"1201395876543423","filter":None,"excl":[],"tk_id":None,"cm":"MoM","ct":None,"budget":23000,"note":""},
    {"nome":"Castello","meta_id":"1489903155429629","filter":None,"excl":[],"tk_id":None,"cm":"MoM","ct":None,"budget":14400,"note":""},
    {"nome":"Della Piana","meta_id":"911357333863123","filter":None,"excl":[],"tk_id":"7504967007843319824","cm":"YoY","ct":"MoM","budget":14000,"note":"Split confronto: Meta YoY, TikTok MoM"},
    {"nome":"Hannah","meta_id":"1528485957725509","filter":["Hannah"],"excl":["Terraces"],"tk_id":None,"cm":"YoY","ct":None,"budget":9000,"note":""},
    {"nome":"Hannah Terraces","meta_id":"1528485957725509","filter":["Terraces"],"excl":[],"tk_id":None,"cm":"MoM","ct":None,"budget":7200,"note":""},
    {"nome":"Hemanaire","meta_id":"217115315497718","filter":None,"excl":[],"tk_id":None,"cm":"MoM","ct":None,"budget":15000,"note":"TikTok verrà attivato più avanti"},
    {"nome":"Livata","meta_id":"4666471140299701","filter":None,"excl":[],"tk_id":None,"cm":"MoM","ct":None,"budget":15000,"note":""},
    {"nome":"Lunetta","meta_id":"687349689221880","filter":None,"excl":[],"tk_id":"7498330316248203280","cm":"YoY","ct":"MoM","budget":18000,"note":"Split confronto: Meta YoY, TikTok MoM"},
    {"nome":"Magari Estates","meta_id":"1372615496521110","filter":None,"excl":[],"tk_id":None,"cm":"MoM","ct":None,"budget":24600,"note":""},
    {"nome":"Marcella Royal","meta_id":"821188209852436","filter":["Marcella"],"excl":[],"tk_id":"7499093699838607377","cm":"YoY","ct":"MoM","budget":14400,"note":"Split confronto: Meta YoY, TikTok MoM"},
    {"nome":"Mare","meta_id":"1432341844596179","filter":None,"excl":[],"tk_id":"7498679494010667009","cm":"MoM","ct":"MoM","budget":15000,"note":""},
    {"nome":"Montemagno","meta_id":"752450855779035","filter":None,"excl":[],"tk_id":None,"cm":"MoM","ct":None,"budget":0,"note":"Aggiunto 25/04/2026 — budget annuo da definire"},
    {"nome":"Terrazza Flavia","meta_id":"821188209852436","filter":["Terrazza"],"excl":[],"tk_id":None,"cm":"YoY","ct":None,"budget":7500,"note":""},
    {"nome":"Villa Ermellina","meta_id":"30233607946222961","filter":None,"excl":[],"tk_id":"7612666695502118929","cm":"MoM","ct":"MoM","budget":16400,"note":""},
    {"nome":"Villa Giada","meta_id":"1849759899186169","filter":None,"excl":[],"tk_id":None,"cm":"MoM","ct":None,"budget":21600,"note":"TikTok presente ma non attivo"},
    {"nome":"Villa Miliani","meta_id":"1353024533007038","filter":None,"excl":[],"tk_id":None,"cm":"MoM","ct":None,"budget":6600,"note":""},
]


def slug_for(year, month):
    return f"{MONTH_IT[month]}-{year}"


def render_page(year, month, data):
    slug = slug_for(year, month)
    period_label = f"{MONTH_IT[month].capitalize()} {year}"
    generated_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    data_json = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    clients_json = json.dumps(CLIENTS, ensure_ascii=False, separators=(",", ":"))
    month_json = json.dumps(MONTH_IT, ensure_ascii=False)
    html = HTML_TEMPLATE.replace("__YEAR__", str(year)) \
                       .replace("__MONTH__", str(month)) \
                       .replace("__PERIOD_LABEL__", period_label) \
                       .replace("__GENERATED_AT__", generated_at) \
                       .replace("__DATA_JSON__", data_json) \
                       .replace("__CLIENTS_JSON__", clients_json) \
                       .replace("__MONTH_IT_JSON__", month_json)
    return slug, html


def update_index(repo_root: Path):
    files = []
    for f in repo_root.glob("*.html"):
        if f.name == "index.html":
            continue
        m = re.match(r"([a-zà-ÿ]+)-(\d{4})\.html$", f.name, re.IGNORECASE)
        if not m:
            continue
        mese, anno = m.group(1).lower(), int(m.group(2))
        rev = {v:k for k,v in MONTH_IT.items()}
        if mese not in rev:
            continue
        files.append({"slug": f.stem, "year": anno, "month": rev[mese], "filename": f.name})
    files.sort(key=lambda x: (x["year"], x["month"]), reverse=True)

    rows_html = ""
    for f in files:
        rows_html += f'''      <li class="report-item">
        <a href="{f["filename"]}">
          <span class="month-name">{MONTH_IT[f["month"]].capitalize()} {f["year"]}</span>
          <span class="arrow">→</span>
        </a>
      </li>\n'''

    index_html = INDEX_TEMPLATE.replace("__ROWS__", rows_html).replace("__UPDATED__", datetime.utcnow().strftime("%Y-%m-%d"))
    (repo_root / "index.html").write_text(index_html, encoding="utf-8")

    # JSON archivio per consumo esterno (es. dashboard-di-controllo)
    base_url = "https://advfmosca.github.io/report-aghc-monthly"
    archive_payload = {
        "updated_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "base_url": base_url,
        "count": len(files),
        "reports": [
            {
                "year": f["year"],
                "month": f["month"],
                "slug": f["slug"],
                "label": f"{MONTH_IT[f['month']].capitalize()} {f['year']}",
                "filename": f["filename"],
                "url": f"{base_url}/{f['slug']}",
            }
            for f in files
        ],
    }
    data_dir = repo_root / "_data"
    data_dir.mkdir(exist_ok=True)
    (data_dir / "archive.json").write_text(json.dumps(archive_payload, ensure_ascii=False, indent=2), encoding="utf-8")


# ============================================================================
# HTML TEMPLATE — Executive Minimal
# ============================================================================
HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Report AGHC — __PERIOD_LABEL__</title>
<style>
:root {
  color-scheme: light;
  --bg: #ffffff;
  --bg-soft: #fafafa;
  --bg-muted: #f4f4f5;
  --text: #1c1c1e;
  --text-soft: #3f3f44;
  --text-muted: #6b6b70;
  --text-dim: #8a8a90;
  --border: #ececef;
  --border-soft: #f4f4f5;
  --pos: #15803d;
  --neg: #b91c1c;
  --warn: #b45309;
  --info: #1d4ed8;
}
* { box-sizing: border-box; }
html, body { margin:0; padding:0; }
body {
  font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  background: var(--bg);
  color: var(--text);
  font-size: 14px;
  line-height: 1.55;
  font-feature-settings: "ss01", "cv11", "tnum";
  -webkit-font-smoothing: antialiased;
}
.app { display: grid; grid-template-columns: 260px minmax(0,1fr); min-height: 100vh; }

/* SIDEBAR */
.sidebar {
  border-right: 1px solid var(--border);
  background: var(--bg-soft);
  padding: 28px 0 60px;
  position: sticky; top: 0;
  height: 100vh; overflow-y: auto;
}
.sidebar .brand {
  padding: 0 24px;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--text-muted);
}
.sidebar .period-current {
  padding: 6px 24px 20px;
  font-size: 18px;
  font-weight: 600;
  color: var(--text);
  letter-spacing: -0.01em;
}
.sidebar .archive-link {
  display: flex; align-items: center; gap: 8px;
  margin: 0 16px 24px;
  padding: 10px 14px;
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: 8px;
  text-decoration: none;
  color: var(--text-soft);
  font-size: 13px;
  transition: all .15s ease;
}
.sidebar .archive-link:hover { border-color: var(--text-dim); color: var(--text); }
.sidebar .archive-link .arrow-back { font-size: 14px; }
.sidebar .nav-section {
  padding: 18px 24px 8px;
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--text-dim);
}
.nav-item {
  display: flex; align-items: center; justify-content: space-between;
  padding: 8px 24px;
  cursor: pointer;
  font-size: 13px;
  color: var(--text-soft);
  position: relative;
  transition: color .12s ease;
}
.nav-item:hover { color: var(--text); }
.nav-item:hover::before {
  content: ""; position: absolute; left: 0; top: 0; bottom: 0;
  width: 2px; background: var(--text-dim);
}
.nav-item.active { color: var(--text); font-weight: 600; }
.nav-item.active::before {
  content: ""; position: absolute; left: 0; top: 0; bottom: 0;
  width: 2px; background: var(--text);
}
.nav-item .badge { font-size: 10px; color: var(--text-dim); font-weight: 400; letter-spacing: 0.04em; }

/* MAIN */
.main { padding: 36px 56px 80px; min-width: 0; max-width: 1080px; }

.client-title {
  margin: 0 0 4px;
  font-size: 28px;
  font-weight: 700;
  letter-spacing: -0.02em;
  color: var(--text);
}
.client-subtitle {
  font-size: 14px;
  color: var(--text-muted);
  margin: 0 0 24px;
}
.client-meta {
  display: flex; flex-wrap: wrap; gap: 18px;
  padding: 14px 0;
  border-top: 1px solid var(--border);
  border-bottom: 1px solid var(--border);
  margin-bottom: 36px;
  font-size: 12px;
  color: var(--text-soft);
}
.client-meta .meta-item { display: flex; flex-direction: column; gap: 2px; }
.client-meta .meta-label { font-size: 10px; text-transform: uppercase; letter-spacing: 0.1em; color: var(--text-dim); }
.client-meta .meta-value { font-size: 13px; font-weight: 600; color: var(--text); }

.note-banner {
  border-left: 2px solid var(--warn);
  background: #fefbf3;
  padding: 10px 14px;
  margin: 8px 0 22px;
  font-size: 12.5px;
  color: var(--text-soft);
  border-radius: 0 4px 4px 0;
}
.note-banner.tiktok-launch { border-left-color: var(--info); background: #f5f8ff; }

.section-title {
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--text-muted);
  margin: 44px 0 14px;
  padding-bottom: 0;
  border: none;
}

/* KPI tables — minimal, no vertical borders */
.kpi-block { margin-bottom: 18px; }
.kpi-block-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--text);
  margin-bottom: 8px;
  display: flex; align-items: center; gap: 6px;
}
.kpi-block-title .info {
  display: inline-flex; align-items: center; justify-content: center;
  width: 16px; height: 16px;
  border-radius: 50%;
  background: var(--bg-muted);
  color: var(--text-muted);
  font-size: 10px;
  font-style: normal;
  cursor: help;
}
table.kpi {
  width: 100%; max-width: 720px;
  border-collapse: collapse;
  font-size: 14px;
}
table.kpi th, table.kpi td {
  padding: 10px 14px;
  border: none;
  border-bottom: 1px solid var(--border-soft);
}
table.kpi th {
  text-align: left;
  font-weight: 500;
  font-size: 11px;
  color: var(--text-dim);
  letter-spacing: 0.05em;
  text-transform: uppercase;
  padding-bottom: 8px;
}
table.kpi th:nth-child(2),
table.kpi th:nth-child(3) { text-align: right; }
table.kpi th:nth-child(4) { text-align: right; width: 90px; }
table.kpi td:first-child {
  font-weight: 500;
  color: var(--text);
  font-size: 13px;
}
table.kpi td:nth-child(2),
table.kpi td:nth-child(3) {
  text-align: right;
  font-variant-numeric: tabular-nums;
  font-size: 14px;
}
table.kpi td:nth-child(2) { font-weight: 600; color: var(--text); }
table.kpi td:nth-child(3) { color: var(--text-muted); }
table.kpi td:nth-child(4) {
  text-align: right;
  font-variant-numeric: tabular-nums;
  font-size: 13px;
  font-weight: 600;
}
table.kpi tr:last-child td { border-bottom: none; }
.delta-pos { color: var(--pos); }
.delta-neg { color: var(--neg); }
.delta-neutral, .delta-na { color: var(--text-dim); font-weight: 500; font-size: 12px; }
.delta-tk-launch { color: var(--info); font-style: italic; font-weight: 500; font-size: 12px; }

/* YTD / Tracking / Proposta — same minimal table */
table.flat {
  width: 100%; max-width: 720px;
  border-collapse: collapse;
  font-size: 14px;
}
table.flat th, table.flat td {
  padding: 9px 14px;
  border: none;
  border-bottom: 1px solid var(--border-soft);
}
table.flat th {
  font-weight: 500;
  font-size: 11px;
  color: var(--text-dim);
  letter-spacing: 0.05em;
  text-transform: uppercase;
  text-align: left;
}
table.flat th:nth-child(n+2),
table.flat td:nth-child(n+2) { text-align: right; font-variant-numeric: tabular-nums; }
table.flat td:first-child { font-weight: 500; color: var(--text-soft); }
table.flat tr.total td { border-top: 1px solid var(--border); border-bottom: none; font-weight: 700; color: var(--text); padding-top: 12px; }
table.flat tr:last-child td { border-bottom: none; }
table.flat td.sparkline-cell { padding-right: 0; padding-left: 8px; width: 80px; }
table.flat td.sparkline-cell svg { display: block; }

.status-line {
  font-weight: 600;
  font-size: 13px;
  padding: 10px 14px;
  border-radius: 6px;
  margin: 14px 0 4px;
  max-width: 720px;
}
.status-in-linea { background: #f0fdf4; color: var(--pos); border: 1px solid #bbf7d0; }
.status-under { background: #fffbeb; color: var(--warn); border: 1px solid #fde68a; }
.status-over { background: #fef2f2; color: var(--neg); border: 1px solid #fecaca; }
.status-neutral { background: var(--bg-muted); color: var(--text-muted); }

.rational {
  background: var(--bg-soft);
  border: 1px solid var(--border);
  padding: 20px 24px;
  margin-top: 18px;
  font-size: 14px;
  line-height: 1.65;
  border-radius: 8px;
  max-width: 720px;
  color: var(--text-soft);
}
.rational p { margin: 0 0 14px; }
.rational p:last-child { margin-bottom: 0; }
.rational p:first-child { color: var(--text); }

/* Budget Plan */
.budget-plan-intro { font-size: 13px; color: var(--text-muted); margin: 0 0 28px; max-width: 720px; line-height: 1.55; }
.budget-plan-client {
  margin-bottom: 28px;
  border: 1px solid var(--border);
  border-radius: 8px;
  overflow: hidden;
}
.budget-plan-client-header {
  background: var(--bg-soft);
  color: var(--text);
  padding: 12px 16px;
  font-weight: 700;
  font-size: 14px;
  letter-spacing: -0.005em;
  border-bottom: 1px solid var(--border);
}
.budget-plan-client-info {
  background: var(--bg-soft);
  padding: 10px 18px;
  font-size: 12px;
  color: var(--text-soft);
  border-bottom: 1px solid var(--border);
}
.budget-plan-warning {
  background: #fef2f2;
  padding: 10px 18px;
  font-size: 12px;
  color: var(--neg);
  font-weight: 600;
  border-bottom: 1px solid var(--border);
}
table.budget-plan-table { width: 100%; border-collapse: collapse; font-size: 13px; }
table.budget-plan-table th, table.budget-plan-table td {
  padding: 8px 14px;
  border-bottom: 1px solid var(--border-soft);
  text-align: left;
}
table.budget-plan-table th {
  background: var(--bg-soft);
  font-weight: 500;
  font-size: 10px;
  color: var(--text-dim);
  letter-spacing: 0.08em;
  text-transform: uppercase;
}
table.budget-plan-table th:nth-child(n+2),
table.budget-plan-table td:nth-child(n+2) { text-align: right; font-variant-numeric: tabular-nums; }
table.budget-plan-table td:first-child { font-weight: 500; color: var(--text); }
table.budget-plan-table tr.total td { background: var(--bg-soft); font-weight: 700; color: var(--text); border-bottom: none; }

/* Header toolbar */
.header-toolbar {
  display: flex; align-items: center; gap: 14px;
  padding: 0 0 22px;
  margin-bottom: 26px;
  border-bottom: 1px solid var(--border);
  font-size: 12px;
  color: var(--text-muted);
}
.header-toolbar .refreshed { margin-left: auto; font-style: normal; }
.header-toolbar .crumb { font-weight: 600; color: var(--text); font-size: 13px; }
.header-toolbar .sep { color: var(--text-dim); }

/* Sparkline SVG */
.spark { display: inline-block; vertical-align: middle; }
.spark path { fill: none; stroke: var(--text); stroke-width: 1.5; }
.spark path.area { fill: var(--text); fill-opacity: 0.06; stroke: none; }
.spark circle.last { fill: var(--text); }

/* Brand logos (inline SVG) */
.brand-logo {
  display: inline-block;
  vertical-align: -3px;
  margin-right: 7px;
  flex-shrink: 0;
}
.platform-cell { display: inline-flex; align-items: center; }
.section-title .brand-logo { margin-right: 4px; vertical-align: -2px; }

/* Mobile */
@media (max-width: 720px) {
  .app { grid-template-columns: 1fr; }
  .sidebar { position: relative; height: auto; padding: 18px 0; }
  .main { padding: 24px 18px 60px; }
  .client-title { font-size: 22px; }
  table.kpi, table.flat { font-size: 13px; }
  table.kpi th, table.kpi td, table.flat th, table.flat td { padding: 8px 10px; }
  .client-meta { flex-direction: column; gap: 12px; }
}
</style>
</head>
<body>
<div class="app">
  <aside class="sidebar">
    <div class="brand">Report AGHC</div>
    <div class="period-current">__PERIOD_LABEL__</div>
    <a class="archive-link" href="index.html"><span class="arrow-back">←</span> Archivio storico</a>
    <div class="nav-section">Overview</div>
    <div id="nav-overview"></div>
    <div class="nav-section">18 Clienti</div>
    <div id="nav-clients"></div>
  </aside>
  <main class="main" id="main"></main>
</div>
<script>
const REPORT_YEAR = __YEAR__;
const REPORT_MONTH = __MONTH__;
const GENERATED_AT = "__GENERATED_AT__";
const DATA = __DATA_JSON__;
const CLIENTS = __CLIENTS_JSON__;
const MONTH_IT = __MONTH_IT_JSON__;

const BUDGET_WEIGHTS = {1:3,2:3,3:5,4:10,5:15,6:15,7:12,8:12,9:5,10:5,11:5,12:10};
const META_SHARE = 0.80;
const TIKTOK_SHARE = 0.20;
const TIKTOK_MIN_MONTHLY = 600;

// === LOGHI UFFICIALI delle piattaforme (SVG inline, self-contained) ===
const LOGO_IG = `<svg class="brand-logo" viewBox="0 0 24 24" width="14" height="14" xmlns="http://www.w3.org/2000/svg" aria-label="Instagram"><defs><linearGradient id="igG" x1="0%" y1="100%" x2="100%" y2="0%"><stop offset="0%" stop-color="#FED576"/><stop offset="26%" stop-color="#F47133"/><stop offset="61%" stop-color="#BC3081"/><stop offset="100%" stop-color="#4C63D2"/></linearGradient></defs><rect x="2" y="2" width="20" height="20" rx="5.5" ry="5.5" fill="url(#igG)"/><path d="M12 7.4a4.6 4.6 0 1 0 0 9.2 4.6 4.6 0 0 0 0-9.2zm0 7.6a3 3 0 1 1 0-6 3 3 0 0 1 0 6zm5.8-7.85a1.1 1.1 0 1 1-2.2 0 1.1 1.1 0 0 1 2.2 0z" fill="#fff"/></svg>`;
const LOGO_FB = `<svg class="brand-logo" viewBox="0 0 24 24" width="14" height="14" xmlns="http://www.w3.org/2000/svg" aria-label="Facebook"><path d="M24 12.073C24 5.405 18.627 0 12 0S0 5.405 0 12.073C0 18.1 4.388 23.094 10.125 24v-8.437H7.078v-3.49h3.047V9.41c0-3.007 1.792-4.668 4.533-4.668 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.927-1.956 1.876v2.25h3.328l-.532 3.49h-2.796V24C19.612 23.094 24 18.1 24 12.073z" fill="#1877F2"/></svg>`;
const LOGO_TK = `<svg class="brand-logo" viewBox="0 0 24 24" width="14" height="14" xmlns="http://www.w3.org/2000/svg" aria-label="TikTok"><path d="M19.59 6.69a4.83 4.83 0 0 1-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 0 1-5.2 1.74 2.89 2.89 0 0 1 2.31-4.64 2.93 2.93 0 0 1 .88.13V9.4a6.84 6.84 0 0 0-1-.05A6.33 6.33 0 0 0 5.6 20.1a6.34 6.34 0 0 0 10.86-4.43V8.61a8.16 8.16 0 0 0 4.77 1.52v-3.4a4.85 4.85 0 0 1-1.64-.04Z" fill="#010101"/></svg>`;
const LOGO_META = `<svg class="brand-logo" viewBox="0 0 24 24" width="14" height="14" xmlns="http://www.w3.org/2000/svg" aria-label="Meta"><path d="M6.915 4.03c-1.968 0-3.683 1.28-4.871 3.113C.704 9.45 0 12.32 0 14.292c0 2.587 1.135 3.886 2.726 3.886 1.93 0 3.317-.927 5.812-5.227l1.183-2.083c.484-.847.992-1.798 1.535-2.811-.85-1.31-1.668-2.305-2.494-2.957-.873-.69-1.747-1.07-2.847-1.07zm10.328 1.215c-1.122 0-2.084.45-3.057 1.43-.967.974-1.916 2.358-2.926 4.045L9.85 13.42c-2.117 3.532-2.733 4.31-3.66 4.31-.85 0-1.342-.687-1.342-1.892 0-2.297.793-4.93 1.96-6.823.94-1.53 2.165-2.288 3.387-2.288 1.024 0 1.873.452 2.834 1.292.875.764 1.668 1.825 2.461 2.96.853-1.184 1.665-2.27 2.518-3.011.847-.737 1.65-1.06 2.467-1.06 1.272 0 2.244.79 2.84 1.964.611 1.207.95 2.84.95 4.466 0 1.42-.265 2.418-.694 3.117-.405.658-.998 1.014-1.673 1.014-.65 0-1.05-.176-1.516-.616-.488-.46-.94-1.16-1.488-2.198l-.847-1.602c-.43-.812-.79-1.504-1.115-2.122-1.18.943-2.122 1.78-2.881 2.413-.83.692-1.466 1.144-2.06 1.144-1.245 0-2.222-.97-2.222-3.205 0-2.073.764-4.516 2.013-6.535.964-1.557 2.18-2.39 3.367-2.39z" fill="#0866FF"/></svg>`;

function monthName(m){ return MONTH_IT[String(m)] || MONTH_IT[m]; }
function capitalize(s){ return s ? s.charAt(0).toUpperCase()+s.slice(1) : s; }
function fmtInt(x){ if(x===null||x===undefined) return "n/d"; return Math.round(x).toLocaleString("it-IT"); }
function fmtEur(x){ if(x===null||x===undefined) return "n/d"; return x.toLocaleString("it-IT",{style:"currency",currency:"EUR",minimumFractionDigits:2,maximumFractionDigits:2}); }
function pct(c,p){ if(p===null||p===undefined||p===0||c===null||c===undefined) return null; return (c-p)/p*100; }
function fmtPct(p){ if(p===null) return "n/d"; const s=p>0?"+":""; return `${s}${p.toFixed(2)}%`; }
function pctClass(p){ if(p===null) return "delta-na"; return p>=0?"delta-pos":"delta-neg"; }
function fmtDelta(p, override){
  if(override) return `<span class="${override.cls}">${override.text}</span>`;
  if(p===null) return `<span class="delta-na">n/d</span>`;
  const arrow = p>=0 ? "↗" : "↘";
  return `<span class="${pctClass(p)}">${arrow} ${fmtPct(p)}</span>`;
}
function comparisonPeriod(y,m,t){ if(t==="YoY") return {y:y-1,m}; if(m===1) return {y:y-1,m:12}; return {y,m:m-1}; }

function emptyMeta(){ return {reach:0,impressions:0,actions_page_engagement:0,clicks:0,spend:0}; }
function emptyTk(){ return {reach:0,impressions:0,engagements:0,clicks:0,spend:0}; }

// SVG sparkline: input array values, returns inline <svg>
function sparkline(values, opts){
  opts = opts || {};
  const w = opts.w || 80, h = opts.h || 22, pad = 2;
  if(!values || values.length === 0 || values.every(v => !v)) return "";
  const min = Math.min(...values), max = Math.max(...values);
  const range = (max - min) || 1;
  const stepX = (w - pad*2) / Math.max(1, values.length - 1);
  const pts = values.map((v,i) => {
    const x = pad + i * stepX;
    const y = h - pad - ((v - min) / range) * (h - pad*2);
    return [x, y];
  });
  const linePath = pts.map((p,i) => (i===0?"M":"L")+p[0].toFixed(1)+","+p[1].toFixed(1)).join(" ");
  const areaPath = linePath + ` L${pts[pts.length-1][0].toFixed(1)},${h-pad} L${pts[0][0].toFixed(1)},${h-pad} Z`;
  const last = pts[pts.length-1];
  return `<svg class="spark" width="${w}" height="${h}" viewBox="0 0 ${w} ${h}" xmlns="http://www.w3.org/2000/svg">
    <path class="area" d="${areaPath}"/>
    <path d="${linePath}"/>
    <circle class="last" cx="${last[0].toFixed(1)}" cy="${last[1].toFixed(1)}" r="2"/>
  </svg>`;
}

function buildClientData(client){
  const compMeta = comparisonPeriod(REPORT_YEAR, REPORT_MONTH, client.cm);
  const periodA = `${capitalize(monthName(REPORT_MONTH))} ${REPORT_YEAR}`;
  const periodBMeta = `${capitalize(monthName(compMeta.m))} ${compMeta.y}`;
  let metaCur, metaPrev;
  if(client.filter){
    const f = DATA.meta_filtered?.[client.nome] || {};
    metaCur = f.current || {facebook:emptyMeta(),instagram:emptyMeta()};
    metaPrev = (client.cm==="YoY") ? (f.prev_yoy || {facebook:emptyMeta(),instagram:emptyMeta()}) : (f.prev_mom || {facebook:emptyMeta(),instagram:emptyMeta()});
  } else {
    metaCur = DATA.meta_by_account.current[client.meta_id] || {facebook:emptyMeta(),instagram:emptyMeta()};
    metaPrev = (client.cm==="YoY")
      ? (DATA.meta_by_account.prev_yoy[client.meta_id] || {facebook:emptyMeta(),instagram:emptyMeta()})
      : (DATA.meta_by_account.prev_mom[client.meta_id] || {facebook:emptyMeta(),instagram:emptyMeta()});
  }
  const estimatedList = DATA.reach_estimated_clients || [];
  const reachEstimated = estimatedList.includes(client.nome);

  let tkCur=null, tkPrev=null, tkPeriodB=null, tkLaunched=false;
  const hasTk = !!client.tk_id;
  if(hasTk){
    tkCur = DATA.tiktok.current[client.tk_id] || emptyTk();
    const compTk = comparisonPeriod(REPORT_YEAR, REPORT_MONTH, client.ct);
    tkPeriodB = `${capitalize(monthName(compTk.m))} ${compTk.y}`;
    tkPrev = (client.ct==="YoY") ? (DATA.tiktok.prev_yoy?.[client.tk_id] || emptyTk()) : (DATA.tiktok.prev_mom?.[client.tk_id] || emptyTk());
    if((tkCur.spend||0)>0 && (tkPrev.spend||0)===0 && (tkPrev.impressions||0)===0){ tkLaunched = true; }
  }

  const ytdRoot = DATA.ytd_spend || {by_client: {}, months: []};
  const ytdMonths = ytdRoot.months && ytdRoot.months.length ? ytdRoot.months : (function(){ const a=[]; for(let m=1;m<=REPORT_MONTH;m++) a.push(m); return a; })();
  const cYtd = ytdRoot.by_client?.[client.nome] || {};

  return { client, periodA, periodBMeta, hasTk, tkPeriodB, metaCur, metaPrev, tkCur, tkPrev, reachEstimated, tkLaunched, ytdMonths, ytdSpend: cYtd };
}

// Articolo italiano corretto prima di un numero in % ("il 81%" → "l'81%")
function artPct(n){
  const v = Math.abs(Math.round(n));
  if(v===1 || v===8 || v===11 || (v>=80 && v<=89)) return `l'${v}%`;
  return `il ${v}%`;
}
function delPct(n){
  const v = Math.abs(Math.round(n));
  if(v===1 || v===8 || v===11 || (v>=80 && v<=89)) return `dell'${v}%`;
  return `del ${v}%`;
}

// Cross-channel insight: se p1 ha raccontato un canale, restituisce una frase sull'altro
function crossChannelInsight(kind, fbReach, fbReachDelta, igReach, igReachDelta){
  const isFbLead = kind === "fb_explode" || kind === "fb_modest";
  const isIgLead = kind === "ig_explode" || kind === "ig_modest";
  if(isFbLead && igReach >= 5000){
    if(igReachDelta !== null && igReachDelta < -25){
      return ` Instagram resta presidiato in modo mirato (${fmtInt(igReach)} utenti unici raggiunti), con il budget concentrato su Facebook dove sta rendendo di più nel mese.`;
    }
    if(igReachDelta !== null && igReachDelta > 20){
      return ` Instagram aggiunge in parallelo ${fmtInt(igReach)} utenti unici raggiunti (+${igReachDelta.toFixed(0)}%), confermando una presenza qualificata sul pubblico mobile-first.`;
    }
    return ` Instagram mantiene un presidio complementare di ${fmtInt(igReach)} utenti unici, a copertura di un pubblico differenziato per età e abitudini di consumo.`;
  }
  if(isIgLead && fbReach >= 5000){
    if(fbReachDelta !== null && fbReachDelta < -25){
      return ` Facebook resta presidiato in modo mirato (${fmtInt(fbReach)} utenti unici raggiunti), con il budget concentrato su Instagram dove sta rendendo di più nel mese.`;
    }
    if(fbReachDelta !== null && fbReachDelta > 20){
      return ` Facebook aggiunge in parallelo ${fmtInt(fbReach)} utenti unici raggiunti (+${fbReachDelta.toFixed(0)}%), a conferma di una presenza multicanale coerente.`;
    }
    return ` Facebook mantiene un presidio complementare di ${fmtInt(fbReach)} utenti unici, garantendo copertura sul pubblico più ampio della piattaforma.`;
  }
  return "";
}

function buildRational(cd){
  const { client, metaCur, metaPrev, tkCur, hasTk, tkLaunched } = cd;
  const m = REPORT_MONTH;
  const monthLow = monthName(m);
  const monthCap = capitalize(monthLow);
  const nextM = (m % 12) + 1;
  const nextMonthLow = monthName(nextM);
  const nextMonthCap = capitalize(nextMonthLow);
  const nextWeight = BUDGET_WEIGHTS[nextM];

  // === Segnali aggregati ===
  const fbReachCur = metaCur.facebook.reach || 0;
  const fbReachPrev = metaPrev.facebook.reach || 0;
  const fbReachDelta = pct(fbReachCur, fbReachPrev);
  const igReachCur = metaCur.instagram.reach || 0;
  const igReachPrev = metaPrev.instagram.reach || 0;
  const igReachDelta = pct(igReachCur, igReachPrev);
  const reachCurMeta = fbReachCur + igReachCur;
  const reachPrevMeta = fbReachPrev + igReachPrev;
  const reachMetaDelta = pct(reachCurMeta, reachPrevMeta);

  const fbEngCur = metaCur.facebook.actions_page_engagement || 0;
  const fbEngPrev = metaPrev.facebook.actions_page_engagement || 0;
  const fbEngDelta = pct(fbEngCur, fbEngPrev);
  const igEngCur = metaCur.instagram.actions_page_engagement || 0;
  const igEngPrev = metaPrev.instagram.actions_page_engagement || 0;
  const igEngDelta = pct(igEngCur, igEngPrev);
  const totEng = fbEngCur + igEngCur;

  const spendCur = (metaCur.facebook.spend || 0) + (metaCur.instagram.spend || 0);
  const spendPrev = (metaPrev.facebook.spend || 0) + (metaPrev.instagram.spend || 0);
  const spendDelta = pct(spendCur, spendPrev);

  // === Caso speciale: account a zero per scelta strategica ===
  if (spendCur === 0 && reachCurMeta === 0) {
    const p1 = `${monthCap} rappresenta una pausa strategica per ${client.nome}, coerente con il calendario annuo del piano media.`;
    const p2 = `Il budget residuo resta integro e pronto a concentrarsi sulle finestre stagionali a più alto ritorno previste nei mesi successivi.`;
    const p3 = `Da ${nextMonthLow} (peso ${nextWeight}% del piano annuo) il presidio riprende ${nextWeight >= 12 ? "nel cuore della stagione, con la pressione necessaria a intercettare la domanda attiva di prenotazione" : "in modo progressivo, pronto a salire sulle finestre più strategiche"}.`;
    return `<p>${p1}</p><p>${p2}</p><p>${p3}</p>`;
  }

  // === Paragrafo 1: cos'è successo (lead con la storia più forte) ===
  let p1, p1Kind;
  if (tkLaunched && tkCur && (tkCur.impressions || 0) > 0) {
    p1 = `${monthCap} inaugura una nuova fase per ${client.nome}: la prima campagna TikTok va live e debutta con ${fmtInt(tkCur.impressions)} visualizzazioni e ${fmtInt(tkCur.reach)} utenti unici raggiunti, aprendo un canale fino a ieri inesplorato dal brand.`;
    p1Kind = "tk_launch";
  } else if (fbReachDelta !== null && fbReachDelta > 100 && (reachMetaDelta === null || reachMetaDelta > 0)) {
    const mul = (1 + fbReachDelta / 100).toFixed(1).replace('.', ',');
    p1 = `${monthCap} segna un cambio di passo per ${client.nome}: Facebook diventa il canale di traino e amplia la copertura di ${mul} volte rispetto al periodo di confronto, raggiungendo ${fmtInt(fbReachCur)} utenti unici.`;
    p1Kind = "fb_explode";
  } else if (igReachDelta !== null && igReachDelta > 80 && igReachCur > 50000) {
    const mul = (1 + igReachDelta / 100).toFixed(1).replace('.', ',');
    p1 = `${monthCap} è il mese di Instagram per ${client.nome}: la copertura cresce di ${mul} volte, portando il messaggio del brand davanti a ${fmtInt(igReachCur)} utenti unici sul canale.`;
    p1Kind = "ig_explode";
  } else if (reachMetaDelta !== null && reachMetaDelta > 30) {
    p1 = `${monthCap} è il mese in cui la copertura Meta cresce in modo netto: il brand entra nello sguardo di ${fmtInt(reachCurMeta)} persone (+${reachMetaDelta.toFixed(0)}% rispetto al periodo di confronto).`;
    p1Kind = "reach_big";
  } else if (spendDelta !== null && spendDelta < -8 && reachMetaDelta !== null && reachMetaDelta > -8) {
    p1 = `${monthCap} è il mese dell'efficienza per ${client.nome}: la copertura Meta resta solida con ${fmtInt(reachCurMeta)} utenti unici raggiunti, con un investimento ridotto ${delPct(spendDelta)}. Ogni euro speso ha lavorato meglio.`;
    p1Kind = "efficiency";
  } else if (fbReachDelta !== null && fbReachDelta > 30) {
    p1 = `${monthCap} consolida la presenza di ${client.nome} su Facebook: ${fmtInt(fbReachCur)} utenti unici raggiunti, +${fbReachDelta.toFixed(0)}% rispetto al periodo di confronto.`;
    p1Kind = "fb_modest";
  } else if (igReachDelta !== null && igReachDelta > 30) {
    p1 = `${monthCap} rafforza la presenza di ${client.nome} su Instagram: ${fmtInt(igReachCur)} utenti unici raggiunti, +${igReachDelta.toFixed(0)}% rispetto al periodo di confronto.`;
    p1Kind = "ig_modest";
  } else if (hasTk && tkCur && (tkCur.impressions || 0) > 100000) {
    p1 = `${monthCap} vede ${client.nome} attivo su entrambi i canali: Meta porta il brand davanti a ${fmtInt(reachCurMeta)} utenti unici, TikTok aggiunge ${fmtInt(tkCur.impressions)} visualizzazioni a presidio del pubblico più giovane.`;
    p1Kind = "tk_present";
  } else {
    p1 = `${monthCap} mantiene il presidio di ${client.nome} su base solida: ${fmtInt(reachCurMeta)} utenti unici raggiunti su Meta, in linea con il posizionamento strategico del mese all'interno del piano annuo.`;
    p1Kind = "neutral";
  }

  // === Paragrafo 2: perché conta (evita di ripetere lo spend delta se p1 lo ha già menzionato) ===
  const spendMentionedInP1 = (p1Kind === "efficiency");
  let p2;
  const p2Lines = [];
  if (fbEngDelta !== null && fbEngDelta > 100 && fbEngCur > 5000) {
    p2Lines.push(`le interazioni sui contenuti Facebook salgono a ${fmtInt(fbEngCur)}, una scala completamente diversa rispetto al periodo di confronto`);
  } else if (igEngDelta !== null && igEngDelta > 40 && igEngCur > 2000) {
    p2Lines.push(`le interazioni Instagram crescono ${delPct(igEngDelta)} e portano il coinvolgimento totale a ${fmtInt(igEngCur)} azioni nel mese`);
  } else if (totEng > 50000) {
    p2Lines.push(`il pubblico interagisce attivamente con i contenuti del brand, con ${fmtInt(totEng)} interazioni totali generate nel mese`);
  }
  if (hasTk && !tkLaunched && tkCur && (tkCur.impressions || 0) > 100000) {
    p2Lines.push(`TikTok continua a presidiare con efficienza il pubblico più giovane (${fmtInt(tkCur.impressions)} visualizzazioni)`);
  }

  if (p2Lines.length > 0) {
    const sent = p2Lines.slice(0, 2).join("; ");
    p2 = sent.charAt(0).toUpperCase() + sent.slice(1) + ".";
    if (!spendMentionedInP1) {
      if (spendDelta !== null && spendDelta < -8) {
        p2 += ` Risultati ottenuti con ${artPct(spendDelta)} di investimento in meno rispetto al periodo di confronto.`;
      } else if (spendDelta !== null && spendDelta > 12) {
        p2 += ` Per sostenere questa traiettoria, l'investimento del mese cresce ${delPct(spendDelta)}.`;
      }
    }
  } else if (spendDelta !== null && spendDelta < -8 && !spendMentionedInP1) {
    p2 = `Il dato chiave del mese è l'efficienza: la copertura resta in linea con il periodo di confronto, ma con ${artPct(spendDelta)} di budget in meno. È il segnale di una strategia di targeting che continua a lavorare bene.`;
  } else if (spendDelta !== null && spendDelta > 12) {
    p2 = `L'investimento del mese sale ${delPct(spendDelta)} per consolidare il momentum, coerente con il peso di ${BUDGET_WEIGHTS[m]}% che il piano annuo riserva a ${monthLow}.`;
  } else if (totEng > 0) {
    p2 = `Il presidio del marchio si mantiene attivo con ${fmtInt(totEng)} interazioni totali su Meta: i contenuti pubblicati continuano a generare conversazioni qualificate intorno a ${client.nome}.`;
  } else {
    p2 = `Il piano del mese resta coerente con la stagionalità: presidio costante a tutela della brand awareness, in attesa delle finestre più strategiche dei mesi successivi.`;
  }

  // Cross-channel insight: aggiunge una frase sull'altro canale se p1 era mono-canale
  p2 += crossChannelInsight(p1Kind, fbReachCur, fbReachDelta, igReachCur, igReachDelta);

  // === Paragrafo 3: cosa stiamo facendo dopo ===
  let p3;
  if (tkLaunched) {
    p3 = `Da ${nextMonthLow} ${client.nome} opera su due leve complementari — Meta per la conversione, TikTok per la scoperta. ${nextMonthCap} pesa il ${nextWeight}% del piano annuo, una finestra ${nextWeight >= 12 ? "centrale per costruire la pressione stagionale" : "utile a consolidare il sistema appena avviato"}.`;
  } else if (hasTk) {
    p3 = `A ${nextMonthLow} (peso ${nextWeight}% del piano annuo) confermiamo il sistema a due velocità: Meta presidia la fase di considerazione e prenotazione, TikTok amplia la scoperta del brand sul pubblico più giovane.`;
  } else if (nextWeight >= 12) {
    p3 = `${nextMonthCap} entra nel cuore della stagione (${nextWeight}% del budget annuo): saliamo sulla pressione per intercettare la domanda attiva nella finestra prenotativa più calda dell'anno.`;
  } else if (nextWeight >= 10) {
    p3 = `A ${nextMonthLow} (${nextWeight}% del piano annuo) la pressione cresce in modo strutturato: prepariamo il pubblico alle finestre di alta stagione che arrivano subito dopo.`;
  } else {
    p3 = `A ${nextMonthLow} (peso ${nextWeight}% del piano annuo) il presidio prosegue strategico, mantenendo il pubblico caldo in vista delle finestre più rilevanti del piano.`;
  }

  return `<p>${p1}</p><p>${p2}</p><p>${p3}</p>`;
}

function kpiBlock(title, periodA, periodB, rows, fmt, withInfoIcon){
  const info = withInfoIcon ? `<span class="info" title="Reach periodo precedente STIMATA — la Meta Marketing API non restituisce più reach per periodi oltre 24 mesi; valore calcolato applicando il rapporto reach/impressions del periodo corrente.">i</span>` : "";
  let h = `<div class="kpi-block"><div class="kpi-block-title">${title}${info}</div><table class="kpi"><thead><tr><th></th><th>${periodA}</th><th>${periodB}</th><th>Δ</th></tr></thead><tbody>`;
  for(const [label, cur, prev, override] of rows){
    const p = pct(cur, prev);
    h += `<tr><td>${label}</td><td>${fmt(cur)}</td><td>${fmt(prev)}</td><td>${fmtDelta(p, override)}</td></tr>`;
  }
  return h + `</tbody></table></div>`;
}

function renderClient(cd){
  const { client, periodA, periodBMeta, tkPeriodB, hasTk, metaCur, metaPrev, tkCur, tkPrev, reachEstimated, tkLaunched, ytdMonths, ytdSpend } = cd;
  let h = `<h1 class="client-title">${client.nome}</h1>
    <p class="client-subtitle">${periodA} <span style="color:var(--text-dim)">vs</span> ${periodBMeta}</p>
    <div class="client-meta">
      <div class="meta-item"><div class="meta-label">Budget annuo</div><div class="meta-value">${fmtEur(client.budget)}</div></div>
      <div class="meta-item"><div class="meta-label">Confronto Meta</div><div class="meta-value">${client.cm}</div></div>
      <div class="meta-item"><div class="meta-label">TikTok</div><div class="meta-value">${hasTk?"Attivo":"—"}</div></div>
      ${client.ct?`<div class="meta-item"><div class="meta-label">Confronto TikTok</div><div class="meta-value">${client.ct}</div></div>`:""}
    </div>`;
  if(client.note) h += `<div class="note-banner">${client.note}</div>`;

  h += `<div class="section-title">${LOGO_META}Meta</div>`;
  for(const [title, field] of [["Account Raggiunti","reach"],["Visualizzazioni","impressions"],["Interazioni","actions_page_engagement"],["Clicks","clicks"]]){
    const wi = (field==="reach") && reachEstimated;
    h += kpiBlock(title, periodA, periodBMeta, [
      [`${LOGO_IG}<span>Instagram</span>`, metaCur.instagram[field], metaPrev.instagram[field]],
      [`${LOGO_FB}<span>Facebook</span>`,  metaCur.facebook[field],  metaPrev.facebook[field]],
    ], fmtInt, wi);
  }
  const spCur = (metaCur.facebook.spend||0)+(metaCur.instagram.spend||0);
  const spPrev = (metaPrev.facebook.spend||0)+(metaPrev.instagram.spend||0);
  h += kpiBlock("Budget Meta", periodA, periodBMeta, [["Totale", spCur, spPrev]], fmtEur, false);

  if(hasTk){
    h += `<div class="section-title">${LOGO_TK}TikTok</div>`;
    if(tkLaunched) h += `<div class="note-banner tiktok-launch">TikTok attivato ad ${capitalize(monthName(REPORT_MONTH))} ${REPORT_YEAR} — primo mese live, confronto MoM non disponibile</div>`;
    const ovr = tkLaunched ? {text:"1° mese live", cls:"delta-tk-launch"} : null;
    for(const [t,f] of [["Account Raggiunti","reach"],["Visualizzazioni","impressions"],["Interazioni","engagements"],["Clicks","clicks"]]){
      h += kpiBlock(t, periodA, tkPeriodB, [[`${LOGO_TK}<span>TikTok</span>`, tkCur[f], tkPrev[f], ovr]], fmtInt, false);
    }
    h += kpiBlock("Budget TikTok", periodA, tkPeriodB, [[`${LOGO_TK}<span>TikTok</span>`, tkCur.spend, tkPrev.spend, ovr]], fmtEur, false);
  }

  const tkSpend = hasTk?(tkCur.spend||0):0;
  const totMonth = spCur + tkSpend;
  h += `<div class="section-title">Spesa Mensile</div><table class="flat"><thead><tr><th>Canale</th><th>Speso ${periodA}</th></tr></thead><tbody>
    <tr><td>${LOGO_META}<span>Meta</span></td><td>${fmtEur(spCur)}</td></tr>
    ${hasTk?`<tr><td>${LOGO_TK}<span>TikTok</span></td><td>${fmtEur(tkSpend)}</td></tr>`:""}
    <tr class="total"><td>Totale</td><td>${fmtEur(totMonth)}</td></tr></tbody></table>`;

  // YTD con sparkline accanto al totale di riga
  h += `<div class="section-title">Riepilogo Spesa YTD</div>`;
  let ytdMeta=0, ytdTk=0;
  const monthlyTotals = [];
  h += `<table class="flat"><thead><tr><th>Mese</th><th>${LOGO_META}Meta</th><th>${LOGO_TK}TikTok</th><th>Totale</th><th></th></tr></thead><tbody>`;
  for(const m of ytdMonths){
    const md = ytdSpend[String(m)] || {meta:0,tiktok:0};
    ytdMeta += (md.meta||0); ytdTk += (md.tiktok||0);
    const rowTot = (md.meta||0)+(md.tiktok||0);
    monthlyTotals.push(rowTot);
    h += `<tr><td>${capitalize(monthName(m))}</td><td>${fmtEur(md.meta||0)}</td><td>${hasTk?fmtEur(md.tiktok||0):"—"}</td><td>${fmtEur(rowTot)}</td><td></td></tr>`;
  }
  const ytdTot = ytdMeta+ytdTk;
  const sparkSvg = sparkline(monthlyTotals, {w:90, h:22});
  h += `<tr class="total"><td>YTD</td><td>${fmtEur(ytdMeta)}</td><td>${hasTk?fmtEur(ytdTk):"—"}</td><td>${fmtEur(ytdTot)}</td><td class="sparkline-cell">${sparkSvg}</td></tr></tbody></table>`;

  // Budget Tracking
  const cumW = ytdMonths.reduce((s,m)=>s+BUDGET_WEIGHTS[m],0);
  const atteso = client.budget * cumW / 100;
  const scarto = ytdTot - atteso;
  const rim = client.budget - ytdTot;
  const tol = atteso * 0.10;
  let st, sc;
  if(atteso===0){ st="Piano non ancora partito"; sc="status-neutral"; }
  else if(Math.abs(scarto)<=tol){ st="In linea col piano"; sc="status-in-linea"; }
  else if(scarto<0){ st=`Under spending di ${fmtEur(Math.abs(scarto))}`; sc="status-under"; }
  else { st=`Over spending di ${fmtEur(Math.abs(scarto))}`; sc="status-over"; }
  h += `<div class="section-title">Budget Tracking Annuo</div>
    <table class="flat"><tbody>
      <tr><td>Budget annuo</td><td>${fmtEur(client.budget)}</td></tr>
      <tr><td>Peso cumulato piano (Gen–${capitalize(monthName(REPORT_MONTH))})</td><td>${cumW}%</td></tr>
      <tr><td>Atteso YTD</td><td>${fmtEur(atteso)}</td></tr>
      <tr><td>Speso YTD</td><td>${fmtEur(ytdTot)}</td></tr>
      <tr><td>Scarto vs piano</td><td>${scarto>=0?"+":"−"}${fmtEur(Math.abs(scarto))}</td></tr>
      <tr><td>Budget rimanente anno</td><td>${fmtEur(rim)}</td></tr>
    </tbody></table>
    <div class="status-line ${sc}">${st}</div>`;

  // Proposta investimento
  const nm = (REPORT_MONTH%12)+1;
  const ny = REPORT_MONTH===12 ? REPORT_YEAR+1 : REPORT_YEAR;
  const nw = BUDGET_WEIGHTS[nm];
  const baseNext = client.budget * nw / 100;
  let metaN, tkN=0, tkNote=null;
  if(hasTk){ metaN = baseNext * META_SHARE; const tkB = baseNext * TIKTOK_SHARE; tkN = Math.max(TIKTOK_MIN_MONTHLY, tkB); tkNote = (tkN===TIKTOK_MIN_MONTHLY && tkB<TIKTOK_MIN_MONTHLY) ? "Min €600/mese" : `Split ${Math.round(TIKTOK_SHARE*100)}%`; }
  else metaN = baseNext;
  const totN = metaN + tkN;
  h += `<div class="section-title">Proposta Investimento ${capitalize(monthName(nm))} ${ny}</div>
    <table class="flat"><thead><tr><th>Canale</th><th>Investimento Suggerito</th><th>Note</th></tr></thead><tbody>
      <tr><td>${LOGO_META}<span>Meta</span></td><td>${fmtEur(metaN)}</td><td style="color:var(--text-muted);font-size:12px">${hasTk?`Split ${Math.round(META_SHARE*100)}%`:"100% budget mensile"}</td></tr>
      ${hasTk?`<tr><td>${LOGO_TK}<span>TikTok</span></td><td>${fmtEur(tkN)}</td><td style="color:var(--text-muted);font-size:12px">${tkNote}</td></tr>`:""}
      <tr class="total"><td>Totale</td><td>${fmtEur(totN)}</td><td style="color:var(--text-muted);font-size:12px">Peso piano ${nw}%</td></tr>
    </tbody></table>`;

  h += `<div class="section-title">Rational</div><div class="rational">${buildRational(cd)}</div>`;
  return h;
}

function renderBudgetPlan(allCD){
  const rem = []; for(let m=REPORT_MONTH+1;m<=12;m++) rem.push(m);
  if(rem.length===0) return `<h1 class="client-title">Piano Budget Residuo</h1><div class="note-banner">Anno concluso — nessun mese residuo.</div>`;
  const tw = rem.reduce((s,m)=>s+BUDGET_WEIGHTS[m],0);
  let h = `<h1 class="client-title">Piano Budget Residuo</h1>
    <p class="client-subtitle">Da ${capitalize(monthName(rem[0]))} a Dicembre ${REPORT_YEAR}</p>
    <p class="budget-plan-intro">Ricalibrazione dei budget sui pesi mensili AGHC — pesi originali rinormalizzati sul totale residuo ${tw}%. Split 80% Meta / 20% TikTok con soglia minima €${TIKTOK_MIN_MONTHLY}/mese TikTok.</p>`;
  for(const cd of allCD){
    const c = cd.client, hasTk = cd.hasTk;
    let ytdTot = 0; for(const m of cd.ytdMonths){ const md=cd.ytdSpend[String(m)]||{}; ytdTot+=(md.meta||0)+(md.tiktok||0); }
    const res = c.budget - ytdTot, num = rem.length;
    let warn=null, metaRes;
    if(hasTk){ const tf=TIKTOK_MIN_MONTHLY*num; const mr=res-tf; if(mr<0){ warn=`Residuo ${fmtEur(res)} < min TikTok totale (${fmtEur(tf)}). TikTok manterrà €${TIKTOK_MIN_MONTHLY}/mese fissi, Meta = €0.`; metaRes=0;} else metaRes=mr; } else metaRes=res;
    h += `<div class="budget-plan-client"><div class="budget-plan-client-header">${c.nome}</div>
      <div class="budget-plan-client-info">Budget annuo: <strong>${fmtEur(c.budget)}</strong> · Speso YTD: <strong>${fmtEur(ytdTot)}</strong> · Residuo: <strong>${fmtEur(res)}</strong>${hasTk?` · TikTok attivo (min €${TIKTOK_MIN_MONTHLY}/mese)`:""}</div>`;
    if(warn) h += `<div class="budget-plan-warning">${warn}</div>`;
    h += `<table class="budget-plan-table"><thead><tr><th>Mese</th><th>Peso piano</th><th>Peso rical.</th><th>Totale mese</th><th>${LOGO_META}Meta</th><th>${LOGO_TK}TikTok</th><th>Note</th></tr></thead><tbody>`;
    let sT=0,sM=0,sK=0;
    for(const m of rem){
      const pw=BUDGET_WEIGHTS[m], pr=tw?pw/tw*100:0;
      let mm,kk,note;
      if(hasTk){ mm=metaRes>0?metaRes*pw/tw:0; kk=TIKTOK_MIN_MONTHLY; note="TikTok fisso · Meta pro-peso"; }
      else { mm=res>0?res*pw/tw:0; kk=0; note="100% Meta"; }
      const t=mm+kk; sT+=t; sM+=mm; sK+=kk;
      h += `<tr><td>${capitalize(monthName(m))}</td><td>${pw}%</td><td>${pr.toFixed(1)}%</td><td>${fmtEur(t)}</td><td>${fmtEur(mm)}</td><td>${hasTk?fmtEur(kk):"—"}</td><td style="color:var(--text-muted);font-size:11px">${note}</td></tr>`;
    }
    h += `<tr class="total"><td>Totale</td><td>${tw}%</td><td>100.0%</td><td>${fmtEur(sT)}</td><td>${fmtEur(sM)}</td><td>${hasTk?fmtEur(sK):"—"}</td><td></td></tr></tbody></table></div>`;
  }
  return h;
}

const STATE = { active: "_overview", allCD: CLIENTS.map(c => buildClientData(c)) };

function setActive(key){ STATE.active = key; document.querySelectorAll(".nav-item").forEach(n=>n.classList.toggle("active", n.dataset.key===key)); render(); }

function render(){
  const main = document.getElementById("main");
  const refreshed = new Date(GENERATED_AT.replace(" UTC"," GMT")).toLocaleString("it-IT",{day:"2-digit",month:"short",year:"numeric"});
  let h = `<div class="header-toolbar">
    <span class="crumb">__PERIOD_LABEL__</span>
    <span class="sep">·</span>
    <span>Snapshot Windsor.ai</span>
    <span class="refreshed">Pubblicato il ${refreshed}</span>
  </div>`;
  if(STATE.active==="_overview") h += renderBudgetPlan(STATE.allCD);
  else { const cd = STATE.allCD.find(x=>x.client.nome===STATE.active); h += cd ? renderClient(cd) : `<div class="note-banner">Cliente non trovato.</div>`; }
  main.innerHTML = h;
  window.scrollTo(0,0);
}

function buildNav(){
  const ov = document.getElementById("nav-overview");
  ov.innerHTML = `<div class="nav-item active" data-key="_overview"><span>Piano Budget Residuo</span></div>`;
  const cn = document.getElementById("nav-clients");
  cn.innerHTML = CLIENTS.map((c,i)=>`<div class="nav-item" data-key="${c.nome}"><span>${c.nome}</span><span class="badge">${c.cm}${c.tk_id?" · TK":""}</span></div>`).join("");
  document.querySelectorAll(".nav-item").forEach(n=>n.addEventListener("click", ()=>setActive(n.dataset.key)));
}

buildNav();
render();
</script>
</body>
</html>
"""

INDEX_TEMPLATE = r"""<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Report AGHC — Archivio mensile</title>
<style>
:root { color-scheme: light;
  --bg:#fafafa; --bg-card:#fff; --text:#1c1c1e; --text-soft:#3f3f44; --text-muted:#6b6b70; --text-dim:#8a8a90; --border:#ececef;
}
* { box-sizing: border-box; }
body {
  margin:0; padding:0;
  font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  background: var(--bg); color: var(--text);
  -webkit-font-smoothing: antialiased;
}
.container { max-width:640px; margin:0 auto; padding:60px 24px 80px; }
.brand-tag { font-size:11px; font-weight:600; letter-spacing:0.14em; text-transform:uppercase; color:var(--text-muted); margin:0 0 10px; }
h1 { color:var(--text); font-size:28px; font-weight:700; letter-spacing:-0.015em; margin:0 0 8px; }
.subtitle { color:var(--text-muted); font-size:15px; margin:0 0 32px; line-height:1.55; }
.tagline { background:var(--bg-card); border:1px solid var(--border); padding:18px 22px; border-radius:10px; margin-bottom:40px; font-size:13.5px; line-height:1.6; color:var(--text-soft); }
.tagline strong { color:var(--text); font-weight:600; }
.section-label { font-size:11px; font-weight:600; text-transform:uppercase; letter-spacing:0.12em; color:var(--text-dim); margin:0 0 14px; }
ul.report-list { list-style:none; padding:0; margin:0; background:var(--bg-card); border:1px solid var(--border); border-radius:10px; overflow:hidden; }
li.report-item { border-bottom:1px solid var(--border); }
li.report-item:last-child { border-bottom:none; }
li.report-item a { display:flex; align-items:center; justify-content:space-between; padding:16px 22px; text-decoration:none; color:var(--text); transition: background .12s ease; }
li.report-item a:hover { background:var(--bg); }
.month-name { font-weight:500; font-size:15px; letter-spacing:-0.005em; }
.arrow { color:var(--text-muted); font-size:18px; transition: transform .15s ease, color .15s ease; }
li.report-item a:hover .arrow { color:var(--text); transform: translateX(2px); }
.footer { text-align:center; font-size:12px; color:var(--text-muted); margin-top:36px; letter-spacing:0.02em; }
</style>
</head>
<body>
<div class="container">
  <p class="brand-tag">Report AGHC</p>
  <h1>Archivio mensile</h1>
  <p class="subtitle">18 hotel clienti · Meta + TikTok Advertising</p>
  <div class="tagline">Report KPI mensili realizzati da <strong>Francesco Maria Mosca</strong> per <strong>AG Hotel Consulting</strong>. Ogni snapshot è una fotografia statica dei dati Windsor.ai al momento della pubblicazione, con confronti YoY/MoM, budget tracking annuo e proposte investimento mese successivo.</div>
  <div class="section-label">Report disponibili</div>
  <ul class="report-list">
__ROWS__  </ul>
  <p class="footer">Aggiornato il __UPDATED__ · Realizzato da Francesco Maria Mosca</p>
</div>
</body>
</html>
"""


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--year", type=int, required=True)
    p.add_argument("--month", type=int, required=True)
    p.add_argument("--data", required=True)
    args = p.parse_args()
    data = json.loads(Path(args.data).read_text(encoding="utf-8"))
    slug, html = render_page(args.year, args.month, data)
    out = ROOT / f"{slug}.html"
    out.write_text(html, encoding="utf-8")
    print(f"✔ Pagina pubblicata: {out}")
    update_index(ROOT)
    print(f"✔ Indice aggiornato: {ROOT/'index.html'}")


if __name__ == "__main__":
    main()
