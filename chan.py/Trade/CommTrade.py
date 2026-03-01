from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

@dataclass
class Order:
    """订单类"""
    order_id: str
    code: str
    price: float
    volume: int
    order_type: str  # 'buy' or 'sell'
    status: str  # 'pending', 'filled', 'cancelled'
    timestamp: str

@dataclass
class Position:
    """持仓类"""
    code: str
    volume: int
    cost_price: float
    current_price: float
    profit: float

class CommTrade(ABC):
    """通用交易接口"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """初始化
        
        Args:
            config: 交易配置
        """
        self.config = config or {}
    
    @abstractmethod
    def connect(self) -> bool:
        """连接交易接口
        
        Returns:
            是否连接成功
        """
        pass
    
    @abstractmethod
    def disconnect(self) -> bool:
        """断开连接
        
        Returns:
            是否断开成功
        """
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
    def cancel_order(self, order_id: str) -> bool:
        """撤单
        
        Args:
            order_id: 订单ID
            
        Returns:
            是否撤单成功
        """
        pass
    
    @abstractmethod
    def get_order_status(self, order_id: str) -> Optional[Dict[str, Any]]:
        """获取订单状态
        
        Args:
            order_id: 订单ID
            
        Returns:
            订单状态
        """
        pass
    
    @abstractmethod
    def get_positions(self) -> List[Position]:
        """获取持仓
        
        Returns:
            持仓列表
        """
        pass
    
    @abstractmethod
    def get_balance(self) -> Optional[Dict[str, Any]]:
        """获取资金余额
        
        Returns:
            资金余额
        """
        pass
    
    def format_code(self, code: str) -> str:
        """格式化股票代码
        
        Args:
            code: 原始股票代码
            
        Returns:
            格式化后的股票代码
        """
        return code
    
    def calculate_profit(self, cost_price: float, current_price: float, volume: int) -> float:
        """计算盈亏
        
        Args:
            cost_price: 成本价
            current_price: 当前价
            volume: 数量
            
        Returns:
            盈亏金额
        """
        return (current_price - cost_price) * volume