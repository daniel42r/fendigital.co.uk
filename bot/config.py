"""Environment-based configuration for the arbitrage bot."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class Config:
    odds_api_key: str
    telegram_bot_token: str
    telegram_chat_id: str
    poll_interval_sec: int
    sports: tuple[str, ...]
    regions: str
    min_profit_pct: float
    total_stake: float
    log_level: str


class ConfigError(RuntimeError):
    """Raised when required configuration is missing or malformed."""


def _require(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise ConfigError(
            f"Missing required env var {name!r}. Copy bot/.env.example to bot/.env "
            "and fill it in."
        )
    return value


def load_config(env_file: str | os.PathLike[str] | None = None) -> Config:
    """Load config from ``bot/.env`` (or a custom path) + process environment."""
    env_path = Path(env_file) if env_file else Path(__file__).parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)

    return Config(
        odds_api_key=_require("ODDS_API_KEY"),
        telegram_bot_token=_require("TELEGRAM_BOT_TOKEN"),
        telegram_chat_id=_require("TELEGRAM_CHAT_ID"),
        poll_interval_sec=int(os.environ.get("POLL_INTERVAL_SEC", "30")),
        sports=tuple(
            s.strip()
            for s in os.environ.get(
                "SPORTS",
                "soccer_epl,soccer_uefa_champs_league,basketball_nba,"
                "americanfootball_nfl,mma_mixed_martial_arts",
            ).split(",")
            if s.strip()
        ),
        regions=os.environ.get("REGIONS", "uk,eu,us"),
        min_profit_pct=float(os.environ.get("MIN_PROFIT_PCT", "0.5")),
        total_stake=float(os.environ.get("TOTAL_STAKE", "100")),
        log_level=os.environ.get("LOG_LEVEL", "INFO").upper(),
    )
