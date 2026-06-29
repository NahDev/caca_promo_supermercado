import logging
from datetime import datetime, timezone

import httpx
from playwright.sync_api import sync_playwright

from caca_promo.core.models import ScrapeSummary, StoreConfig
from caca_promo.storage.database import save_promotions
from caca_promo.stores.platforms.vipcommerce.config import VipCommerceConfig

logger = logging.getLogger(__name__)


class VipCommerceScraper:
    platform = "vipcommerce"

    def __init__(self, config: StoreConfig, platform_config: VipCommerceConfig):
        self.config = config
        self.platform_config = platform_config

    def get_auth_token_via_api(self) -> str:
        headers = self.platform_config.build_headers(self.config.site_url)
        response = httpx.post(
            self.platform_config.login_url,
            headers=headers,
            json=self.platform_config.build_login_payload(),
            timeout=30.0,
        )
        response.raise_for_status()
        body = response.json()
        token = body.get("data") if body.get("success") else None
        if not token:
            raise RuntimeError(f"Login API failed for store {self.config.store_id}: {body}")
        logger.info("Authentication token obtained via API for store %s", self.config.store_id)
        return token

    def get_auth_token_via_browser(self) -> str:
        token_holder: dict[str, str] = {}

        def on_response(response):
            if "auth/loja/login" not in response.url:
                return
            try:
                body = response.json()
                if body.get("success") and body.get("data"):
                    token_holder["token"] = body["data"]
            except Exception as exc:
                logger.warning("Failed to parse login response: %s", exc)

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page()
            page.on("response", on_response)
            page.goto(self.config.offers_url, wait_until="networkidle", timeout=90000)
            page.wait_for_timeout(2000)
            browser.close()

        token = token_holder.get("token")
        if not token:
            raise RuntimeError(
                f"Could not obtain authentication token for store {self.config.store_id}"
            )

        logger.info("Authentication token obtained via browser for store %s", self.config.store_id)
        return token

    def get_auth_token(self) -> str:
        if self.platform_config.login_key:
            try:
                return self.get_auth_token_via_api()
            except Exception as exc:
                logger.warning(
                    "API login failed for %s, falling back to browser: %s",
                    self.config.store_id,
                    exc,
                )
        return self.get_auth_token_via_browser()

    def fetch_offers_page(self, client: httpx.Client, page_number: int) -> dict:
        response = client.get(self.platform_config.offers_api_url, params={"page": page_number})
        response.raise_for_status()
        body = response.json()

        if not body.get("success"):
            raise RuntimeError(
                f"API returned unsuccessful response for {self.config.store_id} page {page_number}"
            )

        return body

    def scrape(self, max_pages: int | None = None) -> ScrapeSummary:
        scraped_at = datetime.now(timezone.utc).isoformat()
        token = self.get_auth_token()
        headers = self.platform_config.build_headers(self.config.site_url, token)

        total_saved = 0
        total_pages = 0
        total_items = 0
        pages_to_fetch = 0

        with httpx.Client(headers=headers, timeout=60.0) as client:
            first_page = self.fetch_offers_page(client, 1)
            paginator = first_page.get("paginator", {})
            total_pages = paginator.get("total_pages", 1)
            total_items = paginator.get("total_items", len(first_page.get("data", [])))
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
                products = page_data.get("data", [])
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
