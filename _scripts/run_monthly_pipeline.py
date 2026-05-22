#!/usr/bin/env python3
"""run_monthly_pipeline.py — Pipeline mensile AGHC.

DEFAULT (dal 22/05/2026 — multi-output + manifest Canva):
  1. Stima reach YoY mancante (idempotente, in-place sul JSON dati)
  2. Copia JSON in <repo>/_data/data-YYYY-MM.json
  3. Genera HTML statico in <repo>/<mese>-<anno>.html + aggiorna index.html
  4. Genera PNG tabelle (3 per cliente) in <reports-root>/<Mese Anno>/Tables/<Cliente>/
  5. Genera data dump MD in <reports-root>/<Mese Anno>/Dynamic Data/<Cliente>.md
  6. Mirror PNG → <repo>/assets/<slug>/<cliente>/ + genera manifest-YYYY-MM.json per Canva
  7. git add + commit + push (GitHub Pages aggiorna in ~30-60s)
  8. Stampa su stdout i link finali per Slack + MANIFEST_URL per Canva orchestration

LEGACY OPZIONALE (--with-xlsx):
  Aggiunge la generazione del file xlsx in <reports-root>/<Mese Anno>/ con post-processing
  (ⓘ stimata + 1° mese live). Utile per export ad-hoc, NON usato dallo scheduled task.

NB: NON fa fetch Windsor.ai — quello deve farlo Claude prima e passare il JSON via --raw-data.

Esempi:
  # Pipeline standard (online-only)
  python3 run_monthly_pipeline.py --year 2026 --month 5 \\
    --raw-data /tmp/data_may_2026.json \\
    --repo-root /tmp/aghc/report-aghc-monthly \\
    --token-file ~/.aghc/github_token

  # Pipeline + xlsx legacy (ad-hoc export)
  python3 run_monthly_pipeline.py --year 2026 --month 5 \\
    --raw-data /tmp/data_may_2026.json \\
    --repo-root /tmp/aghc/report-aghc-monthly \\
    --token-file ~/.aghc/github_token \\
    --with-xlsx --senape-root ~/Desktop/SENAPE/Report\\ AGHC
"""
import argparse, json, subprocess, shutil, sys
from pathlib import Path

MONTH_IT = {1:"Gennaio",2:"Febbraio",3:"Marzo",4:"Aprile",5:"Maggio",6:"Giugno",
            7:"Luglio",8:"Agosto",9:"Settembre",10:"Ottobre",11:"Novembre",12:"Dicembre"}

REPO_URL = "https://advfmosca.github.io/report-aghc-monthly"


def run(cmd, cwd=None, check=True, capture=False):
    if capture:
        r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
        if check and r.returncode != 0:
            sys.stderr.write(f"FAIL: {cmd}\n{r.stderr}\n")
            sys.exit(r.returncode)
        return r.stdout.strip()
    return subprocess.run(cmd, cwd=cwd, check=check)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--year", type=int, required=True)
    p.add_argument("--month", type=int, required=True)
    p.add_argument("--raw-data", required=True, help="JSON dati Windsor pre-aggregati")
    p.add_argument("--repo-root", required=True, help="checkout locale del repo report-aghc-monthly")
    p.add_argument("--token-file", required=True, help="path al file con il PAT GitHub")
    p.add_argument("--reports-root", required=True,
                   help="Root cartella outputs locali (PNG + MD); es. ~/Desktop/COWORK\\ FMM/Report\\ AGHC")
    p.add_argument("--with-xlsx", action="store_true",
                   help="LEGACY: genera anche l'xlsx in --reports-root (default off)")
    p.add_argument("--senape-root", default=None,
                   help="DEPRECATED alias di --reports-root; usato solo per compatibilità storica")
    p.add_argument("--skip-png-md", action="store_true",
                   help="Salta generazione PNG + MD (per debug rapido)")
    p.add_argument("--skip-push", action="store_true")
    args = p.parse_args()

    # Compatibility alias: se l'utente passa --senape-root invece di --reports-root
    reports_root_arg = args.reports_root or args.senape_root
    if not reports_root_arg:
        sys.stderr.write("ERRORE: --reports-root richiesto\n")
        sys.exit(2)

    year, month = args.year, args.month
    mese_it = MONTH_IT[month]
    period_label = f"{mese_it} {year}"
    slug = f"{mese_it.lower()}-{year}"

    raw_path = Path(args.raw_data).resolve()
    repo_root = Path(args.repo_root).resolve()
    scripts = repo_root / "_scripts"
    reports_root = Path(reports_root_arg).resolve()
    reports_root.mkdir(parents=True, exist_ok=True)
    period_dir = reports_root / period_label
    period_dir.mkdir(parents=True, exist_ok=True)
    xlsx_path = None

    # Step count dinamico
    has_png_md = not args.skip_png_md
    # +1 step in più se has_png_md (mirror PNG + manifest Canva)
    total_steps = 4 + (2 if args.with_xlsx else 0) + (3 if has_png_md else 0)
    step = 0
    manifest_path = None
    manifest_url = None
    design_title = None
    def label(n, t): return f"\n[{n}/{total_steps}] {t}"

    # 1. Stima reach (idempotente)
    step += 1
    print(label(step, f"Stima reach YoY su {raw_path.name}…"))
    run(["python3", str(scripts / "estimate_reach.py"), "--data", str(raw_path)])

    # 2. (Opzionale) xlsx
    if args.with_xlsx:
        xlsx_path = period_dir / f"Report AGHC - KPI {period_label}.xlsx"
        step += 1
        print(label(step, f"[LEGACY] Genero xlsx → {xlsx_path}"))
        run(["python3", str(scripts / "generate_sheet.py"), str(raw_path), str(year), str(month), str(xlsx_path)])
        step += 1
        print(label(step, "[LEGACY] Post-processing xlsx (ⓘ stimata + 1° mese live)…"))
        run(["python3", str(scripts / "postprocess_xlsx.py"),
             "--xlsx", str(xlsx_path), "--data", str(raw_path),
             "--year", str(year), "--month", str(month)])

    # 3. Copia JSON nel repo (single source of truth) — skip se è già lì
    step += 1
    repo_data_path = repo_root / "_data" / f"data-{year}-{month:02d}.json"
    repo_data_path.parent.mkdir(exist_ok=True)
    if raw_path.resolve() != repo_data_path.resolve():
        shutil.copy(raw_path, repo_data_path)
        print(label(step, f"JSON copiato in repo: {repo_data_path.relative_to(repo_root)}"))
    else:
        print(label(step, f"JSON già nel repo: {repo_data_path.relative_to(repo_root)} (no copy)"))

    # 4. Genera HTML statico
    step += 1
    print(label(step, "Genero HTML statico (dashboard online)…"))
    run(["python3", str(scripts / "build_static.py"),
         "--year", str(year), "--month", str(month),
         "--data", str(repo_data_path.relative_to(repo_root))],
        cwd=str(repo_root))

    # 4.5. Genera PNG tabelle + data dump MD per i 18 clienti
    if has_png_md:
        step += 1
        tables_dir = period_dir / "Tables"
        print(label(step, f"Genero PNG tabelle → {tables_dir} (18 clienti × 3 PNG)…"))
        run(["python3", str(scripts / "build_tables.py"),
             "--year", str(year), "--month", str(month),
             "--data", str(repo_data_path),
             "--output-dir", str(tables_dir)])
        step += 1
        md_dir = period_dir / "Dynamic Data"
        print(label(step, f"Genero data dump MD → {md_dir} (18 clienti)…"))
        run(["python3", str(scripts / "build_data_dump.py"),
             "--year", str(year), "--month", str(month),
             "--data", str(repo_data_path),
             "--output-dir", str(md_dir)])

        # 4.6. Mirror PNG nel repo + genera manifest Canva
        step += 1
        print(label(step, f"Mirror PNG in <repo>/assets/ + genero manifest Canva…"))
        run(["python3", str(scripts / "build_canva_manifest.py"),
             "--year", str(year), "--month", str(month),
             "--tables-root", str(tables_dir),
             "--repo-root", str(repo_root)])
        manifest_path = repo_root / "_data" / f"manifest-{year}-{month:02d}.json"
        manifest_url = f"{REPO_URL}/_data/manifest-{year}-{month:02d}.json"
        design_title = f"Report AGHC – {period_label}"

    # 5. Push (o skip)
    step += 1
    if args.skip_push:
        print(label(step, "--skip-push attivo, niente push."))
    else:
        print(label(step, "Commit + push…"))
        run(["git", "config", "--local", "credential.helper",
             f'!f() {{ echo "username=advfmosca"; echo "password=$(tr -d \\\\n < {args.token_file})"; }}; f'],
            cwd=str(repo_root))
        run(["git", "add", "-A"], cwd=str(repo_root))
        status = run(["git", "status", "--porcelain"], cwd=str(repo_root), capture=True)
        if not status:
            print("ℹ Nessuna modifica da committare (eseguito già?)")
        else:
            run(["git", "commit", "-m", f"Report {period_label} — pubblicazione automatica"],
                cwd=str(repo_root))
            run(["git", "push", "origin", "main"], cwd=str(repo_root))
            print("✔ Push completato — GitHub Pages aggiorna in ~30-60s")

    # 6. Output finale
    public_url = f"{REPO_URL}/{slug}"
    archive_url = f"{REPO_URL}/"
    print(f"\n========================================")
    print(f"PIPELINE_DONE")
    print(f"PERIOD={period_label}")
    print(f"PUBLIC_URL={public_url}")
    print(f"ARCHIVE_URL={archive_url}")
    if has_png_md:
        print(f"TABLES_DIR={period_dir / 'Tables'}")
        print(f"MD_DIR={period_dir / 'Dynamic Data'}")
        if manifest_url:
            print(f"MANIFEST_URL={manifest_url}")
            print(f"MANIFEST_PATH={manifest_path}")
            print(f"CANVA_DESIGN_TITLE={design_title}")
    if xlsx_path:
        print(f"XLSX_PATH={xlsx_path}")
        print(f"XLSX_LINK=computer://{xlsx_path}")
    print(f"========================================")


if __name__ == "__main__":
    main()
