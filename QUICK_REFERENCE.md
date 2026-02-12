# Quick Reference & Cheat Sheet

## 🚀 Quick Commands

### Initial Setup (First Time)

```bash
# 1. Install dependencies
pip3 install -r requirements.txt

# 2. Edit config with your credentials
nano config.json

# 3. Test connection
python3 test_connection.py

# 4. Run full setup check
python3 setup_test.py
```

### Running the Bot

```bash
# Start the bot
python3 grid_bot_main.py

# Monitor in another terminal
tail -f grid_bot.log

# Stop (press Ctrl+C in bot terminal)
```

### Debugging

```bash
# Quick connection test
python3 test_connection.py

# View last 20 log lines
tail -20 grid_bot.log

# View all errors in log
grep ERROR grid_bot.log

# View current account status
python3 -c "from oanda_connector import create_connector_from_config; c = create_connector_from_config('config.json'); print(c.get_account_summary())"

# View current EUR/USD price
python3 -c "from market_data import MarketData; from oanda_connector import create_connector_from_config; m = MarketData(create_connector_from_config('config.json')); print(m.get_current_price('EUR_USD'))"

# View current grid configuration
python3 -c "from grid_calculator import GridCalculator; c = GridCalculator('config.json'); c.print_grid_report(1.0800)"

# View pending orders
python3 -c "from order_placer import OrderPlacer; from oanda_connector import create_connector_from_config; o = OrderPlacer(create_connector_from_config('config.json')); print(o.get_pending_orders())"

# View open positions
python3 -c "from order_placer import OrderPlacer; from oanda_connector import create_connector_from_config; o = OrderPlacer(create_connector_from_config('config.json')); print(o.get_open_positions())"
```

---

## 📋 Configuration Presets

### 🎓 Beginner (Low Risk)

```json
{
  "account": {
    "environment": "practice"
  },
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
      "units_per_trade": 500
    }
  },
  "safety": {
    "max_loss_usd": 20,
    "max_open_positions": 10
  }
}
```

**Expected:** $10-20/month profit

### 🎯 Standard (Recommended)

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
      "units_per_trade": 1000
    }
  },
  "safety": {
    "max_loss_usd": 50,
    "max_open_positions": 20
  }
}
```

**Expected:** $40-100/month profit

### 🚀 Advanced (Higher Risk)

```json
{
  "trading": {
    "grid_range": {
      "lower_level": 1.0750,
      "upper_level": 1.0850
    },
    "grid_settings": {
      "number_of_grids": 20,
      "grid_spacing_pips": 5
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

**Expected:** $100-200/month profit
**Risk:** Higher capital requirement, more sensitive

---

## 🌍 Preset Strategies by Pair

### EUR/USD (BEST FOR BEGINNERS)

```json
{
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
    "units_per_trade": 1000
  }
}
```

### GBP/USD (MORE VOLATILE)

```json
{
  "instrument": "GBP_USD",
  "grid_range": {
    "lower_level": 1.2500,
    "upper_level": 1.2900
  },
  "grid_settings": {
    "number_of_grids": 20,
    "grid_spacing_pips": 20
  },
  "position_sizing": {
    "units_per_trade": 500
  }
}
```

### USD/JPY (LESS VOLATILE)

```json
{
  "instrument": "USD_JPY",
  "grid_range": {
    "lower_level": 108.00,
    "upper_level": 112.00
  },
  "grid_settings": {
    "number_of_grids": 20,
    "grid_spacing_pips": 20
  },
  "position_sizing": {
    "units_per_trade": 1000
  }
}
```

---

## 📊 Key Formulas

### Profit Per Cycle

```
Profit per cycle = (Grid spacing - Spread) × Units × 0.0001
```

**Example (EUR/USD):**
- Grid spacing: 10 pips
- Spread: 0.8 pips
- Units: 1,000
- Profit: (10 - 0.8) × 1,000 × 0.0001 = $0.92

### Daily Profit

```
Daily profit = Profit per cycle × Expected cycles per day
```

**Example:**
- Profit per cycle: $0.92
- Expected cycles: 4/day
- Daily: $3.68

### Monthly Profit

```
Monthly profit = Daily profit × 20 trading days
```

**Example:**
- Daily: $3.68
- Monthly: $3.68 × 20 = $73.60

### Return on Investment (ROI)

```
ROI % = (Monthly Profit / Capital Used) × 100
```

**Example:**
- Monthly profit: $73.60
- Capital: $200
- ROI: (73.60 / 200) × 100 = 36.8%

### Total Capital Needed

```
Capital = (Units × Current Price / 100,000) × (Grids / 2)
```

**Example:**
- Units: 1,000
- Price: 1.0800
- Grids: 20
- Capital: (1,000 × 1.0800 / 100,000) × 10 = $1.08

---

## ⚠️ Safety Checklist

Running bot? Verify:

- [ ] Using PRACTICE account (not live)
- [ ] Credentials in config.json (not default values)
- [ ] `python3 test_connection.py` shows ✅
- [ ] Grid range makes sense for current price
- [ ] max_loss_usd ≤ 5% of account balance
- [ ] max_open_positions ≤ 20
- [ ] Units per trade ≤ 2% of account
- [ ] Reviewed grid strategy guide
- [ ] Monitor log for errors (tail -f grid_bot.log)
- [ ] Have plan to stop bot if needed

---

## 🔍 Troubleshooting Quick Guide

| Problem | Solution |
|---------|----------|
| "config.json not found" | Run from OANDA-Trading-bot directory |
| "API Token not configured" | Edit config.json, replace placeholder |
| "Connection failed" | Run `python3 test_connection.py` |
| "Orders not placing" | Check account balance, grid range valid |
| "No fills" | Spread too wide, or not trading hours |
| "Bot crashing" | Check grid_bot.log for errors |
| "Too many positions" | Reduce units_per_trade or max_open_positions |
| "High losses" | Tighten max_loss_usd, widen grid_spacing |

---

## 📈 Optimization Timeline

### Week 1: Testing
- Start with practice account
- Small position sizes (500 units)
- Wide grid spacing (20-30 pips)
- Monitor 3-5 cycles
- Document results

### Week 2-3: Refinement
- If profitable: tighten grid (10-15 pips)
- Add more levels: 10 → 20 grids
- Keep position sizes small
- Track daily P&L

### Week 4: Scaling
- If consistent profit: increase units (500 → 1000)
- Narrow grid range by 10%
- Increase check frequency
- Ready for live? (optional)

### Live Trading (Optional)
- Only if profitable 4+ weeks on practice
- Min deposit: $200-500
- Start with 50% of your position size
- Scale up after 1 profitable month

---

## 🛠️ File Structure

```
OANDA-Trading-bot/
├── grid_bot_main.py         ← Main bot (run this!)
├── oanda_connector.py       ← API connection
├── market_data.py           ← Price fetching
├── grid_calculator.py       ← Grid calculations
├── order_placer.py          ← Order management
├── safety_checks.py         ← Risk controls
├── config.json              ← YOUR SETTINGS (edit this!)
├── requirements.txt         ← Dependencies
├── test_connection.py       ← Quick test
├── setup_test.py            ← Full system check
├── grid_bot.log             ← Bot activity log
├── README.md                ← Main documentation
├── SETUP_GUIDE.md           ← Step-by-step setup
├── STRATEGY_GUIDE.md        ← Trading strategy
└── QUICK_REFERENCE.md       ← This file!
```

---

## 💻 Python One-Liners

Copy & paste these directly:

```python
# Test API connection
python3 -c "from oanda_connector import create_connector_from_config as c; c('config.json').test_connection()"

# Get account balance
python3 -c "from oanda_connector import create_connector_from_config as c; print(f'${c(\"config.json\").get_account_balance():.2f}')"

# Get current EUR/USD price
python3 -c "from market_data import MarketData; from oanda_connector import create_connector_from_config as c; print(MarketData(c('config.json')).get_current_price('EUR_USD')['mid'])"

# Show grid configuration
python3 -c "from grid_calculator import GridCalculator as GC; GC('config.json').print_grid_report(1.0800)"

# List pending orders
python3 -c "from order_placer import OrderPlacer as OP; from oanda_connector import create_connector_from_config as c; print(OP(c('config.json')).get_pending_orders())"

# Cancel all orders
python3 -c "from order_placer import OrderPlacer as OP; from oanda_connector import create_connector_from_config as c; print(f'Cancelled: {OP(c(\"config.json\")).cancel_all_orders()}')"

# Get open positions
python3 -c "from order_placer import OrderPlacer as OP; from oanda_connector import create_connector_from_config as c; print(OP(c('config.json')).get_open_positions())"

# Run safety checks
python3 -c "from safety_checks import SafetyChecker as SC; from oanda_connector import create_connector_from_config as c; SC('config.json', c('config.json')).log_safety_status()"
```

---

## 📞 When to Ask for Help

Check these resources in order:

1. **Read the error message carefully**
   - Most errors tell you exactly what's wrong

2. **Check `grid_bot.log`**
   - grep for ERROR: `grep ERROR grid_bot.log`

3. **Run `python3 test_connection.py`**
   - Tests API connection separately

4. **Run `python3 setup_test.py`**
   - Full system diagnostic

5. **Reread the documentation**
   - README.md, SETUP_GUIDE.md, STRATEGY_GUIDE.md

6. **Check OANDA website**
   - Verify token still valid
   - Check account is active

---

## ✅ Pre-Launch Verification

```bash
#!/bin/bash
# Run this to verify everything is ready

echo "🔍 Running Pre-Launch Checks..."
echo

# 1. Check Python
echo "1. Python version:"
python3 --version

# 2. Check dependencies
echo -e "\n2. Checking dependencies..."
pip3 list | grep requests

# 3. Check config
echo -e "\n3. Config file:"
test -f config.json && echo "✓ config.json exists" || echo "✗ config.json missing"

# 4. Test connection
echo -e "\n4. OANDA connection:"
python3 test_connection.py

echo -e "\n✨ All checks complete!"
```

---

## 📚 Resources

**OANDA Official:**
- https://www.oanda.com
- https://developer.oanda.com
- https://www.oanda.com/forex-trading/analysis/

**Grid Trading Info:**
- Search "grid trading strategy"
- YouTube: "How to set up grid trading"
- Reddit: r/algotrading, r/Forex

**Programming Help:**
- Python docs: python.org
- Requests library: requests.readthedocs.io
- Stack Overflow: stackoverflow.com

---

**Last Updated:** February 2026

**Pro Tip:** Save these one-liners in a file called `commands.txt` for quick reference!
