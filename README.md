# Report AGHC — Archivio mensile

Snapshot statici dei report KPI mensili di AG Hotel Consulting (Meta + TikTok Advertising), realizzati da Francesco Maria Mosca.

🌐 **Online:** https://advfmosca.github.io/report-aghc-monthly/

## Struttura
- `index.html` — landing con elenco di tutti i mesi
- `<mese>-<anno>.html` — un report per mese (self-contained, dati baked-in)
- `_data/data-YYYY-MM.json` — dati Windsor.ai pre-aggregati (single source of truth)
- `_scripts/` — generatore Python:
  - `run_monthly_pipeline.py` — orchestrator (HTML + commit + push; xlsx opzionale)
  - `estimate_reach.py` — stima reach YoY mancante (limite Meta API >24m)
  - `build_static.py` — generatore HTML statico
  - `anagrafica.py` — anagrafica 18 clienti AGHC
  - `generate_sheet.py` ⚠️ LEGACY — generatore xlsx (non attivato di default dal 16/05/2026)
  - `postprocess_xlsx.py` ⚠️ LEGACY — annotazioni xlsx (ⓘ stimata + 1° mese live)

## Pipeline mensile (automatica via scheduled task, online-only dal 16/05/2026)
1. Claude fetcha Windsor.ai → produce `_data/data-YYYY-MM.json`
2. `run_monthly_pipeline.py` orchestra:
   - `estimate_reach.py` patcha reach YoY mancante
   - `build_static.py` genera HTML statico + aggiorna index
   - `git push` → GitHub Pages aggiorna in ~30-60s
3. Claude posta su Slack #aghc-report-mensile il link cliccabile

## Rigenera manualmente un mese (solo online)
```bash
python3 _scripts/run_monthly_pipeline.py \
  --year 2026 --month 4 \
  --raw-data _data/data-2026-04.json \
  --repo-root . \
  --token-file ~/.aghc/github_token
```

## Genera anche xlsx (legacy, ad-hoc)
Se serve un xlsx una tantum (es. export per cliente offline), aggiungere `--with-xlsx`:
```bash
python3 _scripts/run_monthly_pipeline.py \
  --year 2026 --month 4 \
  --raw-data _data/data-2026-04.json \
  --repo-root . \
  --token-file ~/.aghc/github_token \
  --with-xlsx \
  --senape-root ~/Desktop/SENAPE/Report\ AGHC
```

## Anagrafica clienti
Vedi `_scripts/anagrafica.py`. Quando cambia: aggiornare lì + ridistribuire.
