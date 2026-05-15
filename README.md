# Report AGHC — Archivio mensile

Snapshot statici dei report KPI mensili di AG Hotel Consulting (Meta + TikTok Advertising), realizzati da Francesco Maria Mosca.

🌐 **Online:** https://advfmosca.github.io/report-aghc-monthly/

## Struttura
- `index.html` — landing con elenco di tutti i mesi
- `<mese>-<anno>.html` — un report per mese (self-contained, dati baked-in)
- `_data/data-YYYY-MM.json` — dati Windsor.ai pre-aggregati
- `_scripts/` — generatore Python:
  - `run_monthly_pipeline.py` — orchestrator (xlsx + HTML + commit + push)
  - `estimate_reach.py` — stima reach YoY mancante (limite Meta API >24m)
  - `generate_sheet.py` — generatore xlsx
  - `postprocess_xlsx.py` — annotazioni xlsx (ⓘ stimata + 1° mese live)
  - `build_static.py` — generatore HTML statico
  - `anagrafica.py` — anagrafica 18 clienti AGHC

## Pipeline mensile (automatica via scheduled task)
1. Claude fetcha Windsor.ai → produce `_data/data-YYYY-MM.json` (raw, reach può essere null su YoY)
2. `run_monthly_pipeline.py` orchestra tutto:
   - `estimate_reach.py` patcha reach YoY mancante
   - `generate_sheet.py` genera xlsx
   - `postprocess_xlsx.py` aggiunge ⓘ + 1° mese live
   - `build_static.py` genera HTML
   - `git push` → GitHub Pages aggiorna
3. Claude posta su Slack #aghc-report-mensile il link cliccabile

## Rigenera manualmente un mese
```bash
python3 _scripts/run_monthly_pipeline.py \
  --year 2026 --month 4 \
  --raw-data _data/data-2026-04.json \
  --senape-root ~/Desktop/SENAPE/Report\ AGHC \
  --repo-root . \
  --token-file ~/.aghc/github_token
```

## Anagrafica clienti
Vedi `_scripts/anagrafica.py`. Quando cambia: aggiornare lì + ridistribuire.
