"""Pure arbitrage-detection math.

For a match with outcomes ``O_1..O_n`` and best-available decimal odds
``p_1..p_n`` across all bookmakers:

* Implied-probability sum: ``S = sum(1/p_i)``
* An arbitrage exists iff ``S < 1``.
* Profit margin:  ``(1 - S) * 100`` percent.
* Stake allocation for a total stake ``T``:  ``t_i = T * (1/p_i) / S``
  This makes the return ``t_i * p_i = T / S`` identical on every outcome.

Works transparently for 2-way (tennis, NBA moneyline, MMA) and 3-way
(football 1X2) markets — the code only cares about ``len(outcomes)``.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable


@dataclass(frozen=True)
class Outcome:
    name: str
    price: float           # decimal odds, e.g. 2.50
    bookmaker: str         # human-readable title, e.g. "Pinnacle"
    bookmaker_key: str     # machine key, e.g. "pinnacle"


@dataclass(frozen=True)
class Bookmaker:
    key: str
    title: str
    outcomes: tuple[Outcome, ...]


@dataclass(frozen=True)
class Match:
    id: str
    sport_key: str
    sport_title: str
    commence_time: datetime
    home_team: str
    away_team: str
    bookmakers: tuple[Bookmaker, ...]


@dataclass(frozen=True)
class ArbLeg:
    outcome_name: str
    price: float
    bookmaker: str
    bookmaker_key: str
    stake: float


@dataclass(frozen=True)
class ArbOpportunity:
    match_id: str
    sport_title: str
    home_team: str
    away_team: str
    commence_time: datetime
    profit_pct: float
    total_stake: float
    guaranteed_return: float
    legs: tuple[ArbLeg, ...]
    detected_at: datetime


def find_best_odds(match: Match) -> dict[str, Outcome]:
    """For each outcome name seen in the match, return the Outcome with the
    highest decimal price across all bookmakers."""
    best: dict[str, Outcome] = {}
    for bm in match.bookmakers:
        for oc in bm.outcomes:
            current = best.get(oc.name)
            if current is None or oc.price > current.price:
                best[oc.name] = oc
    return best


def implied_prob_sum(prices: Iterable[float]) -> float:
    return sum(1.0 / p for p in prices)


def is_arbitrage(
    match: Match,
    min_profit_pct: float,
    total_stake: float = 100.0,
) -> ArbOpportunity | None:
    """Return an ``ArbOpportunity`` if an arb meeting ``min_profit_pct`` exists."""
    best = find_best_odds(match)
    if len(best) < 2:
        return None

    # Sanity: every outcome must appear from at least one bookmaker. If a
    # bookmaker only offers a 2-way H2H but the match is 3-way (football 1X2),
    # we combine outcomes across books anyway — that's the whole point of arb.
    prices = [oc.price for oc in best.values()]
    if any(p <= 1.0 for p in prices):
        return None  # malformed odds

    s = implied_prob_sum(prices)
    profit_pct = (1.0 - s) * 100.0
    if profit_pct < min_profit_pct:
        return None

    legs = tuple(
        ArbLeg(
            outcome_name=name,
            price=oc.price,
            bookmaker=oc.bookmaker,
            bookmaker_key=oc.bookmaker_key,
            stake=round(total_stake * (1.0 / oc.price) / s, 2),
        )
        for name, oc in best.items()
    )
    guaranteed_return = round(total_stake / s, 2)

    return ArbOpportunity(
        match_id=match.id,
        sport_title=match.sport_title,
        home_team=match.home_team,
        away_team=match.away_team,
        commence_time=match.commence_time,
        profit_pct=round(profit_pct, 3),
        total_stake=total_stake,
        guaranteed_return=guaranteed_return,
        legs=legs,
        detected_at=datetime.now(timezone.utc),
    )
