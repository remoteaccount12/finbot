# FinBot

FinBot is a **Python-based backtestable trading system** for the S&P 500. 
The system is fully modular and designed for research, backtesting, and future live execution.
It automates stock trading signals generation and execution for S&P 500 stocks. 
It includes functionality for data fetching, signal generation, email notifications, and trade execution.

## Key Features

| Feature | Description |
|-------|-----------|
| **Multi-Indicator Scoring** | Combines MA Crossover, RSI, MACD, and Bollinger Bands into a normalized composite score |
| **Daily Signal Generation** | Buy/Sell/Hold signals with to execute on next-day open |
| **Backtesting Engine** | Full event-driven simulation with slippage, fees, and equal-weight allocation |
| **Risk Management** | Automatic stop-loss (5%) and take-profit (10%) on all entries |
| **Performance Metrics** | CAGR, Total Return, Max Drawdown, Sharpe Ratio, Trade Count |
| **Portfolio Tracking** | Cash, positions, equity curve, full trade log |
| **CSV Persistence** | Save/load portfolio state for continuity |

## Current Backtest Result (1-Year, 500 S&P Stocks)

```text
Start:          2024-11-04
End:            2025-10-24
Start Equity:   $1,000.00
End Equity:     $936.92
Total Return:   -6.31%
CAGR:           -6.50%
Max Drawdown:   -9.23%
Sharpe (naive): -0.80
Trades:         317


## Components

### 1. Data Management (`data.py`)
- `get_sp500_tickers()`: Fetches current S&P 500 company symbols from Wikipedia
- `get_data_cached()`: Retrieves historical stock data with local caching support

### 2. Signal Generation (`signals.py`)
- `algorithm(input_df, start, end, interval='1d')`: Implements a moving average crossover strategy
  - Calculates 20-day and 50-day simple moving averages
  - Generates Buy/Sell/Hold signals based on MA crossovers
- `get_buy_list_for_date()`: Returns list of stocks to buy for a specific date

### 3. Messaging System (`messaging_gmail.py`)
- Handles email communication for trade signals
- `send_recos_email()`: Sends buy recommendations via Gmail SMTP
- Supports both "BUY" signal notifications and "No signals" updates

### 4. Trade Execution (`exec.py`)
- `execute_user_buys_for_date()`: Processes and executes trades based on user responses
- Includes price verification and slippage handling
- Manages portfolio updates and trade logging

### 5. Reply Processing (`reply_listener.py`)
- Monitors email replies for trade confirmation
- Parses user responses to execute confirmed trades
- Integrates with execution system for trade processing

### 6. Portfolio Management (`portfolio.py`)
- `Portfolio` class for managing trading accounts:
  - Tracks cash balance, positions, trades, and equity curves
  - Handles trade execution with realistic costs (fees and slippage)
  - Supports mark-to-market portfolio valuation
- State Variables:
  - `cash`: Current available cash balance (float)
  - `positions`: Dictionary of current holdings {ticker: shares}
  - `trades`: List of all executed trades with details(Date, Ticker, Side, Price, Shares, Fee)
  - `equity`: List of portfolio snapshots(Date, Equity, Cash, PosValue)
- Key functions:
  - `buy_cash_all()`: Execute buy orders with cash allocation
  - `sell_all()`: Liquidate entire position
  - `mark_to_market()`: Update portfolio value using closing prices
  - `save_portfolio_csv()`: Persist portfolio state to CSV files
  - `load_portfolio_csv()`: Restore portfolio state from saved files
- Maintains detailed trade history and equity curves
- Implements realistic trading costs with configurable fee and slippage rates


## Environment Setup

Required environment variables:
- `GMAIL_ADDRESS`: Gmail address for sending/receiving trade signals
- `GMAIL_APP_PASSWORD`: Gmail app-specific password
- `USER_EMAIL`: Recipient email address for trade signals

## Dependencies

- pandas: Data manipulation and analysis
- yfinance: Yahoo Finance data fetching
- numpy: Numerical computations
- email/smtplib: Email handling
- imaplib: Email reply monitoring
- python-dotenv: Environment variable management

## Directory Structure

```
src/finbot/
├── data.py         # Data fetching and caching
├── exec.py         # Trade execution logic
├── messaging_gmail.py  # Email communication
├── portfolio.py    # Portfolio management and tracking
├── reply_listener.py  # Email reply processing
└── signals.py     # Trading signal generation
```

## Usage

1. The system fetches S&P 500 stock data daily
2. Generates trading signals based on implemented algorithms
3. Sends email notifications with buy recommendations
4. Processes user replies to execute confirmed trades
5. Updates portfolio and maintains trade history

## Configuration

- Default cache directory: `data/data_cache`
- Portfolio storage directory: `portfolio_store/`
- SMTP Server: smtp.gmail.com (Port 465)
- IMAP Server: imap.gmail.com (Port 993)
- Trading parameters:
  - Default starting cash: $1,000
  - Fee basis points: 5 (0.05%)
  - Slippage basis points: 1 (0.01%)
- Portfolio tracking files:
  - `cash.csv`: Current cash balance
  - `positions.csv`: Active positions
  - `trades.csv`: Historical trades
  - `equity.csv`: Portfolio value history


  #TODO
  Add dynamic target and stop loss
  

## `backtest.py` Execution Flow (Function Calls)

```mermaid
flowchart TD
    A[__main__] --> B[get_sp500_tickers()]
    B --> C[random.sample(500)]
    C --> D[get_data_cached()]
    D --> E[algorithm() → signals_dict]
    E --> F[backtest(signals_dict)]
    F --> G[Portfolio.__init__()]
    G --> H[Loop: execute_user_for_date()]
    H --> I[port.mark_to_market()]
    I --> J[Compute metrics]
    J --> K[print(summary)]
    K --> L[Save CSVs]



#Assumptions 
1. exec.py
#Buy only if you don't already have that stock
#Sell only if you already have that stock ie no shorting 
#Execute sells first (free up cash)

#For each stock budget is total cash/num of stocks 