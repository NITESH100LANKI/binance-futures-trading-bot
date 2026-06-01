"""
strategy_loop.py — [BONUS] Configurable Strategy Loop
=======================================================
Runs a repeated order-placement strategy at a configurable interval.
Useful for testing recurring trades or simulating a simple DCA strategy.

Source: Assignment Doc §Bonus §7d — Configurable strategy loop.

Usage:
    python strategy_loop.py --symbol BTCUSDT --side BUY --order-type MARKET \
                            --quantity 0.001 --interval 30 --iterations 3
"""

import argparse
import sys
import time

from binance.exceptions import BinanceAPIException, BinanceRequestException

import config
from bot import create_client, place_order
from logger import setup_logger
from validator import validate_order_params, ValidationError

logger = setup_logger("strategy_loop")


def build_strategy_parser() -> argparse.ArgumentParser:
    """Build CLI parser for the strategy loop."""
    parser = argparse.ArgumentParser(
        prog="strategy_loop.py",
        description=(
            "🔄 [BONUS] Configurable Strategy Loop\n"
            "Executes repeated orders at a fixed interval.\n\n"
            "Example:\n"
            "  python strategy_loop.py --symbol BTCUSDT --side BUY "
            "--order-type MARKET --quantity 0.001 --interval 30 --iterations 3\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--symbol",     type=str,   required=True,  help="Trading pair (e.g. BTCUSDT)")
    parser.add_argument("--side",       type=str,   required=True,  choices=["BUY", "SELL"], help="BUY or SELL")
    parser.add_argument("--order-type", type=str,   required=True,  dest="order_type", choices=["MARKET", "LIMIT"])
    parser.add_argument("--quantity",   type=float, required=True,  help="Quantity per iteration")
    parser.add_argument("--price",      type=float, default=None,   help="Limit price (LIMIT orders only)")
    parser.add_argument("--interval",   type=int,   default=60,     help="Seconds between orders (default: 60)")
    parser.add_argument("--iterations", type=int,   default=5,      help="Number of orders to place (default: 5)")
    return parser


def run_strategy(
    symbol: str,
    side: str,
    order_type: str,
    quantity: float,
    price: float,
    interval: int,
    iterations: int,
) -> None:
    """
    Execute repeated orders at fixed intervals.

    Args:
        symbol:     Trading pair.
        side:       BUY or SELL.
        order_type: MARKET or LIMIT.
        quantity:   Units per order.
        price:      Limit price (LIMIT only).
        interval:   Seconds between orders.
        iterations: Total number of orders to place.
    """
    logger.info("═" * 60)
    logger.info(f"🔄 Strategy Loop Starting")
    logger.info(f"   Symbol: {symbol} | Side: {side} | Type: {order_type}")
    logger.info(f"   Qty: {quantity} | Price: {price} | Interval: {interval}s | Runs: {iterations}")
    logger.info("═" * 60)

    # Validate once before starting
    try:
        validated = validate_order_params(symbol, side, order_type, quantity, price)
    except ValidationError as e:
        logger.error(f"❌ Validation failed: {e}")
        sys.exit(1)

    config.validate_config()
    client = create_client()

    for i in range(1, iterations + 1):
        logger.info(f"\n{'─'*40}")
        logger.info(f"📍 Iteration {i}/{iterations}")
        try:
            place_order(
                client=client,
                symbol=validated["symbol"],
                side=validated["side"],
                order_type=validated["order_type"],
                quantity=validated["quantity"],
                price=validated["price"],
            )
        except BinanceAPIException as e:
            logger.error(f"❌ API Error [{e.status_code}]: {e.message}")
        except BinanceRequestException as e:
            logger.error(f"❌ Network Error: {e.message}")
        except Exception as e:
            logger.error(f"❌ Unexpected Error: {type(e).__name__}: {e}")

        if i < iterations:
            logger.info(f"⏳ Waiting {interval}s before next iteration …")
            time.sleep(interval)

    logger.info("\n" + "═" * 60)
    logger.info(f"✅ Strategy loop complete — {iterations} iterations finished.")
    logger.info("═" * 60)


def main() -> int:
    parser = build_strategy_parser()
    args   = parser.parse_args()

    run_strategy(
        symbol=args.symbol,
        side=args.side,
        order_type=args.order_type,
        quantity=args.quantity,
        price=args.price,
        interval=args.interval,
        iterations=args.iterations,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
