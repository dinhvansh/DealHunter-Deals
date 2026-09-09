from dealhunter.scheduler import policy_for_mode


def test_scheduler_modes():
    assert policy_for_mode("HOT").interval.total_seconds() == 45 * 60
    assert policy_for_mode("NORMAL").interval.total_seconds() == 2 * 60 * 60
