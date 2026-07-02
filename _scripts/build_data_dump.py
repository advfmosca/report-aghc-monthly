#!/usr/bin/env python3
"""build_data_dump.py — Genera SOLO i campi dinamici del template AGHC per copy-paste in Canva.

Strategia: il template Canva originale (icone, layout, branding) resta intatto. Ogni mese
questo script produce 1 file Markdown per cliente con tutti i valori da incollare nei
placeholder del template (numeri tabelle, periodi, rational, budget).

Output (1 file MD per cliente):
  <senape>/<Mese Anno>/Dynamic Data/<Cliente>.md

Workflow Francesco:
  1. Apri il template Canva originale (https://canva.link/...)
  2. Apri il file MD del cliente
  3. Per ogni placeholder, copia il valore dal MD e incollalo in Canva
  4. Esporta PDF, allega al deck

Uso:
  python3 build_data_dump.py --year 2026 --month 4 --client Lunetta \\
    --data _data/data-2026-04.json --output /tmp/lunetta.md

  # Oppure tutti i 18 clienti in cartella:
  python3 build_data_dump.py --year 2026 --month 4 \\
    --data _data/data-2026-04.json --output-dir /tmp/dump
"""
import argparse, json
from pathlib import Path

MONTH_IT = {1:"Gennaio",2:"Febbraio",3:"Marzo",4:"Aprile",5:"Maggio",6:"Giugno",
            7:"Luglio",8:"Agosto",9:"Settembre",10:"Ottobre",11:"Novembre",12:"Dicembre"}
BUDGET_WEIGHTS = {1:3,2:3,3:5,4:10,5:15,6:15,7:12,8:12,9:5,10:5,11:5,12:10}

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
    "Puntebianche Resort":{"meta_id":"1528485957725509","filter":["Puntebianche"],"excl":[],"tk_id":None,"cm":"MoM","ct":None,"budget":0},
    "Terrazza Flavia":{"meta_id":"821188209852436","filter":["Terrazza"],"excl":[],"tk_id":None,"cm":"YoY","ct":None,"budget":7500},
    "Villa Ermellina":{"meta_id":"30233607946222961","filter":None,"excl":[],"tk_id":"7612666695502118929","cm":"MoM","ct":"MoM","budget":16400},
    "Villa Giada":    {"meta_id":"1849759899186169","filter":None,"excl":[],"tk_id":None,"cm":"MoM","ct":None,"budget":21600},
    "Villa Miliani":  {"meta_id":"1353024533007038","filter":None,"excl":[],"tk_id":None,"cm":"MoM","ct":None,"budget":6600},
}


# === Formattazione (matching template Canva: "11.068" / "761,18€" / "-98%") ===
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
    comp_y, comp_m = comparison_period(year, month, cfg["cm"])
    period_a = f"{MONTH_IT[month]} {year}"
    period_b = f"{MONTH_IT[comp_m]} {comp_y}"

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
    tk_cur = tk_prev = None; tk_launched = False; period_b_tk = None
    if has_tk:
        tk_cur = data["tiktok"]["current"].get(cfg["tk_id"]) or empty_tk()
        comp_y_t, comp_m_t = comparison_period(year, month, cfg["ct"])
        period_b_tk = f"{MONTH_IT[comp_m_t]} {comp_y_t}"
        ck = "prev_yoy" if cfg["ct"]=="YoY" else "prev_mom"
        tk_prev = data["tiktok"].get(ck, {}).get(cfg["tk_id"]) or empty_tk()
        if (tk_cur.get("spend") or 0) > 0 and (tk_prev.get("spend") or 0) == 0 and (tk_prev.get("impressions") or 0) == 0:
            tk_launched = True

    ytd_root = data.get("ytd_spend", {})
    ytd_months = ytd_root.get("months", list(range(1, month+1)))
    ytd_client = ytd_root.get("by_client", {}).get(client_name, {})

    return {
        "client_name": client_name, "cfg": cfg, "year": year, "month": month,
        "period_a": period_a, "period_b": period_b, "period_b_tk": period_b_tk,
        "has_tk": has_tk, "tk_launched": tk_launched,
        "meta_cur": meta_cur, "meta_prev": meta_prev,
        "tk_cur": tk_cur, "tk_prev": tk_prev,
        "ytd_months": ytd_months, "ytd_client": ytd_client,
    }


# === Rational (testo plain, 3 paragrafi separati da riga vuota — pronto da incollare nel box) ===
def build_rational(v, focus):
    fb_c = v["meta_cur"]["facebook"]; fb_p = v["meta_prev"]["facebook"]
    ig_c = v["meta_cur"]["instagram"]; ig_p = v["meta_prev"]["instagram"]
    spend_cur = (fb_c.get("spend") or 0) + (ig_c.get("spend") or 0)
    spend_prev = (fb_p.get("spend") or 0) + (ig_p.get("spend") or 0)
    spend_delta = pct(spend_cur, spend_prev)
    fb_reach_cur = fb_c.get("reach") or 0
    fb_reach_delta = pct(fb_reach_cur, fb_p.get("reach") or 0)
    ig_reach_cur = ig_c.get("reach") or 0
    ig_reach_delta = pct(ig_reach_cur, ig_p.get("reach") or 0)
    reach_meta = fb_reach_cur + ig_reach_cur
    fb_eng_cur = fb_c.get("actions_page_engagement") or 0
    fb_eng_prev = fb_p.get("actions_page_engagement") or 0
    fb_eng_delta = pct(fb_eng_cur, fb_eng_prev)
    tot_eng = fb_eng_cur + (ig_c.get("actions_page_engagement") or 0)

    cn = v["client_name"]
    pa = v["period_a"]
    month_cap = MONTH_IT[v["month"]]
    month_low = month_cap.lower()
    next_m = (v["month"] % 12) + 1
    next_low = MONTH_IT[next_m].lower()
    next_w = BUDGET_WEIGHTS[next_m]

    # ===== TikTok =====
    if focus == "tiktok":
        if v["tk_launched"]:
            tk = v["tk_cur"]
            p1 = (f"{month_cap} inaugura una nuova fase per {cn}: la prima campagna TikTok va live e debutta "
                  f"con {fmt_int(tk.get('impressions') or 0)} visualizzazioni e {fmt_int(tk.get('reach') or 0)} "
                  f"utenti unici raggiunti, aprendo un canale fino a ieri inesplorato dal brand.")
            p2 = (f"Il presidio sul pubblico più giovane si attiva nel momento giusto, anticipando le finestre stagionali "
                  f"a più alto traffico di prenotazione.")
            p3 = (f"Da {next_low} {cn} opera su due leve complementari: Meta per la conversione, "
                  f"TikTok per la scoperta del brand.")
            return f"{p1}\n\n{p2}\n\n{p3}"
        if v["tk_cur"] and (v["tk_cur"].get("impressions") or 0) > 0:
            return (f"In {pa} TikTok mantiene un presidio efficiente con {fmt_int(v['tk_cur'].get('impressions') or 0)} "
                    f"impression generate, a conferma di un mix canali ben bilanciato sugli obiettivi di awareness.")
        return f"TikTok in stand-by per {cn} in {pa}; la pressione resta concentrata sui canali principali."

    # ===== META =====
    # Caso speciale: zero attività
    if spend_cur == 0 and reach_meta == 0:
        p1 = f"{month_cap} rappresenta una pausa strategica per {cn}, coerente con il calendario annuo del piano media."
        p2 = "Il budget residuo resta integro e pronto a concentrarsi sulle finestre stagionali a più alto ritorno previste nei mesi successivi."
        nxt_phrase = "nel cuore della stagione" if next_w >= 12 else "in modo progressivo"
        p3 = f"Da {next_low} (peso {next_w}% del piano annuo) il presidio riprende {nxt_phrase}."
        return f"{p1}\n\n{p2}\n\n{p3}"

    # Lead Facebook esploso
    if fb_reach_delta is not None and fb_reach_delta > 100:
        mul = f"{(1 + fb_reach_delta/100):.1f}".replace('.', ',')
        p1 = (f"{month_cap} segna un cambio di passo per {cn}: Facebook diventa il canale di traino e amplia "
              f"la copertura di {mul} volte rispetto al periodo di confronto, raggiungendo {fmt_int(fb_reach_cur)} "
              f"utenti unici.")
    elif spend_delta is not None and spend_delta < -8 and reach_meta > 0:
        p1 = (f"{month_cap} è il mese dell'efficienza per {cn}: la copertura Meta resta solida con "
              f"{fmt_int(reach_meta)} utenti unici raggiunti, con un investimento ridotto del {abs(int(spend_delta))}%. "
              f"Ogni euro speso ha lavorato meglio.")
    else:
        p1 = (f"{month_cap} mantiene il presidio di {cn} su base solida: {fmt_int(reach_meta)} utenti unici "
              f"raggiunti su Meta, in linea con il posizionamento strategico del mese all'interno del piano annuo.")

    # Paragrafo 2: dato di rinforzo
    if fb_eng_delta is not None and fb_eng_delta > 100 and fb_eng_cur > 5000:
        p2 = (f"Le interazioni sui contenuti Facebook salgono a {fmt_int(fb_eng_cur)}, una scala completamente "
              f"diversa rispetto al periodo di confronto.")
    elif tot_eng > 50000:
        p2 = (f"Il pubblico interagisce attivamente con i contenuti del brand, con {fmt_int(tot_eng)} interazioni "
              f"totali generate nel mese.")
    else:
        p2 = (f"Il presidio del marchio si mantiene attivo, con i contenuti pubblicati che continuano a "
              f"generare conversazioni qualificate intorno a {cn}.")

    # Paragrafo 3: prospettiva mese successivo
    if next_w >= 12:
        p3 = (f"{MONTH_IT[next_m]} entra nel cuore della stagione ({next_w}% del budget annuo): saliamo "
              f"sulla pressione per intercettare la domanda attiva nella finestra prenotativa più calda dell'anno.")
    else:
        p3 = (f"A {next_low} (peso {next_w}% del piano annuo) il presidio prosegue strategico, mantenendo "
              f"il pubblico caldo in vista delle finestre più rilevanti del piano.")

    return f"{p1}\n\n{p2}\n\n{p3}"


# === Rendering MD ===
def render_md(v):
    """Genera Markdown del data dump per il cliente."""
    out = []
    cn = v["client_name"]
    pa = v["period_a"]
    pb = v["period_b"]

    out.append(f"# {cn} — {pa}")
    out.append("")
    out.append("> Tutti i campi dinamici da incollare nel TEMPLATE ORIGINALE Canva. "
               "Apri il template, sostituisci i valori, esporta PDF.")
    out.append("")

    # ───────── COVER ─────────
    out.append("## 📄 Slide 1 — Cover")
    out.append("")
    out.append(f"| Campo template | Valore da incollare |")
    out.append(f"|---|---|")
    out.append(f"| `MESE - ANNO` | **{pa.upper()}** |")
    out.append(f"| `NOME HOTEL` | **{cn.upper()}** |")
    out.append("")

    # ───────── META ADVERTISING ─────────
    out.append("## 📊 Slide 2 — Meta Advertising")
    out.append("")
    out.append(f"**Header:**")
    out.append(f"- `MESE ATTUALE - ANNO` → **{pa.upper()}**")
    out.append(f"- `MESE DI CONFRONTO - ANNO` → **{pb.upper()}**")
    out.append("")

    fb_c, fb_p = v["meta_cur"]["facebook"], v["meta_prev"]["facebook"]
    ig_c, ig_p = v["meta_cur"]["instagram"], v["meta_prev"]["instagram"]
    sp_c = (fb_c.get("spend") or 0) + (ig_c.get("spend") or 0)
    sp_p = (fb_p.get("spend") or 0) + (ig_p.get("spend") or 0)

    for kpi_label, field in [
        ("ACCOUNT RAGGIUNTI", "reach"),
        ("VISUALIZZAZIONI", "impressions"),
        ("INTERAZIONI", "actions_page_engagement"),
        ("CLICKS", "clicks"),
    ]:
        out.append(f"### {kpi_label}")
        out.append("")
        out.append("|  | Periodo Attuale | Periodo Precedente | Confronto |")
        out.append("|---|---:|---:|---:|")
        out.append(f"| Instagram | **{fmt_int(ig_c.get(field) or 0)}** | **{fmt_int(ig_p.get(field) or 0)}** | **{fmt_pct(pct(ig_c.get(field) or 0, ig_p.get(field) or 0))}** |")
        out.append(f"| Facebook  | **{fmt_int(fb_c.get(field) or 0)}** | **{fmt_int(fb_p.get(field) or 0)}** | **{fmt_pct(pct(fb_c.get(field) or 0, fb_p.get(field) or 0))}** |")
        out.append("")

    out.append("### BUDGET")
    out.append("")
    out.append("| Periodo Attuale | Periodo Precedente | Confronto |")
    out.append("|---:|---:|---:|")
    out.append(f"| **{fmt_eur(sp_c)}** | **{fmt_eur(sp_p)}** | **{fmt_pct(pct(sp_c, sp_p))}** |")
    out.append("")

    out.append("### RATIONAL (testo da incollare nel box)")
    out.append("")
    out.append("```")
    out.append(build_rational(v, "meta"))
    out.append("```")
    out.append("")

    # ───────── TIKTOK ─────────
    if v["has_tk"]:
        out.append("## 🎵 Slide 3 — Tik Tok Advertising")
        out.append("")
        out.append(f"**Header:**")
        out.append(f"- `MESE ATTUALE - ANNO` → **{pa.upper()}**")
        out.append(f"- `MESE DI CONFRONTO - ANNO` → **{(v['period_b_tk'] or '').upper()}**")
        if v["tk_launched"]:
            out.append("")
            out.append(f"> ⚠️ **1° MESE LIVE**: TikTok appena attivato. La colonna 'Periodo Precedente' è a 0 — "
                       f"sul template Canva sostituiscila con il testo `1° mese live` o lasciala vuota. La "
                       f"colonna 'Confronto' non è significativa, va omessa o sostituita con `1° mese live`.")
        out.append("")

        tk_c = v["tk_cur"] or empty_tk()
        tk_p = v["tk_prev"] or empty_tk()
        launched = v["tk_launched"]

        for kpi_label, field in [
            ("ACCOUNT RAGGIUNTI", "reach"),
            ("VISUALIZZAZIONI", "impressions"),
            ("CLICK ALLA DESTINAZIONE", "clicks"),
        ]:
            cur_v = tk_c.get(field) or 0
            prev_v = tk_p.get(field) or 0
            delta_str = "1° mese live" if launched else fmt_pct(pct(cur_v, prev_v))
            prev_str = "0" if launched else fmt_int(prev_v)
            out.append(f"### {kpi_label}")
            out.append("")
            out.append("| Periodo Attuale | Periodo Precedente | Confronto |")
            out.append("|---:|---:|---:|")
            out.append(f"| **{fmt_int(cur_v)}** | **{prev_str}** | **{delta_str}** |")
            out.append("")

        # Budget TikTok
        tkc = tk_c.get("spend") or 0
        tkp = tk_p.get("spend") or 0
        delta_str = "1° mese live" if launched else fmt_pct(pct(tkc, tkp))
        prev_str = "0,00€" if launched else fmt_eur(tkp)
        out.append("### BUDGET")
        out.append("")
        out.append("| Periodo Attuale | Periodo Precedente | Confronto |")
        out.append("|---:|---:|---:|")
        out.append(f"| **{fmt_eur(tkc)}** | **{prev_str}** | **{delta_str}** |")
        out.append("")

        out.append("### RATIONAL (testo da incollare nel box)")
        out.append("")
        out.append("```")
        out.append(build_rational(v, "tiktok"))
        out.append("```")
        out.append("")

    # ───────── BUDGET ANNUALE ─────────
    out.append("## 💰 Slide 4 — Budget Annuale")
    out.append("")
    budget = v["cfg"]["budget"] or 0
    ytd_months = v["ytd_months"]
    ytd_client = v["ytd_client"]
    tot_meta = tot_tk = 0
    out.append(f"**BUDGET ANNUALE: {fmt_eur(budget)}**")
    out.append("")
    out.append("| MESI | ADS META | ADS TIK TOK | TOTALE |")
    out.append("|---|---:|---:|---:|")
    for m in range(1, 13):
        md = ytd_client.get(str(m), {"meta":0, "tiktok":0}) if m in ytd_months else {"meta":0, "tiktok":0}
        meta_v = md.get("meta") or 0
        tk_v = md.get("tiktok") or 0
        tot_meta += meta_v
        tot_tk += tk_v
        out.append(f"| **{MONTH_IT[m].upper()}** | {fmt_eur(meta_v)} | {fmt_eur(tk_v)} | {fmt_eur(meta_v + tk_v)} |")
    speso = tot_meta + tot_tk
    rimanente = budget - speso
    out.append(f"| **BUDGET SPESO** | **{fmt_eur(tot_meta)}** | **{fmt_eur(tot_tk)}** | **{fmt_eur(speso)}** |")
    out.append(f"| **BUDGET RIMANENTE** |  |  | **{fmt_eur(rimanente)}** |")
    out.append("")
    out.append("---")
    out.append("")
    out.append(f"*Generato automaticamente da pipeline AGHC — dati Windsor.ai · "
               f"Confronto Meta: {v['cfg']['cm']}" + (f" · TikTok: {v['cfg']['ct']}" if v["has_tk"] else "") + "*")

    return "\n".join(out)


# === Main ===
def main():
    p = argparse.ArgumentParser()
    p.add_argument("--year", type=int, required=True)
    p.add_argument("--month", type=int, required=True)
    p.add_argument("--client", help="Nome cliente singolo. Se omesso, genera per tutti i 18.")
    p.add_argument("--data", required=True)
    p.add_argument("--output", help="Path file MD singolo. Richiesto se --client è specificato.")
    p.add_argument("--output-dir", help="Cartella per output multi-cliente. Richiesto se --client è omesso.")
    args = p.parse_args()

    data = json.loads(Path(args.data).read_text(encoding="utf-8"))

    if args.client:
        if args.client not in CLIENTS:
            raise SystemExit(f"Cliente '{args.client}' non trovato. Disponibili: {list(CLIENTS.keys())}")
        if not args.output:
            raise SystemExit("--output richiesto quando si specifica --client")
        v = build_view(args.client, data, args.year, args.month)
        Path(args.output).write_text(render_md(v), encoding="utf-8")
        print(f"✔ {args.client}: {args.output}")
    else:
        if not args.output_dir:
            raise SystemExit("--output-dir richiesto quando --client è omesso")
        outdir = Path(args.output_dir)
        outdir.mkdir(parents=True, exist_ok=True)
        for cn in CLIENTS:
            v = build_view(cn, data, args.year, args.month)
            outpath = outdir / f"{cn}.md"
            outpath.write_text(render_md(v), encoding="utf-8")
            print(f"✔ {cn}: {outpath.name}")


if __name__ == "__main__":
    main()
