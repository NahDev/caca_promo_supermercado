import argparse
import logging
import subprocess
import sys
from pathlib import Path

from caca_promo.core.registry import get_all_store_ids, get_store, list_stores
from caca_promo.export.csv_export import export_to_csv
from caca_promo.report.builder import generate_report
from caca_promo.report.competitive import generate_competitive_report
from caca_promo.storage.database import init_database
from caca_promo.stores.loader import load_stores


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


def resolve_store_ids(store_arg: str | None) -> list[str]:
    if not store_arg or store_arg == "all":
        return get_all_store_ids()
    return [store_arg]


def run_scrape(store_ids: list[str], max_pages: int | None) -> list[dict]:
    results = []
    for store_id in store_ids:
        try:
            entry = get_store(store_id)
            summary = entry.scraper.scrape(max_pages=max_pages)
            results.append(summary.as_dict())
        except Exception as exc:
            logging.getLogger(__name__).error("Scrape failed for %s: %s", store_id, exc)
            results.append({"store_id": store_id, "error": str(exc)})
    return results


def run_export(store_ids: list[str], scraped_at: str | None) -> list[dict]:
    results = []
    for store_id in store_ids:
        entry = get_store(store_id)
        batch = scraped_at or None
        csv_path = export_to_csv(entry.config, scraped_at=batch)
        results.append({"store_id": store_id, "csv_path": str(csv_path)})
    return results


def run_report(store_ids: list[str], scraped_at: str | None) -> list[dict]:
    results = []
    for store_id in store_ids:
        entry = get_store(store_id)
        report_path = generate_report(entry.config, entry.parser, scraped_at=scraped_at)
        results.append({"store_id": store_id, "report_path": str(report_path)})
    return results


def run_dashboard() -> None:
    dashboard_path = Path(__file__).resolve().parent / "caca_promo" / "dashboard" / "app.py"
    subprocess.run(
        [sys.executable, "-m", "streamlit", "run", str(dashboard_path)],
        check=False,
    )


def run_competitive_report(anchor_store_id: str, store_ids: list[str]) -> dict:
    report_path = generate_competitive_report(anchor_store_id, store_ids=store_ids)
    return {"anchor_store_id": anchor_store_id, "report_path": str(report_path)}


def start() -> None:
    setup_logging()
    load_stores()
    init_database()

    store_ids_available = get_all_store_ids()
    parser = argparse.ArgumentParser(description="Scraper de promoções de supermercados")
    parser.add_argument(
        "command",
        choices=["list-stores", "scrape", "export", "report", "all", "dashboard", "competitive-report"],
        help=(
            "list-stores: supermercados disponíveis | scrape: coletar | "
            "export: csv | report: relatório | all: pipeline completo | "
            "dashboard: dashboard B2B | competitive-report: relatório competitivo"
        ),
    )
    parser.add_argument(
        "--store",
        type=str,
        default="pegpese",
        help=f"ID do supermercado ou 'all' para todos (padrão: pegpese). Disponíveis: {', '.join(store_ids_available)}",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=None,
        help="Limita páginas da API durante o scrape (útil para testes)",
    )
    parser.add_argument(
        "--scraped-at",
        type=str,
        default=None,
        help="Timestamp do lote para export/report (padrão: último lote do supermercado)",
    )
    parser.add_argument(
        "--anchor",
        type=str,
        default="pegpese",
        help="Loja âncora para competitive-report (padrão: pegpese)",
    )

    args = parser.parse_args()

    if args.command == "dashboard":
        run_dashboard()
        return

    if args.command == "list-stores":
        stores = list_stores()
        for store in stores:
            print(f"{store.store_id:20} | {store.name:30} | {store.platform:12} | {store.offers_url}")
        return

    store_ids = resolve_store_ids(args.store)
    for store_id in store_ids:
        get_store(store_id)

    if args.command == "scrape":
        print(run_scrape(store_ids, args.max_pages))
        return

    if args.command == "export":
        print(run_export(store_ids, args.scraped_at))
        return

    if args.command == "report":
        print(run_report(store_ids, args.scraped_at))
        return

    if args.command == "competitive-report":
        get_store(args.anchor)
        print(run_competitive_report(args.anchor, store_ids))
        return

    if args.command == "all":
        scrape_results = run_scrape(store_ids, args.max_pages)
        export_results = []
        report_results = []

        for summary in scrape_results:
            if summary.get("error"):
                continue
            store_id = summary["store_id"]
            entry = get_store(store_id)
            try:
                csv_path = export_to_csv(entry.config, scraped_at=summary["scraped_at"])
                report_path = generate_report(
                    entry.config,
                    entry.parser,
                    scraped_at=summary["scraped_at"],
                )
                export_results.append({"store_id": store_id, "csv_path": str(csv_path)})
                report_results.append({"store_id": store_id, "report_path": str(report_path)})
            except Exception as exc:
                logging.getLogger(__name__).error("Export/report failed for %s: %s", store_id, exc)

        print(
            {
                "scrape": scrape_results,
                "export": export_results,
                "report": report_results,
            }
        )
        return

    sys.exit(1)


if __name__ == "__main__":
    start()
