#!/usr/bin/env python3
"""apply_ytd_overrides.py — Backfill idempotente dei valori YTD spend che Windsor
smette di restituire per mesi chiusi (data retention).

Legge _data/ytd_overrides.json e patcha in-place data['ytd_spend']['by_client'].
Semantica backfill: imposta il valore SOLO se quello corrente e' 0/mancante,
cosi' non sovrascrive mai dati reali eventualmente restituiti da Windsor.

Uso: python3 apply_ytd_overrides.py --data <data.json> [--overrides <ytd_overrides.json>]
"""
import argparse, json
from pathlib import Path

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--overrides", default=None)
    args = ap.parse_args()
    data_path = Path(args.data)
    ov_path = Path(args.overrides) if args.overrides else data_path.parent.parent / "_data" / "ytd_overrides.json"
    if not ov_path.exists():
        # fallback: accanto allo script → repo/_data
        ov_path = Path(__file__).resolve().parent.parent / "_data" / "ytd_overrides.json"
    if not ov_path.exists():
        print("ℹ Nessun file ytd_overrides.json trovato — skip"); return

    data = json.loads(data_path.read_text(encoding="utf-8"))
    ov = json.loads(ov_path.read_text(encoding="utf-8")).get("overrides", {})
    byc = data.setdefault("ytd_spend", {}).setdefault("by_client", {})
    months = data["ytd_spend"].setdefault("months", [])
    applied = []
    for client, mmap in ov.items():
        if client not in byc:
            continue  # cliente non presente nel report di questo mese
        for mth, chans in mmap.items():
            mi = int(mth)
            if mi not in months:
                continue  # mese fuori dal range YTD corrente
            cell = byc[client].setdefault(mth, {"meta": 0, "tiktok": 0})
            for chan, val in chans.items():
                cur = cell.get(chan) or 0
                if cur == 0:
                    cell[chan] = val
                    applied.append(f"{client} m{mth} {chan}={val}")
    data_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    if applied:
        print("✔ YTD override applicati:", "; ".join(applied))
    else:
        print("ℹ YTD override: nessun backfill necessario (valori gia' presenti)")

if __name__ == "__main__":
    main()
