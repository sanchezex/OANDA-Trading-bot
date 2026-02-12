# OANDA Grid Trading Bot - Complete Setup Guide

## 📖 Table of Contents
1. [OANDA Account Setup](#1-oanda-account-setup)
2. [Getting API Credentials](#2-getting-api-credentials)
3. [Python Installation](#3-python-installation)
4. [Bot Configuration](#4-bot-configuration)
5. [Testing Connection](#5-testing-connection)
6. [Running the Bot](#6-running-the-bot)
7. [Troubleshooting](#7-troubleshooting)

---

## 1. OANDA Account Setup

### 1.1 Create Practice Account (Recommended)

**Step 1:** Go to [https://www.oanda.com](https://www.oanda.com)

**Step 2:** Click "Open Account" in the top right

**Step 3:** Select "Practice Account"

**Step 4:** Choose your account type:
- Practice Micro (Ideal for learning)
- Practice Standard
- Practice MAXi

**Recommendation:** Start with Practice Micro

**Step 5:** Fill in registration details:
- Email address
- Password
- Name
- Country
- Mobile phone (optional)

**Step 6:** Verify your email address

**Step 7:** Login to your new practice account

**Result:** You now have $100,000 virtual money for testing!

### 1.2 Practice vs Live Account

| Feature | Practice | Live |
|---------|----------|------|
| Initial Capital | $100,000 (virtual) | $0-???  |
| Minimum Deposit | None | $0-100 |
| Real Trading | No | Yes |
| All Features | Yes | Yes |
| Risk | None | Real |
| Learning | Perfect | Not recommended |

**⭐ Recommendation:** Start with practice account for at least 1-2 weeks

---

## 2. Getting API Credentials

### 2.1 Generate API Token

**Step 1:** Login to OANDA account

**Step 2:** Click on account name (top right) → "Settings"

**Step 3:** Look for "Manage API Access" or go to:
```
https://www.oanda.com/account/api
```

**Step 4:** Click "Generate Personal Access Token"

**Step 5:** IMPORTANT - You'll see your token ONE TIME ONLY
- Copy it immediately
- Paste it somewhere safe
- Keep it SECRET (don't share!)

**Example token:**
```
a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6-a1b2c3d4e5f6g7h8i9j0k1l2m3n4
```

### 2.2 Find Your Account ID

Your Account ID is visible in multiple places:

1. **In the API Token screen** - "Your Account ID is:"
2. **In Account Settings** - Usually formatted like: `123-456-789-012`
3. **In the top of the platform** - Shown in browser after login

**Example Account ID:**
```
123-456-789-012
```

### 2.3 Save Your Credentials

Create a safe note with:
```
Token: [YOUR_TOKEN_HERE]
Account ID: [YOUR_ACCOUNT_ID_HERE]
Environment: practice
```

---

## 3. Python Installation

### 3.1 Check Python Is Installed

Open Terminal/Command Prompt and run:
```bash
python3 --version
```

You should see: `Python 3.7+` (3.8, 3.9, 3.10, 3.11 all work)

**If not installed:**
- **Mac:** `brew install python3`
- **Ubuntu/Debian:** `sudo apt-get install python3`
- **Windows:** Download from [python.org](https://www.python.org)

### 3.2 Install Dependencies

Navigate to the bot directory:
```bash
cd /path/to/OANDA-Trading-bot
```

Install required packages:
```bash
pip3 install -r requirements.txt
```

This installs:
- `requests` - For API calls

Verify installation:
```bash
python3 -c "import requests; print('✓ requests installed')"
```

---

## 4. Bot Configuration

### 4.1 Update config.json

Open `config.json` in a text editor

Find these lines:
```json
"account_id": "YOUR_ACCOUNT_ID_HERE",
"access_token": "YOUR_API_TOKEN_HERE",
```

Replace with YOUR actual credentials:
```json
"account_id": "123-456-789-012",
"access_token": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6-a1b2c3d4e5f6g7h8i9j0k1l2m3n4",
```

### 4.2 Verify Other Settings

```json
"environment": "practice",  // Keep as "practice" for testing
```

### 4.3 Sample Configuration (EUR/USD - Recommended)

```json
{
  "account": {
    "account_id": "123-456-789-012",
    "access_token": "your_token_here",
    "environment": "practice"
  },
  "trading": {
    "instrument": "EUR_USD",
    "grid_range": {
      "lower_level": 1.0700,
      "upper_level": 1.0900
    },
    "grid_settings": {
      "number_of_grids": 20,
      "grid_spacing_pips": 10
    },
    "position_sizing": {
      "position_size_per_grid": 10,
      "units_per_trade": 1000
    }
  },
  "safety": {
    "max_loss_usd": 50,
    "max_open_positions": 20,
    "stop_loss_distance_pips": 50,
    "take_profit_distance_pips": 15
  },
  "monitoring": {
    "check_interval_seconds": 60,
    "log_level": "INFO",
    "alert_email": ""
  }
}
```

---

## 5. Testing Connection

### 5.1 Quick Test

Run the quick connection test:
```bash
python3 test_connection.py
```

Expected output:
```
🔗 Testing OANDA API Connection (practice)...
   Account ID: 123-456-789-012
   Token: your_token...

✅ CONNECTION SUCCESSFUL!

Account Type: 🎓 Practice
Balance: $100,000.00
Equity: $100,000.00
Floating P&L: $0.00
Open Positions: 0

Fetching EUR/USD price...
✅ EUR/USD: 1.08500
   Spread: 0.8 pips

✨ Bot is ready to run!
```

### 5.2 Comprehensive Setup Test

For a full system check:
```bash
python3 setup_test.py
```

This tests:
1. ✓ Config file
2. ✓ Credentials
3. ✓ API connection
4. ✓ Market data
5. ✓ Grid configuration
6. ✓ Safety settings
7. ✓ Module imports

### 5.3 Troubleshooting Connection Errors

**Error: "Cannot find config.json"**
- Make sure you're in the OANDA-Trading-bot directory
- Check file exists: `ls config.json`

**Error: "API Token not configured"**
- Open config.json
- Replace `YOUR_API_TOKEN_HERE` with your actual token
- Save file

**Error: "Connection failed: 401"**
- Token is invalid or expired
- Generate new token in OANDA website

**Error: "Connection failed: 404"**
- Account ID is wrong
- Copy correct Account ID from OANDA

---

## 6. Running the Bot

### 6.1 Preview Grid Configuration

Before running, see what your bot will do:

```bash
python3 -c "
from grid_calculator import GridCalculator
from market_data import MarketData
from oanda_connector import create_connector_from_config

# Get current price
connector = create_connector_from_config('config.json')
market = MarketData(connector)
price = market.get_current_price('EUR_USD')

# Show grid setup
calc = GridCalculator('config.json')
calc.print_grid_report(price['mid'], price['spread_pips'])
"
```

### 6.2 Start the Bot

```bash
python3 grid_bot_main.py
```

### 6.3 What the Bot Does

**At startup:**
1. ✓ Tests OANDA connection
2. ✓ Checks account health
3. ✓ Fetches current price
4. ✓ Displays grid configuration
5. ✓ Asks for confirmation

**After start:**
1. 📊 Initializes grid orders
2. 🔄 Monitors price every 60 seconds
3. 📈 Tracks open positions
4. 🛡️ Enforces safety checks
5. 📝 Logs all activity

### 6.4 Monitor the Bot

While running, watch the logs:
```bash
tail -f grid_bot.log
```

### 6.5 Stop the Bot

Press `Ctrl+C` in the terminal

The bot will:
- Stop accepting new orders
- Keep existing orders open
- Print final statistics
- Clean shutdown

---

## 7. Troubleshooting

### 7.1 Bot Startup Issues

**Error: "All startup checks passed" but bot won't start**

Check:
1. Press Enter when asked for confirmation
2. Confirm you typed: `yes`
3. Have sufficient account balance

**Error: "Failed to fetch account summary"**

Try:
1. Verify API token
2. Test: `python3 test_connection.py`
3. Check internet connection

### 7.2 Order Placement Issues

**Orders not being placed:**

1. Check account has balance:
   ```bash
   python3 -c "from oanda_connector import create_connector_from_config; print(create_connector_from_config('config.json').get_account_balance())"
   ```

2. Check grid range is valid:
   - Lower level < Upper level
   - Current price between them

3. Check orders in OANDA website:
   - Login to OANDA
   - Go to "Orders" tab
   - Should see pending orders

**Orders cancelled automatically:**

Reasons:
- Price moved outside grid range
- Account had insufficient margin
- Safety limits triggered

### 7.3 Connection Issues

**Slow connection / Timeouts:**

1. Check internet speed: `ping 8.8.8.8`
2. Try increasing timeout in code
3. Check if OANDA servers are down

**Token expired:**

- Generate new token in OANDA
- Update config.json
- Restart bot

### 7.4 Getting Help

**Check the logs:**
```bash
tail -50 grid_bot.log
```

**Test each component:**
```bash
# Test connection
python3 test_connection.py

# Test market data
python3 -c "from market_data import MarketData; from oanda_connector import create_connector_from_config; m = MarketData(create_connector_from_config('config.json')); print(m.get_current_price('EUR_USD'))"

# Test grid calculator
python3 -c "from grid_calculator import GridCalculator; c = GridCalculator('config.json'); print(c.calculate_grid_levels(1.0800))"
```

---

## 🎯 First Trading Configuration

### Conservative Setup (Low Risk)

Start with small position sizes and wide grid:

```json
{
  "trading": {
    "instrument": "EUR_USD",
    "grid_range": {
      "lower_level": 1.0600,
      "upper_level": 1.1000
    },
    "grid_settings": {
      "number_of_grids": 10,
      "grid_spacing_pips": 40
    },
    "position_sizing": {
      "position_size_per_grid": 5,
      "units_per_trade": 500
    }
  },
  "safety": {
    "max_loss_usd": 25,
    "max_open_positions": 10
  }
}
```

Expected P&L: $10-15/month

### Aggressive Setup (Higher Risk/Reward)

More grids, tighter spacing:

```json
{
  "trading": {
    "grid_range": {
      "lower_level": 1.0700,
      "upper_level": 1.0900
    },
    "grid_settings": {
      "number_of_grids": 20,
      "grid_spacing_pips": 10
    },
    "position_sizing": {
      "units_per_trade": 2000
    }
  },
  "safety": {
    "max_loss_usd": 100,
    "max_open_positions": 20
  }
}
```

Expected P&L: $40-60/month

---

## ✅ Pre-Launch Checklist

Before running the bot, verify:

- [ ] OANDA practice account created
- [ ] API token generated and saved
- [ ] Account ID noted
- [ ] Python 3.7+ installed
- [ ] `pip3 install -r requirements.txt` ran successfully
- [ ] `config.json` has real credentials (not placeholders)
- [ ] `python3 test_connection.py` shows ✅ SUCCESS
- [ ] `python3 setup_test.py` passes all 7 checks
- [ ] Grid configuration reviewed and understood
- [ ] Safety settings are appropriate for your risk tolerance

---

## 📞 Support Resources

### Official OANDA Resources
- OANDA Main: https://www.oanda.com
- API Documentation: https://developer.oanda.com
- Community Forums: https://www.oanda.com/forum

### Useful Commands

```bash
# View recent log entries
tail -20 grid_bot.log

# View all recent errors
grep ERROR grid_bot.log

# Test just the API connection
python3 test_connection.py

# See current account status
python3 -c "from oanda_connector import create_connector_from_config; import json; c = create_connector_from_config('config.json'); print(json.dumps(c.get_account_summary(), indent=2))"

# Check current price
python3 -c "from market_data import MarketData; from oanda_connector import create_connector_from_config; m = MarketData(create_connector_from_config('config.json')); print(m.get_current_price('EUR_USD'))"

# Display grid configuration
python3 -c "from grid_calculator import GridCalculator; c = GridCalculator('config.json'); c.print_grid_report(1.0800)"
```

---

## 🚀 Next Steps

1. ✅ Complete all checklist items above
2. 📊 Run `python3 setup_test.py` - should show all green
3. 🎯 Preview grid: `python3 test_connection.py`
4. 🤖 Start bot: `python3 grid_bot_main.py`
5. 📈 Monitor logs: `tail -f grid_bot.log`
6. 💹 Track results daily

---

**Last Updated:** February 2026

**Questions?** See README.md for more information or check grid_bot.log for error details.
