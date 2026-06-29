from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class StoreConfig:
    store_id: str
    name: str
    platform: str
    site_url: str
    offers_url: str


@dataclass
class ScrapeSummary:
    store_id: str
    store_name: str
    scraped_at: str
    pages_fetched: int
    total_pages_available: int
    total_items_available: int
    records_saved: int

    def as_dict(self) -> dict:
        return {
            "store_id": self.store_id,
            "store_name": self.store_name,
            "scraped_at": self.scraped_at,
            "pages_fetched": self.pages_fetched,
            "total_pages_available": self.total_pages_available,
            "total_items_available": self.total_items_available,
            "records_saved": self.records_saved,
        }


@dataclass
class PromotionDetails:
    product_id: int
    description: str
    product_url: str
    offer_name: str
    offer_tag: str
    old_price: float | None
    offer_price: float | None
    discount_percent: float | None
    savings: float | None
    unit: str
    available: bool
    sku: str
    barcode: str
    brand: str
    regular_price: float | None


class StoreScraper(Protocol):
    config: StoreConfig

    def scrape(self, max_pages: int | None = None) -> ScrapeSummary: ...


class PromotionParser(Protocol):
    config: StoreConfig

    def parse(self, raw_data: str, fallback_description: str = "") -> PromotionDetails: ...
