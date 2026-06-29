from caca_promo.core.models import StoreConfig
from caca_promo.core.registry import StoreEntry, register_store
from caca_promo.stores.platforms.vtex.config import VtexConfig
from caca_promo.stores.platforms.vtex.parser import VtexParser
from caca_promo.stores.platforms.vtex.scraper import VtexScraper

STORE_ID = "mambo"
SITE_URL = "https://www.mambo.com.br"
PRODUCT_CLUSTER_ID = "162"

STORE_CONFIG = StoreConfig(
    store_id=STORE_ID,
    name="Mambo Supermercado",
    platform="vtex",
    site_url=SITE_URL,
    offers_url=f"{SITE_URL}/{PRODUCT_CLUSTER_ID}?map=productClusterIds",
)

PLATFORM_CONFIG = VtexConfig(
    product_cluster_id=PRODUCT_CLUSTER_ID,
    page_size=50,
)


def register() -> None:
    register_store(
        StoreEntry(
            config=STORE_CONFIG,
            scraper=VtexScraper(STORE_CONFIG, PLATFORM_CONFIG),
            parser=VtexParser(STORE_CONFIG),
        )
    )
