#portfolio
import pandas as pd 
import os 

class Portfolio:
    def __init__(self,starting_cash,fee_bps,slippage_bps,stop_pct, target_pct):
        self.cash = float(starting_cash)
        self.positions = {}
        self.fee_bps = float(fee_bps)
        self.slippage_bps = float(slippage_bps)
        self.stop_pct = float(stop_pct)
        self.target_pct = float(target_pct)
        self.trades = []
        self.equity = []
    
    def _apply_costs(self,notional):
        fee = abs(notional)*self.fee_bps/10_000.0
        return fee 
    
    def _exec_price(self,raw_price,side):
        mult = 1+ (self.slippage_bps/10_000) if side == "buy" else 1-(self.slippage_bps/10_000)
        return raw_price*mult
    
    def buy_cash_all(self,ticker,price,date,cash_to_use=None, reason="indicator"):
        if cash_to_use is None:
            cash_to_use =self.cash
        if cash_to_use <= 0:
            return
        px = self._exec_price(price,"buy")
        shares = int(cash_to_use//px)
        if shares <= 0:
            return 
        notional = shares*px
        fee = self._apply_costs(notional)
        total = notional+fee
        if total > self.cash:
            return 
        self.cash -= total
        entry_price = px
        stop_loss = entry_price * (1 - self.stop_pct) if self.stop_pct > 0 else None
        target = entry_price * (1 + self.target_pct) if self.target_pct > 0 else None

        self.positions[ticker] = {
        'shares': shares,
        'entry_price': entry_price,
        'stop_loss': stop_loss,
        'target': target}
        self.trades.append({"Date": date, "Ticker": ticker, "Side": "BUY", "Price": px, "Shares": shares, "Fee": fee, "Reason": reason})
    
    def sell_all(self, ticker, price, date, reason="indicator"):
        if ticker not in self.positions:
            return
        shares = self.positions[ticker]['shares']
        if shares <= 0:
            return
        px = self._exec_price(price, "sell")
        notional = shares * px
        fee = self._apply_costs(notional)
        self.cash += (notional - fee)
        del self.positions[ticker]  
        self.trades.append({"Date": date, "Ticker": ticker, "Side": "SELL", "Price": px, "Shares": shares, "Fee": fee, "Reason": reason})

    def mark_to_market(self,date,close_prices:dict):
        pos_value = 0.0
        for tkr, pos in self.positions.items():
            sh = pos['shares']
            if sh > 0 and tkr in close_prices:
                pos_value += sh * float(close_prices[tkr])
        equity = self.cash + pos_value
        self.equity.append({"Date": date, "Equity": equity, "Cash": self.cash, "PosValue": pos_value})


    def total_value(self):
        if not self.equity:
            return self.cash
        return self.equity[-1]["Equity"]
    
PORTFOLIO_DIR = "portfolio_store"
os.makedirs(PORTFOLIO_DIR, exist_ok=True)

def _csv_path(name): return os.path.join(PORTFOLIO_DIR, name)

def save_portfolio_csv(port):
    # cash
    pd.DataFrame([{"Cash": port.cash}]).to_csv(_csv_path("cash.csv"), index=False)
    # positions
    pos_df = pd.DataFrame(
    [{"Ticker": t, "Shares": pos['shares'], "EntryPrice": pos['entry_price'], "StopLoss": pos['stop_loss'], "Target": pos['target']}
     for t, pos in port.positions.items() if pos['shares'] > 0]
    )
    if pos_df.empty:
        pos_df = pd.DataFrame(columns=["Ticker", "Shares", "EntryPrice", "StopLoss", "Target"])
    pos_df.to_csv(_csv_path("positions.csv"), index=False)
    # trades
    trades_df = pd.DataFrame(port.trades)
    if not trades_df.empty:
        trades_df.to_csv(_csv_path("trades.csv"), index=False)
    elif not os.path.exists(_csv_path("trades.csv")):
        pd.DataFrame(columns=["Date","Ticker","Side","Price","Shares","Fee"]).to_csv(_csv_path("trades.csv"), index=False)
    # equity
    eq_df = pd.DataFrame(port.equity)
    if not eq_df.empty:
        eq_df.to_csv(_csv_path("equity.csv"), index=False)
    elif not os.path.exists(_csv_path("equity.csv")):
        pd.DataFrame(columns=["Date","Equity","Cash","PosValue"]).to_csv(_csv_path("equity.csv"), index=False)

def load_portfolio_csv(starting_cash=1_000, fee_bps=5, slippage_bps=1):
    port = Portfolio(starting_cash=starting_cash, fee_bps=fee_bps, slippage_bps=slippage_bps)
    # cash
    if os.path.exists(_csv_path("cash.csv")):
        cdf = pd.read_csv(_csv_path("cash.csv"))
        if not cdf.empty and "Cash" in cdf.columns:
            port.cash = float(cdf["Cash"].iloc[-1])
    # positions
    if os.path.exists(_csv_path("positions.csv")):
        pdf = pd.read_csv(_csv_path("positions.csv"))
        for _, r in pdf.iterrows():
            port.positions[str(r["Ticker"])] = {
                'shares': int(r["Shares"]),
                'entry_price': float(r.get("EntryPrice", 0)),  # Default 0 if missing (for old CSVs)
                'stop_loss': float(r.get("StopLoss", None)),
                'target': float(r.get("Target", None))
            }
    # trades
    if os.path.exists(_csv_path("trades.csv")):
        tdf = pd.read_csv(_csv_path("trades.csv"))
        if not tdf.empty:
            # Make sure Date stays string or ISO
            port.trades = tdf.to_dict("records")
    # equity
    if os.path.exists(_csv_path("equity.csv")):
        edf = pd.read_csv(_csv_path("equity.csv"))
        if not edf.empty:
            port.equity = edf.to_dict("records")
    return port


