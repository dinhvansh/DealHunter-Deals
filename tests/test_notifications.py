import asyncio

from dealhunter.notifications import AlertMessage, StdoutNotifier


def test_stdout_notifier(capsys):
    asyncio.run(StdoutNotifier().send(AlertMessage("Deal", "SSD giảm giá")))
    assert "SSD giảm giá" in capsys.readouterr().out
