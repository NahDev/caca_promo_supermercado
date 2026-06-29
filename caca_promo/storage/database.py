import json
import logging
import sqlite3
from datetime import datetime, timezone

from caca_promo.config.settings import DATA_DIR, DATABASE_PATH

logger = logging.getLogger(__name__)


def ensure_directories() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def get_connection() -> sqlite3.Connection:
    ensure_directories()
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def _migrate_legacy_schema(connection: sqlite3.Connection) -> None:
    columns = {
        row["name"]
        for row in connection.execute("PRAGMA table_info(promotions_raw)").fetchall()
    }

    if not columns:
        return

    if "store_id" not in columns:
        connection.execute(
            "ALTER TABLE promotions_raw ADD COLUMN store_id TEXT NOT NULL DEFAULT 'pegpese'"
        )
        connection.commit()

    connection.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS idx_promotions_raw_store_product_batch
        ON promotions_raw (store_id, product_id, scraped_at)
        """
    )
    connection.commit()


def init_database() -> None:
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS promotions_raw (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                description TEXT NOT NULL,
                raw_data TEXT NOT NULL,
                source_page INTEGER,
                scraped_at TEXT NOT NULL
            )
            """
        )
        connection.commit()
        _migrate_legacy_schema(connection)

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_promotions_raw_scraped_at
            ON promotions_raw (scraped_at)
            """
        )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_promotions_raw_store_id
            ON promotions_raw (store_id)
            """
        )
        connection.commit()

    logger.info("Database initialized at %s", DATABASE_PATH)


def save_promotions(
    store_id: str,
    products: list[dict],
    source_page: int,
    scraped_at: str | None = None,
) -> int:
    if not products:
        return 0

    scraped_at = scraped_at or datetime.now(timezone.utc).isoformat()
    saved_count = 0

    with get_connection() as connection:
        for product in products:
            product_id = product.get("produto_id") or product.get("id") or product.get("productId")
            description = (
                product.get("descricao")
                or product.get("description")
                or product.get("name")
                or product.get("productName")
                or ""
            )
            if product_id is None:
                logger.warning("Skipping product without product_id: %s", description[:80])
                continue

            cursor = connection.execute(
                """
                INSERT OR IGNORE INTO promotions_raw
                (store_id, product_id, description, raw_data, source_page, scraped_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    store_id,
                    int(product_id),
                    description,
                    json.dumps(product, ensure_ascii=False),
                    source_page,
                    scraped_at,
                ),
            )
            saved_count += cursor.rowcount

        connection.commit()

    logger.info("Saved %s promotions from page %s for store %s", saved_count, source_page, store_id)
    return saved_count


def fetch_all_promotions(
    store_id: str,
    scraped_at: str | None = None,
) -> list[sqlite3.Row]:
    query = "SELECT * FROM promotions_raw WHERE store_id = ?"
    params: list = [store_id]

    if scraped_at:
        query += " AND scraped_at = ?"
        params.append(scraped_at)

    query += " ORDER BY id"

    with get_connection() as connection:
        rows = connection.execute(query, params).fetchall()

    return list(rows)


def fetch_latest_scrape_timestamp(store_id: str) -> str | None:
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT scraped_at FROM promotions_raw
            WHERE store_id = ?
            ORDER BY scraped_at DESC
            LIMIT 1
            """,
            (store_id,),
        ).fetchone()

    return row["scraped_at"] if row else None


def fetch_scrape_timestamps(store_id: str) -> list[str]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT DISTINCT scraped_at FROM promotions_raw
            WHERE store_id = ?
            ORDER BY scraped_at DESC
            """,
            (store_id,),
        ).fetchall()

    return [row["scraped_at"] for row in rows]


def fetch_all_store_ids_in_database() -> list[str]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT DISTINCT store_id FROM promotions_raw
            ORDER BY store_id
            """
        ).fetchall()

    return [row["store_id"] for row in rows]


def fetch_latest_scrape_timestamps_all_stores() -> dict[str, str]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT store_id, scraped_at
            FROM promotions_raw
            WHERE (store_id, scraped_at) IN (
                SELECT store_id, MAX(scraped_at)
                FROM promotions_raw
                GROUP BY store_id
            )
            """
        ).fetchall()

    return {row["store_id"]: row["scraped_at"] for row in rows}


def fetch_promotions_for_stores(
    store_ids: list[str],
    scraped_at_map: dict[str, str],
) -> list[sqlite3.Row]:
    if not store_ids:
        return []

    rows: list[sqlite3.Row] = []
    with get_connection() as connection:
        for store_id in store_ids:
            scraped_at = scraped_at_map.get(store_id)
            if not scraped_at:
                continue
            batch_rows = connection.execute(
                """
                SELECT * FROM promotions_raw
                WHERE store_id = ? AND scraped_at = ?
                ORDER BY id
                """,
                (store_id, scraped_at),
            ).fetchall()
            rows.extend(batch_rows)

    return rows
