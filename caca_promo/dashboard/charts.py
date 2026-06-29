import plotly.express as px
import plotly.graph_objects as go
import pandas as pd


def promotions_by_store_chart(summary_frame: pd.DataFrame) -> go.Figure:
    figure = px.bar(
        summary_frame,
        x="store_name",
        y="total_promotions",
        color="store_name",
        title="Total promotions by store",
        labels={"store_name": "Store", "total_promotions": "Promotions"},
    )
    figure.update_layout(showlegend=False, xaxis_title="", yaxis_title="Promotions")
    return figure


def average_discount_chart(summary_frame: pd.DataFrame) -> go.Figure:
    figure = px.bar(
        summary_frame,
        x="store_name",
        y="average_discount",
        color="store_name",
        title="Average discount by store",
        labels={"store_name": "Store", "average_discount": "Average discount (%)"},
    )
    figure.update_layout(showlegend=False, xaxis_title="", yaxis_title="Discount (%)")
    return figure


def offer_type_donut_chart(distribution_frame: pd.DataFrame, store_name: str) -> go.Figure:
    store_frame = distribution_frame[distribution_frame["store_name"] == store_name]
    figure = px.pie(
        store_frame,
        names="offer_name",
        values="count",
        hole=0.45,
        title=f"Offer mix - {store_name}",
    )
    return figure


def gap_horizontal_chart(comparison_frame: pd.DataFrame, title: str, ascending: bool) -> go.Figure:
    if comparison_frame.empty:
        return go.Figure().update_layout(title=title)

    sorted_frame = comparison_frame.sort_values("gap_amount", ascending=ascending).head(20)
    figure = px.bar(
        sorted_frame,
        x="gap_amount",
        y="description",
        orientation="h",
        title=title,
        labels={"gap_amount": "Price gap (R$)", "description": "Product"},
        color="gap_amount",
        color_continuous_scale="RdYlGn_r" if ascending else "RdYlGn",
    )
    figure.update_layout(showlegend=False, yaxis={"categoryorder": "total ascending"})
    return figure


def discount_box_chart(anchor_frame: pd.DataFrame, competitor_frame: pd.DataFrame, anchor_name: str, competitor_name: str) -> go.Figure:
    anchor_data = anchor_frame.dropna(subset=["discount_percent"]).copy()
    competitor_data = competitor_frame.dropna(subset=["discount_percent"]).copy()
    anchor_data["group"] = anchor_name
    competitor_data["group"] = competitor_name
    combined = pd.concat([anchor_data, competitor_data], ignore_index=True)
    figure = px.box(
        combined,
        x="group",
        y="discount_percent",
        color="group",
        title="Discount distribution",
        labels={"group": "Store", "discount_percent": "Discount (%)"},
    )
    figure.update_layout(showlegend=False, xaxis_title="")
    return figure


def price_heatmap_chart(comparison_frame: pd.DataFrame, anchor_name: str, competitor_name: str) -> go.Figure:
    if comparison_frame.empty:
        return go.Figure().update_layout(title="Price heatmap")

    heatmap_frame = comparison_frame.sort_values("gap_amount", key=lambda values: values.abs(), ascending=False).head(15)
    matrix = pd.DataFrame(
        {
            anchor_name: heatmap_frame["anchor_price"],
            competitor_name: heatmap_frame["competitor_price"],
        },
        index=heatmap_frame["description"],
    )
    figure = px.imshow(
        matrix,
        aspect="auto",
        color_continuous_scale="Blues",
        title="Top matched products price heatmap",
        labels={"color": "Price (R$)"},
    )
    figure.update_layout(xaxis_title="", yaxis_title="")
    return figure


def brand_ranking_chart(brand_frame: pd.DataFrame) -> go.Figure:
    if brand_frame.empty:
        return go.Figure().update_layout(title="Brand ranking")

    top_brands = (
        brand_frame.groupby("brand", as_index=False)["promotions"]
        .sum()
        .sort_values("promotions", ascending=False)
        .head(10)["brand"]
    )
    filtered = brand_frame[brand_frame["brand"].isin(top_brands)]
    figure = px.bar(
        filtered,
        x="brand",
        y="promotions",
        color="store_name",
        barmode="group",
        title="Top brands by promotion count",
        labels={"brand": "Brand", "promotions": "Promotions", "store_name": "Store"},
    )
    return figure


def discount_scatter_chart(frame: pd.DataFrame) -> go.Figure:
    scatter_frame = frame.dropna(subset=["discount_percent", "offer_price"]).copy()
    figure = px.scatter(
        scatter_frame,
        x="offer_price",
        y="discount_percent",
        color="store_name",
        hover_name="description",
        title="Discount vs promotional price",
        labels={"offer_price": "Promotional price (R$)", "discount_percent": "Discount (%)"},
    )
    return figure


def discount_trend_chart(trend_frame: pd.DataFrame) -> go.Figure:
    if trend_frame.empty:
        return go.Figure().update_layout(title="Discount trend over time")

    figure = px.line(
        trend_frame,
        x="scraped_at",
        y="average_discount",
        color="store_name",
        markers=True,
        title="Average discount trend",
        labels={"scraped_at": "Batch", "average_discount": "Average discount (%)", "store_name": "Store"},
    )
    return figure


def price_trend_chart(trend_frame: pd.DataFrame) -> go.Figure:
    if trend_frame.empty:
        return go.Figure().update_layout(title="Comparable basket price trend")

    figure = px.line(
        trend_frame,
        x="scraped_at",
        y="average_price",
        color="store_name",
        markers=True,
        title="Comparable basket average price trend",
        labels={"scraped_at": "Batch", "average_price": "Average price (R$)", "store_name": "Store"},
    )
    return figure
