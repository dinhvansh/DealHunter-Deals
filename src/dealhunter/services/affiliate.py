from __future__ import annotations

import hashlib
from dataclasses import dataclass
from urllib.parse import urlencode


@dataclass(slots=True)
class AffiliateLink:
    destination_url: str
    affiliate_url: str
    redirect_code: str


class AffiliateProvider:
    name = "generic"

    def build_url(self, destination_url: str, campaign: str | None = None) -> str:
        raise NotImplementedError


class QueryParamAffiliateProvider(AffiliateProvider):
    def __init__(self, key: str = "aff_id", value: str = "demo") -> None:
        self.key = key
        self.value = value

    def build_url(self, destination_url: str, campaign: str | None = None) -> str:
        separator = "&" if "?" in destination_url else "?"
        params = {self.key: self.value}
        if campaign:
            params["utm_campaign"] = campaign
        return destination_url + separator + urlencode(params)


def make_redirect_code(destination_url: str, campaign: str | None = None) -> str:
    raw = f"{destination_url}|{campaign or ''}".encode()
    return hashlib.sha256(raw).hexdigest()[:12]


def create_affiliate_link(provider: AffiliateProvider, destination_url: str, campaign: str | None = None) -> AffiliateLink:
    return AffiliateLink(
        destination_url=destination_url,
        affiliate_url=provider.build_url(destination_url, campaign),
        redirect_code=make_redirect_code(destination_url, campaign),
    )
