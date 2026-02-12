#!/usr/bin/env python3
"""
Quick OANDA Connection Test
Tests if your API credentials work with OANDA
"""

import json
import sys

def main():
    # Load config
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
    except FileNotFoundError:
        print("❌ config.json not found!")
        print("Make sure config.json is in the same directory")
        return 1
    except json.JSONDecodeError:
        print("❌ config.json is invalid JSON!")
        return 1
    
    # Check for credentials
    account_id = config['account'].get('account_id', '')
    token = config['account'].get('access_token', '')
    env = config['account'].get('environment', 'practice')
    
    if account_id == "YOUR_ACCOUNT_ID_HERE" or token == "YOUR_API_TOKEN_HERE":
        print("❌ OANDA credentials not configured!")
        print("\nPlease update config.json with:")
        print("  - account_id: Your OANDA account ID")
        print("  - access_token: Your OANDA API token")
        return 1
    
    # Test connection
    print(f"\n🔗 Testing OANDA API Connection ({env})...")
    print(f"   Account ID: {account_id}")
    print(f"   Token: {token[:10]}...\n")
    
    try:
        from oanda_connector import OANDAConnector
        
        connector = OANDAConnector(token, account_id, env)
        
        if connector.test_connection():
            print("✅ CONNECTION SUCCESSFUL!\n")
            
            # Get account summary
            account = connector.get_account_summary()
            balance = float(account.get('balance', 0))
            
            print(f"Account Type: {'🎓 Practice' if env == 'practice' else '💰 Live'}")
            print(f"Balance: ${balance:,.2f}")
            print(f"Equity: ${float(account.get('equity', 0)):,.2f}")
            print(f"Floating P&L: ${float(account.get('unrealizedPL', 0)):,.2f}")
            print(f"Open Positions: {account.get('openPositionCount', 0)}")
            
            # Get current EUR/USD price
            print(f"\nFetching EUR/USD price...")
            from market_data import MarketData
            market = MarketData(connector)
            price = market.get_current_price('EUR_USD')
            
            if price:
                print(f"✅ EUR/USD: {price['mid']}")
                print(f"   Spread: {price['spread_pips']:.2f} pips")
            
            print(f"\n✨ Bot is ready to run!")
            print(f"   Run: python3 grid_bot_main.py")
            return 0
        else:
            print("❌ CONNECTION FAILED!")
            print("Check your credentials and try again")
            return 1
    
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
