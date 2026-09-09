from dealhunter.providers.shopee.provider import ShopeeProvider
from dealhunter.providers.shopee.transport import ChromeJsonTransport, HttpJsonTransport


def test_provider_uses_google_chrome_transport():
    provider = ShopeeProvider(
        transport_mode="chrome",
        chrome_profile_dir="./tmp-profile",
        chrome_headless=True,
    )
    assert isinstance(provider.transport, ChromeJsonTransport)
    assert str(provider.transport.profile_dir).endswith("tmp-profile")


def test_legacy_playwright_mode_maps_to_google_chrome():
    provider = ShopeeProvider(transport_mode="playwright")
    assert isinstance(provider.transport, ChromeJsonTransport)


def test_http_mode_remains_available():
    provider = ShopeeProvider(transport_mode="http")
    assert isinstance(provider.transport, HttpJsonTransport)
