# 🤖 Binance Futures Testnet Trading Bot

A command-line trading bot that places **MARKET** and **LIMIT** orders on the **Binance Futures Testnet** using the official `python-binance` library.

Built as part of the **Python Developer Intern Assignment**.

---

## 📁 Project Structure

```
Trading Bot/
├── bot.py              # Main entry point — CLI + order orchestration
├── config.py           # Environment config loader
├── logger.py           # Dual-handler logger (file + console)
├── validator.py        # Input validation module (fail-fast)
├── test_validator.py   # Unit tests (pytest)
├── requirements.txt    # Python dependencies
├── .env                # ⚠️ Your API keys — DO NOT COMMIT
├── .env.example        # Safe template to share
├── .gitignore          # Excludes .env and caches
└── logs/
    └── bot.log         # Auto-generated trade log
```

---

## ⚙️ Setup

### 1. Prerequisites

- Python 3.9 or higher
- pip

### 2. Clone / Download

```bash
# If using Git:
git clone <your-repo-url>
cd "Trading Bot"

# Or extract the zip and cd into the folder
```

### 3. Create Virtual Environment

```bash
python -m venv venv

# Windows:
venv\Scripts\activate

# macOS/Linux:
source venv/bin/activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure API Keys

```bash
# Copy the example file
copy .env.example .env     # Windows
# cp .env.example .env    # macOS/Linux

# Edit .env and add your Binance Futures Testnet keys:
# Get keys at: https://testnet.binancefuture.com
BINANCE_API_KEY=your_key_here
BINANCE_API_SECRET=your_secret_here
```

> ⚠️ **Never commit `.env` to Git.** It is already in `.gitignore`.

---

## 🚀 Usage

### Place a MARKET Order

```bash
# BUY 0.01 BTC at market price
python bot.py --symbol BTCUSDT --side BUY --order-type MARKET --quantity 0.01

# SELL 0.1 ETH at market price
python bot.py --symbol ETHUSDT --side SELL --order-type MARKET --quantity 0.1
```

### Place a LIMIT Order

```bash
# BUY 0.01 BTC with limit price of 65,000 USDT
python bot.py --symbol BTCUSDT --side BUY --order-type LIMIT --quantity 0.01 --price 65000

# SELL 0.01 BTC with limit price of 70,000 USDT
python bot.py --symbol BTCUSDT --side SELL --order-type LIMIT --quantity 0.01 --price 70000
```

### [BONUS] View Open Positions + PnL

```bash
python bot.py --show-positions
```

### [BONUS] Cancel an Existing Order

```bash
python bot.py --cancel-order --order-id 3926524958 --symbol BTCUSDT
```

### Show Help

```bash
python bot.py --help
```

---

## 📋 Command-Line Arguments

| Argument | Type | Required | Description |
|---|---|---|---|
| `--symbol` | `str` | ✅ (for orders) | Trading pair, e.g. `BTCUSDT` |
| `--side` | `BUY\|SELL` | ✅ (for orders) | Order direction |
| `--order-type` | `MARKET\|LIMIT` | ✅ (for orders) | Order type |
| `--quantity` | `float` | ✅ (for orders) | Amount to trade (must be > 0) |
| `--price` | `float` | ✅ for LIMIT | Limit price (must be > 0) |
| `--show-positions` | flag | ❌ | [BONUS] Show open positions + PnL |
| `--cancel-order` | flag | ❌ | [BONUS] Cancel an order by ID |
| `--order-id` | `int` | with cancel | [BONUS] Order ID to cancel |

---

## ✅ Input Validation

The bot validates **all inputs before making any API call**:

| Validation | Rule |
|---|---|
| Symbol | Non-empty, uppercase alphanumeric, 4–20 chars |
| Side | Must be `BUY` or `SELL` |
| Order Type | Must be `MARKET` or `LIMIT` |
| Quantity | Must be a number > 0 |
| Price | Required for `LIMIT` orders, must be > 0; ignored for `MARKET` |

---

## 📊 Logging

All actions are logged to **two destinations simultaneously**:

- **Console** — Human-readable with colour-coded log levels
- **`logs/bot.log`** — Structured file log with timestamps, auto-rotates at 5 MB (3 backups kept)

### Log Format

```
2026-06-01 14:23:11 | INFO     | trading_bot | ✅ Order placed successfully!
2026-06-01 14:23:11 | INFO     | trading_bot |    ┌─ Order ID   : 3926524958
2026-06-01 14:23:11 | INFO     | trading_bot |    ├─ Symbol     : BTCUSDT
2026-06-01 14:23:11 | INFO     | trading_bot |    └─ Status     : FILLED
```

---

## 🛡️ Error Handling

| Error Type | Handling Strategy |
|---|---|
| `ValidationError` | Human-readable message, exits with code 1 |
| `BinanceAPIException` | Logs API error code + message, exits with code 1 |
| `BinanceRequestException` | Logs network error, suggests retry, exits with code 1 |
| `RuntimeError` (config) | Logs config issue (missing keys), exits with code 1 |
| Unexpected errors | Logs with full traceback (DEBUG level), exits with code 1 |

---

## 🧪 Running Tests

```bash
pytest test_validator.py -v
```

Expected output:
```
test_validator.py::TestValidateSymbol::test_valid_symbol_btcusdt         PASSED
test_validator.py::TestValidateSide::test_valid_buy                      PASSED
test_validator.py::TestValidateOrderType::test_valid_market              PASSED
test_validator.py::TestValidateQuantity::test_valid_quantity_float       PASSED
test_validator.py::TestValidatePrice::test_limit_valid_price             PASSED
test_validator.py::TestValidateOrderParams::test_valid_market_order      PASSED
...
```

---

## 📦 Bonus Features

| Feature | Flag | Status |
|---|---|---|
| Position Tracking | `--show-positions` | ✅ Implemented |
| Cancel Order | `--cancel-order --order-id ID --symbol SYM` | ✅ Implemented |
| PnL Estimation | Displayed alongside positions | ✅ Implemented |
| Configurable Loop | See `strategy_loop.py` | ✅ Implemented |

---

## 📁 Log Proof (Submission Evidence)

The `logs/bot.log` file contains proof of at least:
- ✅ One successful **MARKET** order
- ✅ One successful **LIMIT** order

Both logged with Order ID, symbol, side, quantity, price, and status.

---

## 🔒 Security Notes

- API keys are stored in `.env` which is **git-ignored**
- `.env.example` with placeholder values is provided for setup reference
- Testnet keys only — no real funds involved

---

## 📝 Submission

- **GitHub Repo**: Push all files except `.env`
- **OR Zip**: Include all files, rename `.env` → remove real keys before zipping
- **Required files**: `bot.py`, `config.py`, `logger.py`, `validator.py`, `requirements.txt`, `.env.example`, `.gitignore`, `README.md`, `logs/bot.log`

---

## 🔗 References

- [Binance Futures Testnet](https://testnet.binancefuture.com)
- [python-binance Documentation](https://python-binance.readthedocs.io)
- [Binance Futures API Reference](https://binance-docs.github.io/apidocs/futures/en/)
