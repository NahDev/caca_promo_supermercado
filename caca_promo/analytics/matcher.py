import re
import unicodedata

import pandas as pd
from rapidfuzz import fuzz, process

FUZZY_THRESHOLD = 90
INVALID_BARCODES = {"", "N/D", "0", "0000000000000"}


def normalize_barcode(barcode: str | None) -> str | None:
    if not barcode:
        return None
    cleaned = re.sub(r"\D", "", str(barcode).strip())
    if len(cleaned) < 8 or cleaned in INVALID_BARCODES:
        return None
    return cleaned


def normalize_description(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text.lower())
    normalized = "".join(char for char in normalized if not unicodedata.combining(char))
    normalized = re.sub(r"[^a-z0-9\s]", " ", normalized)
    return re.sub(r"\s+", " ", normalized).strip()


def _build_ean_groups(frame: pd.DataFrame) -> tuple[dict[str, str], dict[str, str]]:
    product_keys: dict[str, str] = {}
    match_methods: dict[str, str] = {}

    for index, row in frame.iterrows():
        barcode = normalize_barcode(row.get("barcode"))
        if not barcode:
            continue
        product_key = f"ean:{barcode}"
        product_keys[str(index)] = product_key
        match_methods[str(index)] = "ean"

    return product_keys, match_methods


def _build_fuzzy_groups(
    frame: pd.DataFrame,
    product_keys: dict[str, str],
    match_methods: dict[str, str],
) -> None:
    unmatched_indices = [
        str(index)
        for index in frame.index
        if str(index) not in product_keys and frame.loc[index, "offer_price"] is not None
    ]
    if not unmatched_indices:
        return

    descriptions = {
        index: normalize_description(frame.loc[int(index), "description"])
        for index in unmatched_indices
    }
    assigned: set[str] = set()

    for index in unmatched_indices:
        if index in assigned:
            continue

        candidates = [
            (other_index, descriptions[other_index])
            for other_index in unmatched_indices
            if other_index != index and other_index not in assigned
        ]
        if not candidates:
            product_key = f"name:{descriptions[index]}"
            product_keys[index] = product_key
            match_methods[index] = "name_only"
            assigned.add(index)
            continue

        match = process.extractOne(
            descriptions[index],
            [candidate[1] for candidate in candidates],
            scorer=fuzz.token_sort_ratio,
            score_cutoff=FUZZY_THRESHOLD,
        )
        if not match:
            product_key = f"name:{descriptions[index]}"
            product_keys[index] = product_key
            match_methods[index] = "name_only"
            assigned.add(index)
            continue

        matched_description = match[0]
        matched_indices = [
            candidate[0]
            for candidate in candidates
            if candidate[1] == matched_description
        ]
        group_members = [index, *matched_indices]
        product_key = f"fuzzy:{descriptions[index]}"
        for member_index in group_members:
            product_keys[member_index] = product_key
            match_methods[member_index] = "fuzzy"
            assigned.add(member_index)


def assign_product_keys(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return frame.copy()

    working_frame = frame.copy()
    product_keys, match_methods = _build_ean_groups(working_frame)
    _build_fuzzy_groups(working_frame, product_keys, match_methods)

    working_frame["product_key"] = working_frame.index.map(
        lambda index: product_keys.get(str(index), f"unique:{index}")
    )
    working_frame["match_method"] = working_frame.index.map(
        lambda index: match_methods.get(str(index), "unique")
    )
    return working_frame


def build_matched_groups(frame: pd.DataFrame) -> pd.DataFrame:
    keyed_frame = assign_product_keys(frame)
    if keyed_frame.empty:
        return pd.DataFrame()

    group_sizes = keyed_frame.groupby("product_key")["store_id"].nunique()
    multi_store_keys = group_sizes[group_sizes > 1].index
    return keyed_frame[keyed_frame["product_key"].isin(multi_store_keys)].copy()


def build_head_to_head(frame: pd.DataFrame, anchor_store_id: str, competitor_store_id: str) -> pd.DataFrame:
    matched_groups = build_matched_groups(frame)
    if matched_groups.empty:
        return pd.DataFrame()

    pivot = matched_groups.pivot_table(
        index="product_key",
        columns="store_id",
        values=["description", "offer_price", "discount_percent", "product_url", "barcode", "match_method"],
        aggfunc="first",
    )
    if anchor_store_id not in pivot["offer_price"].columns:
        return pd.DataFrame()
    if competitor_store_id not in pivot["offer_price"].columns:
        return pd.DataFrame()

    rows = []
    for product_key in pivot.index:
        anchor_price = pivot.loc[product_key, ("offer_price", anchor_store_id)]
        competitor_price = pivot.loc[product_key, ("offer_price", competitor_store_id)]
        if anchor_price is None or competitor_price is None:
            continue

        gap_amount = round(float(anchor_price) - float(competitor_price), 2)
        gap_percent = round((gap_amount / float(competitor_price)) * 100, 1) if competitor_price else None
        rows.append(
            {
                "product_key": product_key,
                "description": pivot.loc[product_key, ("description", anchor_store_id)],
                "barcode": pivot.loc[product_key, ("barcode", anchor_store_id)],
                "match_method": pivot.loc[product_key, ("match_method", anchor_store_id)],
                "anchor_price": float(anchor_price),
                "competitor_price": float(competitor_price),
                "anchor_discount": pivot.loc[product_key, ("discount_percent", anchor_store_id)],
                "competitor_discount": pivot.loc[product_key, ("discount_percent", competitor_store_id)],
                "gap_amount": gap_amount,
                "gap_percent": gap_percent,
                "anchor_url": pivot.loc[product_key, ("product_url", anchor_store_id)],
                "competitor_url": pivot.loc[product_key, ("product_url", competitor_store_id)],
            }
        )

    return pd.DataFrame(rows)
