import json
import logging

from caca_promo.core.models import PromotionDetails, StoreConfig
from caca_promo.report.formatters import parse_float

logger = logging.getLogger(__name__)


class VipCommerceParser:
    def __init__(self, config: StoreConfig):
        self.config = config

    def build_product_url(self, product: dict) -> str:
        product_id = product.get("produto_id") or product.get("id")
        slug = product.get("link") or ""
        if product_id is None:
            return self.config.site_url
        if slug:
            return f"{self.config.site_url}/produto/{product_id}/{slug}"
        return f"{self.config.site_url}/produto/{product_id}"

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

        offer = product.get("oferta") or {}
        old_price = parse_float(offer.get("preco_antigo") or product.get("preco"))
        offer_price = parse_float(offer.get("preco_oferta") or product.get("preco"))
        regular_price = parse_float(product.get("preco"))

        discount_percent = None
        savings = None
        if old_price and offer_price and old_price > 0:
            discount_percent = round(((old_price - offer_price) / old_price) * 100, 1)
            savings = round(old_price - offer_price, 2)

        product_id = product.get("produto_id") or product.get("id") or 0
        brand = product.get("marca")
        if isinstance(brand, dict):
            brand = brand.get("nome") or "N/D"
        brand = brand or "N/D"

        return PromotionDetails(
            product_id=int(product_id),
            description=product.get("descricao") or fallback_description,
            product_url=self.build_product_url(product),
            offer_name=offer.get("nome") or "Sem oferta",
            offer_tag=offer.get("tag") or "N/D",
            old_price=old_price,
            offer_price=offer_price,
            discount_percent=discount_percent,
            savings=savings,
            unit=product.get("unidade_sigla") or "UN",
            available=bool(product.get("disponivel")),
            sku=product.get("sku") or "N/D",
            barcode=product.get("codigo_barras") or "N/D",
            brand=brand,
            regular_price=regular_price,
        )
