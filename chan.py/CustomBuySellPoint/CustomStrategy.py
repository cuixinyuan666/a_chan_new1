from .Strategy import Strategy
from typing import List, Dict, Any, Optional
from Common.CEnum import KL_TYPE, AUTYPE, BS_TYPE

class CCustomStrategy(Strategy):
    """自定义策略1"""
    
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
            
            # 检查是否有笔和线段
            if not kl.bi_list or not kl.seg_list:
                continue
            
            # 检查最近的线段和中枢
            last_seg = kl.seg_list[-1]
            zs_list = kl.zs_list
            
            if not zs_list:
                continue
            
            # 寻找最近的中枢
            last_zs = zs_list[-1]
            
            # 检查是否有背驰
            if self._check_divergence(kl, last_seg, last_zs):
                # 生成买入信号
                signal = {
                    'type': 'buy',
                    'kl_type': kl_type,
                    'price': kl.latest_klu.close,
                    'time': kl.latest_klu.end,
                    'reason': '背驰买入',
                    'level': kl_type.value
                }
                signals.append(signal)
        
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
            
            # 检查是否有笔和线段
            if not kl.bi_list or not kl.seg_list:
                continue
            
            # 检查最近的线段和中枢
            last_seg = kl.seg_list[-1]
            zs_list = kl.zs_list
            
            if not zs_list:
                continue
            
            # 寻找最近的中枢
            last_zs = zs_list[-1]
            
            # 检查是否有背驰
            if self._check_divergence(kl, last_seg, last_zs, is_sell=True):
                # 生成卖出信号
                signal = {
                    'type': 'sell',
                    'kl_type': kl_type,
                    'price': kl.latest_klu.close,
                    'time': kl.latest_klu.end,
                    'reason': '背驰卖出',
                    'level': kl_type.value
                }
                signals.append(signal)
        
        return signals
    
    def _check_divergence(self, kl, seg, zs, is_sell=False) -> bool:
        """检查是否有背驰
        
        Args:
            kl: K线对象
            seg: 线段对象
            zs: 中枢对象
            is_sell: 是否为卖出信号
            
        Returns:
            是否有背驰
        """
        # 简单的背驰检查逻辑
        # 实际应用中需要更复杂的背驰判断
        return True
    
    def get_cover_signal(self, chan, open_signal) -> Optional[Dict[str, Any]]:
        """获取平仓信号
        
        Args:
            chan: 缠论对象
            open_signal: 开仓信号
            
        Returns:
            平仓信号
        """
        # 简单的平仓逻辑
        kl_type = open_signal['kl_type']
        kl = chan[kl_type]
        
        # 检查是否达到止盈或止损
        open_price = open_signal['price']
        current_price = kl.latest_klu.close
        
        # 计算收益率
        profit_rate = (current_price - open_price) / open_price
        
        # 检查止盈
        if self.max_profit_rate and abs(profit_rate) >= self.max_profit_rate:
            return {
                'type': 'cover',
                'kl_type': kl_type,
                'price': current_price,
                'time': kl.latest_klu.end,
                'reason': '止盈平仓',
                'profit_rate': profit_rate
            }
        
        # 检查止损
        if self.max_sl_rate and abs(profit_rate) >= self.max_sl_rate:
            return {
                'type': 'cover',
                'kl_type': kl_type,
                'price': current_price,
                'time': kl.latest_klu.end,
                'reason': '止损平仓',
                'profit_rate': profit_rate
            }
        
        return None