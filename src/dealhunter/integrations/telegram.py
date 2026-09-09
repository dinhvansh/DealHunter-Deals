from __future__ import annotations

from dataclasses import dataclass

import httpx

from dealhunter.notifications import AlertMessage, Notifier


@dataclass(slots=True)
class TelegramNotifier(Notifier):
    bot_token: str
    chat_id: str

    async def send(self, message: AlertMessage) -> None:
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        text = f"{message.title}\n\n{message.body}"
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(url, json={"chat_id": self.chat_id, "text": text, "disable_web_page_preview": True})
            response.raise_for_status()
