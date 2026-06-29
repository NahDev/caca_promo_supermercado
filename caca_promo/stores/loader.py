from caca_promo.core.registry import StoreEntry, register_store
from caca_promo.stores.jaguare import store as jaguare_store
from caca_promo.stores.mambo import store as mambo_store
from caca_promo.stores.paodeacucar import store as paodeacucar_store
from caca_promo.stores.pegpese import store as pegpese_store


def load_stores() -> None:
    pegpese_store.register()
    jaguare_store.register()
    paodeacucar_store.register()
    mambo_store.register()


def register_vtex_store(
    store_id: str,
    name: str,
    site_url: str,
    product_cluster_id: str,
    page_size: int = 50,
) -> None:
    from caca_promo.core.models import StoreConfig
    from caca_promo.stores.platforms.vtex.config import VtexConfig
    from caca_promo.stores.platforms.vtex.parser import VtexParser
    from caca_promo.stores.platforms.vtex.scraper import VtexScraper

    site_url = site_url.rstrip("/")
    store_config = StoreConfig(
        store_id=store_id,
        name=name,
        platform="vtex",
        site_url=site_url,
        offers_url=f"{site_url}/{product_cluster_id}?map=productClusterIds",
    )
    platform_config = VtexConfig(
        product_cluster_id=product_cluster_id,
        page_size=page_size,
    )

    register_store(
        StoreEntry(
            config=store_config,
            scraper=VtexScraper(store_config, platform_config),
            parser=VtexParser(store_config),
        )
    )


def register_gpa_store(
    store_id: str,
    name: str,
    site_url: str,
    brand_prefix: str,
    api_store_id: int,
    special_terms: str,
    results_per_page: int = 48,
) -> None:
    from caca_promo.core.models import StoreConfig
    from caca_promo.stores.platforms.gpa.config import GpaConfig
    from caca_promo.stores.platforms.gpa.parser import GpaParser
    from caca_promo.stores.platforms.gpa.scraper import GpaScraper

    site_url = site_url.rstrip("/")
    store_config = StoreConfig(
        store_id=store_id,
        name=name,
        platform="gpa",
        site_url=site_url,
        offers_url=f"{site_url}/especial/{special_terms}",
    )
    platform_config = GpaConfig(
        brand_prefix=brand_prefix,
        api_store_id=api_store_id,
        special_terms=special_terms,
        results_per_page=results_per_page,
    )

    register_store(
        StoreEntry(
            config=store_config,
            scraper=GpaScraper(store_config, platform_config),
            parser=GpaParser(store_config),
        )
    )


def register_vipcommerce_store(
    store_id: str,
    name: str,
    site_url: str,
    organization_id: str,
    domain_key: str,
    filial_id: str = "1",
    distribution_center_id: str = "1",
    login_key: str | None = "df072f85df9bf7dd71b6811c34bdbaa4f219d98775b56cff9dfa5f8ca1bf8469",
) -> None:
    from caca_promo.core.models import StoreConfig
    from caca_promo.stores.platforms.vipcommerce.config import VipCommerceConfig
    from caca_promo.stores.platforms.vipcommerce.parser import VipCommerceParser
    from caca_promo.stores.platforms.vipcommerce.scraper import VipCommerceScraper

    store_config = StoreConfig(
        store_id=store_id,
        name=name,
        platform="vipcommerce",
        site_url=site_url.rstrip("/"),
        offers_url=f"{site_url.rstrip('/')}/ofertas",
    )
    platform_config = VipCommerceConfig(
        organization_id=organization_id,
        domain_key=domain_key,
        filial_id=filial_id,
        distribution_center_id=distribution_center_id,
        login_key=login_key,
    )

    register_store(
        StoreEntry(
            config=store_config,
            scraper=VipCommerceScraper(store_config, platform_config),
            parser=VipCommerceParser(store_config),
        )
    )
