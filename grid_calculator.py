"""
Grid Calculator Module
Calculates grid levels, spacing, and position sizing for grid trading

Refactored version with:
- Comprehensive edge case handling
- Input validation
- Boundary protection
- Detailed error messages
"""

import json
import logging
from typing import List, Dict, Tuple, Optional
import math

logger = logging.getLogger(__name__)


class GridCalculatorError(Exception):
    """Custom exception for GridCalculator errors"""
    pass


class GridCalculator:
    """Calculates grid trading parameters with comprehensive edge case handling"""
    
    # Constants for validation
    MIN_INSTRUMENT_LEN = 3
    MAX_INSTRUMENT_LEN = 20
    MIN_PRICE = 0.0001
    MAX_PRICE = 100000.0
    MIN_GRIDS = 2
    MAX_GRIDS = 1000
    MIN_UNITS = 1
    MAX_UNITS = 100000000
    MIN_SPREAD = 0.0
    MAX_SPREAD = 1000.0
    MIN_TRADING_DAYS = 1
    MAX_TRADING_DAYS = 31
    MIN_PIPS = 0.00001
    MAX_PIPS = 10000.0
    
    def __init__(self, config_path: str):
        """
        Initialize GridCalculator from config with validation
        
        Args:
            config_path (str): Path to config.json
            
        Raises:
            GridCalculatorError: If config is invalid or missing required fields
        """
        self._validate_config_file(config_path)
        
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        self._validate_config_values()
        
        self.instrument = self.config['trading']['instrument']
        self.lower_level = self.config['trading']['grid_range']['lower_level']
        self.upper_level = self.config['trading']['grid_range']['upper_level']
        self.num_grids = self.config['trading']['grid_settings']['number_of_grids']
        self.grid_spacing_pips = self.config['trading']['grid_settings']['grid_spacing_pips']
        self.position_size = self.config['trading']['position_sizing']['position_size_per_grid']
        self.units_per_trade = self.config['trading']['position_sizing']['units_per_trade']
        
        # Pre-calculate derived values
        self._range_pips = (self.upper_level - self.lower_level) * 10000
        self._actual_grid_spacing = self._range_pips / (self.num_grids - 1)
        
        logger.info(f"GridCalculator initialized: {self.instrument}, "
                   f"Range: {self.lower_level}-{self.upper_level}, "
                   f"Grids: {self.num_grids}")
    
    # ========================
    # VALIDATION METHODS
    # ========================
    
    def _validate_config_file(self, config_path: str) -> None:
        """Validate config file exists and is readable"""
        import os
        if not os.path.exists(config_path):
            raise GridCalculatorError(f"Config file not found: {config_path}")
        if not os.path.isfile(config_path):
            raise GridCalculatorError(f"Path is not a file: {config_path}")
        if os.path.getsize(config_path) == 0:
            raise GridCalculatorError(f"Config file is empty: {config_path}")
    
    def _validate_config_values(self) -> None:
        """Validate all required config values are present and valid"""
        required_keys = [
            ('trading.instrument', self.config.get('trading', {}).get('instrument')),
            ('trading.grid_range.lower_level', self.config.get('trading', {}).get('grid_range', {}).get('lower_level')),
            ('trading.grid_range.upper_level', self.config.get('trading', {}).get('grid_range', {}).get('upper_level')),
            ('trading.grid_settings.number_of_grids', self.config.get('trading', {}).get('grid_settings', {}).get('number_of_grids')),
            ('trading.grid_settings.grid_spacing_pips', self.config.get('trading', {}).get('grid_settings', {}).get('grid_spacing_pips')),
            ('trading.position_sizing.position_size_per_grid', self.config.get('trading', {}).get('position_sizing', {}).get('position_size_per_grid')),
            ('trading.position_sizing.units_per_trade', self.config.get('trading', {}).get('position_sizing', {}).get('units_per_trade')),
        ]
        
        missing = [key for key, value in required_keys if value is None]
        if missing:
            raise GridCalculatorError(f"Missing required config keys: {missing}")
        
        # Validate value ranges
        trading = self.config.get('trading', {})
        
        if not (self.MIN_INSTRUMENT_LEN <= len(trading.get('instrument', '')) <= self.MAX_INSTRUMENT_LEN):
            raise GridCalculatorError(f"Invalid instrument name length")
        
        lower = trading.get('grid_range', {}).get('lower_level', 0)
        upper = trading.get('grid_range', {}).get('upper_level', 0)
        if not (self.MIN_PRICE <= lower <= self.MAX_PRICE):
            raise GridCalculatorError(f"Lower level out of range: {lower}")
        if not (self.MIN_PRICE <= upper <= self.MAX_PRICE):
            raise GridCalculatorError(f"Upper level out of range: {upper}")
        if lower >= upper:
            raise GridCalculatorError(f"Lower level ({lower}) must be less than upper level ({upper})")
        
        num_grids = trading.get('grid_settings', {}).get('number_of_grids', 0)
        if not (self.MIN_GRIDS <= num_grids <= self.MAX_GRIDS):
            raise GridCalculatorError(f"Number of grids out of range: {num_grids}")
        
        grid_spacing = trading.get('grid_settings', {}).get('grid_spacing_pips', 0)
        if not (self.MIN_PIPS <= grid_spacing <= self.MAX_PIPS):
            raise GridCalculatorError(f"Grid spacing out of range: {grid_spacing}")
        
        units_per_trade = trading.get('position_sizing', {}).get('units_per_trade', 0)
        if not (self.MIN_UNITS <= units_per_trade <= self.MAX_UNITS):
            raise GridCalculatorError(f"Units per trade out of range: {units_per_trade}")
    
    @staticmethod
    def _validate_price(price: float, param_name: str = "price") -> None:
        """Validate price parameter"""
        if not isinstance(price, (int, float)):
            raise GridCalculatorError(f"{param_name} must be a number, got {type(price).__name__}")
        if not (GridCalculator.MIN_PRICE <= price <= GridCalculator.MAX_PRICE):
            raise GridCalculatorError(f"{param_name} out of range: {price}")
    
    @staticmethod
    def _validate_units(units: int, param_name: str = "units") -> None:
        """Validate units parameter"""
        if not isinstance(units, int):
            raise GridCalculatorError(f"{param_name} must be an integer, got {type(units).__name__}")
        if not (GridCalculator.MIN_UNITS <= units <= GridCalculator.MAX_UNITS):
            raise GridCalculatorError(f"{param_name} out of range: {units}")
    
    @staticmethod
    def _validate_spread_pips(spread_pips: float, param_name: str = "spread_pips") -> None:
        """Validate spread pips parameter"""
        if not isinstance(spread_pips, (int, float)):
            raise GridCalculatorError(f"{param_name} must be a number, got {type(spread_pips).__name__}")
        if not (GridCalculator.MIN_SPREAD <= spread_pips <= GridCalculator.MAX_SPREAD):
            raise GridCalculatorError(f"{param_name} out of range: {spread_pips}")
    
    # ========================
    # GRID LEVEL CALCULATIONS
    # ========================
    
    def calculate_grid_levels(self, current_price: float = None) -> Dict[str, list]:
        """
        Calculate all grid levels with edge case handling
        
        Args:
            current_price (float): Current market price (optional, for logging only)
            
        Returns:
            dict: Dictionary with 'buy_levels', 'sell_levels', 'all_levels', 
                  'grid_spacing_pips', 'total_grids'
                  
        Raises:
            GridCalculatorError: If grid calculation fails
        """
        try:
            # Handle edge case: very small number of grids
            if self.num_grids < 2:
                raise GridCalculatorError(f"Cannot calculate grid levels with {self.num_grids} grids (minimum 2)")
            
            # Handle edge case: zero or negative range
            if self._range_pips <= 0:
                raise GridCalculatorError(f"Invalid price range: {_format_range(self.lower_level, self.upper_level)}")
            
            # Handle edge case: actual grid spacing becomes zero
            if self._actual_grid_spacing <= 0:
                raise GridCalculatorError(f"Grid spacing too small: {_format_value(self._actual_grid_spacing)} pips")
            
            # Handle edge case: extremely small grid spacing
            if self._actual_grid_spacing < self.MIN_PIPS:
                logger.warning(f"Grid spacing {_format_value(self._actual_grid_spacing)} pips is very small")
            
            grid_levels = []
            for i in range(self.num_grids):
                level = self.lower_level + (i * self._actual_grid_spacing / 10000)
                grid_levels.append(round(level, 5))
            
            # Remove duplicates and sort
            grid_levels = sorted(list(set(grid_levels)))
            
            # Handle edge case: fewer unique levels than requested
            if len(grid_levels) < 2:
                raise GridCalculatorError(
                    f"Price granularity prevents meaningful grid levels "
                    f"({len(grid_levels)} unique levels from {self.num_grids} requested)"
                )
            
            # Distribute levels to buy/sell sides
            split_point = max(1, len(grid_levels) // 2)
            buy_levels = grid_levels[:split_point]
            sell_levels = grid_levels[split_point:]
            
            # Handle edge case: no buy or sell levels
            if len(buy_levels) == 0:
                buy_levels = [self.lower_level]
            if len(sell_levels) == 0:
                sell_levels = [self.upper_level]
            
            result = {
                'buy_levels': buy_levels,
                'sell_levels': sell_levels,
                'all_levels': grid_levels,
                'grid_spacing_pips': self._actual_grid_spacing,
                'total_grids': len(grid_levels),
                'unique_levels_count': len(set(grid_levels))
            }
            
            logger.info(f"Calculated {len(grid_levels)} grid levels "
                       f"({len(buy_levels)} buy, {len(sell_levels)} sell)")
            
            return result
        
        except GridCalculatorError:
            raise
        except Exception as e:
            raise GridCalculatorError(f"Unexpected error calculating grid levels: {str(e)}")
    
    # ========================
    # PROFIT CALCULATIONS
    # ========================
    
    def calculate_profit_per_cycle(self, entry_price: float, exit_price: float, units: int) -> float:
        """
        Calculate gross profit per cycle before spread with validation
        
        Args:
            entry_price (float): Entry price
            exit_price (float): Exit price
            units (int): Number of units traded
            
        Returns:
            float: Profit in USD
            
        Raises:
            GridCalculatorError: If inputs are invalid
        """
        self._validate_price(entry_price, "entry_price")
        self._validate_price(exit_price, "exit_price")
        self._validate_units(units, "units")
        
        pips_difference = (exit_price - entry_price) * 10000
        
        # Handle edge case: extremely large pip differences
        if abs(pips_difference) > self.MAX_PIPS * 1000:
            logger.warning(f"Large pip difference detected: {_format_value(pips_difference)} pips")
        
        profit = pips_difference * units * 0.0001
        
        # Handle edge case: extreme profit values
        if abs(profit) > 1e9:
            logger.warning(f"Extreme profit value: ${_format_value(profit)}")
        
        return round(profit, 2)
    
    def calculate_net_profit_per_cycle(self, entry_price: float, exit_price: float, 
                                       units: int, spread_pips: float = 1.0) -> float:
        """
        Calculate net profit per cycle after accounting for spread costs
        
        Args:
            entry_price (float): Entry price
            exit_price (float): Exit price
            units (int): Number of units traded
            spread_pips (float): Average spread in pips (default 1.0 for EUR/USD)
            
        Returns:
            float: Net profit in USD
        """
        self._validate_spread_pips(spread_pips, "spread_pips")
        
        gross_profit = self.calculate_profit_per_cycle(entry_price, exit_price, units)
        spread_cost = spread_pips * units * 0.0001
        
        # Handle edge case: spread cost exceeds gross profit
        if spread_cost > abs(gross_profit) and gross_profit > 0:
            logger.warning(f"Spread cost ({_format_value(spread_cost)}) exceeds gross profit ({_format_value(gross_profit)})")
        
        net_profit = gross_profit - spread_cost
        return round(net_profit, 2)
    
    # ========================
    # PROJECTION CALCULATIONS
    # ========================
    
    def calculate_daily_projection(self, net_profit_per_cycle: float, 
                                  expected_cycles_per_day: int) -> float:
        """
        Calculate projected daily profit with edge case handling
        
        Args:
            net_profit_per_cycle (float): Net profit per complete grid cycle
            expected_cycles_per_day (int): Expected number of cycles per day
            
        Returns:
            float: Projected daily profit in USD
        """
        if not isinstance(expected_cycles_per_day, int):
            raise GridCalculatorError(f"expected_cycles_per_day must be an integer")
        
        # Handle edge cases
        if expected_cycles_per_day < 0:
            logger.warning(f"Negative cycles per day: {expected_cycles_per_day}, using 0")
            expected_cycles_per_day = 0
        
        if expected_cycles_per_day > 1000:
            logger.warning(f"Very high cycles per day: {expected_cycles_per_day}")
        
        # Handle edge case: negative profit (loss projection)
        if net_profit_per_cycle < 0:
            logger.warning(f"Negative daily profit projection: ${net_profit_per_cycle:.2f}")
        
        return round(net_profit_per_cycle * expected_cycles_per_day, 2)
    
    def calculate_monthly_projection(self, daily_profit: float, 
                                    trading_days: int = 20) -> float:
        """
        Calculate projected monthly profit
        
        Args:
            daily_profit (float): Daily profit
            trading_days (int): Number of trading days per month (1-31)
            
        Returns:
            float: Projected monthly profit in USD
        """
        if not isinstance(trading_days, int):
            raise GridCalculatorError(f"trading_days must be an integer")
        
        # Handle edge cases for trading_days
        if not (self.MIN_TRADING_DAYS <= trading_days <= self.MAX_TRADING_DAYS):
            logger.warning(f"Trading days out of typical range: {trading_days}")
            trading_days = max(self.MIN_TRADING_DAYS, min(trading_days, self.MAX_TRADING_DAYS))
        
        # Handle edge case: negative daily profit
        if daily_profit < 0:
            logger.warning(f"Negative daily profit for monthly projection: ${daily_profit:.2f}")
        
        return round(daily_profit * trading_days, 2)
    
    def calculate_return_on_investment(self, capital: float, monthly_profit: float) -> float:
        """
        Calculate monthly ROI percentage with edge case handling
        
        Args:
            capital (float): Initial capital
            monthly_profit (float): Monthly profit
            
        Returns:
            float: ROI percentage (returns 0 for zero capital to avoid division error)
        """
        if not isinstance(capital, (int, float)):
            raise GridCalculatorError(f"capital must be a number")
        
        if not isinstance(monthly_profit, (int, float)):
            raise GridCalculatorError(f"monthly_profit must be a number")
        
        # Handle edge case: zero or negative capital
        if capital <= 0:
            if monthly_profit == 0:
                return 0.0  # 0% of 0 is 0
            elif monthly_profit > 0:
                logger.warning("Infinite ROI with zero capital and positive profit")
                return float('inf')
            else:
                logger.warning("Negative ROI with zero capital")
                return float('-inf')
        
        # Handle edge case: extreme values
        if capital < 1:
            logger.warning(f"Very small capital: ${capital}")
        
        roi = (monthly_profit / capital) * 100
        
        # Handle edge case: extreme ROI values
        if abs(roi) > 1e6:
            logger.warning(f"Extreme ROI value: {roi:.2f}%")
        
        return round(roi, 2)
    
    def calculate_total_capital_needed(self, units_per_trade: int, num_grids: int, 
                                      price: float, leverage: float = 1.0) -> float:
        """
        Calculate total capital needed for grid strategy with edge case handling
        
        Args:
            units_per_trade (int): Units per grid level
            num_grids (int): Total number of grids
            price (float): Approximate current price
            leverage (float): Leverage factor (1.0 = no leverage)
            
        Returns:
            float: Capital needed in USD (minimum $1.00)
        """
        self._validate_units(units_per_trade, "units_per_trade")
        self._validate_price(price, "price")
        
        if not isinstance(num_grids, int):
            raise GridCalculatorError(f"num_grids must be an integer")
        
        if not isinstance(leverage, (int, float)):
            raise GridCalculatorError(f"leverage must be a number")
        
        # Handle edge cases for leverage
        if leverage <= 0:
            logger.warning(f"Invalid leverage: {leverage}, using 1.0")
            leverage = 1.0
        
        if leverage > 500:
            logger.warning(f"Very high leverage: {leverage}x")
        
        if leverage > 100:
            logger.warning(f"High leverage ({leverage}x) may require additional margin")
        
        # Calculate for half the grids (assuming only buy side)
        active_grids = max(1, num_grids // 2)
        total_units = units_per_trade * active_grids
        
        # Handle edge case: overflow
        if total_units > 1e12:
            raise GridCalculatorError(f"Total units too large: {total_units}")
        
        # Position size in USD = (total_units / 100000) * price
        position_usd = (total_units / 100000) * price
        
        # Handle edge case: extreme position value
        if position_usd > 1e12:
            raise GridCalculatorError(f"Position value too large: ${position_usd:.2f}")
        
        capital_needed = position_usd / leverage
        
        # Handle edge case: very small capital
        if capital_needed < 1.0 and capital_needed > 0:
            logger.info(f"Very small capital needed: ${capital_needed:.4f}")
        
        return round(max(capital_needed, 1.0), 2)  # Minimum $1.00
    
    # ========================
    # REPORT GENERATION
    # ========================
    
    def generate_grid_report(self, current_price: float, spread_pips: float = 0.9) -> Dict:
        """
        Generate comprehensive grid configuration report with edge case handling
        
        Args:
            current_price (float): Current market price
            spread_pips (float): Average spread in pips
            
        Returns:
            dict: Detailed grid report
            
        Raises:
            GridCalculatorError: If report generation fails
        """
        self._validate_price(current_price, "current_price")
        self._validate_spread_pips(spread_pips, "spread_pips")
        
        try:
            grid_data = self.calculate_grid_levels(current_price)
            
            # Calculate example profit
            grid_spacing_pips = self.grid_spacing_pips
            gross_profit = self.calculate_profit_per_cycle(
                current_price, 
                current_price + (grid_spacing_pips / 10000),
                self.units_per_trade
            )
            net_profit = self.calculate_net_profit_per_cycle(
                current_price,
                current_price + (grid_spacing_pips / 10000),
                self.units_per_trade,
                spread_pips
            )
            
            # Handle edge case: operator precedence bug in original code
            # Original: upper - lower * 10000 / grid_spacing
            # Correct: (upper - lower) * 10000 / grid_spacing
            daily_cycles = (self.config['trading']['grid_range']['upper_level'] - 
                           self.config['trading']['grid_range']['lower_level']) * 10000 / grid_spacing_pips
            
            # Handle edge case: zero or negative daily cycles
            if daily_cycles <= 0:
                logger.warning(f"Invalid daily cycles: {daily_cycles}, using 1")
                daily_cycles = 1
            
            daily_projection = self.calculate_daily_projection(net_profit, int(daily_cycles / 2))
            monthly_projection = self.calculate_monthly_projection(daily_projection)
            
            capital_needed = self.calculate_total_capital_needed(
                self.units_per_trade,
                self.num_grids,
                current_price
            )
            
            roi = self.calculate_return_on_investment(capital_needed, monthly_projection)
            
            report = {
                'instrument': self.instrument,
                'current_price': current_price,
                'grid_configuration': {
                    'lower_level': self.lower_level,
                    'upper_level': self.upper_level,
                    'range_pips': self._range_pips,
                    'number_of_grids': self.num_grids,
                    'grid_spacing_pips': grid_spacing_pips,
                    'total_grid_levels': len(grid_data['all_levels']),
                    'unique_levels_count': grid_data.get('unique_levels_count', len(grid_data['all_levels']))
                },
                'position_sizing': {
                    'units_per_trade': self.units_per_trade,
                    'capital_per_grid': self.position_size,
                    'total_capital_needed': capital_needed
                },
                'profitability': {
                    'gross_profit_per_cycle': gross_profit,
                    'spread_cost_per_cycle': spread_pips * self.units_per_trade * 0.0001,
                    'net_profit_per_cycle': net_profit,
                    'expected_daily_projection': daily_projection,
                    'expected_monthly_projection': monthly_projection,
                    'monthly_roi_percent': roi,
                    'is_profitable': net_profit > 0
                },
                'grid_levels': {
                    'buy_levels': grid_data['buy_levels'][:5] + (['...'] if len(grid_data['buy_levels']) > 5 else []),
                    'sell_levels': grid_data['sell_levels'][-5:] + (['...'] if len(grid_data['sell_levels']) > 5 else []),
                    'all_levels_count': len(grid_data['all_levels'])
                },
                'validation': {
                    'is_config_valid': True,
                    'is_profitable': net_profit > 0,
                    'has_enough_levels': len(grid_data['all_levels']) >= 2,
                    'warning_count': 0
                }
            }
            
            # Add warnings for edge cases
            warnings = []
            if self._range_pips < 10:
                warnings.append("Very small price range")
            if self._actual_grid_spacing < 1:
                warnings.append("Very small grid spacing")
            if self.num_grids > 100:
                warnings.append("Large number of grids")
            if roi > 100:
                warnings.append("Very high ROI projection")
            
            report['validation']['warning_count'] = len(warnings)
            if warnings:
                report['validation']['warnings'] = warnings
            
            return report
        
        except GridCalculatorError:
            raise
        except Exception as e:
            raise GridCalculatorError(f"Error generating grid report: {str(e)}")
    
    def print_grid_report(self, current_price: float, spread_pips: float = 0.9) -> None:
        """Print formatted grid configuration report"""
        report = self.generate_grid_report(current_price, spread_pips)
        
        print("\n" + "="*60)
        print(f"GRID BOT CONFIGURATION REPORT - {report['instrument']}")
        print("="*60)
        
        print(f"\nCurrent Price: {report['current_price']}")
        
        print(f"\n📊 GRID CONFIGURATION:")
        print(f"  Range: {report['grid_configuration']['lower_level']} - {report['grid_configuration']['upper_level']}")
        print(f"  Range Width: {report['grid_configuration']['range_pips']:.2f} pips")
        print(f"  Total Grids: {report['grid_configuration']['number_of_grids']}")
        print(f"  Grid Spacing: {report['grid_configuration']['grid_spacing_pips']:.2f} pips")
        print(f"  Unique Levels: {report['grid_configuration']['unique_levels_count']}")
        
        print(f"\n💰 POSITION SIZING:")
        print(f"  Units per Trade: {report['position_sizing']['units_per_trade']}")
        print(f"  Capital per Grid: ${report['position_sizing']['capital_per_grid']}")
        print(f"  Total Capital Needed: ${report['position_sizing']['total_capital_needed']:.2f}")
        
        print(f"\n📈 PROFITABILITY (per cycle):")
        print(f"  Gross Profit: ${report['profitability']['gross_profit_per_cycle']:.2f}")
        print(f"  Spread Cost: ${report['profitability']['spread_cost_per_cycle']:.2f}")
        print(f"  Net Profit: ${report['profitability']['net_profit_per_cycle']:.2f}")
        
        print(f"\n📊 PROJECTIONS:")
        print(f"  Daily Projection: ${report['profitability']['expected_daily_projection']:.2f}")
        print(f"  Monthly Projection: ${report['profitability']['expected_monthly_projection']:.2f}")
        print(f"  Monthly ROI: {report['profitability']['monthly_roi_percent']}%")
        
        # Print warnings if any
        validation = report.get('validation', {})
        if validation.get('warning_count', 0) > 0:
            print(f"\n⚠️  WARNINGS:")
            for warning in validation.get('warnings', []):
                print(f"  - {warning}")
        
        print("\n" + "="*60 + "\n")


# ========================
# HELPER FUNCTIONS
# ========================

def _format_value(value: float) -> str:
    """Format value for display"""
    if abs(value) >= 1e6:
        return f"{value/1e6:.2f}M"
    elif abs(value) >= 1e3:
        return f"{value/1e3:.2f}K"
    elif abs(value) >= 1:
        return f"{value:.2f}"
    else:
        return f"{value:.6f}"


def _format_range(lower: float, upper: float) -> str:
    """Format price range for display"""
    return f"[{lower:.5f}, {upper:.5f}]"

