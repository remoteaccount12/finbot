import numpy as np
import pandas as pd 
from dateutil.relativedelta import relativedelta


def _ma_cross(df: pd.DataFrame, short: int = 20, long: int = 50) -> pd.Series:
    """+1 when short > long, -1 when short < long, 0 otherwise."""
    s = df["Close"].rolling(window=short).mean()
    l = df["Close"].rolling(window=long).mean()
    return np.where(s > l, 1.0, np.where(s < l, -1.0, 0.0))

def _rsi_signal(df: pd.DataFrame, period: int = 14,
                overbought: int = 70, oversold: int = 30) -> pd.Series:
    """Scale RSI to -1 … +1 (oversold → +1, overbought → -1)."""
    delta = df["Close"].diff()
    up, down = delta.clip(lower=0), -delta.clip(upper=0)
    roll_up   = up.ewm(alpha=1/period, adjust=False).mean()
    roll_down = down.ewm(alpha=1/period, adjust=False).mean()
    rs = roll_up / roll_down
    rsi = 100 - (100 / (1 + rs))
    # linear map: 0-30 → +1 … +0, 70-100 → -1 … 0
    score = pd.Series(0.0, index=df.index)
    score = score.where(rsi > oversold,  (oversold - rsi) / oversold)
    score = score.where(rsi < overbought, -(rsi - overbought) / (100 - overbought))
    return score.clip(-1, 1)

def _macd_signal(df: pd.DataFrame,
                 fast: int = 12, slow: int = 26, signal: int = 9) -> pd.Series:
    """Normalised MACD histogram → -1 … +1."""
    e1 = df["Close"].ewm(span=fast,  adjust=False).mean()
    e2 = df["Close"].ewm(span=slow,  adjust=False).mean()
    macd = e1 - e2
    sig  = macd.ewm(span=signal, adjust=False).mean()
    hist = macd - sig
    # simple normalisation by recent volatility
    vol = hist.abs().rolling(window=20).quantile(0.95).replace(0, np.nan)
    return (hist / vol).clip(-1, 1).fillna(0)

def _bb_signal(df: pd.DataFrame, period: int = 20, std: float = 2) -> pd.Series:
    """BB: +1 oversold (below lower), -1 overbought (above upper)."""
    mid = df["Close"].rolling(period).mean()
    stddev = df["Close"].rolling(period).std()
    upper = mid + std * stddev
    lower = mid - std * stddev
    return np.where(df["Close"] < lower, 1.0,
           np.where(df["Close"] > upper, -1.0, 0.0))


# _DEFAULT_INDICATORS = [_ma_cross, _rsi_signal, _macd_signal]
# _DEFAULT_INDICATORS = [_bb_signal, _rsi_signal, _macd_signal]
_DEFAULT_INDICATORS = [_ma_cross, _macd_signal]

def algorithm(input_df,start,end,interval='1d',indicators=None):
    if input_df.empty:
        return None
    
    ind_list = indicators if indicators is not None else _DEFAULT_INDICATORS
    scores = []
    for i, fn in enumerate(ind_list):
        col = f"_score{i}"
        input_df[col] = fn(input_df)
        scores.append(input_df[col])

    # Aggregate score = simple average
    score_df = pd.concat(scores, axis=1)
    input_df["RawScore"] = score_df.mean(axis=1)
    input_df["RawSignal"] = np.where(input_df["RawScore"] > 0.99, "Buy",
                           np.where(input_df["RawScore"] < -0.99, "Sell", "Hold"))
    input_df["Signal"] = input_df["RawSignal"].shift(1)
    input_df["Score"] = input_df["RawScore"].shift(1)
    input_df["ExecPrice"] = input_df["Open"]
    return input_df



def get_buy_list_for_date(signals_dict, trade_date):
    tickers = []
    for tkr, sdf in signals_dict.items():
        if trade_date in sdf.index and str(sdf.loc[trade_date, "Signal"]) == "Buy":
            tickers.append(tkr)
    return sorted(tickers)