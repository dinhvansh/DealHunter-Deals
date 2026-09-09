from dealhunter.services.promotions import DiscountType, VoucherRule, optimize_promotions


def test_promotion_optimizer_stack_groups():
    vouchers = [
        VoucherRule("shop100", DiscountType.FIXED, 100_000, min_spend=1_000_000, stack_group="shop"),
        VoucherRule("shop50", DiscountType.FIXED, 50_000, min_spend=1_000_000, stack_group="shop"),
        VoucherRule("platform20", DiscountType.PERCENT, 20, max_discount=500_000, min_spend=1_500_000, stack_group="platform"),
        VoucherRule("ship30", DiscountType.FREESHIP, 30_000, min_spend=0, stack_group="shipping", confidence=.9),
    ]
    result = optimize_promotions(2_500_000, vouchers)
    assert result.estimated_price == 1_870_000
    assert {v.code for v in result.applied} == {"shop100", "platform20", "ship30"}
    assert result.confidence == .9
