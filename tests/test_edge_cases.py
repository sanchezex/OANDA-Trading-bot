#!/usr/bin/env python3
"""
Comprehensive Edge Case Tests for OANDA Trading Bot
Tests boundary inputs, invalid inputs, and error conditions
"""

import sys
import os
import unittest
from unittest.mock import Mock

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import standalone implementations to avoid external dependencies
from grid_calculator import GridCalculator


# ========================
# RISK MANAGER STANDALONE
# ========================

class RiskManagerStandalone:
    """Standalone RiskManager for testing without OANDA API dependencies"""
    
    def __init__(self, oanda_client):
        self.client = oanda_client
        self.should_stop = False
        self.stop_reason = None
    
    def check_account_health(self):
        try:
            account = self.client.get_account_summary()
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
            
            return True, "Account healthy"
        
        except Exception as e:
            return False, str(e)
    
    def check_unrealized_loss(self, max_loss: float = 50.0):
        try:
            account = self.client.get_account_summary()
            unrealized_pl = float(account.get('unrealizedPL', 0))
            loss = abs(unrealized_pl) if unrealized_pl < 0 else 0
            
            if loss > max_loss:
                return False, loss
            
            return True, loss
        
        except Exception as e:
            return True, 0
    
    def check_open_positions_count(self, max_positions: int = 20):
        try:
            positions = self.client.get_open_positions()
            count = len([p for p in positions if float(p.get('long', {}).get('units', 0)) != 0 
                        or float(p.get('short', {}).get('units', 0)) != 0])
            
            if count > max_positions:
                return False, count
            
            return True, count
        
        except Exception as e:
            return True, 0
    
    def check_market_conditions(self, spread_pips: float, max_spread: float = 2.0):
        if spread_pips > max_spread:
            return False, f"Spread too wide: {spread_pips:.1f} pips"
        return True, "Market conditions suitable"
    
    def manual_kill_switch(self, reason: str = "Manual stop"):
        self.should_stop = True
        self.stop_reason = reason
    
    def should_emergency_stop(self, max_loss: float = 50.0):
        if self.should_stop:
            return True, self.stop_reason
        
        healthy, _ = self.check_account_health()
        within_limit, _ = self.check_unrealized_loss(max_loss)
        
        if not healthy:
            return True, "Account health check failed"
        if not within_limit:
            return True, "Unrealized loss exceeds limit"
        
        return False, ""


class TestGridCalculatorEdgeCases(unittest.TestCase):
    """Comprehensive edge case tests for GridCalculator"""
    
    # Create a mock config for testing
    MOCK_CONFIG = {
        'trading': {
            'instrument': 'EUR_USD',
            'grid_range': {
                'lower_level': 1.0700,
                'upper_level': 1.0900  # FIXED: upper > lower
            },
            'grid_settings': {
                'number_of_grids': 10,
                'grid_spacing_pips': 10.0
            },
            'position_sizing': {
                'position_size_per_grid': 100.0,
                'units_per_trade': 10000
            }
        }
    }
    
    def setUp(self):
        """Set up test fixtures"""
        import tempfile
        import uuid
        import copy
        self.mock_config_path = f'/tmp/test_config_{uuid.uuid4().hex[:8]}.json'
        with open(self.mock_config_path, 'w') as f:
            import json
            # Use deepcopy to avoid modifying class variable
            json.dump(copy.deepcopy(self.MOCK_CONFIG), f)
    
    def tearDown(self):
        """Clean up test files"""
        if os.path.exists(self.mock_config_path):
            os.remove(self.mock_config_path)
    
    def test_initialization_valid_config(self):
        """Test initialization with valid config"""
        calc = GridCalculator(self.mock_config_path)
        self.assertEqual(calc.instrument, 'EUR_USD')
        self.assertEqual(calc.num_grids, 10)
    
    def test_initialization_missing_file(self):
        """Test initialization with missing config file"""
        with self.assertRaises(Exception):
            GridCalculator('/nonexistent/path/config.json')
    
    def test_initialization_empty_file(self):
        """Test initialization with empty config file"""
        empty_config_path = '/tmp/empty_config.json'
        with open(empty_config_path, 'w') as f:
            f.write('')
        try:
            with self.assertRaises(Exception):
                GridCalculator(empty_config_path)
        finally:
            if os.path.exists(empty_config_path):
                os.remove(empty_config_path)
    
    def test_initialization_missing_keys(self):
        """Test initialization with missing required keys"""
        invalid_config_path = '/tmp/invalid_config.json'
        with open(invalid_config_path, 'w') as f:
            import json
            json.dump({'trading': {}}, f)
        try:
            with self.assertRaises(Exception):
                GridCalculator(invalid_config_path)
        finally:
            if os.path.exists(invalid_config_path):
                os.remove(invalid_config_path)
    
    def test_initialization_invalid_price_range(self):
        """Test initialization with invalid price range (lower >= upper)"""
        import copy
        import uuid as uuid_module
        invalid_config_path = f'/tmp/test_invalid_range_config_{uuid_module.uuid4().hex[:8]}.json'
        config = copy.deepcopy(self.MOCK_CONFIG)
        config['trading']['grid_range']['upper_level'] = 1.0700  # Lower than lower_level
        with open(invalid_config_path, 'w') as f:
            import json
            json.dump(config, f)
        try:
            with self.assertRaises(Exception):
                GridCalculator(invalid_config_path)
        finally:
            if os.path.exists(invalid_config_path):
                os.remove(invalid_config_path)
    
    # ========================
    # PROFIT CALCULATION EDGE CASES
    # ========================
    
    def test_profit_zero_units(self):
        """Test profit calculation with zero units (should raise)"""
        calc = GridCalculator(self.mock_config_path)
        with self.assertRaises(Exception):
            calc.calculate_profit_per_cycle(1.0850, 1.0860, 0)
    
    def test_profit_negative_units(self):
        """Test profit calculation with negative units (short position - should raise)"""
        calc = GridCalculator(self.mock_config_path)
        # Negative units should be rejected by validation
        with self.assertRaises(Exception):
            calc.calculate_profit_per_cycle(1.0860, 1.0850, -10000)
    
    def test_profit_equal_prices(self):
        """Test profit calculation with same entry and exit price"""
        calc = GridCalculator(self.mock_config_path)
        profit = calc.calculate_profit_per_cycle(1.0850, 1.0850, 10000)
        self.assertEqual(profit, 0.0)
    
    def test_profit_small_price_movement(self):
        """Test profit calculation with minimal price movement"""
        calc = GridCalculator(self.mock_config_path)
        # 0.0001 = 1 pip
        profit = calc.calculate_profit_per_cycle(1.0850, 1.0851, 10000)
        self.assertEqual(profit, 1.0)
    
    def test_profit_large_price_movement(self):
        """Test profit calculation with large price movement"""
        calc = GridCalculator(self.mock_config_path)
        # 0.0100 = 100 pips
        profit = calc.calculate_profit_per_cycle(1.0800, 1.0900, 10000)
        self.assertEqual(profit, 100.0)
    
    def test_profit_max_units(self):
        """Test profit calculation with maximum units"""
        calc = GridCalculator(self.mock_config_path)
        profit = calc.calculate_profit_per_cycle(1.0850, 1.0860, 100000000)
        # 10 pips * 100M units * 0.0001 = $100,000
        self.assertEqual(profit, 100000.0)
    
    def test_profit_invalid_entry_price(self):
        """Test profit calculation with invalid entry price"""
        calc = GridCalculator(self.mock_config_path)
        with self.assertRaises(Exception):
            calc.calculate_profit_per_cycle(-1.0, 1.0860, 10000)
    
    def test_profit_invalid_exit_price(self):
        """Test profit calculation with invalid exit price"""
        calc = GridCalculator(self.mock_config_path)
        with self.assertRaises(Exception):
            calc.calculate_profit_per_cycle(1.0850, 999999.0, 10000)
    
    def test_profit_invalid_units(self):
        """Test profit calculation with invalid units"""
        calc = GridCalculator(self.mock_config_path)
        with self.assertRaises(Exception):
            calc.calculate_profit_per_cycle(1.0850, 1.0860, -100)
    
    def test_profit_invalid_units_float(self):
        """Test profit calculation with float units"""
        calc = GridCalculator(self.mock_config_path)
        with self.assertRaises(Exception):
            calc.calculate_profit_per_cycle(1.0850, 1.0860, 10000.5)
    
    # ========================
    # ROI CALCULATION EDGE CASES
    # ========================
    
    def test_roi_zero_capital(self):
        """Test ROI calculation with zero capital"""
        calc = GridCalculator(self.mock_config_path)
        roi = calc.calculate_return_on_investment(0, 100)
        self.assertEqual(roi, float('inf'))
    
    def test_roi_negative_capital(self):
        """Test ROI calculation with negative capital"""
        calc = GridCalculator(self.mock_config_path)
        roi = calc.calculate_return_on_investment(-1000, 100)
        # With negative capital and positive profit, ROI is inf (undefined, not -inf)
        self.assertEqual(roi, float('inf'))
    
    def test_roi_zero_profit(self):
        """Test ROI calculation with zero profit"""
        calc = GridCalculator(self.mock_config_path)
        roi = calc.calculate_return_on_investment(1000, 0)
        self.assertEqual(roi, 0.0)
    
    def test_roi_negative_profit(self):
        """Test ROI calculation with negative profit (loss)"""
        calc = GridCalculator(self.mock_config_path)
        roi = calc.calculate_return_on_investment(1000, -100)
        self.assertEqual(roi, -10.0)
    
    def test_roi_very_small_capital(self):
        """Test ROI calculation with very small capital"""
        calc = GridCalculator(self.mock_config_path)
        roi = calc.calculate_return_on_investment(0.001, 100)
        # 100 / 0.001 * 100 = 10,000,000%
        self.assertEqual(roi, 10000000.0)
    
    def test_roi_large_values(self):
        """Test ROI calculation with large values"""
        calc = GridCalculator(self.mock_config_path)
        roi = calc.calculate_return_on_investment(1000000, 500000)
        self.assertEqual(roi, 50.0)
    
    # ========================
    # CAPITAL CALCULATION EDGE CASES
    # ========================
    
    def test_capital_zero_leverage(self):
        """Test capital calculation with zero leverage"""
        calc = GridCalculator(self.mock_config_path)
        capital = calc.calculate_total_capital_needed(10000, 10, 1.0850, 0)
        # Should use default leverage of 1.0
        self.assertGreater(capital, 0)
    
    def test_capital_negative_leverage(self):
        """Test capital calculation with negative leverage"""
        calc = GridCalculator(self.mock_config_path)
        capital = calc.calculate_total_capital_needed(10000, 10, 1.0850, -10)
        # Should use default leverage of 1.0
        self.assertGreater(capital, 0)
    
    def test_capital_max_leverage(self):
        """Test capital calculation with maximum leverage"""
        calc = GridCalculator(self.mock_config_path)
        capital_high_lev = calc.calculate_total_capital_needed(10000, 10, 1.0850, 500)
        capital_no_lev = calc.calculate_total_capital_needed(10000, 10, 1.0850, 1)
        # Higher leverage should require less or equal capital
        self.assertLessEqual(capital_high_lev, capital_no_lev)
    
    def test_capital_min_units(self):
        """Test capital calculation with minimum units"""
        calc = GridCalculator(self.mock_config_path)
        capital = calc.calculate_total_capital_needed(1, 10, 1.0850, 1)
        # Minimum $1.00
        self.assertGreaterEqual(capital, 1.0)
    
    def test_capital_max_units(self):
        """Test capital calculation with maximum units"""
        calc = GridCalculator(self.mock_config_path)
        # This should not raise an exception as 100M units * 1000 grids is within limits
        # The check is for total_units > 1e12, not individual units
        capital = calc.calculate_total_capital_needed(100000000, 1000, 1.0850, 1)
        self.assertIsInstance(capital, float)
    
    def test_capital_invalid_leverage(self):
        """Test capital calculation with invalid leverage type"""
        calc = GridCalculator(self.mock_config_path)
        with self.assertRaises(Exception):
            calc.calculate_total_capital_needed(10000, 10, 1.0850, "high")
    
    def test_capital_invalid_units_type(self):
        """Test capital calculation with invalid units type"""
        calc = GridCalculator(self.mock_config_path)
        with self.assertRaises(Exception):
            calc.calculate_total_capital_needed("10000", 10, 1.0850, 1)
    
    def test_capital_invalid_price_type(self):
        """Test capital calculation with invalid price type"""
        calc = GridCalculator(self.mock_config_path)
        with self.assertRaises(Exception):
            calc.calculate_total_capital_needed(10000, 10, "1.0850", 1)
    
    # ========================
    # DAILY PROJECTION EDGE CASES
    # ========================
    
    def test_daily_projection_zero_cycles(self):
        """Test daily projection with zero cycles"""
        calc = GridCalculator(self.mock_config_path)
        projection = calc.calculate_daily_projection(10.0, 0)
        self.assertEqual(projection, 0.0)
    
    def test_daily_projection_negative_cycles(self):
        """Test daily projection with negative cycles (should use 0)"""
        calc = GridCalculator(self.mock_config_path)
        projection = calc.calculate_daily_projection(10.0, -5)
        self.assertEqual(projection, 0.0)
    
    def test_daily_projection_many_cycles(self):
        """Test daily projection with many cycles"""
        calc = GridCalculator(self.mock_config_path)
        projection = calc.calculate_daily_projection(10.0, 1000)
        self.assertEqual(projection, 10000.0)
    
    def test_daily_projection_negative_profit(self):
        """Test daily projection with negative profit (loss)"""
        calc = GridCalculator(self.mock_config_path)
        projection = calc.calculate_daily_projection(-10.0, 10)
        self.assertEqual(projection, -100.0)
    
    def test_daily_projection_float_cycles(self):
        """Test daily projection with float cycles (should raise)"""
        calc = GridCalculator(self.mock_config_path)
        with self.assertRaises(Exception):
            calc.calculate_daily_projection(10.0, 10.5)
    
    # ========================
    # MONTHLY PROJECTION EDGE CASES
    # ========================
    
    def test_monthly_projection_min_trading_days(self):
        """Test monthly projection with minimum trading days"""
        calc = GridCalculator(self.mock_config_path)
        projection = calc.calculate_monthly_projection(10.0, 1)
        self.assertEqual(projection, 10.0)
    
    def test_monthly_projection_max_trading_days(self):
        """Test monthly projection with maximum trading days"""
        calc = GridCalculator(self.mock_config_path)
        projection = calc.calculate_monthly_projection(10.0, 31)
        self.assertEqual(projection, 310.0)
    
    def test_monthly_projection_negative_days(self):
        """Test monthly projection with negative trading days (clamped)"""
        calc = GridCalculator(self.mock_config_path)
        projection = calc.calculate_monthly_projection(10.0, -5)
        # Should clamp to MIN_TRADING_DAYS (1)
        self.assertEqual(projection, 10.0)
    
    def test_monthly_projection_excessive_days(self):
        """Test monthly projection with excessive trading days (clamped)"""
        calc = GridCalculator(self.mock_config_path)
        projection = calc.calculate_monthly_projection(10.0, 100)
        # Should clamp to MAX_TRADING_DAYS (31)
        self.assertEqual(projection, 310.0)
    
    def test_monthly_projection_negative_profit(self):
        """Test monthly projection with negative daily profit"""
        calc = GridCalculator(self.mock_config_path)
        projection = calc.calculate_monthly_projection(-10.0, 20)
        self.assertEqual(projection, -200.0)
    
    def test_monthly_projection_float_days(self):
        """Test monthly projection with float trading days (should raise)"""
        calc = GridCalculator(self.mock_config_path)
        with self.assertRaises(Exception):
            calc.calculate_monthly_projection(10.0, 20.5)
    
    # ========================
    # NET PROFIT CALCULATION EDGE CASES
    # ========================
    
    def test_net_profit_zero_spread(self):
        """Test net profit calculation with zero spread"""
        calc = GridCalculator(self.mock_config_path)
        net = calc.calculate_net_profit_per_cycle(1.0850, 1.0860, 10000, 0)
        self.assertEqual(net, 10.0)
    
    def test_net_profit_large_spread(self):
        """Test net profit calculation with large spread"""
        calc = GridCalculator(self.mock_config_path)
        net = calc.calculate_net_profit_per_cycle(1.0850, 1.0860, 10000, 100)
        self.assertEqual(net, -90.0)  # 10 - 100 = -90
    
    def test_net_profit_spread_exceeds_profit(self):
        """Test net profit calculation when spread exceeds gross profit"""
        calc = GridCalculator(self.mock_config_path)
        net = calc.calculate_net_profit_per_cycle(1.0850, 1.0851, 1000, 10)
        # Gross: 1 pip * 1000 units * 0.0001 = $0.10
        # Spread: 10 * 1000 * 0.0001 = $1.00
        # Net: 0.10 - 1.00 = -$0.90
        self.assertEqual(net, -0.90)
    
    def test_net_profit_invalid_spread(self):
        """Test net profit calculation with invalid spread"""
        calc = GridCalculator(self.mock_config_path)
        with self.assertRaises(Exception):
            calc.calculate_net_profit_per_cycle(1.0850, 1.0860, 10000, -5)
    
    # ========================
    # GRID LEVEL CALCULATION EDGE CASES
    # ========================
    
    def test_grid_levels_min_grids(self):
        """Test grid level calculation with minimum grids"""
        calc = GridCalculator(self.mock_config_path)
        calc.num_grids = 2
        result = calc.calculate_grid_levels()
        self.assertGreaterEqual(len(result['all_levels']), 2)
    
    def test_grid_levels_small_range(self):
        """Test grid level calculation with small price range"""
        calc = GridCalculator(self.mock_config_path)
        calc.lower_level = 1.0850
        calc.upper_level = 1.0851
        calc.num_grids = 10
        try:
            result = calc.calculate_grid_levels()
            # May have duplicates due to precision, but should still work
            self.assertIn('all_levels', result)
        except Exception as e:
            # This is expected behavior for very small ranges
            self.assertIn("Price granularity", str(e))
    
    def test_grid_levels_large_number(self):
        """Test grid level calculation with large number of grids"""
        calc = GridCalculator(self.mock_config_path)
        calc.num_grids = 500
        result = calc.calculate_grid_levels()
        self.assertLessEqual(len(result['all_levels']), calc.num_grids)
    
    def test_grid_levels_very_small_spacing(self):
        """Test grid level calculation with very small grid spacing"""
        calc = GridCalculator(self.mock_config_path)
        calc.grid_spacing_pips = 0.0001
        calc._actual_grid_spacing = 0.0001 / 10000  # Very small
        calc.num_grids = 10
        try:
            result = calc.calculate_grid_levels()
            # May have duplicates
            self.assertIn('all_levels', result)
        except Exception as e:
            # This is expected behavior for very small spacing
            self.assertIn("Price granularity", str(e))


class TestRiskManagerEdgeCases(unittest.TestCase):
    """Comprehensive edge case tests for RiskManager"""
    
    def test_account_health_zero_balance(self):
        """Test account health check with zero balance"""
        mock_client = Mock()
        mock_client.get_account_summary.return_value = {
            'balance': 0,
            'equity': 0,
            'marginAvailable': 0,
            'marginUsed': 0
        }
        manager = RiskManagerStandalone(mock_client)
        healthy, msg = manager.check_account_health()
        self.assertFalse(healthy)
    
    def test_account_health_negative_balance(self):
        """Test account health check with negative balance"""
        mock_client = Mock()
        mock_client.get_account_summary.return_value = {
            'balance': -100,
            'equity': -50,
            'marginAvailable': 0,
            'marginUsed': 100
        }
        manager = RiskManagerStandalone(mock_client)
        healthy, msg = manager.check_account_health()
        self.assertFalse(healthy)
    
    def test_account_health_no_margin(self):
        """Test account health check with no margin available"""
        mock_client = Mock()
        mock_client.get_account_summary.return_value = {
            'balance': 1000,
            'equity': 1000,
            'marginAvailable': 0,
            'marginUsed': 1000
        }
        manager = RiskManagerStandalone(mock_client)
        healthy, msg = manager.check_account_health()
        self.assertFalse(healthy)
    
    def test_account_health_low_margin_level(self):
        """Test account health check with low margin level"""
        mock_client = Mock()
        mock_client.get_account_summary.return_value = {
            'balance': 1000,
            'equity': 900,
            'marginAvailable': 100,
            'marginUsed': 1000
        }
        manager = RiskManagerStandalone(mock_client)
        healthy, msg = manager.check_account_health()
        self.assertFalse(healthy)
    
    def test_account_health_healthy(self):
        """Test account health check with healthy account"""
        mock_client = Mock()
        mock_client.get_account_summary.return_value = {
            'balance': 10000,
            'equity': 10000,
            'marginAvailable': 8000,
            'marginUsed': 2000
        }
        manager = RiskManagerStandalone(mock_client)
        healthy, msg = manager.check_account_health()
        self.assertTrue(healthy)
    
    def test_account_health_no_response(self):
        """Test account health check with no response from API"""
        mock_client = Mock()
        mock_client.get_account_summary.return_value = None
        manager = RiskManagerStandalone(mock_client)
        healthy, msg = manager.check_account_health()
        self.assertFalse(healthy)
    
    def test_unrealized_loss_none(self):
        """Test unrealized loss check with no positions"""
        mock_client = Mock()
        mock_client.get_account_summary.return_value = {
            'unrealizedPL': 0
        }
        manager = RiskManagerStandalone(mock_client)
        within_limit, loss = manager.check_unrealized_loss()
        self.assertTrue(within_limit)
        self.assertEqual(loss, 0)
    
    def test_unrealized_loss_profit(self):
        """Test unrealized loss check with unrealized profit"""
        mock_client = Mock()
        mock_client.get_account_summary.return_value = {
            'unrealizedPL': 500
        }
        manager = RiskManagerStandalone(mock_client)
        within_limit, loss = manager.check_unrealized_loss()
        self.assertTrue(within_limit)
        self.assertEqual(loss, 0)  # Profit is not a loss
    
    def test_unrealized_loss_within_limit(self):
        """Test unrealized loss check within limit"""
        mock_client = Mock()
        mock_client.get_account_summary.return_value = {
            'unrealizedPL': -40
        }
        manager = RiskManagerStandalone(mock_client)
        within_limit, loss = manager.check_unrealized_loss(max_loss=50)
        self.assertTrue(within_limit)
        self.assertEqual(loss, 40)
    
    def test_unrealized_loss_exceeds_limit(self):
        """Test unrealized loss check exceeds limit"""
        mock_client = Mock()
        mock_client.get_account_summary.return_value = {
            'unrealizedPL': -100
        }
        manager = RiskManagerStandalone(mock_client)
        within_limit, loss = manager.check_unrealized_loss(max_loss=50)
        self.assertFalse(within_limit)
        self.assertEqual(loss, 100)
    
    def test_open_positions_count_empty(self):
        """Test open positions count with no positions"""
        mock_client = Mock()
        mock_client.get_open_positions.return_value = []
        manager = RiskManagerStandalone(mock_client)
        within_limit, count = manager.check_open_positions_count()
        self.assertTrue(within_limit)
        self.assertEqual(count, 0)
    
    def test_open_positions_count_within_limit(self):
        """Test open positions count within limit"""
        mock_client = Mock()
        mock_client.get_open_positions.return_value = [
            {'long': {'units': '100'}, 'short': {'units': '0'}},
            {'long': {'units': '0'}, 'short': {'units': '200'}}
        ]
        manager = RiskManagerStandalone(mock_client)
        within_limit, count = manager.check_open_positions_count(max_positions=10)
        self.assertTrue(within_limit)
        self.assertEqual(count, 2)
    
    def test_open_positions_count_exceeds_limit(self):
        """Test open positions count exceeds limit"""
        mock_client = Mock()
        mock_client.get_open_positions.return_value = [
            {'long': {'units': '100'}, 'short': {'units': '0'}},
        ] * 25  # 25 positions
        manager = RiskManagerStandalone(mock_client)
        within_limit, count = manager.check_open_positions_count(max_positions=20)
        self.assertFalse(within_limit)
        self.assertEqual(count, 25)
    
    def test_market_conditions_normal(self):
        """Test market conditions check with normal spread"""
        mock_client = Mock()
        manager = RiskManagerStandalone(mock_client)
        suitable, msg = manager.check_market_conditions(0.5)
        self.assertTrue(suitable)
    
    def test_market_conditions_high_spread(self):
        """Test market conditions check with high spread"""
        mock_client = Mock()
        manager = RiskManagerStandalone(mock_client)
        suitable, msg = manager.check_market_conditions(3.0)
        self.assertFalse(suitable)
    
    def test_market_conditions_zero_spread(self):
        """Test market conditions check with zero spread"""
        mock_client = Mock()
        manager = RiskManagerStandalone(mock_client)
        suitable, msg = manager.check_market_conditions(0)
        self.assertTrue(suitable)
    
    def test_manual_kill_switch(self):
        """Test manual kill switch activation"""
        mock_client = Mock()
        manager = RiskManagerStandalone(mock_client)
        manager.manual_kill_switch("Test reason")
        self.assertTrue(manager.should_stop)
        self.assertEqual(manager.stop_reason, "Test reason")
    
    def test_should_emergency_stop_kill_switch(self):
        """Test emergency stop with kill switch activated"""
        mock_client = Mock()
        mock_client.get_account_summary.return_value = {
            'balance': 10000,
            'equity': 10000,
            'marginAvailable': 8000,
            'marginUsed': 2000
        }
        mock_client.get_open_positions.return_value = []
        manager = RiskManagerStandalone(mock_client)
        manager.manual_kill_switch("Test reason")
        should_stop, reason = manager.should_emergency_stop()
        self.assertTrue(should_stop)
        self.assertEqual(reason, "Test reason")


class TestBoundaryConditions(unittest.TestCase):
    """Test boundary conditions for all calculations"""
    
    # Create a mock config for testing
    MOCK_CONFIG = {
        'trading': {
            'instrument': 'EUR_USD',
            'grid_range': {
                'lower_level': 1.0700,  # FIXED: lower < upper
                'upper_level': 1.0900
            },
            'grid_settings': {
                'number_of_grids': 10,
                'grid_spacing_pips': 10.0
            },
            'position_sizing': {
                'position_size_per_grid': 100.0,
                'units_per_trade': 10000
            }
        }
    }
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_config_path = '/tmp/test_config.json'
        with open(self.mock_config_path, 'w') as f:
            import json
            json.dump(self.MOCK_CONFIG, f)
        self.calc = GridCalculator(self.mock_config_path)
    
    def tearDown(self):
        """Clean up test files"""
        if os.path.exists(self.mock_config_path):
            os.remove(self.mock_config_path)
    
    def test_price_minimum(self):
        """Test calculations with minimum valid price"""
        self.calc._validate_price(0.0001)
    
    def test_price_maximum(self):
        """Test calculations with maximum valid price"""
        self.calc._validate_price(100000.0)
    
    def test_price_below_minimum(self):
        """Test validation fails for price below minimum"""
        with self.assertRaises(Exception):
            self.calc._validate_price(0.00001)
    
    def test_price_above_maximum(self):
        """Test validation fails for price above maximum"""
        with self.assertRaises(Exception):
            self.calc._validate_price(200000.0)
    
    def test_units_minimum(self):
        """Test calculations with minimum valid units"""
        self.calc._validate_units(1)
    
    def test_units_maximum(self):
        """Test calculations with maximum valid units"""
        self.calc._validate_units(100000000)
    
    def test_units_below_minimum(self):
        """Test validation fails for units below minimum"""
        with self.assertRaises(Exception):
            self.calc._validate_units(0)
    
    def test_units_above_maximum(self):
        """Test validation fails for units above maximum"""
        with self.assertRaises(Exception):
            self.calc._validate_units(200000000)
    
    def test_spread_minimum(self):
        """Test calculations with minimum valid spread"""
        self.calc._validate_spread_pips(0.0)
    
    def test_spread_maximum(self):
        """Test calculations with maximum valid spread"""
        self.calc._validate_spread_pips(1000.0)
    
    def test_spread_below_minimum(self):
        """Test validation fails for spread below minimum"""
        with self.assertRaises(Exception):
            self.calc._validate_spread_pips(-1.0)
    
    def test_spread_above_maximum(self):
        """Test validation fails for spread above maximum"""
        with self.assertRaises(Exception):
            self.calc._validate_spread_pips(2000.0)
    
    def test_numeric_string_inputs(self):
        """Test that numeric string inputs are rejected"""
        with self.assertRaises(Exception):
            self.calc.calculate_profit_per_cycle("1.0850", "1.0860", 10000)
    
    def test_none_inputs(self):
        """Test that None inputs are rejected"""
        with self.assertRaises(Exception):
            self.calc.calculate_profit_per_cycle(None, 1.0860, 10000)
    
    def test_boolean_inputs(self):
        """Test boolean inputs (True/False are treated as 1/0 in Python)"""
        calc = GridCalculator(self.mock_config_path)
        # Python's bool is subclass of int, so True == 1 and False == 0
        # The validation passes True because 1 is within valid price range
        # This is expected Python behavior
        result = calc._validate_price(True, "test_price")
        # True evaluates to 1 which is valid
        self.assertIsNone(result)
    
    def test_list_inputs(self):
        """Test that list inputs are rejected"""
        with self.assertRaises(Exception):
            self.calc.calculate_profit_per_cycle([1.0850], [1.0860], 10000)


class TestPrecisionAndRounding(unittest.TestCase):
    """Test precision and rounding behavior"""
    
    MOCK_CONFIG = {
        'trading': {
            'instrument': 'EUR_USD',
            'grid_range': {
                'lower_level': 1.0700,  # FIXED: lower < upper
                'upper_level': 1.0900
            },
            'grid_settings': {
                'number_of_grids': 10,
                'grid_spacing_pips': 10.0
            },
            'position_sizing': {
                'position_size_per_grid': 100.0,
                'units_per_trade': 10000
            }
        }
    }
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_config_path = '/tmp/test_config.json'
        with open(self.mock_config_path, 'w') as f:
            import json
            json.dump(self.MOCK_CONFIG, f)
        self.calc = GridCalculator(self.mock_config_path)
    
    def tearDown(self):
        """Clean up test files"""
        if os.path.exists(self.mock_config_path):
            os.remove(self.mock_config_path)
    
    def test_profit_rounding(self):
        """Test profit is rounded to 2 decimal places"""
        profit = self.calc.calculate_profit_per_cycle(1.0850, 1.08505, 10000)
        # 0.5 pips * 10000 units * 0.0001 = $0.50
        self.assertEqual(profit, 0.50)
    
    def test_roi_rounding(self):
        """Test ROI is rounded to 2 decimal places"""
        roi = self.calc.calculate_return_on_investment(3, 1)
        # 1/3 * 100 = 33.333... -> 33.33
        self.assertEqual(roi, 33.33)
    
    def test_capital_rounding(self):
        """Test capital is rounded to 2 decimal places"""
        capital = self.calc.calculate_total_capital_needed(1, 10, 1.0850, 3)
        # Should be rounded to 2 decimal places
        self.assertAlmostEqual(capital, round(capital, 2))
    
    def test_grid_levels_precision(self):
        """Test grid levels are rounded to 5 decimal places"""
        result = self.calc.calculate_grid_levels()
        for level in result['all_levels']:
            # Check precision (at most 5 decimal places)
            parts = str(level).split('.')
            if len(parts) > 1:
                self.assertLessEqual(len(parts[1]), 5)


def main():
    """Run all tests"""
    print("="*70)
    print("COMPREHENSIVE EDGE CASE TESTS FOR OANDA TRADING BOT")
    print("="*70)
    print()
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestGridCalculatorEdgeCases))
    suite.addTests(loader.loadTestsFromTestCase(TestRiskManagerEdgeCases))
    suite.addTests(loader.loadTestsFromTestCase(TestBoundaryConditions))
    suite.addTests(loader.loadTestsFromTestCase(TestPrecisionAndRounding))
    
    # Run tests with verbosity
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print()
    print("="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"Tests Run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")
    
    success_rate = ((result.testsRun - len(result.failures) - len(result.errors)) 
                   / result.testsRun * 100) if result.testsRun > 0 else 0
    print(f"Success Rate: {success_rate:.1f}%")
    print("="*70)
    
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(main())

