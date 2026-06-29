from dataclasses import dataclass


@dataclass(frozen=True)
class GpaConfig:
    brand_prefix: str
    api_store_id: int
    special_terms: str
    department: str = "ecom"
    results_per_page: int = 48
    sort_by: str = "relevance"
    api_base: str = "https://api.vendas.gpa.digital"

    @property
    def special_page_url(self) -> str:
        return f"{self.api_base}/{self.brand_prefix}/special-page"

    def build_headers(self, site_url: str) -> dict[str, str]:
        return {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Origin": site_url,
            "Referer": f"{site_url}/",
            "x-origin": "CATALOG",
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
        }

    def build_payload(self, page_number: int) -> dict:
        return {
            "partner": "linx",
            "page": page_number,
            "resultsPerPage": self.results_per_page,
            "terms": self.special_terms,
            "sortBy": self.sort_by,
            "department": self.department,
            "storeId": self.api_store_id,
            "customerPlus": False,
            "allowRedirect": False,
            "filters": [],
        }
