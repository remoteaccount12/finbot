#signals
import numpy as np
import pandas as pd 
from dateutil.relativedelta import relativedelta



def _ma_cross(df: pd.DataFrame, config) -> pd.Series:
    """+1 when short > long, -1 when short < long, 0 otherwise."""
    s = df["Close"].rolling(window=config.signals["ma_cross"]['short_window']).mean()
    l = df["Close"].rolling(window=config.signals["ma_cross"]['long_window']).mean()
    return np.where(s > l, 1.0, np.where(s < l, -1.0, 0.0))

def _rsi_signal(df: pd.DataFrame, config) -> pd.Series:
    """Scale RSI to -1 … +1 (oversold → +1, overbought → -1)."""
    delta = df["Close"].diff()
    period = config.signals["rsi_signal"]['period']
    oversold = config.signals["rsi_signal"]['oversold']
    overbought = config.signals["rsi_signal"]['overbought']

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

def _macd_signal(df: pd.DataFrame,config) -> pd.Series:
    """Normalised MACD histogram → -1 … +1."""
    signal = config.signals["macd_signal"]['signal']
    fast = config.signals["macd_signal"]['fast']
    slow = config.signals["macd_signal"]['slow']
    e1 = df["Close"].ewm(span=fast,  adjust=False).mean()
    e2 = df["Close"].ewm(span=slow,  adjust=False).mean()
    macd = e1 - e2
    sig  = macd.ewm(span=signal, adjust=False).mean()
    hist = macd - sig
    # simple normalisation by recent volatility
    vol = hist.abs().rolling(window=20).quantile(0.95).replace(0, np.nan)
    return (hist / vol).clip(-1, 1).fillna(0)

def _bb_signal(df: pd.DataFrame, config) -> pd.Series:
    """BB: +1 oversold (below lower), -1 overbought (above upper)."""
    period = config.signals["bb_signal"]['period']
    std = config.signals["bb_signal"]['std']
    mid = df["Close"].rolling(period).mean()
    stddev = df["Close"].rolling(period).std()
    upper = mid + std * stddev
    lower = mid - std * stddev
    return np.where(df["Close"] < lower, 1.0,
           np.where(df["Close"] > upper, -1.0, 0.0))

def _atr(df: pd.DataFrame, config) -> pd.Series:
    high_low = df['High'] - df['Low']
    high_close = np.abs(df['High'] - df['Close'].shift())
    low_close = np.abs(df['Low'] - df['Close'].shift())
    tr = pd.concat([high_low,high_close,low_close],axis=1).max(axis=1)
    return tr.rolling(window=config.signals['atr_signal']['period'],min_periods=1).mean()


_INDICATOR_MAP = {
    "ma_cross": _ma_cross,
    "rsi_signal": _rsi_signal,
    "macd_signal": _macd_signal,
    "bb_signal": _bb_signal,
}


def algorithm(input_df,start,end,config,interval='1d'):
    if input_df.empty:
        return None
    input_df["ATR"] = _atr(input_df,config)
    ind_list = config.signals["indicators"]
    scores = []
    for i, fn in enumerate(ind_list):
        col = f"_score{i}"
        input_df[col] = _INDICATOR_MAP[fn](input_df,config)
        scores.append(input_df[col])

    # Aggregate score = simple average
    score_df = pd.concat(scores, axis=1)
    input_df["RawScore"] = score_df.mean(axis=1)
    input_df["RawSignal"] = np.where(input_df["RawScore"] > config.signals["score_threshold_buy"], "Buy",
                           np.where(input_df["RawScore"] < config.signals["score_threshold_sell"], "Sell", "Hold"))
    input_df["Signal"] = input_df["RawSignal"].shift(1)
    input_df["Score"] = input_df["RawScore"].shift(1)
    input_df["ExecPrice"] = input_df["Open"]
    
    input_df["ATR_at_Entry"] = input_df["ATR"].shift(1)
    return input_df



def get_buy_list_for_date(signals_dict, trade_date):
    tickers = []
    for tkr, sdf in signals_dict.items():
        if trade_date in sdf.index and str(sdf.loc[trade_date, "Signal"]) == "Buy":
            tickers.append(tkr)
    return sorted(tickers)