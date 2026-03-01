from typing import Dict, Any, Optional, List
from .CommTrade import CommTrade, Order, Position
import time
import json
import os

class SimTrade(CommTrade):
    """模拟交易"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """初始化
        
        Args:
            config: 交易配置
        """
        super().__init__(config)
        self.orders = {}
        self.positions = {}
        self.balance = self.config.get('initial_balance', 1000000)
        self.transaction_fee = self.config.get('transaction_fee', 0.0003)
        self.data_dir = self.config.get('data_dir', './data')
        self._load_data()
    
    def _load_data(self):
        """加载数据"""
        # 加载订单数据
        order_file = os.path.join(self.data_dir, 'sim_orders.json')
        if os.path.exists(order_file):
            try:
                with open(order_file, 'r') as f:
                    orders_data = json.load(f)
                    for order_id, order_data in orders_data.items():
                        self.orders[order_id] = Order(**order_data)
            except Exception as e:
                print(f"Load orders error: {e}")
        
        # 加载持仓数据
        position_file = os.path.join(self.data_dir, 'sim_positions.json')
        if os.path.exists(position_file):
            try:
                with open(position_file, 'r') as f:
                    positions_data = json.load(f)
                    for code, position_data in positions_data.items():
                        self.positions[code] = Position(**position_data)
            except Exception as e:
                print(f"Load positions error: {e}")
        
        # 加载资金数据
        balance_file = os.path.join(self.data_dir, 'sim_balance.json')
        if os.path.exists(balance_file):
            try:
                with open(balance_file, 'r') as f:
                    balance_data = json.load(f)
                    self.balance = balance_data.get('balance', self.balance)
            except Exception as e:
                print(f"Load balance error: {e}")
    
    def _save_data(self):
        """保存数据"""
        # 确保数据目录存在
        os.makedirs(self.data_dir, exist_ok=True)
        
        # 保存订单数据
        order_file = os.path.join(self.data_dir, 'sim_orders.json')
        try:
            orders_data = {order_id: order.__dict__ for order_id, order in self.orders.items()}
            with open(order_file, 'w') as f:
                json.dump(orders_data, f, indent=2)
        except Exception as e:
            print(f"Save orders error: {e}")
        
        # 保存持仓数据
        position_file = os.path.join(self.data_dir, 'sim_positions.json')
        try:
            positions_data = {code: position.__dict__ for code, position in self.positions.items()}
            with open(position_file, 'w') as f:
                json.dump(positions_data, f, indent=2)
        except Exception as e:
            print(f"Save positions error: {e}")
        
        # 保存资金数据
        balance_file = os.path.join(self.data_dir, 'sim_balance.json')
        try:
            balance_data = {'balance': self.balance}
            with open(balance_file, 'w') as f:
                json.dump(balance_data, f, indent=2)
        except Exception as e:
            print(f"Save balance error: {e}")
    
    def connect(self) -> bool:
        """连接交易接口
        
        Returns:
            是否连接成功
        """
        print("SimTrade connected")
        return True
    
    def disconnect(self) -> bool:
        """断开连接
        
        Returns:
            是否断开成功
        """
        self._save_data()
        print("SimTrade disconnected")
        return True
    
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
        # 计算交易金额
        amount = price * volume
        fee = amount * self.transaction_fee
        total_amount = amount + fee
        
        # 检查资金或持仓
        if order_type == 'buy':
            if self.balance < total_amount:
                print(f"Insufficient balance: {self.balance} < {total_amount}")
                return None
        else:
            if code not in self.positions or self.positions[code].volume < volume:
                print(f"Insufficient position: {self.positions.get(code, {}).get('volume', 0)} < {volume}")
                return None
        
        # 生成订单ID
        order_id = f"order_{int(time.time() * 1000)}"
        
        # 创建订单
        order = Order(
            order_id=order_id,
            code=code,
            price=price,
            volume=volume,
            order_type=order_type,
            status='filled',  # 模拟交易直接成交
            timestamp=time.strftime('%Y-%m-%d %H:%M:%S')
        )
        
        # 更新资金和持仓
        if order_type == 'buy':
            self.balance -= total_amount
            if code in self.positions:
                # 已有持仓，更新成本价
                position = self.positions[code]
                new_volume = position.volume + volume
                new_cost_price = (position.cost_price * position.volume + amount) / new_volume
                self.positions[code] = Position(
                    code=code,
                    volume=new_volume,
                    cost_price=new_cost_price,
                    current_price=price,
                    profit=(price - new_cost_price) * new_volume
                )
            else:
                # 新持仓
                self.positions[code] = Position(
                    code=code,
                    volume=volume,
                    cost_price=price,
                    current_price=price,
                    profit=0
                )
        else:
            # 卖出
            position = self.positions[code]
            profit = (price - position.cost_price) * volume
            self.balance += amount - fee
            
            # 更新持仓
            new_volume = position.volume - volume
            if new_volume > 0:
                self.positions[code] = Position(
                    code=code,
                    volume=new_volume,
                    cost_price=position.cost_price,
                    current_price=price,
                    profit=(price - position.cost_price) * new_volume
                )
            else:
                # 清空持仓
                del self.positions[code]
        
        # 保存订单
        self.orders[order_id] = order
        self._save_data()
        
        print(f"Order placed: {order_id}, {order_type} {volume} {code} at {price}")
        return order_id
    
    def cancel_order(self, order_id: str) -> bool:
        """撤单
        
        Args:
            order_id: 订单ID
            
        Returns:
            是否撤单成功
        """
        if order_id in self.orders:
            order = self.orders[order_id]
            if order.status == 'pending':
                order.status = 'cancelled'
                self._save_data()
                print(f"Order cancelled: {order_id}")
                return True
        return False
    
    def get_order_status(self, order_id: str) -> Optional[Dict[str, Any]]:
        """获取订单状态
        
        Args:
            order_id: 订单ID
            
        Returns:
            订单状态
        """
        if order_id in self.orders:
            return self.orders[order_id].__dict__
        return None
    
    def get_positions(self) -> List[Position]:
        """获取持仓
        
        Returns:
            持仓列表
        """
        return list(self.positions.values())
    
    def get_balance(self) -> Optional[Dict[str, Any]]:
        """获取资金余额
        
        Returns:
            资金余额
        """
        return {
            'balance': self.balance,
            'available': self.balance
        }
    
    def update_position_price(self, code: str, price: float):
        """更新持仓价格
        
        Args:
            code: 股票代码
            price: 当前价格
        """
        if code in self.positions:
            position = self.positions[code]
            self.positions[code] = Position(
                code=code,
                volume=position.volume,
                cost_price=position.cost_price,
                current_price=price,
                profit=(price - position.cost_price) * position.volume
            )
            self._save_data()

if __name__ == '__main__':
    # 示例：使用模拟交易
    trade = SimTrade({'initial_balance': 1000000})
    trade.connect()
    
    # 买入
    order_id = trade.place_order('600000', 10.0, 1000, 'buy')
    print(f"Buy order ID: {order_id}")
    
    # 卖出
    order_id = trade.place_order('600000', 11.0, 500, 'sell')
    print(f"Sell order ID: {order_id}")
    
    # 获取持仓
    positions = trade.get_positions()
    print("Positions:")
    for pos in positions:
        print(pos)
    
    # 获取资金
    balance = trade.get_balance()
    print(f"Balance: {balance}")
    
    trade.disconnect()