# Report AGHC — Archivio mensile

Snapshot statici dei report KPI mensili di AG Hotel Consulting (Meta + TikTok Advertising), generati e pubblicati automaticamente da [FMM Consulting](https://fmmconsulting.it).

🌐 **Online:** https://advfmosca.github.io/report-aghc-monthly/

## Struttura
- `index.html` — landing con l'elenco di tutti i mesi disponibili
- `aprile-2026.html`, `maggio-2026.html`, … — un report per mese
- `_data/` — JSON pre-elaborati dei dati Windsor.ai (input del generatore)
- `_scripts/build_static.py` — generatore HTML statico

## Come si rigenera
```bash
python3 _scripts/build_static.py --year 2026 --month 4 --data _data/data-2026-04.json
```

Lo script aggiorna anche automaticamente `index.html` con la nuova voce.

## Automazione
Il push mensile avviene tramite lo scheduled task `aghc-report-mensile-kpi` che:
1. Fetcha i dati da Windsor.ai per il mese chiuso
2. Salva il JSON in `_data/data-YYYY-MM.json`
3. Genera la pagina HTML
4. Committa e pusha sul repo, GitHub Pages aggiorna in ~30 secondi
