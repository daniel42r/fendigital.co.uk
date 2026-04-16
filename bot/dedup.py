"""Alert deduplication so we don't spam Telegram with the same arb every poll.

An arb is identified by the tuple:
    (match_id, frozenset((outcome_name, bookmaker_key)))

so that a shift from "bet365 offered Home @ 2.50" to "Pinnacle offered Home @ 2.55"
is treated as a *new* opportunity worth re-alerting on.

Re-alerts also fire if the same (match + bookmaker set) comes back with a
profit_pct that has moved by more than ``profit_delta_pp`` percentage points.

Entries self-expire once the match's ``commence_time`` has passed.
"""
from __future__ import annotations

from datetime import datetime, timezone

from .arbitrage import ArbOpportunity


class AlertDedup:
    def __init__(self, profit_delta_pp: float = 0.5):
        self._profit_delta_pp = profit_delta_pp
        # key -> (last_profit_pct, commence_time)
        self._seen: dict[tuple, tuple[float, datetime]] = {}

    @staticmethod
    def _key(opp: ArbOpportunity) -> tuple:
        return (
            opp.match_id,
            frozenset((leg.outcome_name, leg.bookmaker_key) for leg in opp.legs),
        )

    def _purge_expired(self, now: datetime) -> None:
        stale = [k for k, (_, ct) in self._seen.items() if ct <= now]
        for k in stale:
            del self._seen[k]

    def should_alert(self, opp: ArbOpportunity, *, now: datetime | None = None) -> bool:
        now = now or datetime.now(timezone.utc)
        self._purge_expired(now)
        key = self._key(opp)
        prev = self._seen.get(key)
        if prev is None:
            self._seen[key] = (opp.profit_pct, opp.commence_time)
            return True
        prev_profit, _ = prev
        if abs(opp.profit_pct - prev_profit) >= self._profit_delta_pp:
            self._seen[key] = (opp.profit_pct, opp.commence_time)
            return True
        return False

    def __len__(self) -> int:
        return len(self._seen)
