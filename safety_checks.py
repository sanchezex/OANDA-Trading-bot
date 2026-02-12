"""
Safety Checks Module
Implements safety checks, risk management, and kill switches
"""

import json
import logging
from typing import Tuple, Dict, List
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class SafetyChecker:
    """Implements safety checks and risk controls"""
    
    def __init__(self, config_path: str, connector):
        """
        Initialize SafetyChecker
        
        Args:
            config_path (str): Path to config.json
            connector: OANDAConnector instance
        """
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        self.connector = connector
        self.max_loss = self.config['safety']['max_loss_usd']
        self.max_positions = self.config['safety']['max_open_positions']
        self.stop_loss_distance = self.config['safety']['stop_loss_distance_pips']
        self.take_profit_distance = self.config['safety']['take_profit_distance_pips']
        
        self.should_stop = False
        self.stop_reason = None
    
    def check_account_health(self) -> Tuple[bool, str]:
        """
        Check if account is in good health
        
        Returns:
            tuple: (is_healthy, reason)
        """
        try:
            account = self.connector.get_account_summary()
            
            if not account:
                return False, "Cannot fetch account data"
            
            balance = float(account.get('balance', 0))
            equity = float(account.get('equity', 0))
            margin_available = float(account.get('marginAvailable', 0))
            used_margin = float(account.get('marginUsed', 0))
            
            if balance <= 0:
                return False, "Account balance is $0 or negative"
            
            if margin_available <= 0:
                return False, "No margin available"
            
            margin_level = (equity / used_margin * 100) if used_margin > 0 else 100
            
            if margin_level < 100:
                return False, f"Margin level too low: {margin_level:.1f}%"
            
            logger.debug(f"Account Health: Balance=${balance}, Equity=${equity}, Margin Level={margin_level:.1f}%")
            return True, "Account healthy"
        
        except Exception as e:
            logger.error(f"Error checking account health: {str(e)}")
            return False, str(e)
    
    def check_unrealized_loss(self) -> Tuple[bool, float]:
        """
        Check if unrealized loss exceeds maximum
        
        Returns:
            tuple: (is_within_limit, unrealized_loss)
        """
        try:
            account = self.connector.get_account_summary()
            unrealized_pl = float(account.get('unrealizedPL', 0))
            
            # If unrealized P&L is negative, it's a loss
            loss = abs(unrealized_pl) if unrealized_pl < 0 else 0
            
            if loss > self.max_loss:
                logger.warning(f"⚠ Unrealized loss (${loss:.2f}) exceeds max (${self.max_loss:.2f})")
                return False, loss
            
            logger.debug(f"Unrealized loss: ${loss:.2f} (max: ${self.max_loss:.2f})")
            return True, loss
        
        except Exception as e:
            logger.error(f"Error checking unrealized loss: {str(e)}")
            return True, 0
    
    def check_open_positions_count(self) -> Tuple[bool, int]:
        """
        Check if open positions exceed maximum
        
        Returns:
            tuple: (is_within_limit, open_positions_count)
        """
        try:
            count = self.connector.get_open_positions_count()
            
            if count > self.max_positions:
                logger.warning(f"⚠ Open positions ({count}) exceed max ({self.max_positions})")
                return False, count
            
            logger.debug(f"Open positions: {count}/{self.max_positions}")
            return True, count
        
        except Exception as e:
            logger.error(f"Error checking open positions: {str(e)}")
            return True, 0
    
    def check_all_safety_conditions(self) -> Tuple[bool, List[str]]:
        """
        Run all safety checks
        
        Returns:
            tuple: (all_safe, list_of_issues)
        """
        issues = []
        
        # Check account health
        healthy, health_msg = self.check_account_health()
        if not healthy:
            issues.append(f"Account health: {health_msg}")
        
        # Check unrealized loss
        within_limit, loss = self.check_unrealized_loss()
        if not within_limit:
            issues.append(f"Loss control: Unrealized loss ${loss:.2f} exceeds ${self.max_loss:.2f}")
        
        # Check open positions
        positions_ok, count = self.check_open_positions_count()
        if not positions_ok:
            issues.append(f"Position limit: {count} positions exceed {self.max_positions}")
        
        all_safe = len(issues) == 0
        
        if all_safe:
            logger.info("✓ All safety checks passed")
        else:
            logger.warning(f"✗ Safety check issues found: {len(issues)}")
            for issue in issues:
                logger.warning(f"  - {issue}")
        
        return all_safe, issues
    
    def should_emergency_stop(self) -> Tuple[bool, str]:
        """
        Determine if trading should stop immediately
        
        Returns:
            tuple: (should_stop, reason)
        """
        all_safe, issues = self.check_all_safety_conditions()
        
        if self.should_stop:
            return True, self.stop_reason
        
        if not all_safe and len(issues) > 0:
            # Only emergency stop on critical issues
            for issue in issues:
                if "health" in issue.lower() or "loss" in issue.lower():
                    return True, issues[0]
        
        return False, ""
    
    def manual_kill_switch(self, reason: str = "Manual stop"):
        """
        Manually activate kill switch
        
        Args:
            reason (str): Reason for stopping
        """
        self.should_stop = True
        self.stop_reason = reason
        logger.critical(f"🛑 KILL SWITCH ACTIVATED: {reason}")
    
    def validate_order_placement(self, units: int, price: float) -> Tuple[bool, str]:
        """
        Validate if an order can be safely placed
        
        Args:
            units (int): Number of units to trade
            price (float): Order price
            
        Returns:
            tuple: (is_valid, message)
        """
        try:
            # Check basic safety first
            safe, issues = self.check_all_safety_conditions()
            if not safe:
                return False, f"Safety checks failed: {issues[0]}"
            
            account = self.connector.get_account_summary()
            balance = float(account.get('balance', 0))
            
            # Estimate margin requirement (varies by pair)
            # EUR/USD typically 50:1 leverage = 2% margin requirement
            estimated_margin = (units * price) / 50
            
            if estimated_margin > balance * 0.5:  # Don't use more than 50% of balance
                return False, f"Order would use too much margin (${estimated_margin:.2f} > 50% of balance)"
            
            return True, "Order validation passed"
        
        except Exception as e:
            logger.error(f"Error validating order: {str(e)}")
            return False, str(e)
    
    def check_market_conditions(self, market_data, instrument: str) -> Tuple[bool, str]:
        """
        Check if market conditions are suitable for trading
        
        Args:
            market_data: MarketData instance
            instrument (str): Currency pair to check
            
        Returns:
            tuple: (is_suitable, reason)
        """
        try:
            price_data = market_data.get_current_price(instrument)
            
            if not price_data:
                return False, "Cannot fetch price data"
            
            spread = price_data.get('spread_pips', 0)
            
            # For EUR/USD, spread higher than 2 pips is unusual during normal hours
            if spread > 2.0:
                logger.warning(f"Spread is {spread:.1f} pips - wider than normal")
                return False, f"Spread too wide: {spread:.1f} pips"
            
            return True, "Market conditions suitable"
        
        except Exception as e:
            logger.error(f"Error checking market conditions: {str(e)}")
            return False, str(e)
    
    def log_safety_status(self):
        """Log comprehensive safety status"""
        logger.info("="*60)
        logger.info("SAFETY STATUS REPORT")
        logger.info("="*60)
        
        account = self.connector.get_account_summary()
        if account:
            logger.info(f"Balance: ${account.get('balance', 'N/A')}")
            logger.info(f"Equity: ${account.get('equity', 'N/A')}")
            logger.info(f"Unrealized P&L: ${account.get('unrealizedPL', 'N/A')}")
            logger.info(f"Margin Available: ${account.get('marginAvailable', 'N/A')}")
            logger.info(f"Open Positions: {account.get('openPositionCount', 'N/A')}")
        
        all_safe, issues = self.check_all_safety_conditions()
        
        if all_safe:
            logger.info("✓ All systems operational")
        else:
            logger.warning("⚠ Issues detected:")
            for issue in issues:
                logger.warning(f"  {issue}")
        
        if self.should_stop:
            logger.critical(f"🛑 TRADING HALTED: {self.stop_reason}")
        
        logger.info("="*60)
