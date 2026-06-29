from dataclasses import dataclass

from caca_promo.core.models import PromotionParser, StoreConfig, StoreScraper


@dataclass
class StoreEntry:
    config: StoreConfig
    scraper: StoreScraper
    parser: PromotionParser


_STORES: dict[str, StoreEntry] = {}


def register_store(entry: StoreEntry) -> None:
    _STORES[entry.config.store_id] = entry


def list_stores() -> list[StoreConfig]:
    return [entry.config for entry in _STORES.values()]


def get_store(store_id: str) -> StoreEntry:
    if store_id not in _STORES:
        available = ", ".join(sorted(_STORES)) or "nenhum"
        raise ValueError(f"Supermercado '{store_id}' não encontrado. Disponíveis: {available}")
    return _STORES[store_id]


def get_all_store_ids() -> list[str]:
    store_ids = sorted(_STORES)
    if "pegpese" in store_ids:
        store_ids.remove("pegpese")
        return ["pegpese", *store_ids]
    return store_ids
