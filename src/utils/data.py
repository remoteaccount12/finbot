import pandas as pd 
import yfinance as yf
import os 

def get_sp500_tickers():
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    tables = pd.read_html(url, storage_options={"User-Agent":"Mozilla/5.0"})
    syms = tables[0]["Symbol"].astype(str).tolist()
    return [s.replace(".", "-").strip() for s in syms]

def get_data_cached(tickers,start,end,interval="1d", cache_dir="data/data_cache"):
    start_ts, end_ts = pd.Timestamp(start).normalize(), pd.Timestamp(end).normalize()
    last_needed = (end_ts - pd.Timedelta(days=1)).date()
    os.makedirs(cache_dir,exist_ok=True)
    to_fetch = []
    results = {}
    for t in tickers:
        fn = os.path.join(cache_dir,f"{t}.csv")
        if os.path.exists(fn):
            df = pd.read_csv(fn,parse_dates=["Date"],index_col="Date").sort_index()
            have_lo, have_hi = df.index.min().date(), df.index.max().date()
            if have_lo <= start_ts.date() and have_hi >= last_needed:
                results[t] = df.loc[start_ts:end_ts]
                continue
        to_fetch.append(t)

    if to_fetch:
        bulk = yf.download(to_fetch,start=start,end=end,interval=interval,threads=True,group_by='ticker')
        for t in to_fetch:
            try:
                df = bulk[t] if t in bulk else bulk 
                if isinstance(df.columns, pd.MultiIndex):
                    df = df.droplevel(0, axis=1)
                df = df.sort_index()
                df.to_csv(os.path.join(cache_dir, f"{t}.csv"))
                results[t] = df
            except Exception as e:
                print(f"[WARN] {t} failed to fetch: {e}")
    return results