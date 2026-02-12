#!/usr/bin/env python3
"""
OANDA Grid Bot - Setup & Connection Test Script
Run this first to verify your configuration is correct
"""

import json
import sys
import logging
from datetime import datetime

# Configure minimal logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def print_header(title):
    """Print formatted header"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)


def check_config_file():
    """Check if config.json exists and is valid"""
    print_header("STEP 1: Checking Config File")
    
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
        logger.info("✓ config.json found and valid JSON")
        return config
    except FileNotFoundError:
        logger.error("✗ config.json not found!")
        logger.error("  Please ensure config.json is in the same directory as this script")
        return None
    except json.JSONDecodeError:
        logger.error("✗ config.json contains invalid JSON")
        return None


def check_credentials(config):
    """Check if OANDA credentials are configured"""
    print_header("STEP 2: Checking OANDA Credentials")
    
    if not config:
        return False
    
    try:
        account_id = config['account']['account_id']
        token = config['account']['access_token']
        env = config['account']['environment']
        
        # Check for placeholders
        if account_id == "YOUR_ACCOUNT_ID_HERE":
            logger.error("✗ Account ID not configured!")
            logger.error("  Please update config.json with your actual OANDA Account ID")
            return False
        
        if token == "YOUR_API_TOKEN_HERE":
            logger.error("✗ API Token not configured!")
            logger.error("  Please update config.json with your actual OANDA API token")
            return False
        
        logger.info(f"✓ Account ID configured: {account_id}")
        logger.info(f"✓ API Token configured: {token[:10]}...")
        logger.info(f"✓ Environment: {env} (practice/live)")
        
        return True
    
    except KeyError as e:
        logger.error(f"✗ Missing configuration key: {e}")
        return False


def test_connection(config):
    """Test connection to OANDA API"""
    print_header("STEP 3: Testing OANDA API Connection")
    
    if not config:
        logger.error("✗ No configuration to test")
        return False
    
    try:
        from oanda_connector import OANDAConnector
        
        connector = OANDAConnector(
            access_token=config['account']['access_token'],
            account_id=config['account']['account_id'],
            environment=config['account']['environment']
        )
        
        if connector.test_connection():
            logger.info("✓ OANDA API connection successful!")
            
            # Get account details
            account = connector.get_account_summary()
            balance = float(account.get('balance', 0))
            equity = float(account.get('equity', 0))
            positions = int(account.get('openPositionCount', 0))
            
            logger.info(f"✓ Account Balance: ${balance:,.2f}")
            logger.info(f"✓ Account Equity: ${equity:,.2f}")
            logger.info(f"✓ Open Positions: {positions}")
            
            return True
        else:
            logger.error("✗ Failed to connect to OANDA API")
            logger.error("  Check your API token and Account ID")
            return False
    
    except ImportError:
        logger.error("✗ Cannot import oanda_connector module")
        logger.error("  Ensure all modules are in the same directory")
        return False
    except Exception as e:
        logger.error(f"✗ Connection test failed: {str(e)}")
        return False


def fetch_market_data(config):
    """Fetch and display current market data"""
    print_header("STEP 4: Fetching Market Data")
    
    if not config:
        return False
    
    try:
        from oanda_connector import OANDAConnector
        from market_data import MarketData
        
        connector = OANDAConnector(
            access_token=config['account']['access_token'],
            account_id=config['account']['account_id'],
            environment=config['account']['environment']
        )
        
        market = MarketData(connector)
        instrument = config['trading']['instrument']
        
        logger.info(f"Fetching price for {instrument}...")
        price_data = market.get_current_price(instrument)
        
        if not price_data:
            logger.error("✗ Failed to fetch price data")
            return False
        
        logger.info(f"✓ Current Price: {price_data['mid']}")
        logger.info(f"✓ Bid: {price_data['bid']}")
        logger.info(f"✓ Ask: {price_data['ask']}")
        logger.info(f"✓ Spread: {price_data['spread_pips']:.2f} pips")
        logger.info(f"✓ Timestamp: {price_data['timestamp']}")
        
        return True
    
    except Exception as e:
        logger.error(f"✗ Failed to fetch market data: {str(e)}")
        return False


def check_grid_configuration(config):
    """Check and display grid configuration"""
    print_header("STEP 5: Verifying Grid Configuration")
    
    if not config:
        return False
    
    try:
        from grid_calculator import GridCalculator
        from oanda_connector import OANDAConnector
        from market_data import MarketData
        
        # Get current price first
        connector = OANDAConnector(
            access_token=config['account']['access_token'],
            account_id=config['account']['account_id'],
            environment=config['account']['environment']
        )
        market = MarketData(connector)
        price_data = market.get_current_price(config['trading']['instrument'])
        
        if not price_data:
            logger.error("✗ Cannot fetch current price for grid configuration")
            return False
        
        calc = GridCalculator('config.json')
        
        # Get trading settings
        trading = config['trading']
        logger.info(f"✓ Instrument: {trading['instrument']}")
        logger.info(f"✓ Grid Range: {trading['grid_range']['lower_level']} - {trading['grid_range']['upper_level']}")
        logger.info(f"✓ Number of Grids: {trading['grid_settings']['number_of_grids']}")
        logger.info(f"✓ Grid Spacing: {trading['grid_settings']['grid_spacing_pips']} pips")
        logger.info(f"✓ Units per Trade: {trading['position_sizing']['units_per_trade']}")
        
        # Display full report
        print()
        calc.print_grid_report(price_data['mid'], price_data['spread_pips'])
        
        return True
    
    except Exception as e:
        logger.error(f"✗ Grid configuration error: {str(e)}")
        return False


def check_safety_settings(config):
    """Check safety configuration"""
    print_header("STEP 6: Reviewing Safety Settings")
    
    if not config:
        return False
    
    try:
        safety = config['safety']
        
        logger.info(f"✓ Max Loss: ${safety['max_loss_usd']}")
        logger.info(f"✓ Max Open Positions: {safety['max_open_positions']}")
        logger.info(f"✓ Stop Loss Distance: {safety['stop_loss_distance_pips']} pips")
        logger.info(f"✓ Take Profit Distance: {safety['take_profit_distance_pips']} pips")
        
        monitoring = config['monitoring']
        logger.info(f"✓ Check Interval: {monitoring['check_interval_seconds']} seconds")
        logger.info(f"✓ Log Level: {monitoring['log_level']}")
        
        return True
    
    except Exception as e:
        logger.error(f"✗ Safety settings error: {str(e)}")
        return False


def test_imports():
    """Test if all required modules can be imported"""
    print_header("STEP 7: Testing Module Imports")
    
    modules = [
        ('oanda_connector', 'OANDA Connector'),
        ('market_data', 'Market Data'),
        ('grid_calculator', 'Grid Calculator'),
        ('order_placer', 'Order Placer'),
        ('safety_checks', 'Safety Checks'),
        ('grid_bot_main', 'Main Bot'),
    ]
    
    all_ok = True
    for module_name, display_name in modules:
        try:
            __import__(module_name)
            logger.info(f"✓ {display_name} module OK")
        except ImportError as e:
            logger.error(f"✗ {display_name} module missing: {e}")
            all_ok = False
    
    return all_ok


def print_summary(results):
    """Print test summary"""
    print_header("TEST SUMMARY")
    
    total = len(results)
    passed = sum(1 for r in results if r)
    
    logger.info(f"Tests Passed: {passed}/{total}")
    
    if passed == total:
        print("\n" + "🎉 "*10)
        logger.info("ALL CHECKS PASSED!")
        logger.info("Your bot is ready to run!")
        print("🎉 "*10)
        logger.info("\nNext steps:")
        logger.info("1. Review the configuration carefully")
        logger.info("2. Start with practice account (recommended)")
        logger.info("3. Run: python3 grid_bot_main.py")
        return True
    else:
        logger.error(f"\nFix {total - passed} issue(s) before proceeding")
        return False


def main():
    """Main test flow"""
    print("\n")
    print("╔" + "="*68 + "╗")
    print("║" + " "*15 + "OANDA GRID TRADING BOT - SETUP & TEST" + " "*15 + "║")
    print("╚" + "="*68 + "╝")
    
    results = []
    
    # Run all checks
    config = check_config_file()
    results.append(config is not None)
    
    if config:
        results.append(check_credentials(config))
        results.append(test_connection(config))
        results.append(fetch_market_data(config))
        results.append(check_grid_configuration(config))
        results.append(check_safety_settings(config))
    
    results.append(test_imports())
    
    # Print summary
    success = print_summary(results)
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
