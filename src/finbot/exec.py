# src/finbot/exec.py
from __future__ import annotations
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import date, timedelta
from typing import Dict, List, Tuple

from .portfolio import load_portfolio_csv, save_portfolio_csv, Portfolio  


def _ensure_exec_price(ticker: str, df: pd.DataFrame, trade_date: date):
    px = np.nan
    ts = pd.Timestamp(trade_date)

    if (ts in df.index) and ("ExecPrice" in df.columns):
        px = float(df.loc[ts, "ExecPrice"])
    if (ts in df.index) and (("Open" in df.columns) and (pd.isna(px) or px <= 0)):
        px = float(df.loc[ts, "Open"])

    if pd.isna(px) or px <= 0:
        try:
            nxt = ts + pd.Timedelta(days=1)
            tmp = yf.download(ticker, start=ts.date(), end=nxt.date(), interval="1d", progress=False, threads=False)
            if not tmp.empty:
                px = float(tmp["Open"].iloc[0])
        except Exception:
            pass
    return float(px) if not pd.isna(px) else np.nan


def execute_user_buys_for_date(
    signals_dict: Dict[str, pd.DataFrame],
    tickers_executed: List[str],
    trade_date: date,
    *,
    starting_cash: float = 1_000,
    fee_bps: float = 5,
    slippage_bps: float = 1) -> Tuple[Portfolio, List[Tuple[str, float]]]:

    port = load_portfolio_csv(starting_cash=starting_cash, fee_bps=fee_bps, slippage_bps=slippage_bps)

    # build price list
    priced: List[Tuple[str, float]] = []
    for tk in [t.strip().upper() for t in tickers_executed if t.strip()]:
        df = signals_dict.get(tk)
        if df is None:
            continue
        px = _ensure_exec_price(tk, df, trade_date)
        if not (pd.isna(px) or px <= 0):
            priced.append((tk, px))

    if not priced:
        return port, []

    cash_each = port.cash / len(priced)
    fills: List[Tuple[str, float]] = []
    for tk, px in priced:
        before = port.cash
        port.buy_cash_all(ticker=tk, price=px, date=trade_date, cash_to_use=cash_each)
        if port.cash < before:  # trade executed
            fills.append((tk, px))

    save_portfolio_csv(port)
    return port, fills
