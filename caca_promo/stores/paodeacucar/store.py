from caca_promo.core.models import StoreConfig
from caca_promo.core.registry import StoreEntry, register_store
from caca_promo.stores.platforms.gpa.config import GpaConfig
from caca_promo.stores.platforms.gpa.parser import GpaParser
from caca_promo.stores.platforms.gpa.scraper import GpaScraper

STORE_ID = "paodeacucar"
SITE_URL = "https://www.paodeacucar.com"
SPECIAL_SLUG = "ofertasdodia-pao2023"

STORE_CONFIG = StoreConfig(
    store_id=STORE_ID,
    name="Pão de Açúcar",
    platform="gpa",
    site_url=SITE_URL,
    offers_url=f"{SITE_URL}/especial/{SPECIAL_SLUG}",
)

PLATFORM_CONFIG = GpaConfig(
    brand_prefix="pa",
    api_store_id=461,
    special_terms=SPECIAL_SLUG,
)


def register() -> None:
    register_store(
        StoreEntry(
            config=STORE_CONFIG,
            scraper=GpaScraper(STORE_CONFIG, PLATFORM_CONFIG),
            parser=GpaParser(STORE_CONFIG),
        )
    )
