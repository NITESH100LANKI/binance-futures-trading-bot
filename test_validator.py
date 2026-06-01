"""
test_validator.py — Unit Tests for validator.py
================================================
Covers all 6 validation edge cases required by the assignment.

Source: Assignment Doc §Core Requirements §3 — input validation.
ISO 25010 Quality: Testability — automated verification of validation logic.

Run with: pytest test_validator.py -v
"""

import pytest
from validator import (
    validate_symbol,
    validate_side,
    validate_order_type,
    validate_quantity,
    validate_price,
    validate_order_params,
    ValidationError,
)


# ══════════════════════════════════════════════════════════════════════════════
# Tests: validate_symbol
# ══════════════════════════════════════════════════════════════════════════════
class TestValidateSymbol:
    def test_valid_symbol_btcusdt(self):
        assert validate_symbol("BTCUSDT") == "BTCUSDT"

    def test_valid_symbol_lowercase_normalised(self):
        assert validate_symbol("btcusdt") == "BTCUSDT"

    def test_valid_symbol_with_spaces_stripped(self):
        assert validate_symbol("  ETHUSDT  ") == "ETHUSDT"

    def test_invalid_symbol_empty(self):
        with pytest.raises(ValidationError, match="non-empty string"):
            validate_symbol("")

    def test_invalid_symbol_special_chars(self):
        with pytest.raises(ValidationError, match="Invalid symbol"):
            validate_symbol("BTC-USDT")

    def test_invalid_symbol_too_short(self):
        with pytest.raises(ValidationError, match="Invalid symbol"):
            validate_symbol("BT")

    def test_invalid_symbol_none(self):
        with pytest.raises(ValidationError):
            validate_symbol(None)


# ══════════════════════════════════════════════════════════════════════════════
# Tests: validate_side
# ══════════════════════════════════════════════════════════════════════════════
class TestValidateSide:
    def test_valid_buy(self):
        assert validate_side("BUY") == "BUY"

    def test_valid_sell(self):
        assert validate_side("SELL") == "SELL"

    def test_valid_lowercase_buy(self):
        assert validate_side("buy") == "BUY"

    def test_invalid_side(self):
        with pytest.raises(ValidationError, match="Invalid side"):
            validate_side("HOLD")

    def test_invalid_side_empty(self):
        with pytest.raises(ValidationError, match="non-empty string"):
            validate_side("")


# ══════════════════════════════════════════════════════════════════════════════
# Tests: validate_order_type
# ══════════════════════════════════════════════════════════════════════════════
class TestValidateOrderType:
    def test_valid_market(self):
        assert validate_order_type("MARKET") == "MARKET"

    def test_valid_limit(self):
        assert validate_order_type("LIMIT") == "LIMIT"

    def test_valid_lowercase_limit(self):
        assert validate_order_type("limit") == "LIMIT"

    def test_invalid_order_type(self):
        with pytest.raises(ValidationError, match="Invalid order type"):
            validate_order_type("STOP_LOSS")

    def test_invalid_order_type_empty(self):
        with pytest.raises(ValidationError, match="non-empty string"):
            validate_order_type("")


# ══════════════════════════════════════════════════════════════════════════════
# Tests: validate_quantity
# ══════════════════════════════════════════════════════════════════════════════
class TestValidateQuantity:
    def test_valid_quantity_float(self):
        assert validate_quantity(0.01) == 0.01

    def test_valid_quantity_int(self):
        assert validate_quantity(1) == 1.0

    def test_valid_quantity_string_number(self):
        assert validate_quantity("0.05") == 0.05

    def test_invalid_quantity_zero(self):
        with pytest.raises(ValidationError, match="greater than 0"):
            validate_quantity(0)

    def test_invalid_quantity_negative(self):
        with pytest.raises(ValidationError, match="greater than 0"):
            validate_quantity(-1.5)

    def test_invalid_quantity_string(self):
        with pytest.raises(ValidationError, match="must be a number"):
            validate_quantity("not_a_number")

    def test_invalid_quantity_none(self):
        with pytest.raises(ValidationError, match="must be a number"):
            validate_quantity(None)


# ══════════════════════════════════════════════════════════════════════════════
# Tests: validate_price
# ══════════════════════════════════════════════════════════════════════════════
class TestValidatePrice:
    def test_limit_requires_price(self):
        with pytest.raises(ValidationError, match="required for LIMIT"):
            validate_price(None, "LIMIT")

    def test_limit_valid_price(self):
        assert validate_price(65000.0, "LIMIT") == 65000.0

    def test_limit_zero_price(self):
        with pytest.raises(ValidationError, match="greater than 0"):
            validate_price(0, "LIMIT")

    def test_limit_negative_price(self):
        with pytest.raises(ValidationError, match="greater than 0"):
            validate_price(-100, "LIMIT")

    def test_market_price_none_ok(self):
        assert validate_price(None, "MARKET") is None

    def test_market_price_ignored(self):
        # For MARKET orders, price is ignored (returns None regardless)
        assert validate_price(50000, "MARKET") is None


# ══════════════════════════════════════════════════════════════════════════════
# Tests: validate_order_params (integration)
# ══════════════════════════════════════════════════════════════════════════════
class TestValidateOrderParams:
    def test_valid_market_order(self):
        result = validate_order_params("BTCUSDT", "BUY", "MARKET", 0.01)
        assert result == {
            "symbol": "BTCUSDT",
            "side": "BUY",
            "order_type": "MARKET",
            "quantity": 0.01,
            "price": None,
        }

    def test_valid_limit_order(self):
        result = validate_order_params("ETHUSDT", "SELL", "LIMIT", 0.1, 3000.0)
        assert result == {
            "symbol": "ETHUSDT",
            "side": "SELL",
            "order_type": "LIMIT",
            "quantity": 0.1,
            "price": 3000.0,
        }

    def test_limit_without_price_raises(self):
        with pytest.raises(ValidationError, match="required for LIMIT"):
            validate_order_params("BTCUSDT", "BUY", "LIMIT", 0.01)

    def test_invalid_symbol_raises(self):
        with pytest.raises(ValidationError):
            validate_order_params("", "BUY", "MARKET", 0.01)

    def test_invalid_side_raises(self):
        with pytest.raises(ValidationError):
            validate_order_params("BTCUSDT", "HODL", "MARKET", 0.01)

    def test_invalid_quantity_raises(self):
        with pytest.raises(ValidationError):
            validate_order_params("BTCUSDT", "BUY", "MARKET", -5)

    def test_normalisation_applied(self):
        result = validate_order_params("btcusdt", "buy", "market", 0.01)
        assert result["symbol"] == "BTCUSDT"
        assert result["side"] == "BUY"
        assert result["order_type"] == "MARKET"
