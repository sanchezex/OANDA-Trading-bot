# Grid Trading Strategy Guide

## 📚 What is Grid Trading?

Grid trading is an algorithmic trading strategy that:
- Divides price range into equal intervals (grids)
- Places buy orders at lower levels
- Places sell orders at higher levels
- Profits from price oscillations within the range
- Works best in ranging/sideways markets

### Simple Example

**Setup:**
- Current price: $1.0800
- Grid range: $1.0700 - $1.0900 (200 pips)
- 20 grids = 10 pips per grid
- 1,000 units per order

**Grid Levels:**
```
1.0900 ← SELL (highest level)
1.0890 ← SELL
1.0880 ← SELL
1.0870 ← SELL
1.0860 ← SELL
1.0850 ← SELL
1.0840 ← SELL
1.0830 ← SELL
1.0820 ← SELL
1.0810 ← SELL
-----------
1.0800 ← Current Price
-----------
1.0790 ← BUY
1.0780 ← BUY
1.0770 ← BUY
1.0760 ← BUY
1.0750 ← BUY
1.0740 ← BUY
1.0730 ← BUY
1.0720 ← BUY
1.0710 ← BUY
1.0700 ← BUY (lowest level)
```

**How It Profits:**

1. **Price drops to 1.0790:**
   - BUY order at 1.0790 fills
   - Position: LONG 1,000 units
   - Waiting to sell

2. **Price rises to 1.0810:**
   - SELL order at 1.0810 fills
   - Position: CLOSED
   - Profit: (1.0810 - 1.0790) × 1,000 = $20 (gross)
   - Less spread (~$1): = ~$19 profit

3. **Process repeats:**
   - Next BUY at 1.0790
   - Next SELL at 1.0810
   - Profit per cycle: ~$19

---

## 🎯 Best Conditions for Grid Trading

### ✅ GOOD for Grid Trading
- **Ranging markets** (prices oscillate between levels)
- **High volatility days** (more price movement = more cycles)
- **Normal trading hours** (tighter spreads)
- **Stable economic periods** (no major news)
- **Major pairs** (EUR/USD, GBP/USD, USD/JPY)

### ❌ BAD for Grid Trading
- **Strong trending markets** (price keeps moving one direction)
- **Low volatility** (price stays flat, no fills)
- **Around major news** (big gaps, slippage)
- **Weekend gaps** (risk of overnight moves)
- **Exotic pairs** (wide spreads kill profits)

---

## 💰 Configuration Parameters Explained

### 1. Grid Range

**Definition:** Upper and lower price bounds for grid

**Example:**
```json
"grid_range": {
  "lower_level": 1.0700,
  "upper_level": 1.0900
}
```

**How to choose:**

1. **Look at 1-month chart of EUR/USD**
2. **Identify recent support level** → lower_level
3. **Identify recent resistance level** → upper_level
4. **Range should contain ~80% of recent price action**

**Rule of thumb:**
- Look at last 30 days of price history
- Use low = 90th percentile
- Use high = 10th percentile

**Example for EUR/USD:**
- 30-day low: 1.0650
- 30-day high: 1.1000
- Safe range: 1.0700 - 1.0900 (middle 70% of range)

### 2. Number of Grids

**Definition:** How many buy/sell orders to place

**Trade-offs:**

| Grids | Pros | Cons |
|-------|------|------|
| 5-10 | Lower capital needed, simpler | Fewer fills, big gaps between levels |
| 20-30 | Good balance, more cycles | Moderate capital needed |
| 50+ | Many fills, smooth | High capital needed, margin risk |

**Formula:**
```
Grids = Range (in pips) / Desired spacing
```

**Example:**
- Range: 200 pips (1.0700 - 1.0900)
- Desired spacing: 10 pips
- Grids: 200 / 10 = 20 grids

### 3. Grid Spacing

**Definition:** Distance between each price level in pips

**Recommended spacing by pair:**

| Pair | Spread | Spacing | Units |
|------|--------|---------|-------|
| EUR/USD | 0.8 pips | 10 pips | 1,000 |
| GBP/USD | 1.5 pips | 20 pips | 500 |
| USD/JPY | 1.2 pips | 15 pips | 1,000 |

**Calculation:**
```
Profit per cycle = Grid spacing (pips) - Spread (pips)
Example: 10 pips - 0.8 pips = 9.2 pips profit potential
```

### 4. Units Per Trade

**Definition:** Lot size for each order

**Standard sizes:**
- 1 Micro Lot = 1,000 units
- 1 Mini Lot = 10,000 units
- 1 Standard Lot = 100,000 units

**EUR/USD pricing:**
- 1 pip = $0.10 per micro lot
- 1 pip = $1.00 per mini lot
- 1 pip = $10.00 per standard lot

**Example:**
- 1,000 units (micro lot)
- 10 pips profit × $0.10 = $1 per cycle
- Less spread: ~$0.80 net profit

**How to choose:**
1. **Calculate position value:**
   ```
   Position USD = (Units × Current Price) / 100,000
   ```
   
2. **Example:**
   ```
   Units: 1,000
   Price: 1.0800
   Position USD = (1,000 × 1.0800) / 100,000 = $10.80
   ```

3. **Rule: Position < 2% of account balance**
   ```
   Max Position = Account Balance × 0.02
   If balance = $300, max position = $6 → Use 500 units
   ```

### 5. Position Size Per Grid

**Definition:** Capital assigned per grid level

**Calculation:**
```
Capital per grid = Units × Current Price / 100,000
```

**Example:**
- Units: 1,000
- Price: 1.0800
- Capital: (1,000 × 1.0800) / 100,000 = $10.80

**Total capital needed:**
```
Total = Capital per grid × (Number of grids / 2)
(Divide by 2 because only ~half the grids are active simultaneously)
```

---

## 📊 Profit Calculations

### Daily Profit Formula

```
Daily Profit = Net Profit per Cycle × Expected Cycles per Day
```

**Assumptions:**
- EUR/USD moves 50-100 pips daily
- Grid spacing: 10 pips
- Cycles possible: 5-10 per day

**Realistic estimate:**
- EUR/USD: 3-5 cycles/day
- GBP/USD: 5-8 cycles/day
- USD/JPY: 2-4 cycles/day

### Monthly Projection

```
Monthly = Daily Profit × Trading Days
(≈20 trading days per month)
```

**Example:**
- Daily: $0.80
- Monthly: $0.80 × 20 = $16
- On $200 account: 8% monthly ROI

### Break-Even Analysis

```
Cycles needed to break even = Fixed Costs / Net profit per cycle
```

**Costs:**
- Spread per trade: ~0.8 pips × 1,000 units = $0.08
- Entry + Exit: $0.16 per cycle

**Example:**
- Net profit per cycle: $0.80
- Need ~1-2 cycles to cover spread

---

## 🛡️ Risk Management

### Maximum Loss Control

**Setting:**
```json
"safety": {
  "max_loss_usd": 50
}
```

**How it works:**
- Monitor unrealized P&L
- If loss exceeds $50, bot stops trading
- Existing orders cancel
- Prevents account blowup

**Calculation:**
```
Max Loss should be ≤ 5% of account
Example: $300 account → max loss $15
```

### Maximum Positions

**Setting:**
```json
"safety": {
  "max_open_positions": 20
}
```

**Why limit positions:**
- Prevents over-leverage
- Reduces margin requirements
- Better capital efficiency
- Easier to manage

### Position Size Limits

**Rule of Thumb:**
```
Max position size = Account Balance × 0.02 (2%)
Example: $300 account → max $6 per position (500 units)
```

**Leverage Check:**
```
Used Leverage = Total Positions Value / Account Balance
Should be ≤ 50% for safety
```

---

## 🔄 Grid Trading Optimization

### Initial Setup (Week 1)

**Conservative:**
- Range: 200 pips
- Grids: 10
- Spacing: 20 pips
- Units: 500
- Capital: ~$50

**Test:**
- Does price oscillate naturally?
- Are orders filling regularly?
- Is profit capturing as expected?

### Optimization (Week 2-3)

If profitable after Week 1:

**Tighten the range:**
- Reduce from 200 pips to 150 pips
- Keeps orders closer to current price
- More frequent fills

**Add more grids:**
- From 10 → 15-20 grids
- Smaller spacing = more fills
- Smooth out entry points

**Increase position size:**
- From 500 → 1,000 units
- Double positions = double profits
- Keep used leverage < 50%

### Advanced Optimization

**Dynamic grid adjustment:**
- Monitor price movement daily
- If trending up: shift grids higher
- If trending down: shift grids lower
- Keeps orders active

**Market condition detection:**
- In ranging market: tight grids
- In volatile market: wide grids
- Around news: reduce positions
- After news: expand grids

---

## 📈 Currency Pair Selection

### EUR/USD (RECOMMENDED)

**Pros:**
- Most liquid pair
- 0.5-1.0 pip spread
- Ranges well
- Easy to predict
- Good for beginners

**Cons:**
- Smaller daily moves (50-100 pips)
- Lower profit per cycle

**Setup:**
- Range: 200 pips
- Grids: 20
- Spacing: 10 pips

### GBP/USD

**Pros:**
- Highly volatile
- 100-150 pips daily moves
- More cycles = more profit

**Cons:**
- Wider spreads (1.5-2 pips)
- More unpredictable
- Higher risk

**Setup:**
- Range: 300 pips
- Grids: 15
- Spacing: 20 pips

### USD/JPY

**Pros:**
- Lower volatility
- More predictable ranges
- Tight spreads (1-1.5 pips)
- Good for risk-averse

**Cons:**
- Smaller moves (30-50 pips daily)
- Fewer cycles

**Setup:**
- Range: 150 pips
- Grids: 15
- Spacing: 10 pips

### Pairs to Avoid

❌ Exotic pairs (USD/MXN, USD/TRY, etc.)
- Spreads: 5-20 pips (kills profits)
- Low liquidity (hard to fill)

❌ Crypto currency pairs
- Too volatile (~20% swings daily)
- Wide spreads (50+ pips)
- Perfect for liquidation

❌ GBP/JPY, EUR/JPY
- Highly correlated
- Very volatile
- Wide spreads

---

## 📊 Monitoring Your Grid

### Daily Checks

```
Morning (before market open):
1. Check account balance
2. View open positions and P&L
3. Monitor spread levels
4. Check for emergency stops

Midday:
1. Count number of cycles
2. Monitor unrealized P&L
3. Check margin utilization

End of Day:
1. Record daily P&L
2. Review grid fill efficiency
3. Note any issues/improvements
```

### Key Metrics to Track

1. **Fill Rate:**
   ```
   Fills / Pending Orders × 100
   Ideal: 50-70% of orders fill (means grid working)
   ```

2. **Average Profit per Cycle:**
   ```
   Total Daily Profit / Number of cycles
   EUR/USD target: $0.80-1.20
   ```

3. **Capital Efficiency:**
   ```
   Daily Profit / Capital Used × 100
   Good: 1-5% daily return
   ```

4. **Win Rate:**
   ```
   Profitable Cycles / Total Cycles × 100
   Grid trading typically: 85-95% win rate
   ```

---

## ⚠️ Common Mistakes

### ❌ Mistake 1: Too Wide Grids

**Problem:**
- Spacing: 50+ pips
- Few orders fill
- Misses cycles
- Low profitability

**Solution:**
- Tighten to 10-20 pips
- Accept more trades
- Increase capital efficiency

### ❌ Mistake 2: Too High Leverage

**Problem:**
- Position sizes too large
- 1-2 bad cycles wipes account
- Can't recover

**Solution:**
- Position < 2% of account
- Used leverage < 50%
- Build capital first

### ❌ Mistake 3: Trending Market

**Problem:**
- Price keeps going up/down
- Half the grid never fills
- Unbalanced positions
- Growing losses

**Solution:**
- Pause trading when trending
- Use market detection
- Wait for ranging periods

### ❌ Mistake 4: Ignoring Spreads

**Problem:**
- Profit per cycle: 5 pips
- Spread: 1.5 pips
- Real profit: 3.5 pips (30% loss to spread!)

**Solution:**
- Only trade major pairs (tight spreads)
- Factor spread into calculations
- Aim for 10+ pips profit minimum

### ❌ Mistake 5: No Risk Management

**Problem:**
- No position limits
- No loss limits
- Account can blow up quickly

**Solution:**
- Set max_loss to 5% of account
- Limit positions
- Monitor capital regularly

---

## 🎯 Recommended Starting Configuration (EUR/USD)

```json
{
  "account": {
    "account_id": "123-456-789-012",
    "access_token": "your_token",
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
    "max_loss_usd": 30,
    "max_open_positions": 15,
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

**Expected Results:**
- Capital required: ~$100
- Daily cycles: 3-5
- Daily profit: $2-5
- Monthly profit: $40-100
- Monthly ROI: 40-100%

---

## 📞 Do Your Own Research

This guide is educational. Before trading:

1. **Research grid trading** (YouTube, articles, forums)
2. **Paper trade for 2-4 weeks** (OANDA practice)
3. **Track your results meticulously**
4. **Only go live if consistently profitable**
5. **Start small** (deposit minimum)

---

**Last Updated:** February 2026

**Disclaimer:** Grid trading involves risk. Past results do not guarantee future results. Trade only what you can afford to lose.
