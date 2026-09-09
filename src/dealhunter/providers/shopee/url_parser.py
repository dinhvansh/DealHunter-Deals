import re
from urllib.parse import urlparse

_PATTERNS = [
    re.compile(r"/product/(?P<shop>\d+)/(?P<item>\d+)(?:[/?#]|$)"),
    re.compile(r"-i\.(?P<shop>\d+)\.(?P<item>\d+)(?:[/?#]|$)"),
]


def parse_shopee_ids(value: str) -> tuple[str, str]:
    text = value.strip()
    path = urlparse(text).path if "://" in text else text
    for candidate in (text, path):
        for pattern in _PATTERNS:
            match = pattern.search(candidate)
            if match:
                return match.group("shop"), match.group("item")
    raise ValueError(f"Could not parse Shopee shop/item id from: {value}")
