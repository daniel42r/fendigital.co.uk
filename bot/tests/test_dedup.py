"""Unit tests for AlertDedup."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from bot.arbitrage import ArbLeg, ArbOpportunity
from bot.dedup import AlertDedup

NOW = datetime(2030, 1, 1, 12, 0, tzinfo=timezone.utc)
FUTURE = NOW + timedelta(hours=2)


def _opp(profit_pct: float, mapping: dict[str, str], match_id: str = "m1") -> ArbOpportunity:
    legs = tuple(
        ArbLeg(
            outcome_name=outcome,
            price=2.5,
            bookmaker=bmkey.title(),
            bookmaker_key=bmkey,
            stake=50.0,
        )
        for outcome, bmkey in mapping.items()
    )
    return ArbOpportunity(
        match_id=match_id,
        sport_title="EPL",
        home_team="A",
        away_team="B",
        commence_time=FUTURE,
        profit_pct=profit_pct,
        total_stake=100.0,
        guaranteed_return=102.0,
        legs=legs,
        detected_at=NOW,
    )


def test_first_alert_fires():
    d = AlertDedup()
    assert d.should_alert(_opp(1.0, {"Home": "bet365", "Away": "pinnacle"}), now=NOW)


def test_duplicate_does_not_fire():
    d = AlertDedup(profit_delta_pp=0.5)
    opp = _opp(1.0, {"Home": "bet365", "Away": "pinnacle"})
    assert d.should_alert(opp, now=NOW) is True
    assert d.should_alert(opp, now=NOW) is False


def test_profit_change_refires():
    d = AlertDedup(profit_delta_pp=0.5)
    assert d.should_alert(_opp(1.0, {"Home": "bet365", "Away": "pinnacle"}), now=NOW)
    # Same match + bookmakers, but profit shifted by >= 0.5pp
    assert d.should_alert(_opp(1.6, {"Home": "bet365", "Away": "pinnacle"}), now=NOW)
    # Shift below threshold
    assert not d.should_alert(
        _opp(1.7, {"Home": "bet365", "Away": "pinnacle"}), now=NOW
    )


def test_different_bookmaker_mapping_is_new_alert():
    d = AlertDedup()
    assert d.should_alert(_opp(1.0, {"Home": "bet365", "Away": "pinnacle"}), now=NOW)
    # Same match, but now William Hill offers the best "Home" price → new arb
    assert d.should_alert(_opp(1.0, {"Home": "williamhill", "Away": "pinnacle"}), now=NOW)


def test_expired_entries_are_purged():
    d = AlertDedup()
    d.should_alert(_opp(1.0, {"Home": "bet365", "Away": "pinnacle"}), now=NOW)
    assert len(d) == 1
    # Advance time past commence_time → purge on next call
    later = FUTURE + timedelta(seconds=1)
    d.should_alert(
        _opp(1.0, {"Home": "bet365", "Away": "pinnacle"}, match_id="m2"),
        now=later,
    )
    # m1 should have been purged during cleanup
    assert len(d) == 1
