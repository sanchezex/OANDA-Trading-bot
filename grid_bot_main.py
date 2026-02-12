"""
Grid Trading Bot - Main Module
Orchestrates the grid trading strategy using OANDA API
"""

import json
import logging
import sys
import time
from datetime import datetime, timedelta
from typing import Dict, List

from oanda_connector import OANDAConnector, create_connector_from_config
from market_data import MarketData
from grid_calculator import GridCalculator
from order_placer import OrderPlacer
from safety_checks import SafetyChecker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('grid_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class GridTradingBot:
    """Main grid trading bot class"""
    
    def __init__(self, config_path: str = "config.json"):
        """
        Initialize the grid trading bot
        
        Args:
            config_path (str): Path to configuration file
        """
        try:
            # Load configuration
            with open(config_path, 'r') as f:
                self.config = json.load(f)
            
            # Initialize components
            self.connector = create_connector_from_config(config_path)
            self.market_data = MarketData(self.connector)
            self.grid_calc = GridCalculator(config_path)
            self.order_placer = OrderPlacer(self.connector)
            self.safety = SafetyChecker(config_path, self.connector)
            
            self.instrument = self.config['trading']['instrument']
            self.check_interval = self.config['monitoring']['check_interval_seconds']
            
            self.running = False
            self.trade_count = 0
            self.profit_count = 0
            self.loss_count = 0
            
            logger.info("✓ Grid Trading Bot initialized successfully")
        
        except Exception as e:
            logger.error(f"✗ Failed to initialize bot: {str(e)}")
            raise
    
    def startup_checks(self) -> bool:
        """
        Perform startup verification checks
        
        Returns:
            bool: True if all checks pass
        """
        logger.info("\n" + "="*60)
        logger.info("RUNNING STARTUP CHECKS")
        logger.info("="*60)
        
        # Test OANDA connection
        logger.info("\n[1/5] Testing OANDA API connection...")
        if not self.connector.test_connection():
            logger.error("✗ Failed to connect to OANDA")
            return False
        
        # Check account health
        logger.info("[2/5] Checking account health...")
        healthy, msg = self.safety.check_account_health()
        if not healthy:
            logger.error(f"✗ Account health check failed: {msg}")
            return False
        logger.info("✓ Account is healthy")
        
        # Fetch current price
        logger.info(f"[3/5] Fetching {self.instrument} price...")
        price_data = self.market_data.get_current_price(self.instrument)
        if not price_data:
            logger.error("✗ Failed to fetch price")
            return False
        
        current_price = price_data['mid']
        spread = price_data['spread_pips']
        logger.info(f"✓ Current price: {current_price}, Spread: {spread:.2f} pips")
        
        # Check market conditions
        logger.info("[4/5] Checking market conditions...")
        suitable, msg = self.safety.check_market_conditions(self.market_data, self.instrument)
        if not suitable:
            logger.warning(f"⚠ Market condition warning: {msg}")
        
        # Display grid configuration
        logger.info("[5/5] Verifying grid configuration...")
        self.grid_calc.print_grid_report(current_price, spread)
        
        logger.info("✓ All startup checks passed\n")
        return True
    
    def initialize_grid(self) -> bool:
        """
        Initialize grid orders
        
        Returns:
            bool: True if successful
        """
        try:
            # Get current price
            price_data = self.market_data.get_current_price(self.instrument)
            current_price = price_data['mid']
            
            # Calculate grid levels
            grid_levels = self.grid_calc.calculate_grid_levels(current_price)
            buy_levels = grid_levels['buy_levels']
            sell_levels = grid_levels['sell_levels']
            
            logger.info("\n" + "="*60)
            logger.info("INITIALIZING GRID ORDERS")
            logger.info("="*60)
            
            # Cancel any existing orders first
            logger.info("Cancelling existing orders...")
            self.order_placer.cancel_all_orders()
            
            # Place buy orders
            logger.info(f"\nPlacing {len(buy_levels)} BUY orders...")
            buy_orders = self.order_placer.place_grid_buy_orders(
                self.instrument,
                buy_levels,
                self.config['trading']['position_sizing']['units_per_trade']
            )
            
            # Place sell orders
            logger.info(f"\nPlacing {len(sell_levels)} SELL orders...")
            sell_orders = self.order_placer.place_grid_sell_orders(
                self.instrument,
                sell_levels,
                self.config['trading']['position_sizing']['units_per_trade']
            )
            
            logger.info(f"\n✓ Grid initialization complete")
            logger.info(f"  Total orders placed: {len(buy_orders) + len(sell_orders)}")
            logger.info("="*60 + "\n")
            
            return True
        
        except Exception as e:
            logger.error(f"Error initializing grid: {str(e)}")
            return False
    
    def monitor_grid(self):
        """
        Monitor and manage grid positions and rebalancing
        """
        try:
            # Get current state
            price_data = self.market_data.get_current_price(self.instrument)
            current_price = price_data['mid']
            
            pending_orders = self.order_placer.get_pending_orders()
            open_positions = self.order_placer.get_open_positions()
            
            # Log current state
            logger.debug(f"Price: {current_price} | Pending: {len(pending_orders)} | Positions: {len(open_positions)}")
            
            # Check if grid needs rebalancing
            grid_levels = self.grid_calc.calculate_grid_levels(current_price)
            
            # If price has moved significantly, consider rebalancing
            range_size = self.config['trading']['grid_range']['upper_level'] - self.config['trading']['grid_range']['lower_level']
            center = (self.config['trading']['grid_range']['upper_level'] + self.config['trading']['grid_range']['lower_level']) / 2
            
            # Rebalance if price moves outside 70% of range from center
            if abs(current_price - center) > (range_size * 0.35):
                logger.info(f"Price {current_price} moved to edge of range, consider rebalancing")
        
        except Exception as e:
            logger.error(f"Error during monitoring: {str(e)}")
    
    def run_trading_loop(self, duration_hours: int = None):
        """
        Main trading loop
        
        Args:
            duration_hours (int): How long to run (None = indefinite)
        """
        try:
            self.running = True
            start_time = datetime.now()
            
            logger.info("\n" + "="*60)
            logger.info("🤖 GRID TRADING BOT STARTED")
            logger.info("="*60)
            logger.info(f"Instrument: {self.instrument}")
            logger.info(f"Check interval: {self.check_interval} seconds")
            if duration_hours:
                logger.info(f"Duration: {duration_hours} hours")
            logger.info("="*60 + "\n")
            
            iteration = 0
            
            while self.running:
                iteration += 1
                current_time = datetime.now()
                
                # Check if duration exceeded
                if duration_hours:
                    elapsed = (current_time - start_time).total_seconds() / 3600
                    if elapsed > duration_hours:
                        logger.info(f"Duration limit reached ({duration_hours} hours)")
                        break
                
                # Run safety checks
                should_stop, reason = self.safety.should_emergency_stop()
                if should_stop:
                    logger.critical(f"Emergency stop triggered: {reason}")
                    break
                
                # Monitor grid
                try:
                    self.monitor_grid()
                except Exception as e:
                    logger.error(f"Monitoring error: {str(e)}")
                
                # Log status periodically
                if iteration % 60 == 0:  # Every 60 iterations
                    self.log_bot_status()
                
                # Sleep before next check
                time.sleep(self.check_interval)
        
        except KeyboardInterrupt:
            logger.info("\n✓ Bot stopped by user")
        except Exception as e:
            logger.error(f"Fatal error in trading loop: {str(e)}")
        finally:
            self.log_bot_status()
            self.running = False
            logger.info("🛑 Grid Trading Bot stopped\n")
    
    def log_bot_status(self):
        """Log comprehensive bot status"""
        self.safety.log_safety_status()
        
        pending = self.order_placer.get_pending_orders()
        positions = self.order_placer.get_open_positions()
        
        logger.info(f"Pending Orders: {len(pending)}")
        logger.info(f"Open Positions: {len(positions)}")
        
        if positions:
            for pos in positions:
                logger.info(f"  {pos['instrument']}: {pos['long']['units']} L / {pos['short']['units']} S")
    
    def get_bot_statistics(self) -> Dict:
        """
        Get trading statistics
        
        Returns:
            dict: Bot statistics
        """
        account = self.connector.get_account_summary()
        
        stats = {
            'timestamp': datetime.now().isoformat(),
            'balance': float(account.get('balance', 0)),
            'equity': float(account.get('equity', 0)),
            'unrealized_pl': float(account.get('unrealizedPL', 0)),
            'open_positions': self.order_placer.get_open_positions(),
            'pending_orders': self.order_placer.get_pending_orders()
        }
        
        return stats
    
    def print_statistics(self):
        """Print bot statistics"""
        stats = self.get_bot_statistics()
        
        print("\n" + "="*60)
        print("BOT STATISTICS")
        print("="*60)
        print(f"Timestamp: {stats['timestamp']}")
        print(f"Balance: ${stats['balance']:.2f}")
        print(f"Equity: ${stats['equity']:.2f}")
        print(f"Unrealized P&L: ${stats['unrealized_pl']:.2f}")
        print(f"Open Positions: {len(stats['open_positions'])}")
        print(f"Pending Orders: {len(stats['pending_orders'])}")
        print("="*60 + "\n")


def main():
    """Main entry point"""
    
    # Check if config file exists
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
    except FileNotFoundError:
        logger.error("❌ config.json not found!")
        logger.error("Please create config.json with your OANDA credentials")
        sys.exit(1)
    except json.JSONDecodeError:
        logger.error("❌ config.json is invalid JSON!")
        sys.exit(1)
    
    # Check for API credentials
    if config['account']['access_token'] == "YOUR_API_TOKEN_HERE":
        logger.error("❌ Please update config.json with your OANDA API token!")
        logger.error("See README.md for setup instructions")
        sys.exit(1)
    
    # Initialize bot
    bot = GridTradingBot('config.json')
    
    # Run startup checks
    if not bot.startup_checks():
        logger.error("❌ Startup checks failed!")
        sys.exit(1)
    
    # Ask user for confirmation
    print("\n⚠️  IMPORTANT: Review the configuration above")
    print("This bot will execute real trades with your account settings.")
    print("Start with practice account for testing!")
    response = input("\nProceed with grid initialization? (yes/no): ").lower()
    
    if response != "yes":
        logger.info("Bot startup cancelled by user")
        sys.exit(0)
    
    # Initialize grid
    if not bot.initialize_grid():
        logger.error("❌ Failed to initialize grid!")
        sys.exit(1)
    
    # Run trading loop
    # For testing: run for 1 hour, then exit
    bot.run_trading_loop(duration_hours=1)
    
    # Print final statistics
    bot.print_statistics()


if __name__ == "__main__":
    main()
