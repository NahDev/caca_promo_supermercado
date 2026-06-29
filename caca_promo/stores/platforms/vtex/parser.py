import json
import logging

from caca_promo.core.models import PromotionDetails, StoreConfig
from caca_promo.report.formatters import parse_float

logger = logging.getLogger(__name__)


class VtexParser:
    def __init__(self, config: StoreConfig):
        self.config = config

    def _first_item(self, product: dict) -> dict:
        items = product.get("items") or []
        return items[0] if items else {}

    def _first_offer(self, product: dict) -> dict:
        item = self._first_item(product)
        sellers = item.get("sellers") or []
        if not sellers:
            return {}
        return sellers[0].get("commertialOffer") or {}

    def _offer_name(self, product: dict, offer: dict) -> str:
        highlights = product.get("clusterHighlights") or {}
        if highlights:
            return next(iter(highlights.values()), "Oferta")

        list_price = parse_float(offer.get("ListPrice"))
        price = parse_float(offer.get("Price"))
        if list_price and price and list_price > price:
            discount = round(((list_price - price) / list_price) * 100)
            return f"-{discount}%"

        return "Oferta"

    def parse(self, raw_data: str, fallback_description: str = "") -> PromotionDetails:
        try:
            product = json.loads(raw_data)
        except json.JSONDecodeError:
            return PromotionDetails(
                product_id=0,
                description=fallback_description,
                product_url=self.config.site_url,
                offer_name="N/D",
                offer_tag="N/D",
                old_price=None,
                offer_price=None,
                discount_percent=None,
                savings=None,
                unit="N/D",
                available=False,
                sku="N/D",
                barcode="N/D",
                brand="N/D",
                regular_price=None,
            )

        item = self._first_item(product)
        offer = self._first_offer(product)
        list_price = parse_float(offer.get("ListPrice"))
        offer_price = parse_float(offer.get("Price"))
        regular_price = list_price or offer_price

        discount_percent = None
        savings = None
        if list_price and offer_price and list_price > 0 and list_price > offer_price:
            discount_percent = round(((list_price - offer_price) / list_price) * 100, 1)
            savings = round(list_price - offer_price, 2)

        product_url = product.get("link") or self.config.site_url
        if product_url.startswith("/"):
            product_url = f"{self.config.site_url.rstrip('/')}{product_url}"

        highlights = product.get("clusterHighlights") or {}
        offer_tag = next(iter(highlights.keys()), "oferta") if highlights else "oferta"

        return PromotionDetails(
            product_id=int(product.get("productId") or 0),
            description=product.get("productName") or fallback_description,
            product_url=product_url,
            offer_name=self._offer_name(product, offer),
            offer_tag=str(offer_tag),
            old_price=list_price,
            offer_price=offer_price,
            discount_percent=discount_percent,
            savings=savings,
            unit=item.get("measurementUnit") or "UN",
            available=bool(offer.get("IsAvailable")),
            sku=str(item.get("itemId") or product.get("productReference") or "N/D"),
            barcode=str(item.get("ean") or "N/D"),
            brand=str(product.get("brand") or "N/D"),
            regular_price=regular_price,
        )
