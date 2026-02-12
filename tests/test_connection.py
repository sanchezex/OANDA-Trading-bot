#!/usr/bin/env python3
"""
Test OANDA Connection.
Tests if your API credentials work with OANDA.
"""
import sys


def main():
    """Main test function."""
    print("Testing OANDA Connection...")
    
    # Test 1: Check if environment variables can be loaded
    print("\n[1/3] Loading configuration...")
    try:
        from config.settings import Config
        Config.validate()
        print("Configuration loaded.")
        print(f"  Environment: {Config.OANDA_ENVIRONMENT}")
        print(f"  Trading Pair: {Config.TRADING_PAIR}")
    except ValueError as e:
        print(f"Configuration error: {e}")
        print("Please create .env file with your OANDA credentials")
        return 1
    except Exception as e:
        print(f"Error loading configuration: {e}")
        return 1
    
    # Test 2: Initialize OANDA client
    print("\n[2/3] Initializing OANDA client...")
    try:
        from src.connectors.oanda_client import OandaClient
        client = OandaClient()
        print("OANDA client initialized.")
    except Exception as e:
        print(f"Failed to initialize OANDA client: {e}")
        return 1
    
    # Test 3: Test connection
    print("\n[3/3] Testing API connection...")
    try:
        if client.test_connection():
            print("Connection successful!")
            
            # Get account summary
            account = client.get_account_summary()
            balance = float(account.get('balance', 0))
            
            print(f"\nAccount Details:")
            print(f"  Account ID: {account.get('id', 'N/A')}")
            print(f"  Balance: ${balance:,.2f}")
            print(f"  Equity: ${float(account.get('equity', 0)):,.2f}")
            print(f"  Currency: {account.get('currency', 'USD')}")
            
            # Get current price
            price = client.get_current_price(Config.TRADING_PAIR)
            print(f"\n{Config.TRADING_PAIR} Price:")
            print(f"  Bid: {price['bid']}")
            print(f"  Ask: {price['ask']}")
            print(f"  Spread: {price['spread_pips']:.2f} pips")
            
            print("\nAll tests passed!")
            return 0
        else:
            print("Connection failed!")
            return 1
    except Exception as e:
        print(f"Connection error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

