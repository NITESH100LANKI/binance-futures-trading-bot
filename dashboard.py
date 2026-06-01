"""
dashboard.py -- Professional Streamlit Dashboard
=================================================
Visual trading interface for the Binance Futures Testnet Bot.

Wraps existing CLI modules (bot.py, validator.py, config.py, logger.py)
as a pure IMPORT layer -- no existing logic is modified or duplicated.

Run with:
    streamlit run dashboard.py

Architecture:
    dashboard.py   <-- Streamlit UI layer (this file)
        |-- bot.py          create_client, place_order, cancel_order
        |-- validator.py    validate_order_params
        |-- config.py       API credentials, constants
        |-- logger.py       File logging (bot.log updated from UI actions)
"""

# ── Standard library ──────────────────────────────────────────────────────────
import io
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Optional

# ── Third-party ───────────────────────────────────────────────────────────────
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from binance.exceptions import BinanceAPIException, BinanceRequestException

# ── Project modules (existing -- not modified) ────────────────────────────────
import config
from bot import cancel_order as _cancel_order
from bot import create_client
from bot import place_order as _place_order
from validator import ValidationError, validate_order_params


# ═══════════════════════════════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════════
SYMBOLS = [
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT",
    "ADAUSDT", "XRPUSDT", "DOGEUSDT", "LINKUSDT",
    "AVAXUSDT", "MATICUSDT",
]
LOG_FILE = Path("logs/bot.log")

# Binance design tokens
C_YELLOW = "#F0B90B"
C_GREEN  = "#0ECB81"
C_RED    = "#F6465D"
C_DARK   = "#0B0E11"
C_CARD   = "#1E2026"
C_BORDER = "#2B2F36"
C_TEXT   = "#EAECEF"
C_MUTED  = "#848E9C"


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE CONFIG  (must be first Streamlit call)
# ═══════════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Binance Futures Bot",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ═══════════════════════════════════════════════════════════════════════════════
# CUSTOM CSS
# ═══════════════════════════════════════════════════════════════════════════════
CUSTOM_CSS = f"""
<style>
/* ── App background ───────────────────────────────────────────────────────── */
[data-testid="stAppViewContainer"] {{
    background-color: {C_DARK};
}}
[data-testid="stHeader"] {{
    background-color: {C_DARK};
    border-bottom: 1px solid {C_BORDER};
}}
[data-testid="stSidebar"] {{
    background-color: {C_CARD};
    border-right: 1px solid {C_BORDER};
}}
[data-testid="stSidebarContent"] {{
    padding-top: 0;
}}

/* ── Metric cards ─────────────────────────────────────────────────────────── */
[data-testid="metric-container"] {{
    background-color: {C_CARD};
    border: 1px solid {C_BORDER};
    border-radius: 8px;
    padding: 16px 20px;
}}
[data-testid="metric-container"] label {{
    color: {C_MUTED} !important;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.8px;
    text-transform: uppercase;
}}
[data-testid="stMetricValue"] {{
    color: {C_TEXT} !important;
    font-size: 22px !important;
    font-weight: 700 !important;
}}
[data-testid="stMetricDelta"] svg {{
    display: none;
}}

/* ── Tabs ─────────────────────────────────────────────────────────────────── */
[data-testid="stTabs"] [data-baseweb="tab-list"] {{
    background-color: {C_CARD};
    border-radius: 10px;
    padding: 4px;
    gap: 2px;
    border: 1px solid {C_BORDER};
}}
[data-testid="stTabs"] [data-baseweb="tab"] {{
    color: {C_MUTED};
    font-weight: 600;
    font-size: 13px;
    border-radius: 7px;
    padding: 8px 18px;
    border: none;
}}
[data-testid="stTabs"] [aria-selected="true"] {{
    background-color: {C_BORDER} !important;
    color: {C_YELLOW} !important;
}}
[data-testid="stTabsContent"] {{
    padding-top: 20px;
}}

/* ── Primary button (Place Order) ─────────────────────────────────────────── */
[data-testid="stFormSubmitButton"] > button,
[data-testid="stBaseButton-primary"] {{
    background: linear-gradient(135deg, {C_YELLOW} 0%, #D4A200 100%) !important;
    color: {C_DARK} !important;
    font-weight: 700 !important;
    border: none !important;
    border-radius: 6px !important;
    padding: 10px 24px !important;
    font-size: 15px !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 2px 8px rgba(240,185,11,0.25) !important;
}}
[data-testid="stFormSubmitButton"] > button:hover,
[data-testid="stBaseButton-primary"]:hover {{
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 16px rgba(240,185,11,0.4) !important;
}}

/* ── Secondary buttons ────────────────────────────────────────────────────── */
[data-testid="stBaseButton-secondary"] {{
    background-color: {C_CARD} !important;
    color: {C_TEXT} !important;
    border: 1px solid {C_BORDER} !important;
    border-radius: 6px !important;
}}
[data-testid="stBaseButton-secondary"]:hover {{
    border-color: {C_YELLOW} !important;
    color: {C_YELLOW} !important;
}}

/* ── DataFrames ───────────────────────────────────────────────────────────── */
[data-testid="stDataFrame"] {{
    border: 1px solid {C_BORDER};
    border-radius: 8px;
    overflow: hidden;
}}
.stDataFrame thead tr th {{
    background-color: {C_CARD} !important;
    color: {C_MUTED} !important;
    font-size: 11px;
    letter-spacing: 0.6px;
}}

/* ── Inputs ───────────────────────────────────────────────────────────────── */
[data-testid="stNumberInput"] input,
[data-testid="stTextInput"] input {{
    background-color: {C_CARD} !important;
    border: 1px solid {C_BORDER} !important;
    color: {C_TEXT} !important;
    border-radius: 6px !important;
}}
[data-testid="stSelectbox"] [data-baseweb="select"] {{
    background-color: {C_CARD} !important;
    border: 1px solid {C_BORDER} !important;
}}

/* ── Alerts / info boxes ──────────────────────────────────────────────────── */
[data-testid="stAlert"] {{
    border-radius: 8px !important;
}}

/* ── Divider ──────────────────────────────────────────────────────────────── */
hr {{
    border-color: {C_BORDER} !important;
    margin: 8px 0 !important;
}}

/* ── Scrollbar ────────────────────────────────────────────────────────────── */
::-webkit-scrollbar {{ width: 6px; height: 6px; }}
::-webkit-scrollbar-track {{ background: {C_DARK}; }}
::-webkit-scrollbar-thumb {{ background: {C_BORDER}; border-radius: 3px; }}
::-webkit-scrollbar-thumb:hover {{ background: {C_MUTED}; }}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# HELPER: HTML COMPONENTS
# ═══════════════════════════════════════════════════════════════════════════════
def _badge(text: str, color: str, bg_alpha: str = "20") -> str:
    """Return an inline HTML badge string."""
    return (
        f'<span style="background:rgba({int(color[1:3],16)},'
        f'{int(color[3:5],16)},{int(color[5:7],16)},0.{bg_alpha});'
        f'color:{color};border-radius:4px;padding:2px 10px;'
        f'font-size:12px;font-weight:600;">{text}</span>'
    )


def _card(title: str, value: str, sub: str = "", color: str = C_TEXT) -> str:
    """Return an HTML metric card."""
    return (
        f'<div style="background:{C_CARD};border:1px solid {C_BORDER};'
        f'border-radius:10px;padding:18px 20px;">'
        f'<div style="color:{C_MUTED};font-size:11px;font-weight:600;'
        f'letter-spacing:0.8px;text-transform:uppercase;">{title}</div>'
        f'<div style="color:{color};font-size:24px;font-weight:700;'
        f'margin:6px 0 2px;">{value}</div>'
        f'<div style="color:{C_MUTED};font-size:12px;">{sub}</div>'
        f'</div>'
    )


def _section(label: str) -> None:
    """Render a Binance-styled section header."""
    st.markdown(
        f'<div style="font-size:16px;font-weight:700;color:{C_TEXT};'
        f'border-left:3px solid {C_YELLOW};padding-left:12px;'
        f'margin:4px 0 16px;">{label}</div>',
        unsafe_allow_html=True,
    )


def _pnl_color(value: float) -> str:
    return C_GREEN if value >= 0 else C_RED


def _plotly_layout(height: int = 320) -> dict:
    """Shared Plotly dark layout dict."""
    return dict(
        plot_bgcolor=C_DARK,
        paper_bgcolor=C_CARD,
        font=dict(color=C_TEXT, size=12),
        height=height,
        margin=dict(l=16, r=16, t=24, b=16),
        xaxis=dict(gridcolor=C_BORDER, zeroline=True, zerolinecolor=C_BORDER),
        yaxis=dict(gridcolor=C_BORDER),
        legend=dict(bgcolor=C_CARD, bordercolor=C_BORDER),
    )


# ═══════════════════════════════════════════════════════════════════════════════
# CACHED BINANCE CLIENT
# ═══════════════════════════════════════════════════════════════════════════════
@st.cache_resource(show_spinner="Connecting to Binance Futures Testnet...")
def _get_client():
    """
    Create and cache a single Binance Futures Testnet client.

    Returns:
        (client, None)       on success
        (None, error_str)    on failure
    """
    try:
        config.validate_config()
        client = create_client()
        return client, None
    except RuntimeError as e:
        return None, str(e)
    except Exception as e:
        return None, f"{type(e).__name__}: {e}"


# ═══════════════════════════════════════════════════════════════════════════════
# DATA FETCHERS  (all return empty structures on any failure)
# ═══════════════════════════════════════════════════════════════════════════════
def _fetch_balance(client) -> dict:
    """Fetch USDT account balance. Returns dict with zeros on failure."""
    try:
        raw = client.futures_account_balance()
        usdt = next((b for b in raw if b["asset"] == "USDT"), {})
        return {
            "total":    round(float(usdt.get("balance", 0)), 2),
            "available": round(float(usdt.get("availableBalance", 0)), 2),
            "upnl":     round(float(usdt.get("crossUnPnl", 0)), 4),
        }
    except Exception:
        return {"total": 0.0, "available": 0.0, "upnl": 0.0}


def _fetch_positions(client) -> pd.DataFrame:
    """Fetch all open futures positions as a DataFrame."""
    try:
        raw = client.futures_position_information()
        open_pos = [p for p in raw if float(p.get("positionAmt", 0)) != 0]
        if not open_pos:
            return pd.DataFrame()

        rows = []
        for p in open_pos:
            amt    = float(p["positionAmt"])
            entry  = float(p["entryPrice"])
            mark   = float(p["markPrice"])
            upnl   = float(p["unRealizedProfit"])
            lev    = int(p.get("leverage", 1))
            notional = abs(amt) * mark
            roe    = (upnl / (notional / lev) * 100) if notional else 0.0
            rows.append({
                "Symbol":          p["symbol"],
                "Direction":       "LONG" if amt > 0 else "SHORT",
                "Size":            abs(amt),
                "Entry Price":     entry,
                "Mark Price":      mark,
                "Notional (USDT)": round(notional, 2),
                "Unrealized PnL":  round(upnl, 4),
                "ROE %":           round(roe, 2),
                "Leverage":        f"{lev}x",
            })
        return pd.DataFrame(rows)
    except Exception:
        return pd.DataFrame()


def _fetch_open_orders(client) -> pd.DataFrame:
    """Fetch all open orders as a DataFrame."""
    try:
        raw = client.futures_get_open_orders()
        if not raw:
            return pd.DataFrame()
        rows = []
        for o in raw:
            rows.append({
                "Order ID": o["orderId"],
                "Symbol":   o["symbol"],
                "Side":     o["side"],
                "Type":     o["type"],
                "Quantity": float(o["origQty"]),
                "Price":    float(o["price"]),
                "Status":   o["status"],
                "Time":     datetime.fromtimestamp(
                    o["time"] / 1000
                ).strftime("%H:%M:%S"),
            })
        return pd.DataFrame(rows)
    except Exception:
        return pd.DataFrame()


def _fetch_ticker(client, symbol: str) -> dict:
    """Fetch 24h ticker stats for a symbol."""
    try:
        t = client.futures_ticker(symbol=symbol)
        return {
            "last_price":   float(t.get("lastPrice", 0)),
            "change_pct":   float(t.get("priceChangePercent", 0)),
            "high_24h":     float(t.get("highPrice", 0)),
            "low_24h":      float(t.get("lowPrice", 0)),
            "volume":       float(t.get("volume", 0)),
        }
    except Exception:
        return {}


def _parse_logs(max_lines: int = 300) -> list[dict]:
    """Parse logs/bot.log into a list of dicts for display."""
    if not LOG_FILE.exists():
        return []
    pattern = re.compile(
        r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) \| (\w+)\s*\| \S+ \| (.*)"
    )
    entries = []
    try:
        text = LOG_FILE.read_text(encoding="utf-8", errors="replace")
        for line in text.splitlines()[-max_lines:]:
            m = pattern.match(line.strip())
            if m:
                entries.append({
                    "Timestamp": m.group(1),
                    "Level":     m.group(2).strip(),
                    "Message":   m.group(3).strip(),
                })
    except Exception:
        pass
    return entries


# ═══════════════════════════════════════════════════════════════════════════════
# SESSION STATE INIT
# ═══════════════════════════════════════════════════════════════════════════════
def _init_state() -> None:
    defaults = {
        "order_history":      [],      # orders placed this session
        "last_order_msg":     None,    # last success/error message
        "last_order_ok":      None,    # True=success, False=error
        "cancel_msg":         None,
        "cancel_ok":          None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


# ═══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════════════════════════════
def _render_sidebar(client, connected: bool) -> None:
    with st.sidebar:
        # ── Logo ──────────────────────────────────────────────────────────────
        st.markdown(
            f"""
            <div style="text-align:center;padding:24px 0 12px;">
              <div style="font-size:40px;margin-bottom:6px;">📈</div>
              <div style="font-size:18px;font-weight:800;
                          color:{C_YELLOW};letter-spacing:1px;">
                FUTURES BOT
              </div>
              <div style="font-size:11px;color:{C_MUTED};
                          margin-top:2px;">Dashboard v1.0</div>
            </div>
            <div style="text-align:center;margin-bottom:8px;">
              <span style="background:rgba(240,185,11,0.12);
                           color:{C_YELLOW};
                           border:1px solid {C_YELLOW};
                           border-radius:4px;
                           padding:2px 10px;
                           font-size:10px;
                           font-weight:700;
                           letter-spacing:2px;">TESTNET</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.divider()

        # ── Connection status ──────────────────────────────────────────────────
        if connected:
            dot_style = (
                f"display:inline-block;width:8px;height:8px;"
                f"background:{C_GREEN};border-radius:50%;margin-right:6px;"
                f"box-shadow:0 0 6px {C_GREEN};"
            )
            st.markdown(
                f'<div style="font-size:13px;font-weight:600;color:{C_TEXT};">'
                f'<span style="{dot_style}"></span>Connected</div>'
                f'<div style="color:{C_MUTED};font-size:11px;margin-left:14px;">'
                f'Binance Futures Testnet</div>',
                unsafe_allow_html=True,
            )
        else:
            dot_style = (
                f"display:inline-block;width:8px;height:8px;"
                f"background:{C_RED};border-radius:50%;margin-right:6px;"
            )
            st.markdown(
                f'<div style="font-size:13px;font-weight:600;color:{C_RED};">'
                f'<span style="{dot_style}"></span>Disconnected</div>',
                unsafe_allow_html=True,
            )

        # ── Account balance ───────────────────────────────────────────────────
        if connected:
            st.divider()
            _section("Account")
            bal = _fetch_balance(client)
            upnl_color = C_GREEN if bal["upnl"] >= 0 else C_RED
            st.markdown(
                _card(
                    "Wallet Balance",
                    f"${bal['total']:,.2f}",
                    "USDT",
                )
                + "<br>"
                + _card(
                    "Available Margin",
                    f"${bal['available']:,.2f}",
                    f'<span style="color:{upnl_color};">'
                    f'{bal["upnl"]:+.4f} USDT UPnL</span>',
                ),
                unsafe_allow_html=True,
            )

        # ── Controls ──────────────────────────────────────────────────────────
        st.divider()
        if st.button("↺  Refresh Data", use_container_width=True):
            st.cache_resource.clear()
            st.rerun()

        if st.button("⚙  Reset Connection", use_container_width=True):
            st.cache_resource.clear()
            st.rerun()

        st.markdown(
            f'<div style="color:{C_MUTED};font-size:11px;text-align:center;'
            f'margin-top:8px;">'
            f'Updated {datetime.now().strftime("%H:%M:%S")}</div>',
            unsafe_allow_html=True,
        )


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1 — OVERVIEW
# ═══════════════════════════════════════════════════════════════════════════════
def _render_overview(client) -> None:
    _section("Portfolio Overview")

    bal      = _fetch_balance(client)
    pos_df   = _fetch_positions(client)
    ord_df   = _fetch_open_orders(client)

    total_upnl = pos_df["Unrealized PnL"].sum() if not pos_df.empty else 0.0
    upnl_color = C_GREEN if total_upnl >= 0 else C_RED

    # ── Metric row ────────────────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Wallet Balance",  f"${bal['total']:,.2f}",  "USDT")
    with c2:
        st.metric("Available Margin", f"${bal['available']:,.2f}", "USDT")
    with c3:
        st.metric(
            "Unrealized PnL",
            f"${total_upnl:+.4f}",
            f"{len(pos_df)} position(s)",
            delta_color="normal",
        )
    with c4:
        st.metric("Open Orders", str(len(ord_df)), "pending")

    st.divider()

    # ── PnL bar chart ─────────────────────────────────────────────────────────
    if not pos_df.empty:
        _section("Unrealized PnL by Position")

        labels = pos_df["Symbol"] + " · " + pos_df["Direction"]
        values = pos_df["Unrealized PnL"].tolist()
        colors = [C_GREEN if v >= 0 else C_RED for v in values]

        fig = go.Figure(
            go.Bar(
                x=values,
                y=labels,
                orientation="h",
                marker_color=colors,
                marker_line_width=0,
                text=[f"${v:+.4f}" for v in values],
                textposition="outside",
                textfont=dict(size=12, color=C_TEXT),
                hovertemplate=(
                    "<b>%{y}</b><br>"
                    "PnL: $%{x:+.4f}<extra></extra>"
                ),
            )
        )
        layout = _plotly_layout(height=max(200, len(pos_df) * 70 + 80))
        layout["xaxis"]["tickprefix"] = "$"
        fig.update_layout(**layout)
        st.plotly_chart(fig, use_container_width=True)

        # Position details table
        _section("Open Positions Detail")
        styled = pos_df.copy()
        styled["Unrealized PnL"] = styled["Unrealized PnL"].map(
            lambda v: f"${v:+.4f}"
        )
        styled["ROE %"] = styled["ROE %"].map(lambda v: f"{v:+.2f}%")
        styled["Entry Price"] = styled["Entry Price"].map(lambda v: f"{v:,.2f}")
        styled["Mark Price"]  = styled["Mark Price"].map(lambda v: f"{v:,.2f}")
        st.dataframe(styled, use_container_width=True, hide_index=True)

    else:
        st.info("No open positions. Place a trade to see PnL visualisation.", icon="📭")

    st.divider()

    # ── Recent activity feed ──────────────────────────────────────────────────
    _section("Recent Activity")
    logs = _parse_logs(max_lines=50)
    if logs:
        level_colors = {
            "INFO":     C_GREEN,
            "WARNING":  C_YELLOW,
            "ERROR":    C_RED,
            "CRITICAL": "#FF4081",
            "DEBUG":    C_MUTED,
        }
        for entry in reversed(logs[-12:]):
            lv   = entry["Level"]
            col  = level_colors.get(lv, C_TEXT)
            msg  = entry["Message"][:120] + ("…" if len(entry["Message"]) > 120 else "")
            st.markdown(
                f'<div style="padding:6px 0;border-bottom:1px solid {C_BORDER};'
                f'font-size:12px;line-height:1.5;">'
                f'<span style="color:{C_MUTED};">{entry["Timestamp"]}</span>&nbsp;'
                f'<span style="color:{col};font-weight:700;">[{lv}]</span>&nbsp;'
                f'<span style="color:{C_TEXT};">{msg}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )
    else:
        st.info("No log entries yet — place an order to start logging.", icon="📜")


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2 — PLACE ORDER
# ═══════════════════════════════════════════════════════════════════════════════
def _render_place_order(client) -> None:
    left, right = st.columns([3, 2], gap="large")

    with left:
        _section("New Order")

        # Symbol selector (outside form → live updates right panel)
        symbol = st.selectbox("Symbol", SYMBOLS, key="order_symbol")

        col_side, col_type = st.columns(2)
        with col_side:
            side = st.radio("Side", ["BUY", "SELL"], horizontal=False, key="order_side")
        with col_type:
            order_type = st.radio(
                "Order Type", ["MARKET", "LIMIT"], horizontal=False, key="order_type"
            )

        quantity = st.number_input(
            "Quantity (contracts)",
            min_value=0.001, max_value=1000.0,
            value=0.001, step=0.001, format="%.3f",
            help="Number of contracts to trade. Minimum: 0.001",
        )

        price_input: Optional[float] = None
        if order_type == "LIMIT":
            ticker = _fetch_ticker(client, symbol)
            default_price = ticker.get("last_price", 1.0) or 1.0
            price_input = st.number_input(
                "Limit Price (USDT)",
                min_value=0.01,
                value=float(f"{default_price:.2f}"),
                step=1.0,
                format="%.2f",
                help="Order will only execute at this price or better",
            )

        # Notional preview
        ticker = _fetch_ticker(client, symbol)
        ref_price = price_input if order_type == "LIMIT" else ticker.get("last_price", 0)
        if ref_price and quantity:
            notional = quantity * ref_price
            side_color = C_GREEN if side == "BUY" else C_RED
            st.markdown(
                f'<div style="background:{C_CARD};border:1px solid {C_BORDER};'
                f'border-left:3px solid {side_color};'
                f'border-radius:6px;padding:10px 14px;margin:8px 0;">'
                f'<span style="color:{C_MUTED};font-size:12px;">Estimated Notional</span><br>'
                f'<span style="color:{C_TEXT};font-weight:700;font-size:18px;">'
                f'${notional:,.2f} USDT</span>&nbsp;&nbsp;'
                f'<span style="color:{side_color};font-size:12px;font-weight:600;">'
                f'{side} {quantity:.3f} {symbol}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )

        st.markdown("<br>", unsafe_allow_html=True)

        # Place Order button
        btn_label = f"{'BUY' if side == 'BUY' else 'SELL'}  {order_type}"
        if st.button(btn_label, key="place_btn", use_container_width=True, type="primary"):
            with st.spinner(f"Placing {order_type} {side} order..."):
                try:
                    validated = validate_order_params(
                        symbol=symbol,
                        side=side,
                        order_type=order_type,
                        quantity=quantity,
                        price=price_input if order_type == "LIMIT" else None,
                    )
                    response = _place_order(
                        client=client,
                        symbol=validated["symbol"],
                        side=validated["side"],
                        order_type=validated["order_type"],
                        quantity=validated["quantity"],
                        price=validated["price"],
                    )
                    oid    = response.get("orderId", "N/A")
                    status = response.get("status", "N/A")

                    # Persist result & session history
                    st.session_state.last_order_ok  = True
                    st.session_state.last_order_msg = (
                        f"Order placed!  ID: **{oid}**  |  Status: **{status}**"
                    )
                    st.session_state.order_history.insert(0, {
                        "Time":     datetime.now().strftime("%H:%M:%S"),
                        "Symbol":   validated["symbol"],
                        "Side":     side,
                        "Type":     order_type,
                        "Qty":      validated["quantity"],
                        "Price":    price_input if order_type == "LIMIT" else "MKT",
                        "Order ID": oid,
                        "Status":   status,
                    })

                except ValidationError as e:
                    st.session_state.last_order_ok  = False
                    st.session_state.last_order_msg = f"Validation Error: {e}"
                except BinanceAPIException as e:
                    st.session_state.last_order_ok  = False
                    st.session_state.last_order_msg = (
                        f"API Error [{e.status_code}]: {e.message}"
                    )
                except BinanceRequestException as e:
                    st.session_state.last_order_ok  = False
                    st.session_state.last_order_msg = f"Network Error: {e.message}"
                except Exception as e:
                    st.session_state.last_order_ok  = False
                    st.session_state.last_order_msg = f"{type(e).__name__}: {e}"

        # Show persistent result banner
        if st.session_state.last_order_msg:
            if st.session_state.last_order_ok:
                st.success(f"✅  {st.session_state.last_order_msg}")
            else:
                st.error(f"❌  {st.session_state.last_order_msg}")

    with right:
        # ── Market ticker card ────────────────────────────────────────────────
        _section(f"{symbol} Market")
        if ticker:
            lp     = ticker.get("last_price", 0)
            chg    = ticker.get("change_pct", 0)
            hi     = ticker.get("high_24h", 0)
            lo     = ticker.get("low_24h", 0)
            vol    = ticker.get("volume", 0)
            chg_c  = C_GREEN if chg >= 0 else C_RED

            st.markdown(
                f'<div style="background:{C_CARD};border:1px solid {C_BORDER};'
                f'border-radius:10px;padding:20px;">'
                f'<div style="color:{C_MUTED};font-size:11px;letter-spacing:0.8px;'
                f'text-transform:uppercase;">Last Price</div>'
                f'<div style="color:{C_TEXT};font-size:28px;font-weight:800;'
                f'margin:4px 0;">${lp:,.2f}</div>'
                f'<div style="color:{chg_c};font-size:14px;font-weight:600;">'
                f'{chg:+.2f}% (24h)</div>'
                f'<hr style="border-color:{C_BORDER};margin:14px 0;">'
                f'<div style="display:flex;justify-content:space-between;'
                f'font-size:12px;margin-bottom:6px;">'
                f'<span style="color:{C_MUTED};">24h High</span>'
                f'<span style="color:{C_GREEN};font-weight:600;">${hi:,.2f}</span></div>'
                f'<div style="display:flex;justify-content:space-between;'
                f'font-size:12px;margin-bottom:6px;">'
                f'<span style="color:{C_MUTED};">24h Low</span>'
                f'<span style="color:{C_RED};font-weight:600;">${lo:,.2f}</span></div>'
                f'<div style="display:flex;justify-content:space-between;'
                f'font-size:12px;">'
                f'<span style="color:{C_MUTED};">Volume</span>'
                f'<span style="color:{C_TEXT};font-weight:600;">'
                f'{vol:,.0f}</span></div>'
                f'</div>',
                unsafe_allow_html=True,
            )
        else:
            st.warning("Could not fetch market data.")

        # ── Session order history ──────────────────────────────────────────────
        if st.session_state.order_history:
            st.markdown("<br>", unsafe_allow_html=True)
            _section("Session Orders")
            hist_df = pd.DataFrame(st.session_state.order_history[:10])
            st.dataframe(hist_df, use_container_width=True, hide_index=True)


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3 — POSITIONS & PnL
# ═══════════════════════════════════════════════════════════════════════════════
def _render_positions(client) -> None:
    _section("Open Positions & PnL")

    pos_df = _fetch_positions(client)

    if pos_df.empty:
        st.info(
            "No open positions at this time. Place a trade on the **Place Order** tab.",
            icon="📭",
        )
        return

    total_upnl = pos_df["Unrealized PnL"].sum()
    total_notional = pos_df["Notional (USDT)"].sum()
    upnl_c = C_GREEN if total_upnl >= 0 else C_RED

    # ── Summary metrics ───────────────────────────────────────────────────────
    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric("Open Positions", len(pos_df))
    with m2:
        st.metric("Total Notional", f"${total_notional:,.2f}", "USDT")
    with m3:
        st.metric(
            "Total Unrealized PnL",
            f"${total_upnl:+.4f}",
            delta_color="normal",
        )

    st.divider()

    # ── PnL bar chart ─────────────────────────────────────────────────────────
    _section("PnL Visualization")

    labels = pos_df["Symbol"] + "<br>" + pos_df["Direction"]
    values = pos_df["Unrealized PnL"].tolist()
    roe    = pos_df["ROE %"].tolist()
    colors = [C_GREEN if v >= 0 else C_RED for v in values]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Unrealized PnL",
        x=pos_df["Symbol"],
        y=values,
        marker_color=colors,
        marker_line_width=0,
        text=[f"${v:+.4f}" for v in values],
        textposition="outside",
        hovertemplate=(
            "<b>%{x}</b><br>"
            "PnL: $%{y:+.4f}<br>"
            "<extra></extra>"
        ),
    ))
    layout = _plotly_layout(height=300)
    layout["yaxis"]["tickprefix"] = "$"
    layout["showlegend"] = False
    fig.update_layout(**layout)
    st.plotly_chart(fig, use_container_width=True)

    # ── ROE donut chart ───────────────────────────────────────────────────────
    col1, col2 = st.columns(2)
    with col1:
        _section("ROE % per Position")
        fig2 = go.Figure(go.Pie(
            labels=pos_df["Symbol"] + " " + pos_df["Direction"],
            values=[abs(r) for r in roe],
            hole=0.55,
            marker_colors=[C_GREEN if r >= 0 else C_RED for r in roe],
            textinfo="label+percent",
            hovertemplate="<b>%{label}</b><br>ROE: %{value:.2f}%<extra></extra>",
        ))
        fig2.update_layout(**_plotly_layout(height=280))
        st.plotly_chart(fig2, use_container_width=True)

    with col2:
        _section("Notional Allocation")
        fig3 = go.Figure(go.Pie(
            labels=pos_df["Symbol"],
            values=pos_df["Notional (USDT)"].tolist(),
            hole=0.55,
            marker_colors=[C_YELLOW, C_GREEN, C_RED, C_MUTED][: len(pos_df)],
            textinfo="label+percent",
            hovertemplate="<b>%{label}</b><br>Notional: $%{value:,.2f}<extra></extra>",
        ))
        fig3.update_layout(**_plotly_layout(height=280))
        st.plotly_chart(fig3, use_container_width=True)

    st.divider()
    _section("Raw Position Data")
    st.dataframe(pos_df, use_container_width=True, hide_index=True)


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 4 — ORDER MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════════════
def _render_orders(client) -> None:
    _section("Open Orders")

    ord_df = _fetch_open_orders(client)

    if ord_df.empty:
        st.info("No open orders at this time.", icon="📋")
    else:
        st.dataframe(ord_df, use_container_width=True, hide_index=True)

    st.divider()

    # ── Cancel by Order ID ────────────────────────────────────────────────────
    _section("Cancel Order")

    with st.form("cancel_form", clear_on_submit=True):
        cc1, cc2 = st.columns(2)
        with cc1:
            cancel_sym = st.selectbox("Symbol", SYMBOLS, key="cancel_symbol")
        with cc2:
            cancel_id = st.number_input(
                "Order ID",
                min_value=1,
                value=1,
                step=1,
                format="%d",
                help="The numeric Order ID returned when the order was placed",
            )
        cancel_submitted = st.form_submit_button(
            "Cancel Order", use_container_width=True
        )

        if cancel_submitted:
            with st.spinner(f"Cancelling order {cancel_id}..."):
                try:
                    resp = client.futures_cancel_order(
                        symbol=cancel_sym.upper(), orderId=int(cancel_id)
                    )
                    status = resp.get("status", "N/A")
                    st.session_state.cancel_ok  = True
                    st.session_state.cancel_msg = (
                        f"Order **{cancel_id}** cancelled. Status: **{status}**"
                    )
                except BinanceAPIException as e:
                    st.session_state.cancel_ok  = False
                    st.session_state.cancel_msg = (
                        f"API Error [{e.status_code}]: {e.message}"
                    )
                except Exception as e:
                    st.session_state.cancel_ok  = False
                    st.session_state.cancel_msg = f"{type(e).__name__}: {e}"

    if st.session_state.cancel_msg:
        if st.session_state.cancel_ok:
            st.success(f"✅  {st.session_state.cancel_msg}")
        else:
            st.error(f"❌  {st.session_state.cancel_msg}")

    st.divider()

    # ── Session history ───────────────────────────────────────────────────────
    if st.session_state.order_history:
        _section("Session Order History")
        hist_df = pd.DataFrame(st.session_state.order_history)
        st.dataframe(hist_df, use_container_width=True, hide_index=True)

        if st.button("Clear Session History"):
            st.session_state.order_history = []
            st.rerun()


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 5 — TRADE LOG
# ═══════════════════════════════════════════════════════════════════════════════
def _render_logs() -> None:
    _section("Live Trade Log")

    logs = _parse_logs(max_lines=500)

    if not logs:
        st.info(
            "No log entries found. Ensure `logs/bot.log` exists by placing at least one order.",
            icon="📜",
        )
        return

    # Filters
    fc1, fc2, fc3 = st.columns([2, 2, 1])
    with fc1:
        level_filter = st.multiselect(
            "Filter by Level",
            ["INFO", "WARNING", "ERROR", "CRITICAL", "DEBUG"],
            default=["INFO", "WARNING", "ERROR", "CRITICAL"],
        )
    with fc2:
        search = st.text_input("Search messages", placeholder="e.g. Order ID, BTCUSDT…")
    with fc3:
        max_rows = st.selectbox("Show rows", [25, 50, 100, 200], index=1)

    # Apply filters
    filtered = [
        e for e in reversed(logs)
        if e["Level"] in level_filter
        and (search.lower() in e["Message"].lower() if search else True)
    ][:max_rows]

    # Stats bar
    level_counts = {lv: sum(1 for e in logs if e["Level"] == lv) for lv in
                    ["INFO", "WARNING", "ERROR", "CRITICAL", "DEBUG"]}
    sc1, sc2, sc3, sc4, sc5 = st.columns(5)
    for col, lv, color in zip(
        [sc1, sc2, sc3, sc4, sc5],
        ["INFO", "WARNING", "ERROR", "CRITICAL", "DEBUG"],
        [C_GREEN, C_YELLOW, C_RED, "#FF4081", C_MUTED],
    ):
        with col:
            st.markdown(
                f'<div style="background:{C_CARD};border:1px solid {C_BORDER};'
                f'border-top:3px solid {color};border-radius:6px;'
                f'padding:10px;text-align:center;">'
                f'<div style="color:{color};font-size:20px;font-weight:700;">'
                f'{level_counts.get(lv, 0)}</div>'
                f'<div style="color:{C_MUTED};font-size:11px;">{lv}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    st.markdown("<br>", unsafe_allow_html=True)

    # Log table
    if filtered:
        level_colors = {
            "INFO":     C_GREEN,
            "WARNING":  C_YELLOW,
            "ERROR":    C_RED,
            "CRITICAL": "#FF4081",
            "DEBUG":    C_MUTED,
        }
        for entry in filtered:
            lv   = entry["Level"]
            col  = level_colors.get(lv, C_TEXT)
            msg  = entry["Message"]
            st.markdown(
                f'<div style="padding:7px 4px;border-bottom:1px solid {C_BORDER};'
                f'font-size:12px;font-family:monospace;">'
                f'<span style="color:{C_MUTED};min-width:150px;display:inline-block;">'
                f'{entry["Timestamp"]}</span>&nbsp;&nbsp;'
                f'<span style="color:{col};font-weight:700;min-width:70px;'
                f'display:inline-block;">{lv}</span>&nbsp;&nbsp;'
                f'<span style="color:{C_TEXT};">{msg}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )
    else:
        st.warning("No entries match the current filters.")

    # Raw log expander
    with st.expander("📄  View Raw Log File"):
        try:
            raw = LOG_FILE.read_text(encoding="utf-8", errors="replace")
            st.code(raw[-6000:], language="text")   # last ~6 KB
        except Exception as e:
            st.error(f"Could not read log file: {e}")


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════
def main() -> None:
    _init_state()
    client, err = _get_client()
    connected   = client is not None

    _render_sidebar(client, connected)

    # ── Page title ─────────────────────────────────────────────────────────────
    st.markdown(
        f'<h1 style="color:{C_TEXT};font-size:26px;font-weight:800;'
        f'margin-bottom:4px;">Binance Futures Testnet Bot</h1>'
        f'<p style="color:{C_MUTED};font-size:13px;margin-top:0;">'
        f'Real-time trading dashboard &nbsp;|&nbsp; Testnet Mode</p>',
        unsafe_allow_html=True,
    )

    # ── Connection error screen ────────────────────────────────────────────────
    if not connected:
        st.error(
            f"**Cannot connect to Binance Testnet.**\n\n{err}",
            icon="🔌",
        )
        st.markdown("### How to Fix:")
        col_local, col_cloud = st.columns(2)
        with col_local:
            st.markdown(
                """
                **1. Local Development (.env)**
                Ensure you have a `.env` file in your project root with:
                ```ini
                BINANCE_API_KEY=your_testnet_key
                BINANCE_API_SECRET=your_testnet_secret
                ```
                """
            )
        with col_cloud:
            st.markdown(
                """
                **2. Streamlit Cloud (Secrets)**
                Add your credentials to the app's Secrets settings:
                1. Go to your **Streamlit Share Dashboard**
                2. Click the three dots `...` next to your app -> **Settings**
                3. Go to the **Secrets** tab and paste:
                ```toml
                BINANCE_API_KEY = "your_testnet_key"
                BINANCE_API_SECRET = "your_testnet_secret"
                ```
                """
            )
        st.markdown(
            """
            ---
            * 🔑 **Need API Keys?** Get them for free at [testnet.binancefuture.com](https://testnet.binancefuture.com)
            * 🔄 **Already updated?** Click **Reset Connection** in the sidebar.
            """
        )
        st.stop()

    # ── Tabs ───────────────────────────────────────────────────────────────────
    t1, t2, t3, t4, t5 = st.tabs([
        "📊  Overview",
        "🛒  Place Order",
        "📈  Positions & PnL",
        "📋  Order Management",
        "📜  Trade Log",
    ])
    with t1:
        _render_overview(client)
    with t2:
        _render_place_order(client)
    with t3:
        _render_positions(client)
    with t4:
        _render_orders(client)
    with t5:
        _render_logs()


if __name__ == "__main__":
    main()
