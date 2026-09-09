from dealhunter.services.watchlist import WatchMode, WatchRule, should_alert


def test_watchlist_alert_reasons():
    rule = WatchRule("v", mode=WatchMode.HOT, target_price=1_500_000, min_deal_score=90)
    alert, reasons = should_alert(rule, 1_450_000, 92, is_new_low=True)
    assert alert is True
    assert set(reasons) == {"target_price", "deal_score", "historical_low"}
