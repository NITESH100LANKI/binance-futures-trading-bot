"""
validator.py — Order Input Validation Module
=============================================
Provides fail-fast validation for all order parameters before
any API call is made. Raises ValueError with descriptive messages.

Source: Assignment Doc §Core Requirements §3 — input validation requirement.
ISO 25010 Quality: Reliability — prevents malformed requests from reaching the API.
"""

import re
from typing import Optional

from config import VALID_SIDES, VALID_ORDER_TYPES


class ValidationError(ValueError):
    """Raised when order parameter validation fails."""
    pass


def validate_symbol(symbol: str) -> str:
    """
    Validate trading pair symbol.

    Rules:
        - Non-empty string
        - Uppercase alphanumeric (e.g. BTCUSDT, ETHUSDT)
        - Between 5 and 20 characters

    Args:
        symbol: Trading pair string (e.g. 'BTCUSDT').

    Returns:
        Normalised uppercase symbol.

    Raises:
        ValidationError: If symbol is invalid.
    """
    if not symbol or not isinstance(symbol, str):
        raise ValidationError("Symbol must be a non-empty string (e.g. BTCUSDT).")

    normalised = symbol.strip().upper()

    if not re.match(r'^[A-Z0-9]{4,20}$', normalised):
        raise ValidationError(
            f"Invalid symbol '{symbol}'. Must be 4–20 uppercase alphanumeric chars "
            f"(e.g. BTCUSDT, ETHUSDT)."
        )
    return normalised


def validate_side(side: str) -> str:
    """
    Validate order side.

    Args:
        side: 'BUY' or 'SELL' (case-insensitive).

    Returns:
        Normalised uppercase side.

    Raises:
        ValidationError: If side is not BUY or SELL.
    """
    if not side or not isinstance(side, str):
        raise ValidationError("Side must be a non-empty string.")

    normalised = side.strip().upper()
    if normalised not in VALID_SIDES:
        raise ValidationError(
            f"Invalid side '{side}'. Must be one of: {', '.join(sorted(VALID_SIDES))}."
        )
    return normalised


def validate_order_type(order_type: str) -> str:
    """
    Validate order type.

    Args:
        order_type: 'MARKET' or 'LIMIT' (case-insensitive).

    Returns:
        Normalised uppercase order type.

    Raises:
        ValidationError: If order type is unsupported.
    """
    if not order_type or not isinstance(order_type, str):
        raise ValidationError("Order type must be a non-empty string.")

    normalised = order_type.strip().upper()
    if normalised not in VALID_ORDER_TYPES:
        raise ValidationError(
            f"Invalid order type '{order_type}'. "
            f"Must be one of: {', '.join(sorted(VALID_ORDER_TYPES))}."
        )
    return normalised


def validate_quantity(quantity: float) -> float:
    """
    Validate order quantity.

    Args:
        quantity: Number of units to buy/sell (must be > 0).

    Returns:
        Validated quantity as float.

    Raises:
        ValidationError: If quantity is not a positive number.
    """
    try:
        qty = float(quantity)
    except (TypeError, ValueError):
        raise ValidationError(f"Quantity must be a number, got '{quantity}'.")

    if qty <= 0:
        raise ValidationError(
            f"Quantity must be greater than 0, got {qty}."
        )
    return qty


def validate_price(price: Optional[float], order_type: str) -> Optional[float]:
    """
    Validate order price.

    Rules:
        - Required and > 0 for LIMIT orders.
        - Must be None (or ignored) for MARKET orders.

    Args:
        price: Order price (required for LIMIT).
        order_type: Validated order type string ('MARKET' or 'LIMIT').

    Returns:
        Validated price as float, or None for MARKET orders.

    Raises:
        ValidationError: If price is missing for LIMIT, or negative.
    """
    if order_type == "LIMIT":
        if price is None:
            raise ValidationError(
                "Price is required for LIMIT orders. "
                "Use --price to specify a value greater than 0."
            )
        try:
            p = float(price)
        except (TypeError, ValueError):
            raise ValidationError(f"Price must be a number, got '{price}'.")

        if p <= 0:
            raise ValidationError(
                f"Price must be greater than 0 for LIMIT orders, got {p}."
            )
        return p

    # MARKET orders — price is irrelevant
    return None


def validate_order_params(
    symbol: str,
    side: str,
    order_type: str,
    quantity: float,
    price: Optional[float] = None,
) -> dict:
    """
    Validate all order parameters in sequence (fail-fast).

    Args:
        symbol:     Trading pair (e.g. 'BTCUSDT').
        side:       Order side ('BUY' or 'SELL').
        order_type: Order type ('MARKET' or 'LIMIT').
        quantity:   Number of units.
        price:      Limit price (required for LIMIT orders).

    Returns:
        Dict of validated and normalised parameters:
        {'symbol', 'side', 'order_type', 'quantity', 'price'}

    Raises:
        ValidationError: On first failed validation.
    """
    validated_symbol = validate_symbol(symbol)
    validated_side = validate_side(side)
    validated_order_type = validate_order_type(order_type)
    validated_quantity = validate_quantity(quantity)
    validated_price = validate_price(price, validated_order_type)

    return {
        "symbol": validated_symbol,
        "side": validated_side,
        "order_type": validated_order_type,
        "quantity": validated_quantity,
        "price": validated_price,
    }
