import logging
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from caca_promo.analytics.loader import load_promotions_dataframe
from caca_promo.analytics.matcher import build_head_to_head
from caca_promo.analytics.metrics import (
    anchor_position_summary,
    competitiveness_index,
    match_coverage,
    store_summary,
)
from caca_promo.config.settings import OUTPUT_DIR
from caca_promo.core.registry import get_all_store_ids, get_store
from caca_promo.report.formatters import format_currency, format_datetime

logger = logging.getLogger(__name__)
COMPETITIVE_REPORTS_DIR = OUTPUT_DIR / "competitive"


def _format_comparison_table(comparison_frame: pd.DataFrame, limit: int = 30) -> list[str]:
    if comparison_frame.empty:
        return ["No matched products found."]

    lines = []
    losing = comparison_frame.sort_values("gap_amount", ascending=False).head(limit)
    for position, (_, row) in enumerate(losing.iterrows(), start=1):
        lines.append(
            f"{position}. {row['description']} | "
            f"anchor {format_currency(row['anchor_price'])} | "
            f"competitor {format_currency(row['competitor_price'])} | "
            f"gap {format_currency(row['gap_amount'])} ({row['gap_percent']}%)"
        )
    return lines


def build_competitive_report_content(anchor_store_id: str, store_ids: list[str] | None = None) -> str:
    store_ids = store_ids or get_all_store_ids()
    anchor_entry = get_store(anchor_store_id)
    frame = load_promotions_dataframe(store_ids)
    if frame.empty:
        raise RuntimeError("No promotion data found for competitive report")

    summary = store_summary(frame)
    coverage = match_coverage(frame)
    competitiveness = competitiveness_index(frame, anchor_store_id)
    position = anchor_position_summary(frame, anchor_store_id)
    competitors = [store_id for store_id in store_ids if store_id != anchor_store_id]

    lines = [
        f"COMPETITIVE REPORT - {anchor_entry.config.name.upper()}",
        "=" * 70,
        f"Anchor store: {anchor_entry.config.name} ({anchor_store_id})",
        f"Generated at: {format_datetime(datetime.now(timezone.utc).isoformat())}",
        "",
        "EXECUTIVE SUMMARY",
        "-" * 70,
        f"Stores analyzed: {len(store_ids)}",
        f"Total promotions: {int(summary['total_promotions'].sum())}",
        f"Match coverage: {coverage['coverage_percent']:.1f}%",
        f"EAN matches: {coverage['ean_percent']:.1f}%",
        f"Fuzzy matches: {coverage['fuzzy_percent']:.1f}%",
        f"Competitiveness index: {competitiveness:.3f}" if competitiveness is not None else "Competitiveness index: N/D",
        f"Products priced above competitors: {position['losing_count']}",
        f"Products priced below competitors: {position['winning_count']}",
        f"Average price gap: {format_currency(position['average_gap'])}",
        "",
        "STORE SNAPSHOT",
        "-" * 70,
    ]

    for _, row in summary.iterrows():
        lines.append(
            f"{row['store_name']}: {int(row['total_promotions'])} promos | "
            f"avg discount {row['average_discount']:.1f}% | "
            f"total savings {format_currency(row['total_savings'])}"
        )

    for competitor_store_id in competitors:
        competitor_entry = get_store(competitor_store_id)
        comparison = build_head_to_head(frame, anchor_store_id, competitor_store_id)
        lines.extend(
            [
                "",
                f"HEAD-TO-HEAD VS {competitor_entry.config.name.upper()}",
                "-" * 70,
                f"Matched products: {len(comparison)}",
            ]
        )
        lines.extend(_format_comparison_table(comparison))

    return "\n".join(lines).rstrip() + "\n"


def generate_competitive_report(
    anchor_store_id: str,
    store_ids: list[str] | None = None,
    output_path: Path | None = None,
) -> Path:
    COMPETITIVE_REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    content = build_competitive_report_content(anchor_store_id, store_ids=store_ids)

    if output_path is None:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        output_path = COMPETITIVE_REPORTS_DIR / f"competitive_report_{anchor_store_id}_{timestamp}.txt"

    output_path.write_text(content, encoding="utf-8")
    logger.info("Competitive report saved to %s", output_path)
    return output_path
