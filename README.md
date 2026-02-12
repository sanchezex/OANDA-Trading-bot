# OANDA Grid Trading Bot

A professional, modular grid trading bot for automated forex trading using the OANDA API. Designed for EUR/USD with easy configuration for other pairs.

## Features

- **Automated Grid Trading**: Automated buy/sell orders at predefined price levels
- **Risk Management**: Built-in safety checks, position limits, and loss controls
- **Real-time Monitoring**: Continuous market monitoring and position tracking
- **Easy Configuration**: Environment-based configuration via .env file
- **Paper Trading**: Full compatibility with OANDA practice accounts
- **Detailed Logging**: Comprehensive logging to logs/ directory

## Quick Start

### Step 1: Create OANDA Account

1. Visit [OANDA.com](https://www.oanda.com)
2. Click "Open Account"
3. Choose "Practice Account" (recommended for testing)
4. Register and verify your email
5. You will receive $100,000 virtual money for testing

### Step 2: Get API Credentials

1. Log into your OANDA practice account
2. Go to Account Settings -> Manage API Access
3. Click "Generate Personal Access Token"
4. Save your token (keep it private!)
5. Note your Account ID

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Configure the Bot

1. Copy `.env.example` to `.env`
2. Edit `.env` and add your credentials:

```env
OANDA_ACCOUNT_ID=your_account_id_here
OANDA_ACCESS_TOKEN=your_access_token_here
OANDA_ENVIRONMENT=practice
TRADING_PAIR=EUR_USD
GRID_LOWER_BOUND=1.0700
GRID_UPPER_BOUND=1.0900
NUMBER_OF_GRIDS=20
POSITION_SIZE=1000
```

### Step 5: Test Connection

```bash
python tests/test_connection.py
```

### Step 6: Run the Bot

```bash
python main.py
```

## Project Structure

```
OANDA-Trading-bot/
├── config/
│   ├── __init__.py
│   └── settings.py          # Configuration loader
├── src/
│   ├── __init__.py
│   ├── connectors/
│   │   ├── __init__.py
│   │   └── oanda_client.py  # OANDA API wrapper
│   ├── strategies/
│   │   ├── __init__.py
│   │   └── grid_strategy.py  # Grid trading logic
│   ├── managers/
│   │   ├── __init__.py
│   │   ├── order_manager.py # Order placement/tracking
│   │   └── risk_manager.py  # Safety controls
│   └── utils/
│       ├── __init__.py
│       ├── logger.py        # Logging system
│       └── helpers.py       # Utility functions
├── tests/
│   ├── __init__.py
│   └── test_connection.py   # Connection test
├── logs/
│   └── .gitkeep
├── data/
│   └── .gitkeep
├── main.py                  # Main entry point
├── requirements.txt         # Python dependencies
├── .env.example             # Configuration template
└── .gitignore
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| OANDA_ACCOUNT_ID | Your OANDA account ID | required |
| OANDA_ACCESS_TOKEN | Your OANDA API token | required |
| OANDA_ENVIRONMENT | 'practice' or 'live' | practice |
| TRADING_PAIR | Currency pair | EUR_USD |
| GRID_LOWER_BOUND | Bottom of trading range | 1.0700 |
| GRID_UPPER_BOUND | Top of trading range | 1.0900 |
| NUMBER_OF_GRIDS | Total number of grid levels | 20 |
| POSITION_SIZE | Units per order | 1000 |
| MAX_LOSS_PERCENT | Max loss percentage | 10 |
| STOP_LOSS_PIPS | Stop loss distance | 50 |
| TAKE_PROFIT_PIPS | Take profit distance | 10 |
| CHECK_INTERVAL | Bot check interval (seconds) | 60 |
| LOG_LEVEL | Logging level | INFO |

### Example .env File

```env
# OANDA API Credentials
OANDA_ACCOUNT_ID=123-456-789
OANDA_ACCESS_TOKEN=abcdef123456
OANDA_ENVIRONMENT=practice

# Trading Configuration
TRADING_PAIR=EUR_USD
GRID_LOWER_BOUND=1.0700
GRID_UPPER_BOUND=1.0900
NUMBER_OF_GRIDS=20
POSITION_SIZE=1000

# Risk Management
MAX_LOSS_PERCENT=10
STOP_LOSS_PIPS=50
TAKE_PROFIT_PIPS=10

# Bot Settings
CHECK_INTERVAL=60
LOG_LEVEL=INFO
```

## Safety Features

- **Max Loss Limit**: Stops trading if loss exceeds configured amount
- **Position Limit**: Prevents opening too many positions
- **Account Health Check**: Monitors margin level and balance
- **Market Condition Check**: Warns about unusual spreads
- **Manual Kill Switch**: Can stop the bot programmatically

## Monitoring

### View Logs

```bash
tail -f logs/bot_*.log
```

### Check Bot Status

```python
from main import GridTradingBot

bot = GridTradingBot()
stats = bot.get_bot_statistics()
print(stats)
```

## Troubleshooting

### Connection Failed

- Check your API token is correct
- Verify your Account ID
- Ensure internet connection
- Check that oandapyV20 is installed

### No Orders Being Placed

- Account has sufficient balance
- API token has necessary permissions
- Configured price range is valid
- Bot is not in emergency stop mode

### Orders Not Filling

- Price has not reached grid level yet
- Spread too wide
- Order cancelled by bot (check logs)
- Account margin insufficient

## Important Disclaimers

- Past performance is not indicative of future results
- Grid trading involves risk of losses
- Start with practice account and small position sizes
- Only trade with money you can afford to lose
- This bot is provided as-is without warranties

## License

MIT License

---

**Last Updated:** February 2026

