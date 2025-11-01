import os, pickle, random
from dotenv import load_dotenv
load_dotenv()
from datetime import date
from dateutil.relativedelta import relativedelta
from src.finbot.data import get_sp500_tickers, get_data_cached
from src.finbot.signals import algorithm, get_buy_list_for_date
from src.finbot.messaging_gmail import send_recos_email

# pick universe
sp_list = get_sp500_tickers()
random.seed(42)
sp_sampled = random.sample(sp_list, 50)

end = date.today() - relativedelta(days=3)
start = end - relativedelta(years=1)
ticker_dict = get_data_cached(sp_sampled, start, end)

signals_dict = {k: algorithm(v, start, end) for k, v in ticker_dict.items()}
# persist for sms server
with open("signals_dict.pkl", "wb") as f:
  pickle.dump(signals_dict, f)

# send BUY list (for today's open)
buy_list = get_buy_list_for_date(signals_dict, trade_date=end)
send_recos_email(buy_list, trade_date=end)
print("Sent daily recommendations.")