from typing import Dict, Any, Optional, List
from .CommTrade import CommTrade, Order, Position
from Config.EnvConfig import env

class FutuTrade(CommTrade):
    """富途交易接口"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """初始化
        
        Args:
            config: 交易配置
        """
        super().__init__(config)
        self.api = None
        self._init_api()
    
    def _init_api(self):
        """初始化API"""
        try:
            from futu import OpenTradeContext
            
            # 从配置获取参数
            host = self.config.get('host', '127.0.0.1')
            port = self.config.get('port', 11111)
            
            # 初始化交易接口
            self.api = OpenTradeContext(host=host, port=port)
        except ImportError:
            print("Futu API not installed, please install futu-api")
        except Exception as e:
            print(f"Init Futu API error: {e}")
    
    def connect(self) -> bool:
        """连接交易接口
        
        Returns:
            是否连接成功
        """
        if self.api:
            print("FutuTrade connected")
            return True
        return False
    
    def disconnect(self) -> bool:
        """断开连接
        
        Returns:
            是否断开成功
        """
        if self.api:
            try:
                self.api.close()
                print("FutuTrade disconnected")
                return True
            except Exception as e:
                print(f"Disconnect error: {e}")
        return False
    
    def place_order(self, code: str, price: float, volume: int, order_type: str) -> Optional[str]:
        """下单
        
        Args:
            code: 股票代码
            price: 价格
            volume: 数量
            order_type: 订单类型 ('buy' or 'sell')
            
        Returns:
            订单ID
        """
        if not self.api:
            return None
        
        try:
            # 格式化代码
            futu_code = self.format_code(code)
            
            # 下单
            ret, data = self.api.place_order(
                price=price,
                qty=volume,
                code=futu_code,
                trd_side='BUY' if order_type == 'buy' else 'SELL',
                order_type='NORMAL',
                adjust_limit=0,
                time_in_force='DAY'
            )
            
            if ret == 0 and not data.empty:
                order_id = data.iloc[0]['order_id']
                print(f"Order placed: {order_id}, {order_type} {volume} {code} at {price}")
                return order_id
            else:
                print(f"Place order failed: {data}")
                return None
        except Exception as e:
            print(f"Place order error: {e}")
            return None
    
    def cancel_order(self, order_id: str) -> bool:
        """撤单
        
        Args:
            order_id: 订单ID
            
        Returns:
            是否撤单成功
        """
        if not self.api:
            return False
        
        try:
            ret, data = self.api.cancel_order(order_id=order_id)
            if ret == 0:
                print(f"Order cancelled: {order_id}")
                return True
            else:
                print(f"Cancel order failed: {data}")
                return False
        except Exception as e:
            print(f"Cancel order error: {e}")
            return False
    
    def get_order_status(self, order_id: str) -> Optional[Dict[str, Any]]:
        """获取订单状态
        
        Args:
            order_id: 订单ID
            
        Returns:
            订单状态
        """
        if not self.api:
            return None
        
        try:
            ret, data = self.api.query_order_list(order_id=order_id)
            if ret == 0 and not data.empty:
                order_data = data.iloc[0].to_dict()
                return {
                    'order_id': order_data.get('order_id'),
                    'code': order_data.get('code'),
                    'price': order_data.get('price'),
                    'volume': order_data.get('qty'),
                    'order_type': 'buy' if order_data.get('trd_side') == 'BUY' else 'sell',
                    'status': order_data.get('order_status'),
                    'timestamp': order_data.get('create_time')
                }
            return None
        except Exception as e:
            print(f"Get order status error: {e}")
            return None
    
    def get_positions(self) -> List[Position]:
        """获取持仓
        
        Returns:
            持仓列表
        """
        if not self.api:
            return []
        
        try:
            ret, data = self.api.position_list()
            if ret == 0 and not data.empty:
                positions = []
                for _, row in data.iterrows():
                    position = Position(
                        code=row.get('code'),
                        volume=row.get('qty'),
                        cost_price=row.get('cost_price'),
                        current_price=row.get('cur_price'),
                        profit=row.get('unrealized_pl')
                    )
                    positions.append(position)
                return positions
            return []
        except Exception as e:
            print(f"Get positions error: {e}")
            return []
    
    def get_balance(self) -> Optional[Dict[str, Any]]:
        """获取资金余额
        
        Returns:
            资金余额
        """
        if not self.api:
            return None
        
        try:
            ret, data = self.api.accinfo_query()
            if ret == 0 and not data.empty:
                balance_data = data.iloc[0].to_dict()
                return {
                    'balance': balance_data.get('total_assets'),
                    'available': balance_data.get('available_cash')
                }
            return None
        except Exception as e:
            print(f"Get balance error: {e}")
            return None
    
    def format_code(self, code: str) -> str:
        """格式化股票代码
        
        Args:
            code: 原始股票代码
            
        Returns:
            格式化后的股票代码
        """
        # 根据代码长度判断市场
        if len(code) == 6:
            return f"HK.{code}"  # 港股
        elif len(code) == 5:
            return f"HK.{code}"  # 港股
        elif code.isdigit():
            return f"US.{code}"  # 美股
        return code