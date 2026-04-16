# Arbitrage Betting Bot

A Python bot that polls [The Odds API](https://the-odds-api.com/) for live
match odds across multiple bookmakers, finds arbitrage opportunities (sure
bets), and sends them to a Telegram chat.

**Detection only.** This bot does not place bets.

---

## How arbitrage works

For a match with outcomes `O_1..O_n` and best decimal odds `p_1..p_n` across
all bookmakers:

- Implied-probability sum `S = Σ 1/p_i`
- If `S < 1`, an arbitrage exists.
- Profit margin: `(1 - S) * 100 %`.
- Stake allocation for a total stake `T`: `t_i = T * (1/p_i) / S`. The return
  `t_i * p_i = T / S` is then the same regardless of which outcome wins — a
  guaranteed profit.

Works the same way for 2-way (tennis, NBA moneyline, MMA) and 3-way (football
1X2) markets.

---

## Prerequisites

- Python 3.11+
- A free [The Odds API](https://the-odds-api.com/) key (500 req/month on free
  plan — see **Quota tuning** below)
- A Telegram account

---

## Step 1 — Create a Telegram bot

1. Open Telegram and message [@BotFather](https://t.me/BotFather).
2. Send `/newbot`, pick a name and a username ending in `bot`.
3. BotFather replies with an **HTTP API token** — save it for `TELEGRAM_BOT_TOKEN`.
4. Open a chat with your new bot and send it any message (e.g. `hi`).
5. Visit `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates` in a browser
   and copy the numeric `chat.id` value from the JSON response — that goes in
   `TELEGRAM_CHAT_ID`.

To send alerts to a **channel** instead: add the bot as an admin of the
channel, then use the channel's `@username` (public) or numeric `-100...` id
(private) as `TELEGRAM_CHAT_ID`.

---

## Step 2 — Install and configure

```bash
cd bot
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# Edit .env and fill in ODDS_API_KEY, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
```

---

## Step 3 — Verify everything works (dry-run)

From the **repo root** (not from inside `bot/`):

```bash
python -m bot --dry-run
```

This runs a single polling cycle, logs arbs to stdout instead of sending
Telegram messages, and exits. You'll see lines like:

```
odds fetched sport=soccer_epl used=12 remaining=488
cycle done sports=5 matches=137 arbs=0 alerts_sent=0 dedup_cache=0
```

Zero arbs on a given cycle is normal — major pre-match markets are efficiently
priced. To force a Telegram test alert end-to-end, temporarily set
`MIN_PROFIT_PCT=-5.0` in `.env` (accepts negative margins, so every match
"alerts"), run once, then revert.

---

## Step 4 — Run continuously

```bash
python -m bot
```

The bot polls every `POLL_INTERVAL_SEC` seconds, honours `Ctrl-C` for a clean
shutdown, and deduplicates alerts so the same arb isn't spammed every cycle
(re-alerts fire only when the bookmaker set changes, or the profit margin
shifts by ≥0.5 percentage points).

---

## Configuration reference (`.env`)

| Var | Default | Notes |
|-----|---------|-------|
| `ODDS_API_KEY` | — | **Required.** From the-odds-api.com. |
| `TELEGRAM_BOT_TOKEN` | — | **Required.** From @BotFather. |
| `TELEGRAM_CHAT_ID` | — | **Required.** Numeric id or `@channelname`. |
| `POLL_INTERVAL_SEC` | `30` | See **Quota tuning** below. |
| `SPORTS` | 5 defaults | Comma-separated Odds API sport keys. |
| `REGIONS` | `uk,eu,us` | Comma-separated: `uk`, `eu`, `us`, `au`. |
| `MIN_PROFIT_PCT` | `0.5` | Minimum arb margin to alert on. |
| `TOTAL_STAKE` | `100` | Used only for stake-split numbers in messages. |
| `LOG_LEVEL` | `INFO` | `DEBUG` / `INFO` / `WARNING` / `ERROR`. |

---

## Quota tuning

Each sport = 1 API request per poll cycle. With 5 sports enabled, monthly cost
is `5 * (30 * 24 * 3600 / interval)`:

| `POLL_INTERVAL_SEC` | Monthly requests | Suggested plan |
|---------------------|------------------|----------------|
| 30  | ~432,000 | $119/mo (500k) |
| 60  | ~216,000 | $119/mo (500k) |
| 300 | ~43,000  | $30/mo  (100k) |
| 900 | ~14,000  | $10/mo  (20k)  |
| 3600| ~3,600   | Free (500) — barely |

The user asked for "every second" — that is **not achievable** on any public
API plan, and bookmaker odds don't change that fast anyway. Start at 300s,
tune down once you understand your quota.

---

## Legal note

Arbitrage betting is legal in most jurisdictions, but **violates the Terms
of Service of nearly every bookmaker**. Consequences, in order of likelihood:

1. Stakes limited to pennies.
2. Account closed and balance returned.
3. Funds withheld pending an investigation.

Use multiple accounts, small stakes, and soft bookmakers at your own risk.
This tool only *detects* opportunities — what you do with them is on you.
