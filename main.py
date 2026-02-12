#!/usr/bin/env python3
"""
Grid Trading Bot - Main Entry Point.
Orchestrates the grid trading strategy using OANDA API.
"""
import sys
import time
from datetime import datetime
from typing import Dict

from config.settings import Config
from src.connectors.oanda_client import OandaClient
from src.strategies.grid_strategy import GridStrategy
from src.managers.order_manager import OrderManager
from src.managers.risk_manager import RiskManager
from src.utils.logger import logger


class GridTradingBot:
    """Main grid trading bot class."""
    
    def __init__(self):
        """Initialize the grid trading bot."""
        try:
            # Validate configuration
            Config.validate()
            
            # Initialize components
            self.client = OandaClient()
            self.strategy = GridStrategy()
            self.order_manager = OrderManager(self.client)
            self.risk_manager = RiskManager(self.client)
            
            self.instrument = Config.TRADING_PAIR
            self.check_interval = Config.CHECK_INTERVAL
            
            self.running = False
            
            logger.info("Grid Trading Bot initialized successfully.")
        
        except Exception as e:
            logger.error(f"Failed to initialize bot: {str(e)}")
            raise
    
    def startup_checks(self) -> bool:
        """
        Perform startup verification checks.
        
        Returns:
            bool: True if all checks pass
        """
        logger.info("\n" + "="*60)
        logger.info("RUNNING STARTUP CHECKS")
        logger.info("="*60)
        
        # Test OANDA connection
        logger.info("\n[1/4] Testing OANDA API connection...")
        if not self.client.test_connection():
            logger.error("Failed to connect to OANDA")
            return False
        logger.info("Connected to OANDA.")
        
        # Check account health
        logger.info("[2/4] Checking account health...")
        healthy, msg = self.risk_manager.check_account_health()
        if not healthy:
            logger.error(f"Account health check failed: {msg}")
            return False
        logger.info("Account is healthy.")
        
        # Fetch current price
        logger.info(f"[3/4] Fetching {self.instrument} price...")
        price_data = self.client.get_current_price(self.instrument)
        if not price_data:
            logger.error("Failed to fetch price")
            return False
        
        current_price = price_data['mid']
        spread_pips = price_data['spread_pips']
        logger.info(f"Current price: {current_price}, Spread: {spread_pips:.2f} pips.")
        
        # Check market conditions
        logger.info("[4/4] Checking market conditions...")
        suitable, msg = self.risk_manager.check_market_conditions(spread_pips)
        if not suitable:
            logger.warning(f"Market condition warning: {msg}")
        
        # Display grid configuration
        self.strategy.print_grid_report(current_price, spread_pips)
        
        logger.info("All startup checks passed.\n")
        return True
    
    def initialize_grid(self) -> bool:
        """
        Initialize grid orders.
        
        Returns:
            bool: True if successful
        """
        try:
            # Get current price
            price_data = self.client.get_current_price(self.instrument)
            current_price = price_data['mid']
            
            # Calculate grid levels
            grid_levels = self.strategy.calculate_grid_levels(current_price)
            buy_levels = grid_levels['buy_levels']
            sell_levels = grid_levels['sell_levels']
            
            logger.info("\n" + "="*60)
            logger.info("INITIALIZING GRID ORDERS")
            logger.info("="*60)
            
            # Cancel any existing orders first
            logger.info("Cancelling existing orders...")
            self.order_manager.cancel_all_orders()
            
            # Place buy orders
            logger.info(f"\nPlacing {len(buy_levels)} BUY orders...")
            buy_orders = self.order_manager.place_grid_buy_orders(
                self.instrument,
                buy_levels,
                Config.POSITION_SIZE
            )
            
            # Place sell orders
            logger.info(f"\nPlacing {len(sell_levels)} SELL orders...")
            sell_orders = self.order_manager.place_grid_sell_orders(
                self.instrument,
                sell_levels,
                Config.POSITION_SIZE
            )
            
            logger.info(f"\nGrid initialization complete.")
            logger.info(f"Total orders placed: {len(buy_orders) + len(sell_orders)}")
            logger.info("="*60 + "\n")
            
            return True
        
        except Exception as e:
            logger.error(f"Error initializing grid: {str(e)}")
            return False
    
    def monitor_grid(self):
        """Monitor and manage grid positions and rebalancing."""
        try:
            # Get current state
            price_data = self.client.get_current_price(self.instrument)
            current_price = price_data['mid']
            
            pending_orders = self.order_manager.get_pending_orders()
            open_positions = self.order_manager.get_open_positions()
            
            # Log current state
            logger.debug(f"Price: {current_price} | Pending: {len(pending_orders)} | Positions: {len(open_positions)}")
            
            # Check if grid needs rebalancing
            grid_levels = self.strategy.calculate_grid_levels(current_price)
            
            # If price has moved significantly, consider rebalancing
            range_size = Config.GRID_UPPER_BOUND - Config.GRID_LOWER_BOUND
            center = (Config.GRID_UPPER_BOUND + Config.GRID_LOWER_BOUND) / 2
            
            # Rebalance if price moves outside 70% of range from center
            if abs(current_price - center) > (range_size * 0.35):
                logger.info(f"Price {current_price} moved to edge of range, consider rebalancing")
        
        except Exception as e:
            logger.error(f"Error during monitoring: {str(e)}")
    
    def run_trading_loop(self, duration_hours: int = None):
        """
        Main trading loop.
        
        Args:
            duration_hours: How long to run (None = indefinite)
        """
        try:
            self.running = True
            start_time = datetime.now()
            
            logger.info("\n" + "="*60)
            logger.info("GRID TRADING BOT STARTED")
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
                should_stop, reason = self.risk_manager.should_emergency_stop()
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
            logger.info("\nBot stopped by user.")
        except Exception as e:
            logger.error(f"Fatal error in trading loop: {str(e)}")
        finally:
            self.log_bot_status()
            self.running = False
            logger.info("Grid Trading Bot stopped.\n")
    
    def log_bot_status(self):
        """Log comprehensive bot status."""
        self.risk_manager.log_safety_status()
        
        pending = self.order_manager.get_pending_orders()
        positions = self.order_manager.get_open_positions()
        
        logger.info(f"Pending Orders: {len(pending)}")
        logger.info(f"Open Positions: {len(positions)}")
        
        if positions:
            for pos in positions:
                long_units = float(pos.get('long', {}).get('units', 0))
                short_units = float(pos.get('short', {}).get('units', 0))
                logger.info(f"  {pos['instrument']}: {long_units} L / {short_units} S")
    
    def get_bot_statistics(self) -> Dict:
        """
        Get trading statistics.
        
        Returns:
            dict: Bot statistics
        """
        account = self.client.get_account_summary()
        
        stats = {
            'timestamp': datetime.now().isoformat(),
            'balance': float(account.get('balance', 0)),
            'equity': float(account.get('equity', 0)),
            'unrealized_pl': float(account.get('unrealizedPL', 0)),
            'open_positions': self.order_manager.get_open_positions(),
            'pending_orders': self.order_manager.get_pending_orders()
        }
        
        return stats
    
    def print_statistics(self):
        """Print bot statistics."""
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
    """Main entry point."""
    
    # Check for API credentials
    if not Config.OANDA_ACCOUNT_ID or not Config.OANDA_ACCESS_TOKEN:
        logger.error("OANDA credentials not configured!")
        logger.error("Please create .env file with your OANDA credentials")
        logger.error("See .env.example for template")
        sys.exit(1)
    
    # Initialize bot
    bot = GridTradingBot()
    
    # Run startup checks
    if not bot.startup_checks():
        logger.error("Startup checks failed!")
        sys.exit(1)
    
    # Ask user for confirmation
    print("\nIMPORTANT: Review the configuration above.")
    print("This bot will execute real trades with your account settings.")
    print("Start with practice account for testing!")
    response = input("\nProceed with grid initialization? (yes/no): ").lower()
    
    if response != "yes":
        logger.info("Bot startup cancelled by user.")
        sys.exit(0)
    
    # Initialize grid
    if not bot.initialize_grid():
        logger.error("Failed to initialize grid!")
        sys.exit(1)
    
    # Run trading loop
    # For testing: run for 1 hour, then exit
    bot.run_trading_loop(duration_hours=1)
    
    # Print final statistics
    bot.print_statistics()


if __name__ == "__main__":
    main()

