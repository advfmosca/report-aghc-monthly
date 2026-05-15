#!/usr/bin/env python3
"""build_static.py — Genera la pagina HTML statica self-contained del report mensile AGHC.

Input:
  --year 2026 --month 4 --data _data/data-2026-04.json

Output:
  - <slug>.html (es. aprile-2026.html) nella root del repo
  - index.html ricostruito con la lista di tutti i mesi disponibili

Uso da scheduled task mensile:
  python3 _scripts/build_static.py --year 2026 --month 4 --data _data/data-2026-04.json
"""
import argparse, json, sys, re, os
from pathlib import Path
from datetime import datetime

MONTH_IT = {1:"gennaio",2:"febbraio",3:"marzo",4:"aprile",5:"maggio",6:"giugno",
            7:"luglio",8:"agosto",9:"settembre",10:"ottobre",11:"novembre",12:"dicembre"}

ROOT = Path(__file__).resolve().parent.parent

# Anagrafica (replica fonte di verità _generator/anagrafica.py — riscritta in JSON-friendly format)
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
    """Build a self-contained HTML report for the given month."""
    slug = slug_for(year, month)
    period_label = f"{MONTH_IT[month].capitalize()} {year}"
    generated_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    # Embed data + anagrafica + month name into the HTML as JS consts
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
    """Rebuild index.html scanning available <slug>.html files in root."""
    files = []
    for f in repo_root.glob("*.html"):
        if f.name == "index.html":
            continue
        # filename: mese-anno.html → estrai
        m = re.match(r"([a-zà-ÿ]+)-(\d{4})\.html$", f.name, re.IGNORECASE)
        if not m:
            continue
        mese, anno = m.group(1).lower(), int(m.group(2))
        # rev MONTH_IT
        rev = {v:k for k,v in MONTH_IT.items()}
        if mese not in rev:
            continue
        files.append({"slug": f.stem, "year": anno, "month": rev[mese], "filename": f.name})
    # sort newest first
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


# ============================================================================
# HTML TEMPLATES
# ============================================================================
HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Report AGHC — __PERIOD_LABEL__</title>
<style>
:root { color-scheme: light; }
* { box-sizing: border-box; }
body { margin:0; padding:0; font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif; background:#fff; color:#1c2024; font-size:13px; line-height:1.45; }
.app { display:grid; grid-template-columns:240px 1fr; min-height:100vh; }
.sidebar { border-right:1px solid #e3e6ea; background:#f7f8fa; padding:12px 0; position:sticky; top:0; height:100vh; overflow-y:auto; }
.sidebar h1 { font-size:13px; font-weight:700; color:#1F4E78; margin:6px 14px 4px; text-transform:uppercase; letter-spacing:0.5px; }
.sidebar .period { margin:0 14px 14px; font-size:12px; color:#6c757d; font-weight:600; }
.nav-item { display:flex; align-items:center; justify-content:space-between; padding:7px 14px; cursor:pointer; font-size:13px; border-left:3px solid transparent; transition:background .12s ease; }
.nav-item:hover { background:#ebeef2; }
.nav-item.active { background:#e1ecf7; border-left-color:#1F4E78; font-weight:600; color:#1F4E78; }
.nav-item .badge { font-size:10px; color:#6c757d; }
.nav-section { margin-top:14px; padding:4px 14px; font-size:10px; font-weight:700; text-transform:uppercase; letter-spacing:0.8px; color:#6c757d; }
.archive-link { display:block; margin:14px; padding:7px 10px; background:#fff; border:1px solid #d6dce3; border-radius:6px; text-align:center; text-decoration:none; color:#1F4E78; font-size:12px; font-weight:600; }
.archive-link:hover { background:#e1ecf7; }
.main { padding:18px 28px 60px; min-width:0; }
.client-header { background:linear-gradient(135deg,#1F4E78 0%,#2A6CA8 100%); color:#fff; padding:16px 20px; border-radius:8px; margin-bottom:12px; }
.client-header h2 { margin:0; font-size:18px; font-weight:700; }
.client-header .meta { margin-top:6px; font-size:12px; opacity:0.85; }
.note-banner { background:#FFF2CC; border-left:3px solid #BF8F00; padding:8px 12px; margin:8px 0 14px; font-size:12px; color:#5d4d00; font-style:italic; border-radius:0 4px 4px 0; }
.note-banner.tiktok-launch { background:#DDEBF7; border-left-color:#2F5496; color:#1a3a5c; }
.section-title { font-size:12px; font-weight:700; color:#1F4E78; text-transform:uppercase; letter-spacing:0.5px; margin:22px 0 6px; padding-bottom:6px; border-bottom:2px solid #1F4E78; }
.kpi-title { font-size:12px; font-weight:700; color:#1F4E78; margin:14px 0 4px; text-transform:uppercase; letter-spacing:0.3px; }
.kpi-title .info { color:#BF8F00; margin-left:4px; cursor:help; font-size:11px; }
table.kpi,table.ytd,table.tracking,table.proposta { width:100%; max-width:720px; border-collapse:collapse; background:#fff; margin-bottom:4px; font-size:12.5px; }
table.kpi th,table.kpi td,table.ytd th,table.ytd td,table.tracking th,table.tracking td,table.proposta th,table.proposta td { border:1px solid #d6dce3; padding:6px 10px; text-align:center; }
table.kpi th,table.ytd th,table.tracking th,table.proposta th { background:#D9E1F2; font-weight:700; font-size:11px; color:#1c2024; text-transform:uppercase; letter-spacing:0.3px; }
table.kpi td:first-child,table.kpi th:first-child,table.ytd td:first-child,table.tracking td:first-child,table.proposta td:first-child { text-align:left; font-weight:600; }
.delta-pos { color:#548235; font-weight:700; }
.delta-neg { color:#C00000; font-weight:700; }
.delta-neutral { color:#595959; }
.delta-na { color:#595959; font-style:italic; font-size:11px; }
.delta-tk-launch { color:#2F5496; font-style:italic; font-weight:700; font-size:11px; }
tr.total td { font-weight:700; background:#f0f3f7; }
.status-line { font-weight:700; font-size:13px; padding:6px 10px; border-radius:4px; margin:6px 0; }
.status-in-linea { background:#e2efda; color:#548235; }
.status-under { background:#fff4ce; color:#BF8F00; }
.status-over { background:#f8d7da; color:#C00000; }
.status-neutral { background:#f0f0f0; color:#595959; }
.rational { background:#f7f8fa; border-left:4px solid #1F4E78; padding:12px 16px; margin-top:14px; font-size:13px; line-height:1.55; border-radius:0 4px 4px 0; max-width:720px; }
.budget-plan { padding:6px 0 30px; }
.budget-plan-client { margin-bottom:24px; }
.budget-plan-client-header { background:#2F5496; color:#fff; padding:8px 14px; font-weight:700; font-size:14px; border-radius:6px 6px 0 0; }
.budget-plan-client-info { background:#f7f8fa; padding:6px 14px; font-size:12px; font-style:italic; color:#1F4E78; font-weight:600; border-left:1px solid #d6dce3; border-right:1px solid #d6dce3; }
.budget-plan-warning { background:#f8d7da; padding:8px 14px; font-size:12px; color:#C00000; font-weight:700; border-left:1px solid #d6dce3; border-right:1px solid #d6dce3; }
table.budget-plan-table { width:100%; border-collapse:collapse; font-size:12px; }
table.budget-plan-table th,table.budget-plan-table td { border:1px solid #d6dce3; padding:5px 8px; text-align:center; }
table.budget-plan-table th { background:#D9E1F2; font-weight:700; text-transform:uppercase; font-size:10.5px; }
table.budget-plan-table td:first-child { text-align:left; font-weight:600; }
table.budget-plan-table tr.total td { background:#f0f3f7; font-weight:700; }
.header-toolbar { display:flex; align-items:center; gap:12px; margin-bottom:14px; padding:8px 14px; background:#f7f8fa; border-radius:6px; font-size:12px; }
.header-toolbar label { font-weight:600; color:#1F4E78; }
.header-toolbar .refreshed { margin-left:auto; color:#6c757d; font-style:italic; }
@media (max-width: 720px) {
  .app { grid-template-columns: 1fr; }
  .sidebar { position:relative; height:auto; max-height:none; }
  .main { padding:14px 16px 60px; }
  table.kpi,table.ytd,table.tracking,table.proposta { font-size:11px; }
  table.kpi td,table.kpi th { padding:4px 6px; }
}
</style>
</head>
<body>
<div class="app">
  <aside class="sidebar">
    <h1>Report AGHC</h1>
    <div class="period">__PERIOD_LABEL__</div>
    <a class="archive-link" href="index.html">← Archivio storico</a>
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
const SHARED_ACCOUNTS = new Set(["1312718426033158","1528485957725509","821188209852436"]);

function monthName(m){ return MONTH_IT[String(m)] || MONTH_IT[m]; }
function fmtInt(x){ if(x===null||x===undefined) return "n/d"; return Math.round(x).toLocaleString("it-IT"); }
function fmtEur(x){ if(x===null||x===undefined) return "n/d"; return x.toLocaleString("it-IT",{style:"currency",currency:"EUR",minimumFractionDigits:2,maximumFractionDigits:2}); }
function pct(c,p){ if(p===null||p===undefined||p===0||c===null||c===undefined) return null; return (c-p)/p*100; }
function fmtPct(p){ if(p===null) return "n/d"; const s=p>0?"+":""; return `${s}${p.toFixed(2)}%`; }
function pctClass(p){ if(p===null) return "delta-na"; return p>=0?"delta-pos":"delta-neg"; }
function comparisonPeriod(y,m,t){ if(t==="YoY") return {y:y-1,m}; if(m===1) return {y:y-1,m:12}; return {y,m:m-1}; }
function capitalize(s){ return s.charAt(0).toUpperCase()+s.slice(1); }

function emptyMeta(){ return {reach:0,impressions:0,actions_page_engagement:0,clicks:0,spend:0}; }
function emptyTk(){ return {reach:0,impressions:0,engagements:0,clicks:0,spend:0}; }

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
  // Detect reach estimation: legge dalla lista esplicita "reach_estimated_clients"
  // popolata da estimate_reach.py durante la pipeline.
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

  // YTD per cliente
  const ytdRoot = DATA.ytd_spend || {by_client: {}, months: []};
  const ytdMonths = ytdRoot.months && ytdRoot.months.length ? ytdRoot.months : (function(){ const a=[]; for(let m=1;m<=REPORT_MONTH;m++) a.push(m); return a; })();
  const cYtd = ytdRoot.by_client?.[client.nome] || {};

  return { client, periodA, periodBMeta, hasTk, tkPeriodB, metaCur, metaPrev, tkCur, tkPrev, reachEstimated, tkLaunched, ytdMonths, ytdSpend: cYtd };
}

function buildRational(cd){
  const { client, periodA, metaCur, metaPrev, tkCur, hasTk } = cd;
  const m = REPORT_MONTH;
  const spendCur = (metaCur.facebook.spend||0)+(metaCur.instagram.spend||0);
  const spendPrev = (metaPrev.facebook.spend||0)+(metaPrev.instagram.spend||0);
  const spendDelta = pct(spendCur, spendPrev);
  const ig = pct(metaCur.instagram.impressions, metaPrev.instagram.impressions);
  const fb = pct(metaCur.facebook.reach, metaPrev.facebook.reach);
  const imp = pct((metaCur.facebook.impressions||0)+(metaCur.instagram.impressions||0), (metaPrev.facebook.impressions||0)+(metaPrev.instagram.impressions||0));
  let open;
  if(spendDelta!==null && spendDelta>5) open = `${periodA} si apre con un incremento strategico del budget pubblicitario Meta (${fmtPct(spendDelta)}), scelta coerente con il posizionamento del mese all'interno del piano annuo (peso ${BUDGET_WEIGHTS[m]}%).`;
  else if(spendDelta!==null && spendDelta<-5) open = `In ${periodA} l'allocazione Meta è stata consapevolmente contenuta (${fmtPct(spendDelta)}) per concentrare pressione sulle finestre strategiche successive, coerentemente con il piano AGHC.`;
  else open = `${periodA} vede una continuità di investimento Meta in linea con il periodo di confronto (peso mensile ${BUDGET_WEIGHTS[m]}% sul piano annuo), a presidio costante del brand.`;
  const wins = [];
  if(ig!==null && ig>0) wins.push(`Instagram consolida la share of voice con visualizzazioni in crescita (${fmtPct(ig)})`);
  if(fb!==null && fb>0) wins.push(`Facebook amplia la copertura (${fmtPct(fb)})`);
  if(hasTk && (tkCur?.impressions||0)>0) wins.push(`TikTok genera ${fmtInt(tkCur.impressions)} impression a presidio efficiente`);
  if(wins.length===0){ const t=(metaCur.facebook.reach||0)+(metaCur.instagram.reach||0); if(t>0) wins.push(`il presidio del brand resta solido con oltre ${fmtInt(t)} utenti unici raggiunti`); }
  const winsLine = wins.length ? " " + wins.slice(0,2).join("; ").replace(/^./, c=>c.toUpperCase()) + ", a conferma di un mix canali ben bilanciato sugli obiettivi di awareness." : "";
  const anyDecline = (imp!==null && imp<-5) || (fb!==null && fb<-5);
  const ctx = anyDecline ? ` Eventuali flessioni su reach e interazioni riflettono il consueto rialzo dei CPM Meta nel comparto ricettivo e una competizione d'asta più densa.` : ` Il costo per risultato si mantiene efficiente in un contesto d'asta più selettivo.`;
  const nextM = (m%12)+1;
  const close = ` La base costruita in ${periodA} prepara ${capitalize(monthName(nextM))} (peso ${BUDGET_WEIGHTS[nextM]}% del piano annuo).`;
  return open + winsLine + ctx + close;
}

function kpiTable(title, periodA, periodB, rows, fmt, withInfoIcon){
  const info = withInfoIcon ? `<span class="info" title="Reach periodo precedente STIMATA — la Meta Marketing API non restituisce più reach per periodi oltre 24 mesi; valore calcolato applicando il rapporto reach/impressions del periodo corrente.">ⓘ</span>` : "";
  let h = `<div class="kpi-title">${title}${info}</div><table class="kpi"><thead><tr><th></th><th>${periodA}</th><th>${periodB}</th><th>Confronto</th></tr></thead><tbody>`;
  for(const [label, cur, prev, override] of rows){
    const p = pct(cur, prev);
    const dc = override ? `<td class="${override.cls}">${override.text}</td>` : `<td class="${pctClass(p)}">${fmtPct(p)}</td>`;
    h += `<tr><td>${label}</td><td>${fmt(cur)}</td><td>${fmt(prev)}</td>${dc}</tr>`;
  }
  return h + `</tbody></table>`;
}

function renderClient(cd){
  const { client, periodA, periodBMeta, tkPeriodB, hasTk, metaCur, metaPrev, tkCur, tkPrev, reachEstimated, tkLaunched, ytdMonths, ytdSpend } = cd;
  let h = `<div class="client-header"><h2>${client.nome} — ${periodA} vs ${periodBMeta}</h2>
    <div class="meta">Budget annuo: ${fmtEur(client.budget)} · Confronto Meta: ${client.cm} · TikTok: ${hasTk?"attivo":"non gestito"}${client.ct?` · Confronto TikTok: ${client.ct}`:""}</div></div>`;
  if(client.note) h += `<div class="note-banner">📌 ${client.note}</div>`;
  h += `<div class="section-title">Meta (Facebook + Instagram)</div>`;
  for(const [title, field] of [["Account Raggiunti","reach"],["Visualizzazioni","impressions"],["Interazioni","actions_page_engagement"],["Clicks","clicks"]]){
    const wi = (field==="reach") && reachEstimated;
    h += kpiTable(title, periodA, periodBMeta, [
      ["Instagram", metaCur.instagram[field], metaPrev.instagram[field]],
      ["Facebook",  metaCur.facebook[field],  metaPrev.facebook[field]],
    ], fmtInt, wi);
  }
  const spCur = (metaCur.facebook.spend||0)+(metaCur.instagram.spend||0);
  const spPrev = (metaPrev.facebook.spend||0)+(metaPrev.instagram.spend||0);
  h += kpiTable("Budget Meta", periodA, periodBMeta, [["Totale", spCur, spPrev]], fmtEur, false);

  if(hasTk){
    h += `<div class="section-title">TikTok</div>`;
    if(tkLaunched) h += `<div class="note-banner tiktok-launch">📌 TikTok attivato ad ${capitalize(monthName(REPORT_MONTH))} ${REPORT_YEAR} — primo mese live, confronto MoM non disponibile</div>`;
    const ovr = tkLaunched ? {text:"1° mese live", cls:"delta-tk-launch"} : null;
    for(const [t,f] of [["Account Raggiunti","reach"],["Visualizzazioni","impressions"],["Interazioni","engagements"],["Clicks","clicks"]]){
      h += kpiTable(t, periodA, tkPeriodB, [["TikTok", tkCur[f], tkPrev[f], ovr]], fmtInt, false);
    }
    h += kpiTable("Budget TikTok", periodA, tkPeriodB, [["TikTok", tkCur.spend, tkPrev.spend, ovr]], fmtEur, false);
  }

  const tkSpend = hasTk?(tkCur.spend||0):0;
  const totMonth = spCur + tkSpend;
  h += `<div class="section-title">Spesa Mensile</div><table class="ytd"><thead><tr><th>Canale</th><th>Speso ${periodA}</th></tr></thead><tbody>
    <tr><td>Meta</td><td>${fmtEur(spCur)}</td></tr>
    ${hasTk?`<tr><td>TikTok</td><td>${fmtEur(tkSpend)}</td></tr>`:""}
    <tr class="total"><td>TOTALE</td><td>${fmtEur(totMonth)}</td></tr></tbody></table>`;

  h += `<div class="section-title">Riepilogo Spesa YTD</div>`;
  let ytdMeta=0, ytdTk=0;
  h += `<table class="ytd"><thead><tr><th>Mese</th><th>Meta</th><th>TikTok</th><th>Totale</th></tr></thead><tbody>`;
  for(const m of ytdMonths){
    const md = ytdSpend[String(m)] || {meta:0,tiktok:0};
    ytdMeta += (md.meta||0); ytdTk += (md.tiktok||0);
    h += `<tr><td>${capitalize(monthName(m))}</td><td>${fmtEur(md.meta||0)}</td><td>${hasTk?fmtEur(md.tiktok||0):"—"}</td><td>${fmtEur((md.meta||0)+(md.tiktok||0))}</td></tr>`;
  }
  const ytdTot = ytdMeta+ytdTk;
  h += `<tr class="total"><td>TOTALE YTD</td><td>${fmtEur(ytdMeta)}</td><td>${hasTk?fmtEur(ytdTk):"—"}</td><td>${fmtEur(ytdTot)}</td></tr></tbody></table>`;

  const cumW = ytdMonths.reduce((s,m)=>s+BUDGET_WEIGHTS[m],0);
  const atteso = client.budget * cumW / 100;
  const scarto = ytdTot - atteso;
  const rim = client.budget - ytdTot;
  const tol = atteso * 0.10;
  let st, sc;
  if(atteso===0){ st="— (piano non ancora partito)"; sc="status-neutral"; }
  else if(Math.abs(scarto)<=tol){ st="✓ IN LINEA col piano"; sc="status-in-linea"; }
  else if(scarto<0){ st=`⚠ UNDER SPENDING di ${fmtEur(Math.abs(scarto))}`; sc="status-under"; }
  else { st=`⚠ OVER SPENDING di ${fmtEur(Math.abs(scarto))}`; sc="status-over"; }
  h += `<div class="section-title">Budget Tracking Annuo</div><table class="tracking"><tbody>
    <tr><td>Budget annuo</td><td colspan="3">${fmtEur(client.budget)}</td></tr>
    <tr><td>Peso cumulato piano (Gen–${capitalize(monthName(REPORT_MONTH))})</td><td colspan="3">${cumW}%</td></tr>
    <tr><td>Atteso YTD</td><td colspan="3">${fmtEur(atteso)}</td></tr>
    <tr><td>Speso YTD</td><td colspan="3">${fmtEur(ytdTot)}</td></tr>
    <tr><td>Scarto vs piano</td><td colspan="3">${scarto>=0?"+":"−"}${fmtEur(Math.abs(scarto))}</td></tr>
    <tr><td>Budget rimanente anno</td><td colspan="3">${fmtEur(rim)}</td></tr>
  </tbody></table><div class="status-line ${sc}">Status pacing: ${st}</div>`;

  const nm = (REPORT_MONTH%12)+1;
  const ny = REPORT_MONTH===12 ? REPORT_YEAR+1 : REPORT_YEAR;
  const nw = BUDGET_WEIGHTS[nm];
  const baseNext = client.budget * nw / 100;
  let metaN, tkN=0, tkNote=null;
  if(hasTk){ metaN = baseNext * META_SHARE; const tkB = baseNext * TIKTOK_SHARE; tkN = Math.max(TIKTOK_MIN_MONTHLY, tkB); tkNote = (tkN===TIKTOK_MIN_MONTHLY && tkB<TIKTOK_MIN_MONTHLY) ? "Min €600/mese" : `Split ${Math.round(TIKTOK_SHARE*100)}%`; }
  else metaN = baseNext;
  const totN = metaN + tkN;
  h += `<div class="section-title">Proposta Investimento ${capitalize(monthName(nm))} ${ny}</div>
    <table class="proposta"><thead><tr><th>Canale</th><th>Investimento Suggerito</th><th>Note</th></tr></thead><tbody>
      <tr><td>Meta</td><td>${fmtEur(metaN)}</td><td>${hasTk?`Split ${Math.round(META_SHARE*100)}%`:"100% budget mensile"}</td></tr>
      ${hasTk?`<tr><td>TikTok</td><td>${fmtEur(tkN)}</td><td>${tkNote}</td></tr>`:""}
      <tr class="total"><td>TOTALE</td><td>${fmtEur(totN)}</td><td>Peso piano ${nw}%</td></tr>
    </tbody></table>`;
  h += `<div class="section-title">Rational</div><div class="rational">${buildRational(cd)}</div>`;
  return h;
}

function renderBudgetPlan(allCD){
  const rem = []; for(let m=REPORT_MONTH+1;m<=12;m++) rem.push(m);
  if(rem.length===0) return `<h2 style="margin:0 0 12px;color:#1F4E78">Piano Budget Residuo</h2><div class="note-banner">Anno concluso — nessun mese residuo.</div>`;
  const tw = rem.reduce((s,m)=>s+BUDGET_WEIGHTS[m],0);
  let h = `<h2 style="margin:0 0 6px;color:#1F4E78">Piano Budget Residuo — da ${capitalize(monthName(rem[0]))} a Dicembre ${REPORT_YEAR}</h2>
    <p style="font-size:12px;color:#595959;font-style:italic;margin:0 0 14px;max-width:900px">Ricalibrazione dei budget sui pesi mensili AGHC — pesi originali rinormalizzati sul totale residuo ${tw}%. Split 80% Meta / 20% TikTok con soglia minima €${TIKTOK_MIN_MONTHLY}/mese TikTok.</p><div class="budget-plan">`;
  for(const cd of allCD){
    const c = cd.client, hasTk = cd.hasTk;
    let ytdTot = 0; for(const m of cd.ytdMonths){ const md=cd.ytdSpend[String(m)]||{}; ytdTot+=(md.meta||0)+(md.tiktok||0); }
    const res = c.budget - ytdTot, num = rem.length;
    let warn=null, metaRes;
    if(hasTk){ const tf=TIKTOK_MIN_MONTHLY*num; const mr=res-tf; if(mr<0){ warn=`⚠ Residuo ${fmtEur(res)} < min TikTok totale (${fmtEur(tf)}). TikTok manterrà €${TIKTOK_MIN_MONTHLY}/mese fissi, Meta = €0.`; metaRes=0;} else metaRes=mr; } else metaRes=res;
    h += `<div class="budget-plan-client"><div class="budget-plan-client-header">${c.nome}</div>
      <div class="budget-plan-client-info">Budget annuo: ${fmtEur(c.budget)} · Speso YTD: ${fmtEur(ytdTot)} · Residuo: ${fmtEur(res)}${hasTk?` · TikTok: attivo (min €${TIKTOK_MIN_MONTHLY}/mese)`:" · TikTok: non gestito"}</div>`;
    if(warn) h += `<div class="budget-plan-warning">${warn}</div>`;
    h += `<table class="budget-plan-table"><thead><tr><th>Mese</th><th>Peso piano</th><th>Peso rical.</th><th>Totale mese</th><th>Meta</th><th>TikTok</th><th>Note</th></tr></thead><tbody>`;
    let sT=0,sM=0,sK=0;
    for(const m of rem){
      const pw=BUDGET_WEIGHTS[m], pr=tw?pw/tw*100:0;
      let mm,kk,note;
      if(hasTk){ mm=metaRes>0?metaRes*pw/tw:0; kk=TIKTOK_MIN_MONTHLY; note="TikTok fisso €600 · Meta pro-peso"; }
      else { mm=res>0?res*pw/tw:0; kk=0; note="100% Meta"; }
      const t=mm+kk; sT+=t; sM+=mm; sK+=kk;
      h += `<tr><td>${capitalize(monthName(m))}</td><td>${pw}%</td><td>${pr.toFixed(1)}%</td><td>${fmtEur(t)}</td><td>${fmtEur(mm)}</td><td>${hasTk?fmtEur(kk):"—"}</td><td>${note}</td></tr>`;
    }
    h += `<tr class="total"><td>TOTALE</td><td>${tw}%</td><td>100.0%</td><td>${fmtEur(sT)}</td><td>${fmtEur(sM)}</td><td>${hasTk?fmtEur(sK):"—"}</td><td></td></tr></tbody></table></div>`;
  }
  return h + `</div>`;
}

const STATE = { active: "_overview", allCD: CLIENTS.map(c => buildClientData(c)) };

function setActive(key){ STATE.active = key; document.querySelectorAll(".nav-item").forEach(n=>n.classList.toggle("active", n.dataset.key===key)); render(); }

function render(){
  const main = document.getElementById("main");
  const refreshed = new Date(GENERATED_AT.replace(" UTC"," GMT")).toLocaleString("it-IT",{day:"2-digit",month:"short",year:"numeric",hour:"2-digit",minute:"2-digit"});
  let h = `<div class="header-toolbar"><label>Mese:</label><strong>__PERIOD_LABEL__</strong><span class="refreshed">Pubblicato il ${refreshed} · Fonte: Windsor.ai · Snapshot statico</span></div>`;
  if(STATE.active==="_overview") h += renderBudgetPlan(STATE.allCD);
  else { const cd = STATE.allCD.find(x=>x.client.nome===STATE.active); h += cd ? renderClient(cd) : `<div class="error">Cliente non trovato.</div>`; }
  main.innerHTML = h;
  window.scrollTo(0,0);
}

function buildNav(){
  const ov = document.getElementById("nav-overview");
  ov.innerHTML = `<div class="nav-item active" data-key="_overview"><span>Piano Budget Residuo</span></div>`;
  const cn = document.getElementById("nav-clients");
  cn.innerHTML = CLIENTS.map((c,i)=>`<div class="nav-item" data-key="${c.nome}"><span>${i+1}. ${c.nome}</span><span class="badge">${c.cm}${c.tk_id?"·TK":""}</span></div>`).join("");
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
:root { color-scheme: light; }
body { margin:0; font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif; background:#f7f8fa; color:#1c2024; }
.container { max-width:720px; margin:0 auto; padding:40px 24px 60px; }
h1 { color:#1F4E78; font-size:24px; margin:0 0 6px; }
.subtitle { color:#6c757d; font-size:14px; margin:0 0 28px; }
.tagline { background:#fff; border-left:4px solid #1F4E78; padding:14px 18px; border-radius:0 6px 6px 0; margin-bottom:32px; font-size:13px; line-height:1.55; color:#1c2024; }
.section-label { font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:0.8px; color:#6c757d; margin:0 0 10px; }
ul.report-list { list-style:none; padding:0; margin:0; background:#fff; border:1px solid #e3e6ea; border-radius:8px; overflow:hidden; }
li.report-item { border-bottom:1px solid #e3e6ea; }
li.report-item:last-child { border-bottom:none; }
li.report-item a { display:flex; align-items:center; justify-content:space-between; padding:14px 20px; text-decoration:none; color:#1c2024; transition:background .15s ease; }
li.report-item a:hover { background:#f0f3f7; color:#1F4E78; }
.month-name { font-weight:600; font-size:15px; }
.arrow { color:#1F4E78; font-size:18px; font-weight:600; }
.empty { background:#fff; border:1px dashed #d6dce3; border-radius:8px; padding:30px; text-align:center; color:#6c757d; font-style:italic; }
.footer { text-align:center; font-size:11px; color:#6c757d; margin-top:30px; }
.footer a { color:#1F4E78; }
</style>
</head>
<body>
<div class="container">
  <h1>Report AGHC</h1>
  <p class="subtitle">Archivio storico mensile · 18 hotel clienti · Meta + TikTok Advertising</p>
  <div class="tagline">Report KPI mensili realizzati da <strong>Francesco Maria Mosca</strong> per <strong>AG Hotel Consulting</strong>. Ogni snapshot è una fotografia statica dei dati Windsor.ai al momento della pubblicazione, con confronti YoY/MoM, budget tracking annuo e proposte investimento mese successivo.</div>
  <div class="section-label">Report disponibili</div>
  <ul class="report-list">
__ROWS__  </ul>
  <div class="footer">Aggiornato il __UPDATED__ · Realizzato da Francesco Maria Mosca</div>
</div>
</body>
</html>
"""


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--year", type=int, required=True)
    p.add_argument("--month", type=int, required=True)
    p.add_argument("--data", required=True, help="path al JSON dei dati elaborati")
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
