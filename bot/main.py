"""Main polling loop: fetch odds, detect arbs, notify via Telegram."""
from __future__ import annotations

import argparse
import asyncio
import signal
import sys

from loguru import logger

from .arbitrage import is_arbitrage
from .config import Config, ConfigError, load_config
from .dedup import AlertDedup
from .odds_client import OddsAPIError, OddsClient
from .telegram_notifier import TelegramNotifier, format_message


def _configure_logging(level: str) -> None:
    logger.remove()
    logger.add(sys.stderr, level=level)


async def _poll_once(
    cfg: Config,
    odds: OddsClient,
    tele: TelegramNotifier | None,
    dedup: AlertDedup,
) -> None:
    total_matches = 0
    total_arbs = 0
    total_sent = 0
    for sport in cfg.sports:
        try:
            matches = await odds.fetch_odds(sport)
        except OddsAPIError as e:
            logger.error("Fetch failed for {}: {}", sport, e)
            continue
        total_matches += len(matches)
        for m in matches:
            opp = is_arbitrage(
                m,
                min_profit_pct=cfg.min_profit_pct,
                total_stake=cfg.total_stake,
            )
            if opp is None:
                continue
            total_arbs += 1
            if not dedup.should_alert(opp):
                logger.debug("Dedup suppressed {}", opp.match_id)
                continue
            if tele is None:
                logger.info("[dry-run] arb found:\n{}", format_message(opp))
                total_sent += 1
            else:
                ok = await tele.send_arb(opp)
                if ok:
                    total_sent += 1
                    logger.info(
                        "Alerted {:.2f}% arb on {} vs {}",
                        opp.profit_pct,
                        opp.home_team,
                        opp.away_team,
                    )
    logger.info(
        "cycle done sports={} matches={} arbs={} alerts_sent={} dedup_cache={}",
        len(cfg.sports),
        total_matches,
        total_arbs,
        total_sent,
        len(dedup),
    )


async def run(dry_run: bool = False) -> None:
    try:
        cfg = load_config()
    except ConfigError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(2)
    _configure_logging(cfg.log_level)
    logger.info(
        "Starting bot dry_run={} interval={}s sports={} regions={} min_profit={}%",
        dry_run,
        cfg.poll_interval_sec,
        ",".join(cfg.sports),
        cfg.regions,
        cfg.min_profit_pct,
    )
    dedup = AlertDedup()
    stop = asyncio.Event()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, stop.set)
        except NotImplementedError:  # pragma: no cover - Windows
            pass

    async with OddsClient(api_key=cfg.odds_api_key, regions=cfg.regions) as odds:
        tele: TelegramNotifier | None
        if dry_run:
            tele = None
            await _poll_once(cfg, odds, tele, dedup)
            return
        async with TelegramNotifier(
            bot_token=cfg.telegram_bot_token,
            chat_id=cfg.telegram_chat_id,
        ) as tele:
            while not stop.is_set():
                try:
                    await _poll_once(cfg, odds, tele, dedup)
                except Exception as e:  # noqa: BLE001 - want resilience
                    logger.exception("Unhandled error in poll cycle: {}", e)
                try:
                    await asyncio.wait_for(
                        stop.wait(), timeout=cfg.poll_interval_sec
                    )
                except asyncio.TimeoutError:
                    pass
    logger.info("Shutdown complete.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Arbitrage betting bot.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run one cycle, log arbs to stdout instead of sending to Telegram.",
    )
    args = parser.parse_args()
    asyncio.run(run(dry_run=args.dry_run))


if __name__ == "__main__":
    main()
