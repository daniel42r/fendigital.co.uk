"""Send arbitrage alerts to a Telegram chat via the Bot API."""
from __future__ import annotations

import asyncio
import html

import httpx
from loguru import logger

from .arbitrage import ArbOpportunity

TELEGRAM_API = "https://api.telegram.org/bot{token}/sendMessage"


def format_message(opp: ArbOpportunity) -> str:
    """Render an ArbOpportunity as Telegram-HTML."""
    lines = [
        f"<b>🎯 ARB {opp.profit_pct:.2f}% — {html.escape(opp.sport_title)}</b>",
        f"{html.escape(opp.home_team)} vs {html.escape(opp.away_team)}",
        f"Kick-off: {opp.commence_time.strftime('%Y-%m-%d %H:%M UTC')}",
        "",
    ]
    for leg in opp.legs:
        lines.append(
            f"• <b>{html.escape(leg.outcome_name)}</b> @ {leg.price:.2f} "
            f"({html.escape(leg.bookmaker)}) — stake {leg.stake:.2f}"
        )
    lines.append("")
    lines.append(
        f"Total stake {opp.total_stake:.2f} → guaranteed return "
        f"{opp.guaranteed_return:.2f}"
    )
    return "\n".join(lines)


class TelegramNotifier:
    def __init__(self, bot_token: str, chat_id: str, timeout: float = 10.0):
        self._url = TELEGRAM_API.format(token=bot_token)
        self._chat_id = chat_id
        self._client = httpx.AsyncClient(timeout=timeout)

    async def close(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> "TelegramNotifier":
        return self

    async def __aexit__(self, *_exc) -> None:
        await self.close()

    async def send(self, text: str, max_retries: int = 3) -> bool:
        payload = {
            "chat_id": self._chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }
        backoff = 1.0
        for attempt in range(1, max_retries + 1):
            try:
                resp = await self._client.post(self._url, json=payload)
                if resp.status_code == 200:
                    return True
                if resp.status_code in (400, 401, 403):
                    # Not retryable — bad token / chat id / formatting.
                    logger.error(
                        "Telegram send failed (no retry): {} {}",
                        resp.status_code,
                        resp.text[:200],
                    )
                    return False
                logger.warning(
                    "Telegram send attempt {}/{} got {}: {}",
                    attempt,
                    max_retries,
                    resp.status_code,
                    resp.text[:200],
                )
            except httpx.HTTPError as e:
                logger.warning(
                    "Telegram send attempt {}/{} errored: {}", attempt, max_retries, e
                )
            if attempt < max_retries:
                await asyncio.sleep(backoff)
                backoff *= 2
        return False

    async def send_arb(self, opp: ArbOpportunity) -> bool:
        return await self.send(format_message(opp))
