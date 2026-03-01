from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class Strategy(ABC):
    """策略抽象基类"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """初始化策略
        
        Args:
            config: 策略配置参数
        """
        self.config = config or {}
        self.strict_open = self.config.get('strict_open', True)
        self.use_qjt = self.config.get('use_qjt', True)
        self.short_shelling = self.config.get('short_shelling', True)
        self.judge_on_close = self.config.get('judge_on_close', True)
        self.max_sl_rate = self.config.get('max_sl_rate', None)
        self.max_profit_rate = self.config.get('max_profit_rate', None)
    
    @abstractmethod
    def get_buy_signal(self, chan) -> List[Dict[str, Any]]:
        """获取买入信号
        
        Args:
            chan: 缠论对象
            
        Returns:
            买入信号列表
        """
        pass
    
    @abstractmethod
    def get_sell_signal(self, chan) -> List[Dict[str, Any]]:
        """获取卖出信号
        
        Args:
            chan: 缠论对象
            
        Returns:
            卖出信号列表
        """
        pass
    
    def get_cover_signal(self, chan, open_signal) -> Optional[Dict[str, Any]]:
        """获取平仓信号
        
        Args:
            chan: 缠论对象
            open_signal: 开仓信号
            
        Returns:
            平仓信号
        """
        pass
    
    def is_active(self, chan) -> bool:
        """判断股票是否活跃
        
        Args:
            chan: 缠论对象
            
        Returns:
            是否活跃
        """
        # 默认实现：检查最近30根K线的活跃度
        stock_no_active_day = self.config.get('stock_no_active_day', 30)
        stock_no_active_thred = self.config.get('stock_no_active_thred', 3)
        stock_distinct_price_thred = self.config.get('stock_distinct_price_thred', 25)
        
        # 实现逻辑：检查一字线数量和股价多样性
        return True