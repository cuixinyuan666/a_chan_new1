from typing import Dict, Any, Optional
from Common.CEnum import KL_TYPE, BS_TYPE

class Signal:
    """信号类"""
    
    def __init__(self, signal_type: str, kl_type: KL_TYPE, price: float, time, reason: str = ''):
        """初始化信号
        
        Args:
            signal_type: 信号类型（buy, sell, cover）
            kl_type: K线类型
            price: 价格
            time: 时间
            reason: 原因
        """
        self.type = signal_type
        self.kl_type = kl_type
        self.price = price
        self.time = time
        self.reason = reason
        self.extra = {}
    
    def add_extra(self, key: str, value: Any):
        """添加额外信息
        
        Args:
            key: 键
            value: 值
        """
        self.extra[key] = value
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典
        
        Returns:
            字典形式的信号信息
        """
        return {
            'type': self.type,
            'kl_type': self.kl_type.name,
            'price': self.price,
            'time': self.time,
            'reason': self.reason,
            'extra': self.extra
        }
    
    def __str__(self) -> str:
        """字符串表示
        
        Returns:
            字符串表示
        """
        return f"Signal(type={self.type}, kl_type={self.kl_type.name}, price={self.price}, time={self.time}, reason={self.reason})"

class SignalMonitor:
    """信号监控类"""
    
    def __init__(self):
        """初始化信号监控"""
        self.signals = []
    
    def add_signal(self, signal: Signal):
        """添加信号
        
        Args:
            signal: 信号
        """
        self.signals.append(signal)
    
    def get_signals_by_type(self, signal_type: str) -> list[Signal]:
        """按类型获取信号
        
        Args:
            signal_type: 信号类型
            
        Returns:
            信号列表
        """
        return [signal for signal in self.signals if signal.type == signal_type]
    
    def get_latest_signal(self, signal_type: Optional[str] = None) -> Optional[Signal]:
        """获取最新的信号
        
        Args:
            signal_type: 信号类型（可选）
            
        Returns:
            最新的信号
        """
        if not self.signals:
            return None
        
        if signal_type:
            filtered_signals = self.get_signals_by_type(signal_type)
            if filtered_signals:
                return filtered_signals[-1]
            return None
        
        return self.signals[-1]
    
    def to_dict(self) -> list[Dict[str, Any]]:
        """转换为字典列表
        
        Returns:
            字典列表
        """
        return [signal.to_dict() for signal in self.signals]
    
    def __len__(self) -> int:
        """获取长度
        
        Returns:
            长度
        """
        return len(self.signals)
    
    def __getitem__(self, index) -> Signal:
        """获取指定索引的信号
        
        Args:
            index: 索引
            
        Returns:
            信号
        """
        return self.signals[index]