import json
import logging

from caca_promo.core.models import PromotionDetails, StoreConfig
from caca_promo.report.formatters import parse_float

logger = logging.getLogger(__name__)


class GpaParser:
    def __init__(self, config: StoreConfig):
        self.config = config

    def _offer_label(self, promotion: dict) -> str:
        percent_discount = promotion.get("percentDiscount")
        if percent_discount:
            return f"{percent_discount}% OFF"

        buy_quantity = promotion.get("promotionQuantityBuy")
        pay_quantity = promotion.get("promotionQuantityPayFor")
        if buy_quantity and pay_quantity:
            return f"Leve {buy_quantity} pague {pay_quantity}"

        seal_color = promotion.get("promotionSealColor")
        if seal_color:
            return f"Oferta {seal_color.title()}"

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

        promotion = product.get("productPromotion") or {}
        regular_price = parse_float(product.get("price"))
        offer_price = parse_float(
            promotion.get("unitPrice")
            or promotion.get("promotionNominalPrice")
            or product.get("price")
        )
        old_price = regular_price

        discount_percent = parse_float(promotion.get("percentDiscount"))
        savings = None
        if discount_percent is None and regular_price and offer_price and regular_price > offer_price:
            discount_percent = round(((regular_price - offer_price) / regular_price) * 100, 1)
            savings = round(regular_price - offer_price, 2)
        elif regular_price and offer_price and regular_price > offer_price:
            savings = round(regular_price - offer_price, 2)

        product_url = product.get("urlDetails") or self.config.site_url
        offer_name = self._offer_label(promotion)
        offer_tag = promotion.get("promotionSealColor") or "oferta"

        return PromotionDetails(
            product_id=int(product.get("id") or 0),
            description=product.get("name") or fallback_description,
            product_url=product_url,
            offer_name=offer_name,
            offer_tag=str(offer_tag).lower(),
            old_price=old_price,
            offer_price=offer_price,
            discount_percent=discount_percent,
            savings=savings,
            unit="UN",
            available=bool(product.get("stock")),
            sku=str(product.get("sku") or "N/D"),
            barcode=str((product.get("attributes") or {}).get("ean") or "N/D"),
            brand=str(product.get("brand") or "N/D"),
            regular_price=regular_price,
        )
