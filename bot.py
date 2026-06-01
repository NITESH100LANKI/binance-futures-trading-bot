"""
bot.py — Binance Futures Testnet Trading Bot (Main Entry Point)
===============================================================
CLI-based trading bot that places MARKET and LIMIT orders on the
Binance Futures Testnet.

Usage Examples:
    # Place a MARKET BUY order for 0.01 BTC
    python bot.py --symbol BTCUSDT --side BUY --order-type MARKET --quantity 0.01

    # Place a LIMIT SELL order for 0.01 BTC at $65,000
    python bot.py --symbol BTCUSDT --side SELL --order-type LIMIT --quantity 0.01 --price 65000

    # Show positions (bonus)
    python bot.py --show-positions

    # Cancel an order by ID (bonus)
    python bot.py --cancel-order --order-id 12345678 --symbol BTCUSDT

Source: Assignment Doc §Core Requirements §2, §3, §4, §5
"""

import argparse
import json
import sys
from typing import Optional

from binance import Client
from binance.exceptions import BinanceAPIException, BinanceRequestException

import config
from logger import setup_logger
from validator import validate_order_params, ValidationError


# ── Module-level logger ────────────────────────────────────────────────────────
logger = setup_logger("trading_bot")


# ── Binance Client Factory ─────────────────────────────────────────────────────
def create_client() -> Client:
    """
    Initialise and return a Binance Futures Testnet client.

    The python-binance library's `testnet=True` flag sets the base URL to
    https://testnet.binancefuture.com automatically.

    Returns:
        Authenticated Binance Client configured for Futures Testnet.

    Raises:
        RuntimeError: If API keys are missing from config.
    """
    config.validate_config()
    logger.debug("Initialising Binance Futures Testnet client …")
    client = Client(
        api_key=config.API_KEY,
        api_secret=config.API_SECRET,
        testnet=True,
    )
    logger.info("✅ Connected to Binance Futures Testnet successfully.")
    return client


# ── Order Placement ────────────────────────────────────────────────────────────
def place_order(
    client: Client,
    symbol: str,
    side: str,
    order_type: str,
    quantity: float,
    price: Optional[float] = None,
) -> dict:
    """
    Place a futures order on Binance Testnet.

    Dispatches to the correct sub-function based on order_type.
    All parameters are assumed to be pre-validated.

    Args:
        client:     Authenticated Binance client.
        symbol:     Trading pair (e.g. 'BTCUSDT').
        side:       'BUY' or 'SELL'.
        order_type: 'MARKET' or 'LIMIT'.
        quantity:   Number of units.
        price:      Limit price (LIMIT orders only).

    Returns:
        Full API response dict.

    Raises:
        BinanceAPIException: On API-level errors (logged automatically).
        BinanceRequestException: On network/request errors.
    """
    logger.info(
        f"📤 Placing {order_type} {side} order | "
        f"Symbol: {symbol} | Qty: {quantity}"
        + (f" | Price: {price}" if price else "")
    )

    if order_type == "MARKET":
        response = _place_market_order(client, symbol, side, quantity)
    else:
        response = _place_limit_order(client, symbol, side, quantity, price)

    # ── Log full response ──────────────────────────────────────────────────────
    _log_order_response(response)
    return response


def _place_market_order(
    client: Client,
    symbol: str,
    side: str,
    quantity: float,
) -> dict:
    """Execute a MARKET order on Binance Futures Testnet."""
    return client.futures_create_order(
        symbol=symbol,
        side=side,
        type="MARKET",
        quantity=quantity,
    )


def _place_limit_order(
    client: Client,
    symbol: str,
    side: str,
    quantity: float,
    price: float,
) -> dict:
    """Execute a LIMIT GTC order on Binance Futures Testnet."""
    return client.futures_create_order(
        symbol=symbol,
        side=side,
        type="LIMIT",
        quantity=quantity,
        price=str(price),          # Binance expects string for price
        timeInForce="GTC",         # Good Till Cancelled
    )


def _log_order_response(response: dict) -> None:
    """Parse and log key fields from an order response."""
    order_id = response.get("orderId", "N/A")
    status = response.get("status", "N/A")
    symbol = response.get("symbol", "N/A")
    side = response.get("side", "N/A")
    order_type = response.get("type", "N/A")
    qty = response.get("origQty", "N/A")
    avg_price = response.get("avgPrice", response.get("price", "N/A"))
    client_id = response.get("clientOrderId", "N/A")

    logger.info(
        "[ORDER] Placed successfully!\n"
        f"  Order ID   : {order_id}\n"
        f"  Client ID  : {client_id}\n"
        f"  Symbol     : {symbol}\n"
        f"  Side       : {side}\n"
        f"  Type       : {order_type}\n"
        f"  Quantity   : {qty}\n"
        f"  Avg Price  : {avg_price}\n"
        f"  Status     : {status}"
    )
    logger.debug(f"Full API Response: {json.dumps(response, indent=2)}")


# ── Bonus: Position Tracking ──────────────────────────────────────────────────
def show_positions(client: Client) -> None:
    """
    [BONUS] Query and display all open futures positions.

    Source: Assignment Doc §Bonus §7a — Position tracking.
    """
    logger.info("📊 Fetching open positions …")
    try:
        positions = client.futures_position_information()
        open_positions = [p for p in positions if float(p.get("positionAmt", 0)) != 0]

        if not open_positions:
            logger.info("No open positions found.")
            return

        logger.info(f"Found {len(open_positions)} open position(s):")
        for pos in open_positions:
            symbol = pos.get("symbol")
            amt = float(pos.get("positionAmt", 0))
            entry_price = float(pos.get("entryPrice", 0))
            mark_price = float(pos.get("markPrice", 0))
            unrealised_pnl = float(pos.get("unRealizedProfit", 0))

            # PnL Estimation [Bonus §7c]
            direction = "LONG" if amt > 0 else "SHORT"
            pnl_sign = "+" if unrealised_pnl >= 0 else "-"

            logger.info(
                f"  [{pnl_sign}] {symbol} | {direction} {abs(amt)} units\n"
                f"      Entry Price    : {entry_price:.4f}\n"
                f"      Mark Price     : {mark_price:.4f}\n"
                f"      Unrealised PnL : {unrealised_pnl:.4f} USDT"
            )

    except BinanceAPIException as e:
        logger.error(f"❌ Failed to fetch positions: [{e.status_code}] {e.message}")


# ── Bonus: Cancel Order ───────────────────────────────────────────────────────
def cancel_order(client: Client, symbol: str, order_id: int) -> None:
    """
    [BONUS] Cancel an existing order by order ID.

    Source: Assignment Doc §Bonus §7b — Order cancellation.

    Args:
        client:   Authenticated Binance client.
        symbol:   Trading pair the order belongs to.
        order_id: Integer order ID to cancel.
    """
    logger.info(f"🗑️  Cancelling order {order_id} for {symbol} …")
    try:
        response = client.futures_cancel_order(symbol=symbol, orderId=order_id)
        logger.info(
            f"✅ Order {order_id} cancelled successfully. "
            f"Status: {response.get('status', 'N/A')}"
        )
        logger.debug(f"Cancel response: {json.dumps(response, indent=2)}")
    except BinanceAPIException as e:
        logger.error(
            f"❌ Failed to cancel order {order_id}: [{e.status_code}] {e.message}"
        )


# ── CLI Argument Parser ────────────────────────────────────────────────────────
def build_parser() -> argparse.ArgumentParser:
    """
    Build and return the CLI argument parser.

    Source: Assignment Doc §Core Requirements §2 — CLI interface.
    """
    parser = argparse.ArgumentParser(
        prog="bot.py",
        description=(
            "Binance Futures Testnet Trading Bot\n"
            "Place MARKET and LIMIT orders via command-line interface.\n\n"
            "Examples:\n"
            "  python bot.py --symbol BTCUSDT --side BUY"
            " --order-type MARKET --quantity 0.01\n"
            "  python bot.py --symbol BTCUSDT --side SELL"
            " --order-type LIMIT --quantity 0.01 --price 65000\n"
            "  python bot.py --show-positions\n"
            "  python bot.py --cancel-order --order-id 12345678 --symbol BTCUSDT\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # ── Order parameters ───────────────────────────────────────────────────────
    order_group = parser.add_argument_group("Order Parameters")
    order_group.add_argument(
        "--symbol",
        type=str,
        metavar="SYMBOL",
        help="Trading pair symbol, e.g. BTCUSDT (required for order placement).",
    )
    order_group.add_argument(
        "--side",
        type=str,
        choices=["BUY", "SELL"],
        metavar="SIDE",
        help="Order side: BUY or SELL.",
    )
    order_group.add_argument(
        "--order-type",
        type=str,
        dest="order_type",
        choices=["MARKET", "LIMIT"],
        metavar="TYPE",
        help="Order type: MARKET or LIMIT.",
    )
    order_group.add_argument(
        "--quantity",
        type=float,
        metavar="QTY",
        help="Quantity to trade (must be > 0).",
    )
    order_group.add_argument(
        "--price",
        type=float,
        metavar="PRICE",
        default=None,
        help="Limit price (required for LIMIT orders, must be > 0).",
    )

    # ── Bonus actions ──────────────────────────────────────────────────────────
    bonus_group = parser.add_argument_group("Bonus Actions")
    bonus_group.add_argument(
        "--show-positions",
        action="store_true",
        dest="show_positions",
        help="[BONUS] Display all open futures positions with PnL.",
    )
    bonus_group.add_argument(
        "--cancel-order",
        action="store_true",
        dest="cancel_order",
        help="[BONUS] Cancel an existing order by ID.",
    )
    bonus_group.add_argument(
        "--order-id",
        type=int,
        dest="order_id",
        metavar="ID",
        help="[BONUS] Order ID to cancel (use with --cancel-order).",
    )

    return parser


# ── Main Orchestration ─────────────────────────────────────────────────────────
def main() -> int:
    """
    Entry point — parse args, validate, connect, place order, log result.

    Returns:
        Exit code: 0 on success, 1 on any error.
    """
    parser = build_parser()
    args = parser.parse_args()  # Must run first; --help exits here

    logger.info("=" * 60)
    logger.info("[BOT] Binance Futures Testnet Trading Bot -- Starting")
    logger.info("=" * 60)

    # ── Connect to Binance ─────────────────────────────────────────────────────
    try:
        client = create_client()
    except RuntimeError as e:
        logger.critical(f"Configuration error: {e}")
        return 1

    # ── BONUS: Show positions ──────────────────────────────────────────────────
    if args.show_positions:
        show_positions(client)
        return 0

    # ── BONUS: Cancel order ────────────────────────────────────────────────────
    if args.cancel_order:
        if not args.order_id or not args.symbol:
            logger.error(
                "❌ --cancel-order requires both --order-id and --symbol. "
                "Example: python bot.py --cancel-order --order-id 12345 --symbol BTCUSDT"
            )
            return 1
        cancel_order(client, args.symbol.upper(), args.order_id)
        return 0

    # ── Validate required order args ───────────────────────────────────────────
    required_args = [args.symbol, args.side, args.order_type, args.quantity]
    if any(arg is None for arg in required_args):
        logger.error(
            "❌ Missing required arguments for order placement.\n"
            "   Required: --symbol, --side, --order-type, --quantity\n"
            "   Run: python bot.py --help"
        )
        parser.print_usage(sys.stderr)
        return 1

    # ── Input Validation ───────────────────────────────────────────────────────
    try:
        validated = validate_order_params(
            symbol=args.symbol,
            side=args.side,
            order_type=args.order_type,
            quantity=args.quantity,
            price=args.price,
        )
        logger.info(
            f"✅ Validation passed: {validated['order_type']} {validated['side']} "
            f"{validated['quantity']} {validated['symbol']}"
            + (f" @ {validated['price']}" if validated['price'] else "")
        )
    except ValidationError as e:
        logger.error(f"❌ Validation error: {e}")
        return 1

    # ── Place the order ────────────────────────────────────────────────────────
    try:
        place_order(
            client=client,
            symbol=validated["symbol"],
            side=validated["side"],
            order_type=validated["order_type"],
            quantity=validated["quantity"],
            price=validated["price"],
        )
        return 0

    except BinanceAPIException as e:
        logger.error(
            f"❌ Binance API Error [{e.status_code}]: {e.message}\n"
            f"   Code: {e.code}"
        )
        logger.debug("Full exception info:", exc_info=True)
        return 1

    except BinanceRequestException as e:
        logger.error(
            f"❌ Network/Request Error: {e.message}\n"
            "   Check your internet connection and try again."
        )
        logger.debug("Full exception info:", exc_info=True)
        return 1

    except Exception as e:
        logger.critical(f"❌ Unexpected error: {type(e).__name__}: {e}")
        logger.debug("Full traceback:", exc_info=True)
        return 1

    finally:
        logger.info("=" * 60)
        logger.info("[BOT] Trading Bot -- Session ended.")
        logger.info("=" * 60)


if __name__ == "__main__":
    sys.exit(main())
