from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class AlertMessage:
    title: str
    body: str


class Notifier:
    async def send(self, message: AlertMessage) -> None:
        raise NotImplementedError


class StdoutNotifier(Notifier):
    async def send(self, message: AlertMessage) -> None:
        print(f"{message.title}\n{message.body}")
