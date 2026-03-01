from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class CommSnapshot(ABC):
    """snapshot通用父类"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """初始化
        
        Args:
            config: 配置参数
        """
        self.config = config or {}
    
    @abstractmethod
    def get_snapshot(self, code: str) -> Optional[Dict[str, Any]]:
        """获取股票快照
        
        Args:
            code: 股票代码
            
        Returns:
            股票快照信息
        """
        pass
    
    @abstractmethod
    def get_multi_snapshot(self, codes: list[str]) -> Dict[str, Optional[Dict[str, Any]]]:
        """批量获取股票快照
        
        Args:
            codes: 股票代码列表
            
        Returns:
            股票快照信息字典
        """
        pass
    
    def _format_snapshot(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """格式化快照数据
        
        Args:
            data: 原始快照数据
            
        Returns:
            格式化后的快照数据
        """
        # 统一的快照数据格式
        return {
            'code': data.get('code', ''),
            'name': data.get('name', ''),
            'price': data.get('price', 0),
            'open': data.get('open', 0),
            'high': data.get('high', 0),
            'low': data.get('low', 0),
            'pre_close': data.get('pre_close', 0),
            'change': data.get('change', 0),
            'change_pct': data.get('change_pct', 0),
            'volume': data.get('volume', 0),
            'amount': data.get('amount', 0),
            'time': data.get('time', None)
        }
    
    def is_supported(self, code: str) -> bool:
        """判断是否支持该股票
        
        Args:
            code: 股票代码
            
        Returns:
            是否支持
        """
        # 默认支持所有股票
        return True