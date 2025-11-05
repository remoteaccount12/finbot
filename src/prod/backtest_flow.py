import pandas as pd
import numpy as np
import random
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
import os 
import json


from src.utils.data import get_sp500_tickers, get_data_cached
from src.utils.signals import algorithm
from src.utils.backtest import backtest
from src.utils.config import Config



RESULTS_JSONL = "data/results/backtest_runs.jsonl"
os.makedirs(os.path.dirname(RESULTS_JSONL), exist_ok=True)

sp_list = get_sp500_tickers()
random.seed(42)  
sp_sampled = random.sample(sp_list, 500)  

end, start = date.today() - relativedelta(days=15), date.today() - relativedelta(years=1)        
ticker_dict = get_data_cached(sp_sampled,start,end)

config = Config()
signals_dict = {k:algorithm(v,start,end,config) for k,v in ticker_dict.items()}
res = backtest(signals_dict, config)

res["trades"].to_csv("data/results/trades.csv")
res["equity"].to_csv("data/results/equity.csv")

run_record = {
    "timestamp": datetime.now().isoformat(),
    "random_seed": 42,
    "start_date": start.isoformat(),
    "end_date": end.isoformat(),
    "num_tickers": len(sp_sampled),
    "signals_config": config.signals,
    "backtest_config": config.backtest,
    "summary": {
        **res["summary"],
        "Start": res["summary"]["Start"].isoformat(),   
        "End": res["summary"]["End"].isoformat(),       
    },
    "num_trades": len(res["trades"]),
    "final_equity": res["summary"].get("EndEquity", res["summary"].get("StartEquity")),
}


print("\n" + "="*60)
print("BACKTEST RUN LOGGED")
print("="*60)
print(f"File → {RESULTS_JSONL}")
print(f"Timestamp → {run_record['timestamp']}")
print(f"Final Equity → ${run_record['final_equity']:,.2f}")
print(f"CAGR → {run_record['summary'].get('CAGR', 0):.1%}")
print(f"Trades → {run_record['num_trades']}")
print(f"Config → allocate_equal={config.backtest['allocate_equal_on_buy']}, "
      f"threshold={config.signals['score_threshold_buy']}")
print("="*60 + "\n")

with open(RESULTS_JSONL, "a", encoding="utf-8") as f:
    f.write(json.dumps(run_record, ensure_ascii=False) + "\n")