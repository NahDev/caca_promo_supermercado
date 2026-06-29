import pandas as pd
import streamlit as st

from caca_promo.analytics.loader import load_historical_dataframe, load_promotions_dataframe
from caca_promo.analytics.matcher import build_head_to_head
from caca_promo.analytics.metrics import (
    anchor_position_summary,
    brand_ranking,
    competitiveness_index,
    exclusive_products,
    historical_discount_trend,
    historical_price_trend,
    match_coverage,
    offer_type_distribution,
    price_increase_alerts,
    store_summary,
)
from caca_promo.core.registry import get_all_store_ids, get_store, list_stores
from caca_promo.dashboard import charts
from caca_promo.dashboard.components import render_chart_with_export, render_dataframe_with_export, render_metric_row
from caca_promo.storage.database import fetch_scrape_timestamps


def _store_options() -> dict[str, str]:
    return {store.store_id: store.name for store in list_stores()}


@st.cache_data(show_spinner=False)
def cached_promotions_dataframe(store_ids: tuple[str, ...], scraped_at_signature: str) -> pd.DataFrame:
    del scraped_at_signature
    return load_promotions_dataframe(list(store_ids))


@st.cache_data(show_spinner=False)
def cached_historical_dataframe(store_ids: tuple[str, ...]) -> pd.DataFrame:
    return load_historical_dataframe(list(store_ids))


def _comparison_export_frame(comparison_frame: pd.DataFrame) -> pd.DataFrame:
    if comparison_frame.empty:
        return comparison_frame
    return comparison_frame.rename(
        columns={
            "description": "product",
            "barcode": "ean",
            "anchor_price": "anchor_price",
            "competitor_price": "competitor_price",
            "gap_amount": "gap_amount",
            "gap_percent": "gap_percent",
            "anchor_url": "anchor_url",
            "competitor_url": "competitor_url",
            "match_method": "match_method",
        }
    )[
        [
            "product",
            "ean",
            "anchor_price",
            "competitor_price",
            "gap_amount",
            "gap_percent",
            "match_method",
            "anchor_url",
            "competitor_url",
        ]
    ]


def render_sidebar(store_options: dict[str, str]) -> tuple[str, str, str, list[str]]:
    st.sidebar.title("Caça Promo B2B")
    st.sidebar.caption("Competitive pricing intelligence for supermarkets")

    store_ids = list(store_options.keys())
    anchor_store_id = st.sidebar.selectbox(
        "Your store",
        options=store_ids,
        format_func=lambda store_id: store_options[store_id],
    )
    competitor_options = [store_id for store_id in store_ids if store_id != anchor_store_id]
    competitor_store_id = st.sidebar.selectbox(
        "Competitor",
        options=competitor_options,
        format_func=lambda store_id: store_options[store_id],
    )

    selected_stores = st.sidebar.multiselect(
        "Stores in analysis",
        options=store_ids,
        default=store_ids,
        format_func=lambda store_id: store_options[store_id],
    )
    page = st.sidebar.radio(
        "Page",
        options=[
            "Executive overview",
            "Head-to-head",
            "Market analysis",
            "Time evolution",
        ],
    )

    batch_labels = {}
    for store_id in selected_stores:
        timestamps = fetch_scrape_timestamps(store_id)
        if timestamps:
            batch_labels[store_id] = timestamps[0]

    batch_signature = "|".join(f"{store_id}:{scraped_at}" for store_id, scraped_at in batch_labels.items())
    frame = cached_promotions_dataframe(tuple(selected_stores), batch_signature)

    if batch_labels:
        st.sidebar.markdown("**Latest batches**")
        for store_id, scraped_at in batch_labels.items():
            st.sidebar.write(f"{store_options[store_id]}: {scraped_at}")

    position = anchor_position_summary(frame, anchor_store_id)
    st.sidebar.markdown("**ROI snapshot**")
    st.sidebar.write(
        f"{position['losing_count']} products priced above competitors "
        f"(avg gap R$ {position['average_gap']:.2f})"
    )
    return anchor_store_id, competitor_store_id, page, selected_stores, batch_signature, frame


def render_executive_page(frame: pd.DataFrame, anchor_store_id: str) -> None:
    st.header("Executive overview")
    summary = store_summary(frame)
    coverage = match_coverage(frame)
    competitiveness = competitiveness_index(frame, anchor_store_id)

    render_metric_row(
        [
            ("Stores", str(summary["store_name"].nunique() if not summary.empty else 0)),
            ("Total promotions", str(int(summary["total_promotions"].sum()) if not summary.empty else 0)),
            ("Match coverage", f"{coverage['coverage_percent']:.1f}%"),
            ("Competitiveness index", f"{competitiveness:.3f}" if competitiveness is not None else "N/D"),
        ]
    )

    if not summary.empty:
        render_chart_with_export(
            charts.promotions_by_store_chart(summary),
            "promotions_by_store.png",
        )
        render_chart_with_export(
            charts.average_discount_chart(summary),
            "average_discount_by_store.png",
        )

    distribution = offer_type_distribution(frame)
    if not distribution.empty:
        store_names = distribution["store_name"].unique().tolist()
        selected_store = st.selectbox("Offer mix store", options=store_names)
        render_chart_with_export(
            charts.offer_type_donut_chart(distribution, selected_store),
            "offer_mix.png",
        )

    st.subheader("Store summary")
    render_dataframe_with_export(summary, "store_summary.csv")


def render_head_to_head_page(
    frame: pd.DataFrame,
    anchor_store_id: str,
    competitor_store_id: str,
    store_options: dict[str, str],
) -> None:
    st.header("Head-to-head comparison")
    anchor_name = store_options[anchor_store_id]
    competitor_name = store_options[competitor_store_id]
    comparison = build_head_to_head(frame, anchor_store_id, competitor_store_id)

    if comparison.empty:
        st.warning("No matched products found between the selected stores.")
        return

    losing = comparison[comparison["gap_amount"] > 0]
    winning = comparison[comparison["gap_amount"] < 0]
    render_metric_row(
        [
            ("Matched products", str(len(comparison))),
            ("You lose", str(len(losing))),
            ("You win", str(len(winning))),
            ("Avg gap", f"R$ {comparison['gap_amount'].mean():.2f}"),
        ]
    )

    render_chart_with_export(
        charts.gap_horizontal_chart(losing, f"Top gaps where {anchor_name} is more expensive", ascending=False),
        "top_losing_gaps.png",
    )
    render_chart_with_export(
        charts.gap_horizontal_chart(winning, f"Top gaps where {anchor_name} is cheaper", ascending=True),
        "top_winning_gaps.png",
    )

    anchor_frame = frame[frame["store_id"] == anchor_store_id]
    competitor_frame = frame[frame["store_id"] == competitor_store_id]
    render_chart_with_export(
        charts.discount_box_chart(anchor_frame, competitor_frame, anchor_name, competitor_name),
        "discount_distribution.png",
    )
    render_chart_with_export(
        charts.price_heatmap_chart(comparison, anchor_name, competitor_name),
        "price_heatmap.png",
    )

    export_frame = _comparison_export_frame(comparison)
    render_dataframe_with_export(
        export_frame,
        f"gap_report_{anchor_store_id}_vs_{competitor_store_id}.csv",
        caption="Commercial export for client presentations",
    )


def render_market_page(frame: pd.DataFrame) -> None:
    st.header("Market analysis")
    brands = brand_ranking(frame)
    render_chart_with_export(charts.brand_ranking_chart(brands), "brand_ranking.png")
    render_dataframe_with_export(brands, "brand_ranking.csv")

    render_chart_with_export(charts.discount_scatter_chart(frame), "discount_scatter.png")

    exclusive = exclusive_products(frame)[
        ["store_name", "description", "offer_price", "discount_percent", "product_url", "match_method"]
    ]
    st.subheader("Exclusive promotions")
    render_dataframe_with_export(exclusive, "exclusive_products.csv")


def render_time_page(store_ids: list[str]) -> None:
    st.header("Time evolution")
    historical_frame = cached_historical_dataframe(tuple(store_ids))
    if historical_frame.empty:
        st.info("Run more scrape batches to unlock time-based insights.")
        return

    discount_trend = historical_discount_trend(historical_frame)
    price_trend = historical_price_trend(historical_frame)
    alerts = price_increase_alerts(historical_frame)

    render_chart_with_export(charts.discount_trend_chart(discount_trend), "discount_trend.png")
    render_chart_with_export(charts.price_trend_chart(price_trend), "price_trend.png")
    render_dataframe_with_export(alerts, "price_increase_alerts.csv", caption="Products with price increases")


def start() -> None:
    st.set_page_config(page_title="Caça Promo B2B", layout="wide")
    store_options = _store_options()
    anchor_store_id, competitor_store_id, page, selected_stores, _, frame = render_sidebar(store_options)

    if not selected_stores:
        st.warning("Select at least one store.")
        return

    if frame.empty:
        st.error("No promotion data found. Run `python main.py all --store all` first.")
        return

    if page == "Executive overview":
        render_executive_page(frame, anchor_store_id)
    elif page == "Head-to-head":
        render_head_to_head_page(frame, anchor_store_id, competitor_store_id, store_options)
    elif page == "Market analysis":
        render_market_page(frame)
    else:
        render_time_page(selected_stores)


if __name__ == "__main__":
    start()
