import pandas as pd

from caca_promo.analytics.matcher import assign_product_keys, build_head_to_head, build_matched_groups


def store_summary(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame()

    grouped = frame.groupby(["store_id", "store_name"], as_index=False).agg(
        total_promotions=("product_id", "count"),
        available_count=("available", lambda values: int(values.sum())),
        average_discount=("discount_percent", "mean"),
        median_discount=("discount_percent", "median"),
        total_savings=("savings", lambda values: round(values.fillna(0).sum(), 2)),
    )
    grouped["average_discount"] = grouped["average_discount"].round(1)
    grouped["median_discount"] = grouped["median_discount"].round(1)
    return grouped


def offer_type_distribution(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame()

    return (
        frame.groupby(["store_name", "offer_name"], as_index=False)
        .size()
        .rename(columns={"size": "count"})
    )


def match_coverage(frame: pd.DataFrame) -> dict[str, float]:
    keyed_frame = assign_product_keys(frame)
    if keyed_frame.empty:
        return {"coverage_percent": 0.0, "ean_percent": 0.0, "fuzzy_percent": 0.0}

    matched = build_matched_groups(keyed_frame)
    total_products = len(keyed_frame)
    matched_products = len(matched)
    coverage_percent = round((matched_products / total_products) * 100, 1) if total_products else 0.0

    method_counts = keyed_frame["match_method"].value_counts()
    ean_percent = round((method_counts.get("ean", 0) / total_products) * 100, 1)
    fuzzy_percent = round((method_counts.get("fuzzy", 0) / total_products) * 100, 1)
    return {
        "coverage_percent": coverage_percent,
        "ean_percent": ean_percent,
        "fuzzy_percent": fuzzy_percent,
    }


def competitiveness_index(frame: pd.DataFrame, anchor_store_id: str) -> float | None:
    matched_groups = build_matched_groups(frame)
    if matched_groups.empty or anchor_store_id not in matched_groups["store_id"].unique():
        return None

    pivot = matched_groups.pivot_table(
        index="product_key",
        columns="store_id",
        values="offer_price",
        aggfunc="first",
    )
    if anchor_store_id not in pivot.columns:
        return None

    market_average = pivot.drop(columns=[anchor_store_id], errors="ignore").mean(axis=1)
    anchor_prices = pivot[anchor_store_id]
    valid_rows = anchor_prices.notna() & market_average.notna()
    if not valid_rows.any():
        return None

    index_value = (anchor_prices[valid_rows] / market_average[valid_rows]).mean()
    return round(float(index_value), 3)


def anchor_position_summary(frame: pd.DataFrame, anchor_store_id: str) -> dict[str, float | int]:
    competitors = [store_id for store_id in frame["store_id"].unique() if store_id != anchor_store_id]
    losing_count = 0
    winning_count = 0
    tied_count = 0
    gap_amounts: list[float] = []

    for competitor_store_id in competitors:
        comparison = build_head_to_head(frame, anchor_store_id, competitor_store_id)
        if comparison.empty:
            continue
        losing_count += int((comparison["gap_amount"] > 0).sum())
        winning_count += int((comparison["gap_amount"] < 0).sum())
        tied_count += int((comparison["gap_amount"] == 0).sum())
        gap_amounts.extend(comparison["gap_amount"].dropna().tolist())

    valid_gaps = [gap for gap in gap_amounts if pd.notna(gap)]
    average_gap = round(sum(valid_gaps) / len(valid_gaps), 2) if valid_gaps else 0.0
    return {
        "losing_count": losing_count,
        "winning_count": winning_count,
        "tied_count": tied_count,
        "average_gap": average_gap,
    }


def brand_ranking(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame()

    brand_frame = frame.copy()
    brand_frame["brand"] = brand_frame["brand"].replace({"": "Unknown", None: "Unknown"})
    ranking = (
        brand_frame.groupby(["brand", "store_name"], as_index=False)
        .agg(
            promotions=("product_id", "count"),
            average_discount=("discount_percent", "mean"),
            average_price=("offer_price", "mean"),
        )
        .sort_values(["promotions", "average_discount"], ascending=[False, False])
    )
    ranking["average_discount"] = ranking["average_discount"].round(1)
    ranking["average_price"] = ranking["average_price"].round(2)
    return ranking


def exclusive_products(frame: pd.DataFrame) -> pd.DataFrame:
    keyed_frame = assign_product_keys(frame)
    if keyed_frame.empty:
        return pd.DataFrame()

    store_counts = keyed_frame.groupby("product_key")["store_id"].nunique()
    exclusive_keys = store_counts[store_counts == 1].index
    exclusive_frame = keyed_frame[keyed_frame["product_key"].isin(exclusive_keys)].copy()
    return exclusive_frame.sort_values(["store_name", "description"])


def historical_discount_trend(historical_frame: pd.DataFrame) -> pd.DataFrame:
    if historical_frame.empty:
        return pd.DataFrame()

    trend = (
        historical_frame.groupby(["store_name", "scraped_at"], as_index=False)
        .agg(average_discount=("discount_percent", "mean"))
        .sort_values("scraped_at")
    )
    trend["average_discount"] = trend["average_discount"].round(1)
    return trend


def historical_price_trend(historical_frame: pd.DataFrame) -> pd.DataFrame:
    if historical_frame.empty:
        return pd.DataFrame()

    matched_groups = build_matched_groups(historical_frame)
    if matched_groups.empty:
        return pd.DataFrame()

    recurring_keys = (
        matched_groups.groupby("product_key")["scraped_at"]
        .nunique()
        .loc[lambda values: values > 1]
        .index
    )
    recurring = matched_groups[matched_groups["product_key"].isin(recurring_keys)]
    trend = (
        recurring.groupby(["store_name", "scraped_at"], as_index=False)
        .agg(average_price=("offer_price", "mean"))
        .sort_values("scraped_at")
    )
    trend["average_price"] = trend["average_price"].round(2)
    return trend


def price_increase_alerts(
    historical_frame: pd.DataFrame,
    threshold_percent: float = 5.0,
) -> pd.DataFrame:
    if historical_frame.empty:
        return pd.DataFrame()

    working_frame = historical_frame.sort_values("scraped_at").copy()
    alerts = []

    for (store_id, store_name, product_id), group in working_frame.groupby(
        ["store_id", "store_name", "product_id"]
    ):
        if len(group) < 2:
            continue
        previous_row = group.iloc[-2]
        latest_row = group.iloc[-1]
        previous_price = previous_row["offer_price"]
        latest_price = latest_row["offer_price"]
        if previous_price is None or latest_price is None or previous_price <= 0:
            continue
        change_percent = ((latest_price - previous_price) / previous_price) * 100
        if change_percent >= threshold_percent:
            alerts.append(
                {
                    "store_id": store_id,
                    "store_name": store_name,
                    "product_id": product_id,
                    "description": latest_row["description"],
                    "previous_price": previous_price,
                    "latest_price": latest_price,
                    "change_percent": round(change_percent, 1),
                    "previous_batch": previous_row["scraped_at"],
                    "latest_batch": latest_row["scraped_at"],
                }
            )

    return pd.DataFrame(alerts).sort_values("change_percent", ascending=False)
