# python -m src.prod.backtest_flow
import pandas as pd
import numpy as np
import random
from datetime import date
from dateutil.relativedelta import relativedelta

from src.utils.data import get_sp500_tickers, get_data_cached
from src.utils.signals import algorithm
from src.utils.backtest import backtest
from src.utils.config import Config


sp_list = get_sp500_tickers()
random.seed(42)  
sp_sampled = random.sample(sp_list, 50)  

end, start = date.today() - relativedelta(days=10), date.today() - relativedelta(years=1)        
ticker_dict = get_data_cached(sp_sampled,start,end)

config = Config()
signals_dict = {k:algorithm(v,start,end,config) for k,v in ticker_dict.items()}
res = backtest(signals_dict, config)
print(res["summary"])
res["trades"].to_csv("data/results/trades.csv")
res["equity"].to_csv("data/results/equity.csv")