# FinBot

FinBot is a Python-based financial trading bot that automates stock trading signals generation and execution for S&P 500 stocks. It includes functionality for data fetching, signal generation, email notifications, and trade execution.

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