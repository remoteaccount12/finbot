import numpy as np
import pandas as pd 
from dateutil.relativedelta import relativedelta


def algorithm(input_df,start,end,interval='1d'):
    if input_df.empty:
        return None
    input_df["SM20"] = input_df["Close"].rolling(window=20).mean()
    input_df["SM50"] = input_df["Close"].rolling(window=50).mean()
    input_df["Signal"] = "Hold"
    input_df["RawSignal"] = np.where(input_df["SM20"]>input_df["SM50"],"Buy",
                                     np.where(input_df["SM20"]<input_df["SM50"],"Sell","Hold"))
    input_df["Signal"] = input_df["RawSignal"].shift(1)
    input_df["ExecPrice"] = input_df["Open"]
    # return input_df.dropna(subset=["Signal"])
    return input_df


def get_buy_list_for_date(signals_dict, trade_date):
    tickers = []
    for tkr, sdf in signals_dict.items():
        if trade_date - relativedelta(days=1) in sdf.index and str(sdf.loc[trade_date- relativedelta(days=1), "RawSignal"]) == "Buy":
            tickers.append(tkr)
    return sorted(tickers)