import pandas as pd
import numpy as np
import random
from datetime import date
from dateutil.relativedelta import relativedelta

from .portfolio import Portfolio
from .data import get_sp500_tickers, get_data_cached
from .signals import algorithm
from .exec import execute_user_for_date

def backtest(signals_dict_or_df,starting_cash=1_000,fee_bps=5, slippage_bps=1, allocate_equal_on_buy=True):
    if isinstance(signals_dict_or_df,pd.DataFrame):
        signals_dict = {"TICKER": signals_dict_or_df.copy()}
    else:
        signals_dict = {k: v.copy() for k, v in signals_dict_or_df.items()}
    
    all_dates = sorted(set().union(*[df.index for df in signals_dict.values()]))
    port = Portfolio(starting_cash=starting_cash,fee_bps=fee_bps, slippage_bps=slippage_bps)
    posture = {t: 0 for t in signals_dict}
    
    for trade_date in all_dates:
        port, posture = execute_user_for_date(signals_dict,port,posture,trade_date,allocate_equal_on_buy)
        
    equity_df = pd.DataFrame(port.equity).set_index("Date").sort_index()
    trades_df = pd.DataFrame(port.trades)

    if not equity_df.empty:
        ret = equity_df["Equity"].pct_change().fillna(0.0)
        cum_ret = (1 + ret).prod() - 1
        years = max(1e-9, (equity_df.index[-1] - equity_df.index[0]).days / 365.25)
        cagr = (equity_df["Equity"].iloc[-1] / equity_df["Equity"].iloc[0]) ** (1 / years) - 1 if years > 0 else np.nan
        dd = (equity_df["Equity"] / equity_df["Equity"].cummax() - 1).min()
        sharpe = np.sqrt(252) * (ret.mean() / (ret.std() + 1e-12))
        summary = {
            "Start": equity_df.index[0],
            "End": equity_df.index[-1],
            "StartEquity": equity_df["Equity"].iloc[0],
            "EndEquity": equity_df["Equity"].iloc[-1],
            "TotalReturn": cum_ret,
            "CAGR": cagr,
            "MaxDrawdown": dd,
            "Sharpe(naive)": sharpe,
            "Trades": len(trades_df) if not trades_df.empty else 0,
        }
    else:
        summary = {}

    return {"equity": equity_df, "trades": trades_df, "summary": summary, "portfolio": port}

if __name__ == "__main__":
    sp_list = get_sp500_tickers()
    random.seed(42)  
    sp_sampled = random.sample(sp_list, 500)  
    
    end, start = date.today() - relativedelta(days=10), date.today() - relativedelta(years=1)        
    ticker_dict = get_data_cached(sp_sampled,start,end)

    signals_dict = {k:algorithm(v,start,end) for k,v in ticker_dict.items()}
    res = backtest(signals_dict, starting_cash=100_000)
    print(res["summary"])
    res["trades"].to_csv("data/results/trades.csv")
    res["equity"].to_csv("data/results/equity.csv")