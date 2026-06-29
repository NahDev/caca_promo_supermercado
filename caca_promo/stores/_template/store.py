"""
Template para adicionar um novo supermercado na plataforma VIP Commerce.

1. Copie esta pasta para caca_promo/stores/<nome_do_mercado>/
2. Ajuste STORE_ID, SITE_URL e PLATFORM_CONFIG
3. Importe e chame register() em caca_promo/stores/loader.py

Para descobrir organization_id e domain_key:
- Abra o site /ofertas no navegador
- Inspecione requisições para services.vipcommerce.com.br
"""

from caca_promo.core.models import StoreConfig
from caca_promo.core.registry import StoreEntry, register_store
from caca_promo.stores.platforms.vipcommerce.config import VipCommerceConfig
from caca_promo.stores.platforms.vipcommerce.parser import VipCommerceParser
from caca_promo.stores.platforms.vipcommerce.scraper import VipCommerceScraper

STORE_ID = "meu_supermercado"
SITE_URL = "https://www.exemplo.com.br"

STORE_CONFIG = StoreConfig(
    store_id=STORE_ID,
    name="Meu Supermercado",
    platform="vipcommerce",
    site_url=SITE_URL,
    offers_url=f"{SITE_URL}/ofertas",
)

PLATFORM_CONFIG = VipCommerceConfig(
    organization_id="00",
    domain_key="exemplo.com.br",
    filial_id="1",
    distribution_center_id="1",
)


def register() -> None:
    register_store(
        StoreEntry(
            config=STORE_CONFIG,
            scraper=VipCommerceScraper(STORE_CONFIG, PLATFORM_CONFIG),
            parser=VipCommerceParser(STORE_CONFIG),
        )
    )
