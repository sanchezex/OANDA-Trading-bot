# Vercel Deployment Guide

This guide explains how to deploy the OANDA Trading Bot to Vercel.

## Prerequisites

1. **Vercel Account** - Sign up at https://vercel.com
2. **GitHub/GitLab/Bitbucket Repository** - Push your code to a git repository
3. **OANDA API Credentials** - Get your practice or live API credentials

## Deployment Steps

### Step 1: Prepare Your Repository

Ensure your repository contains:
- `api/trading.py` - Flask API endpoints
- `vercel.json` - Vercel configuration
- `requirements.txt` - Python dependencies

### Step 2: Connect to Vercel

1. Go to https://vercel.com and sign in
2. Click "Add New..." → "Project"
3. Import your git repository
4. Configure the project:
   - Framework Preset: Other
   - Build Command: (leave empty)
   - Output Directory: (leave empty)

### Step 3: Configure Environment Variables

In the Vercel project settings, add the following environment variables:

| Variable | Description | Example |
|----------|-------------|---------|
| `OANDA_ACCOUNT_ID` | Your OANDA account ID | 123-456-7890 |
| `OANDA_ACCESS_TOKEN` | Your OANDA API token | abc123... |
| `OANDA_ENVIRONMENT` | practice or live | practice |
| `API_KEY` | Your custom API key for securing endpoints | your_secure_key |
| `TRADING_PAIR` | Currency pair to trade | EUR_USD |
| `GRID_LOWER_BOUND` | Lower price bound | 1.0700 |
| `GRID_UPPER_BOUND` | Upper price bound | 1.0900 |
| `NUMBER_OF_GRIDS` | Number of grid levels | 20 |
| `POSITION_SIZE` | Units per trade | 1000 |

### Step 4: Deploy

Click "Deploy" and wait for the build to complete.

### Step 5: Test the API

Your API will be available at `https://your-project.vercel.app/api/`

Test endpoints:
- `GET /api/health` - Health check
- `GET /api/status` - Bot status (requires API key)
- `GET /api/account` - Account info
- `GET /api/positions` - Open positions
- `GET /api/orders` - Pending orders

Include your API key in the request header:
```
X-API-Key: your_secure_api_key
```

## API Endpoints

### Public Endpoints
- `GET /api/health` - Health check (no auth required)
- `POST /api/calculator/profit` - Calculate profit
- `POST /api/calculator/capital` - Calculate required capital

### Protected Endpoints (require X-API-Key header)
- `GET /api/status` - Get bot status
- `GET /api/account` - Get account info
- `GET /api/positions` - Get open positions
- `GET /api/orders` - Get pending orders
- `POST /api/orders` - Place an order
- `DELETE /api/orders/{id}` - Cancel an order
- `POST /api/orders/cancel-all` - Cancel all orders
- `POST /api/grid/init` - Initialize grid
- `GET /api/grid/levels` - Get grid levels
- `GET /api/safety/check` - Run safety checks
- `GET /api/price/{instrument}` - Get current price

## Important Notes

### Security
- Always change the `API_KEY` from the default
- Use HTTPS in production
- Consider adding rate limiting

### Limitations
- Vercel functions have a 10-second timeout for free tier
- The trading bot is designed to run continuously - Vercel is better suited for API endpoints rather than continuous trading
- For continuous trading, consider using a VPS or dedicated server

### Testing
1. Use practice/demo OANDA account first
2. Test with small position sizes
3. Monitor your account closely

## Local Development

To test locally:

```bash
# Install dependencies
pip install -r requirements.txt

# Run the Flask app
python api/trading.py

# Or use flask command
FLASK_APP=api/trading.py flask run
```

## Troubleshooting

### Import Errors
If you see import errors, make sure all dependencies are in requirements.txt

### Timeout Errors
For long-running operations, consider breaking them into smaller requests

### Environment Variables
Make sure all required environment variables are set in Vercel project settings

