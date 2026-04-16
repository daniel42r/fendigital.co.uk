"""Async client for The Odds API v4.

Docs: https://the-odds-api.com/liveapi/guides/v4/
"""
from __future__ import annotations

from datetime import datetime

import httpx
from loguru import logger

from .arbitrage import Bookmaker, Match, Outcome

BASE_URL = "https://api.the-odds-api.com/v4"


class OddsAPIError(RuntimeError):
    pass


class OddsClient:
    def __init__(self, api_key: str, regions: str = "uk,eu,us", timeout: float = 15.0):
        self._api_key = api_key
        self._regions = regions
        self._client = httpx.AsyncClient(timeout=timeout)

    async def close(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> "OddsClient":
        return self

    async def __aexit__(self, *_exc) -> None:
        await self.close()

    async def fetch_odds(self, sport_key: str) -> list[Match]:
        """Fetch H2H (match-winner) odds for ``sport_key`` across configured regions."""
        url = f"{BASE_URL}/sports/{sport_key}/odds"
        params = {
            "apiKey": self._api_key,
            "regions": self._regions,
            "markets": "h2h",
            "oddsFormat": "decimal",
            "dateFormat": "iso",
        }
        try:
            resp = await self._client.get(url, params=params)
        except httpx.HTTPError as e:
            raise OddsAPIError(f"Network error fetching {sport_key}: {e}") from e

        remaining = resp.headers.get("x-requests-remaining", "?")
        used = resp.headers.get("x-requests-used", "?")

        if resp.status_code == 401:
            raise OddsAPIError(
                "401 Unauthorized — check ODDS_API_KEY in bot/.env"
            )
        if resp.status_code == 422:
            logger.warning(
                "422 for sport {} — bad sport key? body={}",
                sport_key,
                resp.text[:200],
            )
            return []
        if resp.status_code == 429:
            raise OddsAPIError(
                f"429 Rate limited. Quota used={used} remaining={remaining}. "
                "Increase POLL_INTERVAL_SEC or upgrade plan."
            )
        if resp.status_code >= 500:
            raise OddsAPIError(f"Upstream {resp.status_code}: {resp.text[:200]}")
        resp.raise_for_status()

        logger.debug(
            "odds fetched sport={} used={} remaining={}",
            sport_key,
            used,
            remaining,
        )

        return [_parse_match(m) for m in resp.json()]


def _parse_match(data: dict) -> Match:
    bookmakers: list[Bookmaker] = []
    for bm in data.get("bookmakers", []):
        # Find the H2H market (there's only one per bookmaker when markets=h2h).
        h2h = next(
            (mk for mk in bm.get("markets", []) if mk.get("key") == "h2h"),
            None,
        )
        if h2h is None:
            continue
        outcomes = tuple(
            Outcome(
                name=o["name"],
                price=float(o["price"]),
                bookmaker=bm.get("title", bm["key"]),
                bookmaker_key=bm["key"],
            )
            for o in h2h.get("outcomes", [])
            if "price" in o
        )
        if outcomes:
            bookmakers.append(
                Bookmaker(
                    key=bm["key"],
                    title=bm.get("title", bm["key"]),
                    outcomes=outcomes,
                )
            )

    return Match(
        id=data["id"],
        sport_key=data.get("sport_key", ""),
        sport_title=data.get("sport_title", ""),
        commence_time=datetime.fromisoformat(
            data["commence_time"].replace("Z", "+00:00")
        ),
        home_team=data.get("home_team", ""),
        away_team=data.get("away_team", ""),
        bookmakers=tuple(bookmakers),
    )
