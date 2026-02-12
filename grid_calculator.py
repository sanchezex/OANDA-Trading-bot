"""
Grid Calculator Module
Calculates grid levels, spacing, and position sizing for grid trading
"""

import json
import logging
from typing import List, Dict, Tuple
import math

logger = logging.getLogger(__name__)


class GridCalculator:
    """Calculates grid trading parameters"""
    
    def __init__(self, config_path: str):
        """
        Initialize GridCalculator from config
        
        Args:
            config_path (str): Path to config.json
        """
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        self.instrument = self.config['trading']['instrument']
        self.lower_level = self.config['trading']['grid_range']['lower_level']
        self.upper_level = self.config['trading']['grid_range']['upper_level']
        self.num_grids = self.config['trading']['grid_settings']['number_of_grids']
        self.grid_spacing_pips = self.config['trading']['grid_settings']['grid_spacing_pips']
        self.position_size = self.config['trading']['position_sizing']['position_size_per_grid']
        self.units_per_trade = self.config['trading']['position_sizing']['units_per_trade']
    
    def calculate_grid_levels(self, current_price: float = None) -> Dict[str, list]:
        """
        Calculate all grid levels
        
        Args:
            current_price (float): Current market price (optional)
            
        Returns:
            dict: Dictionary with 'buy_levels' and 'sell_levels'
        """
        range_pips = (self.upper_level - self.lower_level) * 10000
        actual_grid_spacing = range_pips / (self.num_grids - 1)
        
        logger.info(f"Grid Range: {self.lower_level} - {self.upper_level}")
        logger.info(f"Range: {range_pips} pips")
        logger.info(f"Actual grid spacing: {actual_grid_spacing:.2f} pips")
        
        grid_levels = []
        for i in range(self.num_grids):
            level = self.lower_level + (i * actual_grid_spacing / 10000)
            grid_levels.append(round(level, 5))
        
        grid_levels = sorted(list(set(grid_levels)))
        
        buy_levels = grid_levels[:self.num_grids // 2]
        sell_levels = grid_levels[self.num_grids // 2:]
        
        result = {
            'buy_levels': buy_levels,
            'sell_levels': sell_levels,
            'all_levels': grid_levels,
            'grid_spacing_pips': actual_grid_spacing,
            'total_grids': len(grid_levels)
        }
        
        logger.info(f"Calculated {len(grid_levels)} grid levels")
        logger.info(f"Buy levels: {len(buy_levels)}, Sell levels: {len(sell_levels)}")
        
        return result
    
    def calculate_profit_per_cycle(self, entry_price: float, exit_price: float, units: int) -> float:
        """
        Calculate gross profit per cycle before spread
        
        Args:
            entry_price (float): Entry price
            exit_price (float): Exit price
            units (int): Number of units traded
            
        Returns:
            float: Profit in USD
        """
        pips_difference = (exit_price - entry_price) * 10000
        profit = pips_difference * units * 0.0001
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
        gross_profit = self.calculate_profit_per_cycle(entry_price, exit_price, units)
        spread_cost = spread_pips * units * 0.0001
        net_profit = gross_profit - spread_cost
        return round(net_profit, 2)
    
    def calculate_daily_projection(self, net_profit_per_cycle: float, expected_cycles_per_day: int) -> float:
        """
        Calculate projected daily profit
        
        Args:
            net_profit_per_cycle (float): Net profit per complete grid cycle
            expected_cycles_per_day (int): Expected number of cycles per day
            
        Returns:
            float: Projected daily profit in USD
        """
        return round(net_profit_per_cycle * expected_cycles_per_day, 2)
    
    def calculate_monthly_projection(self, daily_profit: float, trading_days: int = 20) -> float:
        """
        Calculate projected monthly profit
        
        Args:
            daily_profit (float): Daily profit
            trading_days (int): Number of trading days per month
            
        Returns:
            float: Projected monthly profit in USD
        """
        return round(daily_profit * trading_days, 2)
    
    def calculate_return_on_investment(self, capital: float, monthly_profit: float) -> float:
        """
        Calculate monthly ROI percentage
        
        Args:
            capital (float): Initial capital
            monthly_profit (float): Monthly profit
            
        Returns:
            float: ROI percentage
        """
        return round((monthly_profit / capital) * 100, 2)
    
    def calculate_total_capital_needed(self, units_per_trade: int, num_grids: int, 
                                      price: float, leverage: float = 1.0) -> float:
        """
        Calculate total capital needed for grid strategy
        
        Args:
            units_per_trade (int): Units per grid level
            num_grids (int): Total number of grids
            price (float): Approximate current price
            leverage (float): Leverage factor (1.0 = no leverage)
            
        Returns:
            float: Capital needed in USD
        """
        # Calculate for half the grids (assuming only buy side)
        active_grids = num_grids // 2
        total_units = units_per_trade * active_grids
        
        # For EUR/USD, 1 pip = $0.0001 per unit (100k units = $10)
        # Position size in USD = (total_units / 100000) * price
        position_usd = (total_units / 100000) * price
        capital_needed = position_usd / leverage
        
        return round(capital_needed, 2)
    
    def generate_grid_report(self, current_price: float, spread_pips: float = 0.9) -> Dict:
        """
        Generate comprehensive grid configuration report
        
        Args:
            current_price (float): Current market price
            spread_pips (float): Average spread in pips
            
        Returns:
            dict: Detailed grid report
        """
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
        
        daily_cycles = self.config['trading']['grid_range']['upper_level'] - \
                      self.config['trading']['grid_range']['lower_level'] * 10000 / grid_spacing_pips
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
                'range_pips': (self.upper_level - self.lower_level) * 10000,
                'number_of_grids': self.num_grids,
                'grid_spacing_pips': grid_spacing_pips,
                'total_grid_levels': len(grid_data['all_levels'])
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
                'monthly_roi_percent': roi
            },
            'grid_levels': {
                'buy_levels': grid_data['buy_levels'][:5] + ['...'],
                'sell_levels': grid_data['sell_levels'][-5:] + ['...']
            }
        }
        
        return report
    
    def print_grid_report(self, current_price: float, spread_pips: float = 0.9):
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
        
        print("\n" + "="*60 + "\n")
