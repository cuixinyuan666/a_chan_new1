from .Strategy import Strategy
from typing import List, Dict, Any, Optional
from Common.CEnum import KL_TYPE, BS_TYPE

class CSegBspStrategy(Strategy):
    """线段买卖点策略"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """初始化策略
        
        Args:
            config: 策略配置参数
        """
        super().__init__(config)
    
    def get_buy_signal(self, chan) -> List[Dict[str, Any]]:
        """获取买入信号
        
        Args:
            chan: 缠论对象
            
        Returns:
            买入信号列表
        """
        signals = []
        
        # 遍历所有级别
        for kl_type in chan.kl_types:
            kl = chan[kl_type]
            
            # 检查是否有线段买卖点
            if not hasattr(kl, 'seg_bsp_list') or not kl.seg_bsp_list:
                continue
            
            # 获取最近的线段买卖点
            seg_bsp_list = kl.seg_bsp_list
            
            # 寻找最近的买入点
            for bsp in reversed(seg_bsp_list):
                if bsp.type == BS_TYPE.BUY:
                    # 检查是否是最近的买卖点
                    if self._is_recent_bsp(bsp, kl):
                        # 生成买入信号
                        signal = {
                            'type': 'buy',
                            'kl_type': kl_type,
                            'price': kl.latest_klu.close,
                            'time': kl.latest_klu.end,
                            'reason': f'线段{self._get_bsp_type_str(bsp.type)}买卖点',
                            'level': kl_type.value,
                            'bsp': bsp
                        }
                        signals.append(signal)
                        break
        
        return signals
    
    def get_sell_signal(self, chan) -> List[Dict[str, Any]]:
        """获取卖出信号
        
        Args:
            chan: 缠论对象
            
        Returns:
            卖出信号列表
        """
        signals = []
        
        # 遍历所有级别
        for kl_type in chan.kl_types:
            kl = chan[kl_type]
            
            # 检查是否有线段买卖点
            if not hasattr(kl, 'seg_bsp_list') or not kl.seg_bsp_list:
                continue
            
            # 获取最近的线段买卖点
            seg_bsp_list = kl.seg_bsp_list
            
            # 寻找最近的卖出点
            for bsp in reversed(seg_bsp_list):
                if bsp.type == BS_TYPE.SELL:
                    # 检查是否是最近的买卖点
                    if self._is_recent_bsp(bsp, kl):
                        # 生成卖出信号
                        signal = {
                            'type': 'sell',
                            'kl_type': kl_type,
                            'price': kl.latest_klu.close,
                            'time': kl.latest_klu.end,
                            'reason': f'线段{self._get_bsp_type_str(bsp.type)}买卖点',
                            'level': kl_type.value,
                            'bsp': bsp
                        }
                        signals.append(signal)
                        break
        
        return signals
    
    def _is_recent_bsp(self, bsp, kl) -> bool:
        """检查是否是最近的买卖点
        
        Args:
            bsp: 买卖点对象
            kl: K线对象
            
        Returns:
            是否是最近的买卖点
        """
        # 简单逻辑：检查买卖点是否在最近的K线范围内
        latest_time = kl.latest_klu.end
        bsp_time = bsp.end_klu.end
        
        # 计算时间差（天数）
        time_diff = (latest_time - bsp_time).days
        
        # 如果买卖点在最近30天内，则认为是最近的
        return time_diff <= 30
    
    def _get_bsp_type_str(self, bsp_type) -> str:
        """获取买卖点类型字符串
        
        Args:
            bsp_type: 买卖点类型
            
        Returns:
            买卖点类型字符串
        """
        type_map = {
            BS_TYPE.BUY: '买点',
            BS_TYPE.SELL: '卖点',
            BS_TYPE.BUY1: '1类买点',
            BS_TYPE.SELL1: '1类卖点',
            BS_TYPE.BUY2: '2类买点',
            BS_TYPE.SELL2: '2类卖点',
            BS_TYPE.BUY3: '3类买点',
            BS_TYPE.SELL3: '3类卖点'
        }
        return type_map.get(bsp_type, '买卖点')
    
    def get_cover_signal(self, chan, open_signal) -> Optional[Dict[str, Any]]:
        """获取平仓信号
        
        Args:
            chan: 缠论对象
            open_signal: 开仓信号
            
        Returns:
            平仓信号
        """
        # 复用父类的平仓逻辑
        return super().get_cover_signal(chan, open_signal)