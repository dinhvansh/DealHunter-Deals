from dealhunter.services.affiliate import QueryParamAffiliateProvider, create_affiliate_link


def test_affiliate_link_generation_is_stable():
    provider = QueryParamAffiliateProvider("aff_id", "abc")
    first = create_affiliate_link(provider, "https://example.com/p/1", "telegram")
    second = create_affiliate_link(provider, "https://example.com/p/1", "telegram")
    assert "aff_id=abc" in first.affiliate_url
    assert first.redirect_code == second.redirect_code
