import logging
import math
from datetime import datetime, timezone

import httpx

from caca_promo.core.models import ScrapeSummary, StoreConfig
from caca_promo.storage.database import save_promotions
from caca_promo.stores.platforms.vtex.config import VtexConfig

logger = logging.getLogger(__name__)


class VtexScraper:
    platform = "vtex"

    def __init__(self, config: StoreConfig, platform_config: VtexConfig):
        self.config = config
        self.platform_config = platform_config
        self.search_url = f"{config.site_url.rstrip('/')}/api/catalog_system/pub/products/search"

    def fetch_offers_page(self, client: httpx.Client, page_number: int) -> tuple[list[dict], int]:
        start_index = (page_number - 1) * self.platform_config.page_size
        end_index = start_index + self.platform_config.page_size - 1
        response = client.get(
            self.search_url,
            params=self.platform_config.build_search_params(start_index, end_index),
        )
        response.raise_for_status()
        _, total_items = self.platform_config.parse_resources_header(response.headers.get("resources"))
        return response.json(), total_items

    def scrape(self, max_pages: int | None = None) -> ScrapeSummary:
        scraped_at = datetime.now(timezone.utc).isoformat()
        headers = self.platform_config.build_headers()

        total_saved = 0
        total_pages = 0
        total_items = 0
        pages_to_fetch = 0

        with httpx.Client(headers=headers, timeout=60.0) as client:
            first_products, total_items = self.fetch_offers_page(client, 1)
            total_pages = max(1, math.ceil(total_items / self.platform_config.page_size))
            pages_to_fetch = total_pages if max_pages is None else min(total_pages, max_pages)

            logger.info(
                "Starting scrape for %s: %s items across %s pages (fetching %s pages)",
                self.config.store_id,
                total_items,
                total_pages,
                pages_to_fetch,
            )

            for page_number in range(1, pages_to_fetch + 1):
                products = first_products if page_number == 1 else self.fetch_offers_page(client, page_number)[0]
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
