"""
Order Manager Module.
Handles order placement, modification, and management on OANDA.
"""
from typing import Dict, List
from src.connectors.oanda_client import OandaClient
from src.utils.logger import logger


class OrderManager:
    """Handles order placement and management."""
    
    def __init__(self, oanda_client: OandaClient):
        """
        Initialize OrderManager.
        
        Args:
            oanda_client: OandaClient instance
        """
        self.client = oanda_client
        self.account_id = oanda_client.account_id
    
    def place_limit_order(self, instrument: str, units: int, price: float, 
                         order_type: str = "BUY", stop_loss: float = None,
                         take_profit: float = None) -> Dict:
        """
        Place a limit order.
        
        Args:
            instrument: Currency pair (e.g., 'EUR_USD')
            units: Number of units to trade
            price: Limit price
            order_type: 'BUY' or 'SELL'
            stop_loss: Optional stop loss price
            take_profit: Optional take profit price
            
        Returns:
            Order response from API
        """
        try:
            order_data = {
                "order": {
                    "instrument": instrument,
                    "units": units if order_type == "BUY" else -units,
                    "price": str(round(price, 5)),
                    "type": "LIMIT",
                    "timeInForce": "GTC"  # Good till cancelled
                }
            }
            
            if stop_loss:
                order_data["order"]["stopLossOnFill"] = {
                    "price": str(round(stop_loss, 5))
                }
            
            if take_profit:
                order_data["order"]["takeProfitOnFill"] = {
                    "price": str(round(take_profit, 5))
                }
            
            response = self.client.place_limit_order(instrument, units, price, take_profit, stop_loss)
            
            if "orderFillTransaction" in response or "orderCreateTransaction" in response:
                logger.info(f"Limit order placed: {order_type}")
                logger.info(f"  Instrument: {instrument}")
                logger.info(f"  Units: {units}")
                logger.info(f"  Price: {price}")
                return response
            else:
                logger.error(f"Failed to place order: {response}")
                return response
        
        except Exception as e:
            logger.error(f"Error placing limit order: {str(e)}")
            return {"error": str(e)}
    
    def place_market_order(self, instrument: str, units: int, order_type: str = "BUY",
                         stop_loss: float = None, take_profit: float = None) -> Dict:
        """
        Place a market order (executes immediately).
        
        Args:
            instrument: Currency pair
            units: Number of units
            order_type: 'BUY' or 'SELL'
            stop_loss: Optional stop loss
            take_profit: Optional take profit
            
        Returns:
            Order response
        """
        try:
            response = self.client.place_market_order(instrument, units)
            
            if "orderFillTransaction" in response:
                logger.info(f"Market order executed: {order_type}")
                logger.info(f"  Instrument: {instrument}")
                logger.info(f"  Units: {units}")
                return response
            else:
                logger.error(f"Failed to place market order: {response}")
                return response
        
        except Exception as e:
            logger.error(f"Error placing market order: {str(e)}")
            return {"error": str(e)}
    
    def get_pending_orders(self) -> List[Dict]:
        """
        Get all pending orders.
        
        Returns:
            List of pending orders
        """
        try:
            response = self.client.get_pending_orders()
            
            if "orders" in response:
                pending = [o for o in response["orders"] if o["state"] == "PENDING"]
                logger.info(f"Found {len(pending)} pending orders")
                return pending
            else:
                logger.error(f"Failed to fetch orders: {response}")
                return []
        
        except Exception as e:
            logger.error(f"Error fetching pending orders: {str(e)}")
            return []
    
    def cancel_order(self, order_id: str) -> bool:
        """
        Cancel a pending order.
        
        Args:
            order_id: Order ID to cancel
            
        Returns:
            True if successful
        """
        try:
            response = self.client.cancel_order(order_id)
            
            if "orderCancelTransaction" in response:
                logger.info(f"Order {order_id} cancelled")
                return True
            else:
                logger.error(f"Failed to cancel order: {response}")
                return False
        
        except Exception as e:
            logger.error(f"Error cancelling order: {str(e)}")
            return False
    
    def cancel_all_orders(self) -> int:
        """
        Cancel all pending orders.
        
        Returns:
            Number of orders cancelled
        """
        pending = self.get_pending_orders()
        cancelled_count = 0
        
        for order in pending:
            if self.cancel_order(order["id"]):
                cancelled_count += 1
        
        logger.info(f"Cancelled {cancelled_count} orders")
        return cancelled_count
    
    def place_grid_buy_orders(self, instrument: str, buy_levels: List[float],
                             units: int) -> List[Dict]:
        """
        Place grid buy orders at specified levels.
        
        Args:
            instrument: Currency pair
            buy_levels: List of price levels to buy at
            units: Units per order
            
        Returns:
            List of order responses
        """
        orders = []
        logger.info(f"Placing {len(buy_levels)} BUY grid orders...")
        
        for i, price in enumerate(buy_levels, 1):
            order = self.place_limit_order(instrument, units, price, "BUY")
            orders.append(order)
            logger.info(f"  [{i}/{len(buy_levels)}] BUY at {price}")
        
        return orders
    
    def place_grid_sell_orders(self, instrument: str, sell_levels: List[float],
                              units: int) -> List[Dict]:
        """
        Place grid sell orders at specified levels.
        
        Args:
            instrument: Currency pair
            sell_levels: List of price levels to sell at
            units: Units per order
            
        Returns:
            List of order responses
        """
        orders = []
        logger.info(f"Placing {len(sell_levels)} SELL grid orders...")
        
        for i, price in enumerate(sell_levels, 1):
            order = self.place_limit_order(instrument, units, price, "SELL")
            orders.append(order)
            logger.info(f"  [{i}/{len(sell_levels)}] SELL at {price}")
        
        return orders
    
    def get_open_positions(self) -> List[Dict]:
        """
        Get all open positions.
        
        Returns:
            List of open positions
        """
        try:
            response = self.client.get_open_positions()
            
            if "positions" in response:
                open_positions = [p for p in response["positions"] 
                                 if float(p["long"]["units"]) != 0 or float(p["short"]["units"]) != 0]
                logger.info(f"Found {len(open_positions)} open positions")
                return open_positions
            else:
                return []
        
        except Exception as e:
            logger.error(f"Error fetching open positions: {str(e)}")
            return []
    
    def get_position_by_instrument(self, instrument: str) -> Dict:
        """
        Get position for a specific instrument.
        
        Args:
            instrument: Currency pair
            
        Returns:
            Position details
        """
        positions = self.get_open_positions()
        
        for position in positions:
            if position["instrument"] == instrument:
                return position
        
        return {}
    
    def close_position(self, instrument: str) -> Dict:
        """
        Close all positions for an instrument.
        
        Args:
            instrument: Currency pair
            
        Returns:
            Close response
        """
        try:
            response = self.client.close_position(instrument)
            logger.info(f"Closed all positions for {instrument}")
            return response
        
        except Exception as e:
            logger.error(f"Error closing position: {str(e)}")
            return {"error": str(e)}

