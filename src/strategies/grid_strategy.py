"""
Grid Trading Strategy Implementation.
Contains all grid calculation and trading logic.
"""
import numpy as np
from typing import List, Dict
from config.settings import Config
from src.utils.logger import logger


class GridStrategy:
    """
    Grid trading strategy calculator.
    Handles grid level calculations and profit projections.
    """
    
    def __init__(self):
        """Initialize grid strategy with config parameters."""
        self.instrument = Config.TRADING_PAIR
        self.lower_bound = Config.GRID_LOWER_BOUND
        self.upper_bound = Config.GRID_UPPER_BOUND
        self.num_grids = Config.NUMBER_OF_GRIDS
        self.position_size = Config.POSITION_SIZE
        
        # Calculate grid parameters
        self.grid_spacing = (self.upper_bound - self.lower_bound) / self.num_grids
        self.grid_levels = self._calculate_grid_levels()
        
        logger.info(f"Grid Strategy initialized: {self.num_grids} grids "
                   f"between {self.lower_bound} and {self.upper_bound}")
        logger.info(f"Grid spacing: {self.grid_spacing:.5f} ({self.grid_spacing * 10000:.1f} pips)")
    
    def _calculate_grid_levels(self) -> List[float]:
        """
        Calculate all grid price levels.
        
        Returns:
            List of grid prices from lower to upper bound
        """
        levels = np.linspace(self.lower_bound, self.upper_bound, self.num_grids + 1)
        return [round(level, 5) for level in levels]
    
    def get_grid_levels(self) -> List[float]:
        """Get all grid levels."""
        return self.grid_levels
    
    def get_buy_levels(self, current_price: float) -> List[float]:
        """
        Get grid levels where we should place buy orders (below current price).
        
        Args:
            current_price: Current market price
            
        Returns:
            List of buy levels
        """
        buy_levels = [level for level in self.grid_levels if level < current_price]
        return buy_levels
    
    def get_sell_levels(self, current_price: float) -> List[float]:
        """
        Get grid levels where we should place sell orders (above current price).
        
        Args:
            current_price: Current market price
            
        Returns:
            List of sell levels
        """
        sell_levels = [level for level in self.grid_levels if level > current_price]
        return sell_levels
    
    def get_target_price(self, entry_price: float, is_buy: bool) -> float:
        """
        Get target price for a position.
        
        Args:
            entry_price: Entry price
            is_buy: True if buy order, False if sell order
            
        Returns:
            Target price (next grid level)
        """
        if is_buy:
            targets = [level for level in self.grid_levels if level > entry_price]
            return min(targets) if targets else entry_price + self.grid_spacing
        else:
            targets = [level for level in self.grid_levels if level < entry_price]
            return max(targets) if targets else entry_price - self.grid_spacing
    
    def is_price_in_range(self, price: float) -> bool:
        """
        Check if price is within grid range.
        
        Args:
            price: Price to check
            
        Returns:
            True if in range, False otherwise
        """
        return self.lower_bound <= price <= self.upper_bound
    
    def calculate_required_capital(self) -> Dict:
        """
        Calculate total capital required for the grid.
        
        Returns:
            Dictionary with capital requirements
        """
        num_buy_grids = self.num_grids // 2
        total_units = num_buy_grids * self.position_size
        avg_entry_price = (self.lower_bound + self.upper_bound) / 2
        required_capital = total_units * avg_entry_price
        margin_buffer = required_capital * 0.2  # 20% buffer
        
        return {
            'required_capital': required_capital,
            'margin_buffer': margin_buffer,
            'total_recommended': required_capital + margin_buffer,
            'max_positions': num_buy_grids,
            'position_size': self.position_size
        }
    
    def get_grid_statistics(self) -> Dict:
        """
        Get statistics about the grid setup.
        
        Returns:
            Dictionary with grid statistics
        """
        capital = self.calculate_required_capital()
        profit_per_cycle = self.position_size * self.grid_spacing
        
        return {
            'instrument': self.instrument,
            'num_grids': self.num_grids,
            'lower_bound': self.lower_bound,
            'upper_bound': self.upper_bound,
            'grid_spacing': self.grid_spacing,
            'grid_spacing_pips': self.grid_spacing * 10000,
            'position_size': self.position_size,
            'profit_per_cycle': profit_per_cycle,
            **capital
        }
    
    def calculate_profit_per_cycle(self, entry_price: float, exit_price: float, units: int) -> float:
        """
        Calculate gross profit per cycle before spread.
        
        Args:
            entry_price: Entry price
            exit_price: Exit price
            units: Number of units traded
            
        Returns:
            Profit in USD
        """
        pips_difference = (exit_price - entry_price) * 10000
        profit = pips_difference * units * 0.0001
        return round(profit, 2)
    
    def calculate_net_profit_per_cycle(self, entry_price: float, exit_price: float, 
                                       units: int, spread_pips: float = 1.0) -> float:
        """
        Calculate net profit per cycle after spread costs.
        
        Args:
            entry_price: Entry price
            exit_price: Exit price
            units: Number of units traded
            spread_pips: Spread in pips
            
        Returns:
            Net profit in USD
        """
        gross_profit = self.calculate_profit_per_cycle(entry_price, exit_price, units)
        spread_cost = spread_pips * units * 0.0001
        return round(gross_profit - spread_cost, 2)
    
    def calculate_grid_levels(self, current_price: float = None) -> Dict[str, list]:
        """
        Calculate all grid levels for buy and sell orders.
        
        Args:
            current_price: Current market price (unused, for compatibility)
            
        Returns:
            Dictionary with buy_levels, sell_levels, and all_levels
        """
        range_pips = (self.upper_bound - self.lower_bound) * 10000
        actual_grid_spacing = range_pips / (self.num_grids - 1)
        
        logger.info(f"Grid Range: {self.lower_bound} - {self.upper_bound}")
        logger.info(f"Range: {range_pips} pips")
        logger.info(f"Actual grid spacing: {actual_grid_spacing:.2f} pips")
        
        grid_levels = []
        for i in range(self.num_grids):
            level = self.lower_bound + (i * actual_grid_spacing / 10000)
            grid_levels.append(round(level, 5))
        
        grid_levels = sorted(list(set(grid_levels)))
        
        buy_levels = grid_levels[:self.num_grids // 2]
        sell_levels = grid_levels[self.num_grids // 2:]
        
        return {
            'buy_levels': buy_levels,
            'sell_levels': sell_levels,
            'all_levels': grid_levels,
            'grid_spacing_pips': actual_grid_spacing,
            'total_grids': len(grid_levels)
        }
    
    def generate_grid_report(self, current_price: float, spread_pips: float = 0.9) -> Dict:
        """
        Generate comprehensive grid configuration report.
        
        Args:
            current_price: Current market price
            spread_pips: Average spread in pips
            
        Returns:
            Detailed grid report dictionary
        """
        grid_data = self.calculate_grid_levels(current_price)
        grid_spacing_pips = self.grid_spacing * 10000
        
        gross_profit = self.calculate_profit_per_cycle(
            current_price, 
            current_price + (grid_spacing_pips / 10000),
            self.position_size
        )
        net_profit = self.calculate_net_profit_per_cycle(
            current_price,
            current_price + (grid_spacing_pips / 10000),
            self.position_size,
            spread_pips
        )
        
        daily_cycles = (self.upper_bound - self.lower_bound) * 10000 / grid_spacing_pips
        daily_projection = self.calculate_daily_projection(net_profit, int(daily_cycles / 2))
        monthly_projection = self.calculate_monthly_projection(daily_projection)
        
        capital_needed = self.calculate_required_capital()
        roi = self.calculate_return_on_investment(
            capital_needed['required_capital'], 
            monthly_projection
        )
        
        return {
            'instrument': self.instrument,
            'current_price': current_price,
            'grid_configuration': {
                'lower_level': self.lower_bound,
                'upper_level': self.upper_bound,
                'range_pips': (self.upper_bound - self.lower_bound) * 10000,
                'number_of_grids': self.num_grids,
                'grid_spacing_pips': grid_spacing_pips,
                'total_grid_levels': len(grid_data['all_levels'])
            },
            'position_sizing': {
                'units_per_trade': self.position_size,
                'capital_per_grid': self.position_size,
                'total_capital_needed': capital_needed['required_capital']
            },
            'profitability': {
                'gross_profit_per_cycle': gross_profit,
                'spread_cost_per_cycle': spread_pips * self.position_size * 0.0001,
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
    
    def calculate_daily_projection(self, net_profit_per_cycle: float, cycles_per_day: int) -> float:
        """
        Calculate projected daily profit.
        
        Args:
            net_profit_per_cycle: Net profit per complete grid cycle
            cycles_per_day: Expected number of cycles per day
            
        Returns:
            Projected daily profit in USD
        """
        return round(net_profit_per_cycle * cycles_per_day, 2)
    
    def calculate_monthly_projection(self, daily_profit: float, trading_days: int = 20) -> float:
        """
        Calculate projected monthly profit.
        
        Args:
            daily_profit: Daily profit
            trading_days: Number of trading days per month
            
        Returns:
            Projected monthly profit in USD
        """
        return round(daily_profit * trading_days, 2)
    
    def calculate_return_on_investment(self, capital: float, monthly_profit: float) -> float:
        """
        Calculate monthly ROI percentage.
        
        Args:
            capital: Initial capital
            monthly_profit: Monthly profit
            
        Returns:
            ROI percentage
        """
        return round((monthly_profit / capital) * 100, 2) if capital > 0 else 0
    
    def print_grid_summary(self):
        """Print a summary of the grid configuration."""
        stats = self.get_grid_statistics()
        
        print("\n" + "="*60)
        print("GRID TRADING STRATEGY SUMMARY")
        print("="*60)
        print(f"Instrument:        {stats['instrument']}")
        print(f"Grid Range:        {stats['lower_bound']:.5f} - {stats['upper_bound']:.5f}")
        print(f"Number of Grids:   {stats['num_grids']}")
        print(f"Grid Spacing:      {stats['grid_spacing']:.5f} ({stats['grid_spacing_pips']:.1f} pips)")
        print(f"Position Size:     {stats['position_size']} units")
        print(f"\nCapital Requirements:")
        print(f"Required Capital:  ${stats['required_capital']:.2f}")
        print(f"Margin Buffer:     ${stats['margin_buffer']:.2f}")
        print(f"Total Recommended: ${stats['total_recommended']:.2f}")
        print(f"\nProfit Potential:")
        print(f"Per Grid Cycle:    ${stats['profit_per_cycle']:.2f}")
        print("="*60 + "\n")
    
    def print_grid_report(self, current_price: float, spread_pips: float = 0.9):
        """Print formatted grid configuration report."""
        report = self.generate_grid_report(current_price, spread_pips)
        
        print("\n" + "="*60)
        print(f"GRID BOT CONFIGURATION REPORT - {report['instrument']}")
        print("="*60)
        
        print(f"\nCurrent Price: {report['current_price']}")
        
        print(f"\nGRID CONFIGURATION:")
        print(f"  Range: {report['grid_configuration']['lower_level']} - {report['grid_configuration']['upper_level']}")
        print(f"  Range Width: {report['grid_configuration']['range_pips']:.2f} pips")
        print(f"  Total Grids: {report['grid_configuration']['number_of_grids']}")
        print(f"  Grid Spacing: {report['grid_configuration']['grid_spacing_pips']:.2f} pips")
        
        print(f"\nPOSITION SIZING:")
        print(f"  Units per Trade: {report['position_sizing']['units_per_trade']}")
        print(f"  Capital per Grid: ${report['position_sizing']['capital_per_grid']}")
        print(f"  Total Capital Needed: ${report['position_sizing']['total_capital_needed']:.2f}")
        
        print(f"\nPROFITABILITY (per cycle):")
        print(f"  Gross Profit: ${report['profitability']['gross_profit_per_cycle']:.2f}")
        print(f"  Spread Cost: ${report['profitability']['spread_cost_per_cycle']:.2f}")
        print(f"  Net Profit: ${report['profitability']['net_profit_per_cycle']:.2f}")
        
        print(f"\nPROJECTIONS:")
        print(f"  Daily Projection: ${report['profitability']['expected_daily_projection']:.2f}")
        print(f"  Monthly Projection: ${report['profitability']['expected_monthly_projection']:.2f}")
        print(f"  Monthly ROI: {report['profitability']['monthly_roi_percent']}%")
        
        print("\n" + "="*60 + "\n")

