from caca_promo.core.models import StoreConfig
from caca_promo.core.registry import StoreEntry, register_store
from caca_promo.stores.platforms.vipcommerce.config import VipCommerceConfig
from caca_promo.stores.platforms.vipcommerce.parser import VipCommerceParser
from caca_promo.stores.platforms.vipcommerce.scraper import VipCommerceScraper

STORE_ID = "jaguare"
SITE_URL = "https://www.supermercadojaguare.com.br"

STORE_CONFIG = StoreConfig(
    store_id=STORE_ID,
    name="Supermercado Jaguaré",
    platform="vipcommerce",
    site_url=SITE_URL,
    offers_url=f"{SITE_URL}/ofertas",
)

PLATFORM_CONFIG = VipCommerceConfig(
    organization_id="244",
    domain_key="supermercadojaguare.com.br",
    filial_id="1",
    distribution_center_id="1",
    login_key="df072f85df9bf7dd71b6811c34bdbaa4f219d98775b56cff9dfa5f8ca1bf8469",
)


def register() -> None:
    register_store(
        StoreEntry(
            config=STORE_CONFIG,
            scraper=VipCommerceScraper(STORE_CONFIG, PLATFORM_CONFIG),
            parser=VipCommerceParser(STORE_CONFIG),
        )
    )
