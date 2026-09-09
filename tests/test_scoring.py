from dealhunter.services.price_history import PriceStats
from dealhunter.services.scoring import compute_scores


def test_good_deal_scores_high_and_confidence_matters():
    stats = PriceStats(2_000_000, 2_700_000, 2_800_000, 2_900_000, 2_300_000, 2_300_000, 2_300_000, 20)
    good = compute_scores(2_000_000, 1_900_000, stats, .95, seller_trust=.95, product_quality=.9, popularity=.8, affiliate_available=True)
    uncertain = compute_scores(2_000_000, 1_900_000, stats, .4, seller_trust=.95, product_quality=.9, popularity=.8, affiliate_available=True)
    assert good.deal_score > 80
    assert good.opportunity_score > uncertain.opportunity_score
    assert good.share_score > 80
