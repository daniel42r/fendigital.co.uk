"""Unit tests for the arbitrage math."""
from __future__ import annotations

from datetime import datetime, timezone

from bot.arbitrage import (
    Bookmaker,
    Match,
    Outcome,
    find_best_odds,
    implied_prob_sum,
    is_arbitrage,
)


def _match(bookmakers: list[Bookmaker]) -> Match:
    return Match(
        id="test-match",
        sport_key="soccer_epl",
        sport_title="EPL",
        commence_time=datetime(2030, 1, 1, tzinfo=timezone.utc),
        home_team="Home",
        away_team="Away",
        bookmakers=tuple(bookmakers),
    )


def _bm(key: str, prices: dict[str, float]) -> Bookmaker:
    return Bookmaker(
        key=key,
        title=key.title(),
        outcomes=tuple(
            Outcome(name=n, price=p, bookmaker=key.title(), bookmaker_key=key)
            for n, p in prices.items()
        ),
    )


def test_find_best_odds_picks_highest_price_per_outcome():
    m = _match(
        [
            _bm("a", {"Home": 2.10, "Draw": 3.30, "Away": 3.80}),
            _bm("b", {"Home": 2.50, "Draw": 3.10, "Away": 3.00}),
            _bm("c", {"Home": 2.00, "Draw": 3.40, "Away": 4.10}),
        ]
    )
    best = find_best_odds(m)
    assert best["Home"].price == 2.50 and best["Home"].bookmaker_key == "b"
    assert best["Draw"].price == 3.40 and best["Draw"].bookmaker_key == "c"
    assert best["Away"].price == 4.10 and best["Away"].bookmaker_key == "c"


def test_implied_prob_sum_three_way():
    # A fair three-way market with no margin sums to 1.0
    assert abs(implied_prob_sum([3.0, 3.0, 3.0]) - 1.0) < 1e-9


def test_is_arbitrage_true_three_way():
    # Best prices 2.50 / 3.40 / 4.10 → S = 0.4 + 0.294... + 0.244... ≈ 0.9381
    # Profit ≈ 6.19%
    m = _match(
        [
            _bm("a", {"Home": 2.10, "Draw": 3.30, "Away": 3.80}),
            _bm("b", {"Home": 2.50, "Draw": 3.10, "Away": 3.00}),
            _bm("c", {"Home": 2.00, "Draw": 3.40, "Away": 4.10}),
        ]
    )
    opp = is_arbitrage(m, min_profit_pct=0.5, total_stake=100.0)
    assert opp is not None
    assert 6.0 < opp.profit_pct < 6.5

    # Return on every outcome should equal total_stake / S (same regardless of outcome)
    returns = [leg.stake * leg.price for leg in opp.legs]
    assert max(returns) - min(returns) < 0.05  # rounding tolerance
    assert sum(leg.stake for leg in opp.legs) == 100.00 or abs(
        sum(leg.stake for leg in opp.legs) - 100.0
    ) < 0.05


def test_is_arbitrage_false_three_way_with_margin():
    # Typical bookmaker margin: S > 1 → no arb
    m = _match([_bm("a", {"Home": 2.10, "Draw": 3.30, "Away": 3.50})])
    assert is_arbitrage(m, min_profit_pct=0.0) is None


def test_is_arbitrage_two_way():
    # Tennis / NBA moneyline, 2-way:  1/2.10 + 1/2.10 = 0.952 → ~4.76% arb
    m = _match(
        [
            _bm("a", {"Player A": 2.10, "Player B": 1.70}),
            _bm("b", {"Player A": 1.80, "Player B": 2.10}),
        ]
    )
    opp = is_arbitrage(m, min_profit_pct=0.5, total_stake=1000.0)
    assert opp is not None
    assert 4.5 < opp.profit_pct < 5.0
    assert len(opp.legs) == 2


def test_is_arbitrage_below_min_profit_pct_returns_none():
    m = _match(
        [
            _bm("a", {"Home": 2.02, "Away": 2.02}),  # arb ~0.99% profit
        ]
    )
    assert is_arbitrage(m, min_profit_pct=5.0) is None
    opp = is_arbitrage(m, min_profit_pct=0.5)
    assert opp is not None


def test_is_arbitrage_rejects_malformed_odds():
    m = _match([_bm("a", {"Home": 1.0, "Away": 100.0})])  # price == 1.0 is invalid
    assert is_arbitrage(m, min_profit_pct=-100.0) is None
