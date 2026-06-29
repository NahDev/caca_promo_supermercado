import csv
import logging
from datetime import datetime, timezone
from pathlib import Path

from caca_promo.config.settings import EXPORTS_DIR
from caca_promo.core.models import StoreConfig
from caca_promo.storage.database import fetch_all_promotions, fetch_latest_scrape_timestamp

logger = logging.getLogger(__name__)


def export_to_csv(
    store: StoreConfig,
    output_path: Path | None = None,
    scraped_at: str | None = None,
) -> Path:
    store_exports_dir = EXPORTS_DIR / store.store_id
    store_exports_dir.mkdir(parents=True, exist_ok=True)
    scraped_at = scraped_at or fetch_latest_scrape_timestamp(store.store_id)

    if not scraped_at:
        raise RuntimeError(f"Nenhuma promoção encontrada para {store.name}")

    rows = fetch_all_promotions(store_id=store.store_id, scraped_at=scraped_at)
    if not rows:
        raise RuntimeError(f"Nenhuma promoção encontrada para {store.name} no lote {scraped_at}")

    if output_path is None:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        output_path = store_exports_dir / f"promotions_{timestamp}.csv"

    fieldnames = [
        "id",
        "store_id",
        "product_id",
        "description",
        "raw_data",
        "source_page",
        "scraped_at",
    ]

    with output_path.open("w", newline="", encoding="utf-8-sig") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()

        for row in rows:
            writer.writerow(
                {
                    "id": row["id"],
                    "store_id": row["store_id"],
                    "product_id": row["product_id"],
                    "description": row["description"],
                    "raw_data": row["raw_data"],
                    "source_page": row["source_page"],
                    "scraped_at": row["scraped_at"],
                }
            )

    logger.info("Exported %s records to %s", len(rows), output_path)
    return output_path
