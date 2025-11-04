import os, pickle, random
from dotenv import load_dotenv
load_dotenv()
from datetime import date
from dateutil.relativedelta import relativedelta
import pandas as pd 

from src.utils.data import get_sp500_tickers, get_data_cached
from src.utils.signals import algorithm, get_buy_list_for_date
from src.utils.exec import execute_user_for_date
from src.utils.portfolio import Portfolio

sp_list = get_sp500_tickers()
random.seed(42)  
sp_sampled = random.sample(sp_list, 500)  

end, start = date.today() - relativedelta(days=10), date.today() - relativedelta(years=1)        
ticker_dict = get_data_cached(sp_sampled,start,end)

signals_dict = {k:algorithm(v,start,end) for k,v in ticker_dict.items()}


fee_bps=5
slippage_bps=1
allocate_equal_on_buy = True
trade_date = date.today() - relativedelta(days=23)
trade_date = trade_date.strftime('%Y-%m-%d')
port = Portfolio(starting_cash=10_000,fee_bps=fee_bps, slippage_bps=slippage_bps)

buy_list = get_buy_list_for_date(signals_dict, trade_date=trade_date)
# print(buy_list)

posture = {t: 0 for t in signals_dict}
port, posture = execute_user_for_date(signals_dict,port,posture,trade_date,allocate_equal_on_buy)
equity_df = pd.DataFrame(port.equity).set_index("Date").sort_index()
trades_df = pd.DataFrame(port.trades)


print(equity_df)
print(trades_df)
