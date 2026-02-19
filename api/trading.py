"""
Vercel API endpoint for trading operations.
Provides HTTP endpoints for the grid trading bot.
"""
import os
import json
from datetime import datetime
from flask import Flask, request, jsonify
from functools import wraps

app = Flask(__name__)

# Load environment variables
from dotenv import load_dotenv
load_dotenv()


def require_auth(f):
    """Decorator to require API key authentication."""
    @wraps(f)
    def decorated(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        expected_key = os.getenv('API_KEY', 'dev_key_change_in_production')
        
        if api_key != expected_key:
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated


def get_client():
    """Get OANDA client instance."""
    from src.connectors.oanda_client import OandaClient
    return OandaClient()


def get_order_manager():
    """Get order manager instance."""
    from src.managers.order_manager import OrderManager
    return OrderManager(get_client())


def get_risk_manager():
    """Get risk manager instance."""
    from src.managers.risk_manager import RiskManager
    return RiskManager(get_client())


def get_strategy():
    """Get grid strategy instance."""
    from src.strategies.grid_strategy import GridStrategy
    return GridStrategy()


@app.route('/', methods=['GET'])
def root():
    """Root endpoint - redirects to API info."""
    return jsonify({
        'service': 'OANDA Grid Trading Bot API',
        'version': '1.0.0',
        'endpoints': {
            'health': '/api/health',
            'calculator_profit': '/api/calculator/profit (POST)',
            'calculator_capital': '/api/calculator/capital (POST)',
            'status': '/api/status (requires auth)',
            'account': '/api/account (requires auth)',
            'positions': '/api/positions (requires auth)',
            'orders': '/api/orders (requires auth)',
            'grid_init': '/api/grid/init (POST, requires auth)',
            'grid_levels': '/api/grid/levels (GET, requires auth)',
            'safety_check': '/api/safety/check (GET, requires auth)',
            'price': '/api/price/{instrument} (GET, requires auth)'
        },
        'docs': 'See VERCEL_DEPLOY.md for more details'
    })


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'OANDA Grid Trading Bot'
    })


@app.route('/api/status', methods=['GET'])
@require_auth
def get_status():
    """Get current bot status."""
    try:
        client = get_client()
        
        # Get account info
        account = client.get_account_summary()
        
        # Get positions
        positions = client.get_open_positions()
        
        # Get pending orders
        pending = client.get_pending_orders()
        
        return jsonify({
            'success': True,
            'data': {
                'account': account,
                'positions': positions,
                'pending_orders': pending,
                'timestamp': datetime.now().isoformat()
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/account', methods=['GET'])
@require_auth
def get_account():
    """Get account information."""
    try:
        client = get_client()
        account = client.get_account_summary()
        
        return jsonify({
            'success': True,
            'data': account
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/positions', methods=['GET'])
@require_auth
def get_positions():
    """Get open positions."""
    try:
        client = get_client()
        positions = client.get_open_positions()
        
        return jsonify({
            'success': True,
            'data': positions
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/orders', methods=['GET'])
@require_auth
def get_orders():
    """Get pending orders."""
    try:
        client = get_client()
        orders = client.get_pending_orders()
        
        return jsonify({
            'success': True,
            'data': orders
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/orders', methods=['POST'])
@require_auth
def place_order():
    """Place a new order."""
    try:
        data = request.get_json()
        
        instrument = data.get('instrument', 'EUR_USD')
        units = data.get('units')
        order_type = data.get('order_type', 'BUY')  # BUY or SELL
        price = data.get('price')
        stop_loss = data.get('stop_loss')
        take_profit = data.get('take_profit')
        
        if not units or not price:
            return jsonify({
                'success': False,
                'error': 'units and price are required'
            }), 400
        
        client = get_client()
        order_manager = get_order_manager()
        
        # Validate order placement
        risk_manager = get_risk_manager()
        is_valid, message = risk_manager.validate_order_placement(
            units=units,
            price=price,
            max_margin_percent=50.0
        )
        
        if not is_valid:
            return jsonify({
                'success': False,
                'error': message
            }), 400
        
        # Place the order
        result = order_manager.place_limit_order(
            instrument=instrument,
            units=units,
            price=price,
            order_type=order_type,
            stop_loss=stop_loss,
            take_profit=take_profit
        )
        
        return jsonify({
            'success': True,
            'data': result
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/orders/<order_id>', methods=['DELETE'])
@require_auth
def cancel_order(order_id):
    """Cancel a specific order."""
    try:
        client = get_client()
        result = client.cancel_order(order_id)
        
        return jsonify({
            'success': True,
            'data': result
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/orders/cancel-all', methods=['POST'])
@require_auth
def cancel_all_orders():
    """Cancel all pending orders."""
    try:
        order_manager = get_order_manager()
        count = order_manager.cancel_all_orders()
        
        return jsonify({
            'success': True,
            'data': {
                'cancelled_count': count
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/grid/init', methods=['POST'])
@require_auth
def initialize_grid():
    """Initialize grid orders."""
    try:
        client = get_client()
        strategy = get_strategy()
        order_manager = get_order_manager()
        
        # Get current price
        instrument = request.json.get('instrument', 'EUR_USD') if request.json else 'EUR_USD'
        price_data = client.get_current_price(instrument)
        current_price = price_data['mid']
        
        # Calculate grid levels
        grid_levels = strategy.calculate_grid_levels(current_price)
        buy_levels = grid_levels['buy_levels']
        sell_levels = grid_levels['sell_levels']
        
        # Cancel existing orders
        order_manager.cancel_all_orders()
        
        # Place buy orders
        buy_orders = order_manager.place_grid_buy_orders(
            instrument,
            buy_levels,
            strategy.position_size
        )
        
        # Place sell orders
        sell_orders = order_manager.place_grid_sell_orders(
            instrument,
            sell_levels,
            strategy.position_size
        )
        
        return jsonify({
            'success': True,
            'data': {
                'buy_orders': len(buy_orders),
                'sell_orders': len(sell_orders),
                'total_orders': len(buy_orders) + len(sell_orders),
                'grid_levels': grid_levels
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/grid/levels', methods=['GET'])
@require_auth
def get_grid_levels():
    """Get current grid levels."""
    try:
        client = get_client()
        strategy = get_strategy()
        
        instrument = request.args.get('instrument', 'EUR_USD')
        price_data = client.get_current_price(instrument)
        current_price = price_data['mid']
        
        grid_levels = strategy.calculate_grid_levels(current_price)
        
        return jsonify({
            'success': True,
            'data': grid_levels
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/safety/check', methods=['GET'])
@require_auth
def safety_check():
    """Run safety checks."""
    try:
        risk_manager = get_risk_manager()
        
        # Check account health
        healthy, reason = risk_manager.check_account_health()
        
        # Check unrealized loss
        within_limit, loss = risk_manager.check_unrealized_loss(max_loss=50.0)
        
        # Check positions count
        positions_ok, count = risk_manager.check_open_positions_count(max_positions=20)
        
        # Full safety check
        all_safe, issues = risk_manager.check_all_safety_conditions(
            max_loss=50.0,
            max_positions=20
        )
        
        return jsonify({
            'success': True,
            'data': {
                'account_healthy': healthy,
                'health_reason': reason,
                'within_loss_limit': within_limit,
                'unrealized_loss': loss,
                'positions_within_limit': positions_ok,
                'positions_count': count,
                'all_safe': all_safe,
                'issues': issues
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/price/<instrument>', methods=['GET'])
@require_auth
def get_price(instrument):
    """Get current price for an instrument."""
    try:
        client = get_client()
        price_data = client.get_current_price(instrument)
        
        return jsonify({
            'success': True,
            'data': price_data
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/calculator/profit', methods=['POST'])
def calculate_profit():
    """Calculate profit for a trade."""
    try:
        data = request.get_json()
        
        entry_price = data.get('entry_price')
        exit_price = data.get('exit_price')
        units = data.get('units')
        
        if not all([entry_price, exit_price, units]):
            return jsonify({
                'success': False,
                'error': 'entry_price, exit_price, and units are required'
            }), 400
        
        from grid_calculator import GridCalculator
        
        # Create temporary config for calculator
        config = {
            'trading': {
                'instrument': 'EUR_USD',
                'grid_range': {'lower_level': 1.0700, 'upper_level': 1.0900},
                'grid_settings': {'number_of_grids': 10, 'grid_spacing_pips': 20},
                'position_sizing': {'position_size_per_grid': 100, 'units_per_trade': 1000}
            },
            'safety': {
                'max_loss_usd': 50.0,
                'max_open_positions': 20,
                'stop_loss_distance_pips': 50,
                'take_profit_distance_pips': 100
            },
            'oanda': {
                'environment': 'practice',
                'api_token': 'test_token',
                'account_id': 'test_account'
            }
        }
        
        import tempfile
        import json
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config, f)
            config_path = f.name
        
        calculator = GridCalculator(config_path)
        
        gross_profit = calculator.calculate_profit_per_cycle(
            entry_price, exit_price, units
        )
        
        spread_pips = data.get('spread_pips', 0)
        net_profit = calculator.calculate_net_profit_per_cycle(
            entry_price, exit_price, units, spread_pips
        )
        
        # Clean up
        os.unlink(config_path)
        
        return jsonify({
            'success': True,
            'data': {
                'gross_profit': gross_profit,
                'net_profit': net_profit,
                'spread_cost': spread_pips * units * 0.0001 if spread_pips else 0
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/calculator/capital', methods=['POST'])
def calculate_capital():
    """Calculate required capital."""
    try:
        data = request.get_json()
        
        units_per_trade = data.get('units_per_trade', 1000)
        num_grids = data.get('num_grids', 10)
        price = data.get('price', 1.0800)
        leverage = data.get('leverage', 1.0)
        
        from grid_calculator import GridCalculator
        
        config = {
            'trading': {
                'instrument': 'EUR_USD',
                'grid_range': {'lower_level': 1.0700, 'upper_level': 1.0900},
                'grid_settings': {'number_of_grids': 10, 'grid_spacing_pips': 20},
                'position_sizing': {'position_size_per_grid': 100, 'units_per_trade': 1000}
            },
            'safety': {'max_loss_usd': 50.0},
            'oanda': {'environment': 'practice'}
        }
        
        import tempfile
        import json
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config, f)
            config_path = f.name
        
        calculator = GridCalculator(config_path)
        
        capital = calculator.calculate_total_capital_needed(
            units_per_trade, num_grids, price, leverage
        )
        
        os.unlink(config_path)
        
        return jsonify({
            'success': True,
            'data': {
                'required_capital': capital,
                'units_per_trade': units_per_trade,
                'num_grids': num_grids,
                'price': price,
                'leverage': leverage
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# For local development
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

