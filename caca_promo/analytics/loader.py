import pandas as pd

from caca_promo.core.registry import get_all_store_ids, get_store
from caca_promo.storage.database import (
    fetch_latest_scrape_timestamps_all_stores,
    fetch_promotions_for_stores,
    fetch_scrape_timestamps,
)


def _promotion_to_row(store_id: str, store_name: str, scraped_at: str, promotion) -> dict:
    return {
        "store_id": store_id,
        "store_name": store_name,
        "scraped_at": scraped_at,
        "product_id": promotion.product_id,
        "description": promotion.description,
        "product_url": promotion.product_url,
        "offer_name": promotion.offer_name,
        "offer_tag": promotion.offer_tag,
        "offer_price": promotion.offer_price,
        "old_price": promotion.old_price,
        "discount_percent": promotion.discount_percent,
        "savings": promotion.savings,
        "unit": promotion.unit,
        "available": promotion.available,
        "sku": promotion.sku,
        "barcode": promotion.barcode,
        "brand": promotion.brand,
        "regular_price": promotion.regular_price,
    }


def resolve_scraped_at_map(
    store_ids: list[str],
    scraped_at_map: dict[str, str] | None = None,
) -> dict[str, str]:
    if scraped_at_map:
        return {store_id: scraped_at_map[store_id] for store_id in store_ids if store_id in scraped_at_map}

    latest_map = fetch_latest_scrape_timestamps_all_stores()
    return {store_id: latest_map[store_id] for store_id in store_ids if store_id in latest_map}


def load_promotions_dataframe(
    store_ids: list[str] | None = None,
    scraped_at_map: dict[str, str] | None = None,
) -> pd.DataFrame:
    store_ids = store_ids or get_all_store_ids()
    batch_map = resolve_scraped_at_map(store_ids, scraped_at_map)
    if not batch_map:
        return pd.DataFrame()

    rows = fetch_promotions_for_stores(list(batch_map.keys()), batch_map)
    records = []

    for row in rows:
        store_id = row["store_id"]
        entry = get_store(store_id)
        promotion = entry.parser.parse(row["raw_data"], row["description"])
        records.append(
            _promotion_to_row(
                store_id,
                entry.config.name,
                batch_map[store_id],
                promotion,
            )
        )

    return pd.DataFrame(records)


def load_historical_dataframe(store_ids: list[str] | None = None) -> pd.DataFrame:
    store_ids = store_ids or get_all_store_ids()
    records = []

    for store_id in store_ids:
        entry = get_store(store_id)
        for scraped_at in fetch_scrape_timestamps(store_id):
            batch_rows = fetch_promotions_for_stores([store_id], {store_id: scraped_at})
            for row in batch_rows:
                promotion = entry.parser.parse(row["raw_data"], row["description"])
                records.append(
                    _promotion_to_row(
                        store_id,
                        entry.config.name,
                        scraped_at,
                        promotion,
                    )
                )

    return pd.DataFrame(records)
