from caca_promo.storage.database import (
    fetch_all_promotions,
    fetch_latest_scrape_timestamp,
    fetch_scrape_timestamps,
    init_database,
    save_promotions,
)

__all__ = [
    "fetch_all_promotions",
    "fetch_latest_scrape_timestamp",
    "fetch_scrape_timestamps",
    "init_database",
    "save_promotions",
]
