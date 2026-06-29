import logging
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from caca_promo.config.settings import REPORTS_DIR
from caca_promo.core.models import PromotionDetails, PromotionParser, StoreConfig
from caca_promo.report.formatters import format_currency, format_datetime
from caca_promo.storage.database import fetch_all_promotions, fetch_latest_scrape_timestamp

logger = logging.getLogger(__name__)


def format_promotion_block(index: int, promotion: PromotionDetails) -> list[str]:
    availability = "Sim" if promotion.available else "Não"
    discount_text = (
        f"{promotion.discount_percent:.1f}%"
        if promotion.discount_percent is not None
        else "N/D"
    )
    savings_text = format_currency(promotion.savings)

    return [
        f"{index}. {promotion.description}",
        f"   Link: {promotion.product_url}",
        f"   ID do produto: {promotion.product_id} | SKU: {promotion.sku} | EAN: {promotion.barcode}",
        f"   Marca: {promotion.brand} | Unidade: {promotion.unit} | Disponível: {availability}",
        f"   Tipo de oferta: {promotion.offer_name} (tag: {promotion.offer_tag})",
        f"   Preço promocional: {format_currency(promotion.offer_price)}",
        f"   Preço anterior: {format_currency(promotion.old_price)}",
        f"   Preço de catálogo: {format_currency(promotion.regular_price)}",
        f"   Desconto: {discount_text} | Economia: {savings_text}",
        "",
    ]


def build_report_content(
    store: StoreConfig,
    parser: PromotionParser,
    scraped_at: str | None = None,
) -> str:
    scraped_at = scraped_at or fetch_latest_scrape_timestamp(store.store_id)
    if not scraped_at:
        raise RuntimeError(f"Nenhuma promoção encontrada para {store.name}")

    rows = fetch_all_promotions(store_id=store.store_id, scraped_at=scraped_at)
    if not rows:
        raise RuntimeError(f"Nenhuma promoção encontrada para {store.name} no lote {scraped_at}")

    promotions = [parser.parse(row["raw_data"], row["description"]) for row in rows]
    offer_counter: Counter[str] = Counter(promotion.offer_name for promotion in promotions)
    available_count = sum(1 for promotion in promotions if promotion.available)
    unavailable_count = len(promotions) - available_count

    discounts = [promotion for promotion in promotions if promotion.discount_percent is not None]
    discounts.sort(key=lambda item: item.discount_percent or 0, reverse=True)
    top_discounts = discounts[:20]

    average_discount = (
        round(sum(item.discount_percent for item in discounts) / len(discounts), 1)
        if discounts
        else 0
    )
    max_discount = discounts[0].discount_percent if discounts else 0
    total_savings = round(sum(item.savings or 0 for item in discounts), 2)

    lines = [
        f"RELATÓRIO DE PROMOÇÕES - {store.name.upper()}",
        "=" * 70,
        f"Supermercado: {store.name} ({store.store_id})",
        f"Plataforma: {store.platform}",
        f"Gerado em: {format_datetime(datetime.now(timezone.utc).isoformat())}",
        f"Lote de coleta: {format_datetime(scraped_at)}",
        f"Fonte: {store.offers_url}",
        "",
        "RESUMO GERAL",
        "-" * 70,
        f"Total de promoções: {len(promotions)}",
        f"Produtos disponíveis: {available_count}",
        f"Produtos indisponíveis: {unavailable_count}",
        f"Tipos de oferta distintos: {len(offer_counter)}",
        "",
        "RESUMO POR TIPO DE OFERTA",
        "-" * 70,
    ]

    for offer_name, count in offer_counter.most_common():
        lines.append(f"{offer_name}: {count}")

    lines.extend(
        [
            "",
            "ESTATÍSTICAS DE DESCONTO",
            "-" * 70,
            f"Produtos com desconto calculado: {len(discounts)}",
            f"Desconto médio: {average_discount:.1f}%",
            f"Maior desconto: {max_discount:.1f}%",
            f"Economia total estimada (soma dos descontos): {format_currency(total_savings)}",
            "",
            "MAIORES DESCONTOS (TOP 20)",
            "-" * 70,
        ]
    )

    if top_discounts:
        for index, promotion in enumerate(top_discounts, start=1):
            lines.extend(format_promotion_block(index, promotion))
    else:
        lines.append("Nenhum dado de desconto disponível.")
        lines.append("")

    lines.extend(
        [
            "LISTAGEM COMPLETA DE PROMOÇÕES",
            "-" * 70,
        ]
    )

    sorted_promotions = sorted(promotions, key=lambda item: item.description.lower())
    for index, promotion in enumerate(sorted_promotions, start=1):
        lines.extend(format_promotion_block(index, promotion))

    return "\n".join(lines).rstrip() + "\n"


def generate_report(
    store: StoreConfig,
    parser: PromotionParser,
    output_path: Path | None = None,
    scraped_at: str | None = None,
) -> Path:
    store_reports_dir = REPORTS_DIR / store.store_id
    store_reports_dir.mkdir(parents=True, exist_ok=True)
    content = build_report_content(store, parser, scraped_at=scraped_at)

    if output_path is None:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        output_path = store_reports_dir / f"promotions_report_{timestamp}.txt"

    output_path.write_text(content, encoding="utf-8")
    logger.info("Report saved to %s", output_path)
    return output_path
