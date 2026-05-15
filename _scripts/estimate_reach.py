#!/usr/bin/env python3
"""estimate_reach.py — Stima reach Aprile-anno-precedente quando Meta API restituisce null.

La Meta Marketing API non restituisce più reach per periodi >24 mesi. Per i clienti con
confronto YoY questo causa "n/d" sul KPI Reach. Questo script post-processa il JSON dati
(in-place) e patcha i valori reach mancanti applicando il rapporto reach/impressions del
periodo corrente — fallback su MoM se il corrente non è utilizzabile.

Uso:
  python3 estimate_reach.py --data <data.json>

Modifica il file in-place e segna `reach_estimated: true` sui clienti affected (per la UI).
"""
import argparse, json
from pathlib import Path

PLATFORMS = ("facebook", "instagram")

# Set di account/clienti per cui il confronto Meta è YoY (replica anagrafica)
YOY_ACCOUNTS = {"911357333863123", "687349689221880"}  # Della Piana, Lunetta
YOY_FILTERED = {"Accentodì", "Adèsso", "Hannah", "Marcella Royal", "Terrazza Flavia"}


def ratio_or_none(d, plat):
    impr = (d.get(plat, {}).get("impressions") or 0)
    reach = (d.get(plat, {}).get("reach") or 0)
    if impr > 0 and reach > 0:
        return reach / impr
    return None


def estimate_block(target, refs):
    """target = blocco prev_yoy {facebook:{...}, instagram:{...}}, refs = [current, prev_mom]."""
    any_estimated = False
    for plat in PLATFORMS:
        t = target.get(plat) or {}
        impr_yoy = (t.get("impressions") or 0)
        reach_yoy = (t.get("reach") or 0)
        if impr_yoy <= 0 or reach_yoy > 0:
            continue  # niente da stimare
        ratio = None
        for r in refs:
            if not r:
                continue
            ratio = ratio_or_none(r, plat)
            if ratio is not None:
                break
        if ratio is None:
            continue
        est = min(impr_yoy * ratio, impr_yoy)
        t["reach"] = round(est)
        target[plat] = t
        any_estimated = True
    return any_estimated


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--data", required=True)
    args = p.parse_args()
    path = Path(args.data)
    data = json.loads(path.read_text(encoding="utf-8"))

    affected = []

    # Account non-shared YoY
    for acc_id in YOY_ACCOUNTS:
        target = data.get("meta_by_account", {}).get("prev_yoy", {}).get(acc_id)
        cur = data.get("meta_by_account", {}).get("current", {}).get(acc_id)
        mom = data.get("meta_by_account", {}).get("prev_mom", {}).get(acc_id)
        if target:
            if estimate_block(target, [cur, mom]):
                affected.append(acc_id)

    # Filtered (account condivisi)
    for nm in YOY_FILTERED:
        f = data.get("meta_filtered", {}).get(nm)
        if f and f.get("prev_yoy"):
            if estimate_block(f["prev_yoy"], [f.get("current"), f.get("prev_mom")]):
                affected.append(nm)

    # Annota su data['reach_estimated_clients'] per la UI
    if affected:
        # Mappa account_id → nome cliente per i 2 non-shared
        ACCOUNT_TO_NAME = {"911357333863123": "Della Piana", "687349689221880": "Lunetta"}
        affected_names = sorted({ACCOUNT_TO_NAME.get(a, a) for a in affected})
        data["reach_estimated_clients"] = affected_names
        print(f"✔ Reach YoY stimata per: {', '.join(affected_names)}")
    else:
        data["reach_estimated_clients"] = []
        print("ℹ Nessuna stima reach necessaria (tutti i valori YoY già presenti)")

    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
