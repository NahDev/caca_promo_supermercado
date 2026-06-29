import logging
from datetime import datetime, timezone

import httpx

from caca_promo.core.models import ScrapeSummary, StoreConfig
from caca_promo.storage.database import save_promotions
from caca_promo.stores.platforms.gpa.config import GpaConfig

logger = logging.getLogger(__name__)


class GpaScraper:
    platform = "gpa"

    def __init__(self, config: StoreConfig, platform_config: GpaConfig):
        self.config = config
        self.platform_config = platform_config

    def fetch_offers_page(self, client: httpx.Client, page_number: int) -> dict:
        response = client.post(
            self.platform_config.special_page_url,
            json=self.platform_config.build_payload(page_number),
        )
        response.raise_for_status()
        return response.json()

    def scrape(self, max_pages: int | None = None) -> ScrapeSummary:
        scraped_at = datetime.now(timezone.utc).isoformat()
        headers = self.platform_config.build_headers(self.config.site_url)

        total_saved = 0
        total_pages = 0
        total_items = 0
        pages_to_fetch = 0

        with httpx.Client(headers=headers, timeout=60.0) as client:
            first_page = self.fetch_offers_page(client, 1)
            total_pages = first_page.get("totalPages", 1)
            total_items = first_page.get("totalProducts", len(first_page.get("products", [])))
            pages_to_fetch = total_pages if max_pages is None else min(total_pages, max_pages)

            logger.info(
                "Starting scrape for %s: %s items across %s pages (fetching %s pages)",
                self.config.store_id,
                total_items,
                total_pages,
                pages_to_fetch,
            )

            for page_number in range(1, pages_to_fetch + 1):
                page_data = first_page if page_number == 1 else self.fetch_offers_page(client, page_number)
                products = page_data.get("products", [])
                saved = save_promotions(
                    store_id=self.config.store_id,
                    products=products,
                    source_page=page_number,
                    scraped_at=scraped_at,
                )
                total_saved += saved
                logger.info(
                    "Store %s page %s/%s processed (%s products)",
                    self.config.store_id,
                    page_number,
                    pages_to_fetch,
                    len(products),
                )

        summary = ScrapeSummary(
            store_id=self.config.store_id,
            store_name=self.config.name,
            scraped_at=scraped_at,
            pages_fetched=pages_to_fetch,
            total_pages_available=total_pages,
            total_items_available=total_items,
            records_saved=total_saved,
        )
        logger.info("Scrape finished for %s: %s", self.config.store_id, summary.as_dict())
        return summary
