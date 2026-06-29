from dataclasses import dataclass


@dataclass(frozen=True)
class VipCommerceConfig:
    organization_id: str
    domain_key: str
    filial_id: str
    distribution_center_id: str
    login_key: str | None = None
    api_base: str = "https://services.vipcommerce.com.br/api-admin/v1"

    @property
    def login_url(self) -> str:
        return f"{self.api_base}/org/{self.organization_id}/auth/loja/login"

    @property
    def offers_api_url(self) -> str:
        return (
            f"{self.api_base}/org/{self.organization_id}/filial/{self.filial_id}"
            f"/centro_distribuicao/{self.distribution_center_id}/loja/produtos/em-oferta"
        )

    def build_headers(self, site_url: str, token: str | None = None) -> dict[str, str]:
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Origin": site_url,
            "Referer": f"{site_url}/",
            "domainkey": self.domain_key,
            "organizationid": self.organization_id,
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
        }
        if token:
            headers["Authorization"] = f"Bearer {token}"
            headers["sessao-id"] = ""
        else:
            headers["Authorization"] = "Bearer"
        return headers

    def build_login_payload(self) -> dict[str, str]:
        if not self.login_key:
            raise ValueError("login_key is required for API authentication")
        return {
            "domain": self.domain_key,
            "username": "loja",
            "key": self.login_key,
        }
