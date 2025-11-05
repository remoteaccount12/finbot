# exec.py
from __future__ import annotations
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import date, timedelta
from typing import Dict, List, Tuple


def _collect_signal_trades(signals_dict: Dict[str, pd.DataFrame],posture: dict,trade_date: date,top_n_buys: int):
    todays_buys_candidates = []
    todays_sells = []
    for tkr, df in signals_dict.items():
        if trade_date not in df.index:
            continue
        row = df.loc[trade_date]
        sig = row["Signal"]
        exec_px = row["ExecPrice"]
        score = float(row["Score"]) if not pd.isna(row["Score"]) else 0.0
        if sig == "Buy" and posture.get(tkr, 0) == 0: #Buy only if you don't already have that stock
            todays_buys_candidates.append((tkr, exec_px, score))
        elif sig == "Sell" and posture.get(tkr, 0) == 1:  # Sell only if you already have that stock ie no shorting 
            todays_sells.append((tkr, exec_px))
    
    if todays_buys_candidates:
        todays_buys_candidates.sort(key=lambda x: x[2], reverse=True)
        todays_buys = todays_buys_candidates[:top_n_buys]
    else:
        todays_buys = []
    return todays_buys, todays_sells

def _exec_sells(signals_dict: Dict[str, pd.DataFrame],port: List[str],posture: dict,trade_date: date,todays_sells):
    # 2) Execute sells first (free up cash)
    for tkr, px in todays_sells:
        port.sell_all(tkr, px, trade_date, reason="indicator")
        posture[tkr] = 0

    # 2.5) Check for target/stop loss on remaining positions 
    todays_tp_sells = []
    todays_sl_sells = []
    for tkr in list(port.positions.keys()):
        if posture.get(tkr, 0) == 0:
            continue
        if trade_date not in signals_dict.get(tkr, pd.DataFrame()).index:
            continue
        row = signals_dict[tkr].loc[trade_date]
        pos = port.positions.get(tkr, {})
        target = pos.get('target')
        stop_loss = pos.get('stop_loss')
        close_px = row["Close"]
        if target is not None and close_px >= target:
            todays_tp_sells.append((tkr, close_px))
        elif stop_loss is not None and close_px <= stop_loss:
            todays_sl_sells.append((tkr, close_px))

    for tkr, px in todays_tp_sells:
        port.sell_all(tkr, px, trade_date, reason="target")
        posture[tkr] = 0

    for tkr, px in todays_sl_sells:
        port.sell_all(tkr, px, trade_date, reason="stoploss")
        posture[tkr] = 0

    return posture,port

def _exec_buys(port: List[str],posture: dict,trade_date: date,todays_buys,allocate_equal_on_buy,max_daily_exposure_pct):
    # 3) Execute buys (allocate equally across new buys if requested)
    if not todays_buys:
        return posture, port
    max_cash_to_deploy = port.total_value() * max_daily_exposure_pct
    cash_to_deploy = min(port.cash, max_cash_to_deploy)

    if allocate_equal_on_buy:
        cash_per_buy = cash_to_deploy / len(todays_buys)
        for tkr, px, _score in todays_buys:
            port.buy_cash_all(tkr, px, trade_date, cash_to_use=cash_per_buy, reason="indicator")
            if port.positions.get(tkr, {}).get("shares", 0) > 0:
                posture[tkr] = 1
    else:
        scores = [max(s, 1e-9) for _t, _p, s in todays_buys]
        total_score = sum(scores)
        for (tkr, px, score), weight in zip(todays_buys, [s/total_score for s in scores]):
            cash_this_buy = cash_to_deploy * weight
            port.buy_cash_all(tkr, px, trade_date,cash_to_use=cash_this_buy,reason="indicator")
            if port.positions.get(tkr, {}).get("shares", 0) > 0:
                posture[tkr] = 1


    return posture,port

def _mark_to_mark(signals_dict: Dict[str, pd.DataFrame],port: List[str],trade_date: date):
    # 4) Mark to market using Close prices of today (if available)
    close_prices = {}
    for tkr, df in signals_dict.items():
        if trade_date in df.index:
            close_prices[tkr] = df.loc[trade_date,"Close"]
    port.mark_to_market(trade_date,close_prices)
    return port




def execute_user_for_date(signals_dict: Dict[str, pd.DataFrame],port: List[str],posture,trade_date: date,allocate_equal_on_buy, top_n_buys,max_daily_exposure_pct):

    todays_buys,todays_sells=_collect_signal_trades(signals_dict,posture,trade_date,top_n_buys)
    posture,port = _exec_sells(signals_dict,port,posture,trade_date,todays_sells)
    posture,port = _exec_buys(port,posture,trade_date,todays_buys,allocate_equal_on_buy,max_daily_exposure_pct)
    port = _mark_to_mark(signals_dict,port,trade_date)
    
    return port, posture