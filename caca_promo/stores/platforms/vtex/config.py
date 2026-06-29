from dataclasses import dataclass


@dataclass(frozen=True)
class VtexConfig:
    product_cluster_id: str
    page_size: int = 50

    def build_search_params(self, start_index: int, end_index: int) -> dict[str, str | int]:
        return {
            "fq": f"productClusterIds:{self.product_cluster_id}",
            "_from": start_index,
            "_to": end_index,
        }

    @staticmethod
    def parse_resources_header(header: str | None) -> tuple[int, int]:
        if not header or "/" not in header:
            return 0, 0
        range_part, total_part = header.split("/", 1)
        total_items = int(total_part)
        if "-" not in range_part:
            return 0, total_items
        _, end_index = range_part.split("-", 1)
        return int(end_index), total_items

    def build_headers(self) -> dict[str, str]:
        return {
            "Accept": "application/json",
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
        }
