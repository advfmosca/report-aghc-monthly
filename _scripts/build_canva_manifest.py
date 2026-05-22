#!/usr/bin/env python3
"""build_canva_manifest.py — Mirror PNG tabelle nel repo + genera manifest JSON per Canva.

Per ogni cliente nell'anagrafica:
  1. Cerca i PNG già generati in <tables-root>/<Cliente>/01_meta.png, 02_tiktok.png (se attivo), 03_budget.png
  2. Li copia in <repo>/assets/<slug-periodo>/<slug-cliente>/<name>.png
  3. Costruisce un manifest JSON con la lista ordinata di slide per il file Canva mensile

Output stdout: path del manifest generato.

Esempio:
  python3 build_canva_manifest.py --year 2026 --month 5 \\
    --tables-root "~/Desktop/COWORK FMM/Report AGHC/Maggio 2026/Tables" \\
    --repo-root /tmp/aghc_work/report-aghc-monthly
"""
import argparse, json, re, shutil, sys, unicodedata
from pathlib import Path

# Import anagrafica dal repo
sys.path.insert(0, str(Path(__file__).parent))
from anagrafica import CLIENTS, MONTH_IT  # type: ignore

BASE_URL = "https://advfmosca.github.io/report-aghc-monthly"


def slugify(value: str) -> str:
    """Trasforma 'Hannah Terraces' → 'hannah-terraces', 'Accentodì' → 'accentodi'."""
    value = unicodedata.normalize("NFKD", value)
    value = value.encode("ascii", "ignore").decode("ascii")
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "-", value).strip("-")
    return value


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--year", type=int, required=True)
    p.add_argument("--month", type=int, required=True)
    p.add_argument("--tables-root", required=True,
                   help="Cartella locale con i PNG già generati (es. ~/Desktop/COWORK FMM/Report AGHC/<Mese Anno>/Tables)")
    p.add_argument("--repo-root", required=True,
                   help="Checkout locale del repo report-aghc-monthly")
    args = p.parse_args()

    year, month = args.year, args.month
    mese_it = MONTH_IT[month]
    mese_upper = mese_it.upper()
    period_label = f"{mese_it} {year}"
    period_slug = f"{mese_it.lower()}-{year}"

    tables_root = Path(args.tables_root).expanduser().resolve()
    repo_root = Path(args.repo_root).resolve()
    assets_dir = repo_root / "assets" / period_slug
    manifest_path = repo_root / "_data" / f"manifest-{year}-{month:02d}.json"

    assets_dir.mkdir(parents=True, exist_ok=True)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    clients_payload = []
    missing = []
    mirrored_total = 0

    for c in CLIENTS:
        nome = c["nome"]
        client_slug = slugify(nome)
        client_tables = tables_root / nome
        client_assets = assets_dir / client_slug
        client_assets.mkdir(parents=True, exist_ok=True)

        # Determina PNG attesi: 01_meta sempre, 02_tiktok se attivo, 03_budget sempre
        expected = ["01_meta.png", "03_budget.png"]
        if c.get("tiktok_account_id"):
            expected.insert(1, "02_tiktok.png")

        pages = [
            {
                "type": "divider",
                "text": f"INIZIO REPORT — {nome.upper()} — {mese_upper} {year}",
            }
        ]

        for fname in expected:
            src = client_tables / fname
            if not src.exists():
                missing.append(f"{nome}/{fname}")
                continue
            dst = client_assets / fname
            shutil.copy2(src, dst)
            mirrored_total += 1
            pages.append({
                "type": "image",
                "url": f"{BASE_URL}/assets/{period_slug}/{client_slug}/{fname}",
                "local_path": str(dst),
                "kind": fname.split("_", 1)[1].split(".")[0],  # meta | tiktok | budget
            })

        pages.append({
            "type": "divider",
            "text": f"FINE REPORT — {nome.upper()} — {mese_upper} {year}",
        })

        clients_payload.append({
            "nome": nome,
            "slug": client_slug,
            "tiktok_active": bool(c.get("tiktok_account_id")),
            "pages": pages,
        })

    manifest = {
        "period_label": period_label,
        "period_slug": period_slug,
        "year": year,
        "month": month,
        "design_title": f"Report AGHC – {period_label}",
        "design_dimensions": {"width": 1920, "height": 1080, "preset": "Presentation_16_9"},
        "divider_style": {
            "background_color": "#FFFFFF",
            "text_color": "#000000",
            "font_weight": "bold",
            "text_align": "center",
            "font_size_pt": 56,
            "note": "Minimal: testo nero centrato su sfondo bianco",
        },
        "base_url": BASE_URL,
        "assets_root": f"{BASE_URL}/assets/{period_slug}",
        "total_clients": len(clients_payload),
        "total_pages": sum(len(c["pages"]) for c in clients_payload),
        "mirrored_pngs": mirrored_total,
        "missing_pngs": missing,
        "clients": clients_payload,
    }

    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"MANIFEST_PATH={manifest_path}")
    print(f"MANIFEST_URL={BASE_URL}/_data/manifest-{year}-{month:02d}.json")
    print(f"ASSETS_DIR={assets_dir}")
    print(f"TOTAL_CLIENTS={len(clients_payload)}")
    print(f"TOTAL_PAGES={manifest['total_pages']}")
    print(f"MIRRORED_PNGS={mirrored_total}")
    if missing:
        print(f"MISSING_PNGS_COUNT={len(missing)}")
        for m in missing:
            print(f"  - {m}")


if __name__ == "__main__":
    main()
