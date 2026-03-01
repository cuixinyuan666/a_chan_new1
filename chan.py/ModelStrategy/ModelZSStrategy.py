from typing import List, Dict, Any, Optional
import pandas as pd
from .ModelBSPStrategy import ModelBSPStrategy

class ModelZSStrategy(ModelBSPStrategy):
    """模型中枢策略"""
    
    def extract_features(self, chan) -> pd.DataFrame:
        """提取中枢相关特征
        
        Args:
            chan: 缠论对象
            
        Returns:
            特征数据
        """
        features = {}
        
        # 基础特征
        features['close'] = chan.latest_klu.close
        features['volume'] = chan.latest_klu.volume
        
        # 中枢特征
        if hasattr(chan, 'zs_list') and chan.zs_list:
            latest_zs = chan.zs_list[-1]
            features['zs_count'] = len(chan.zs_list)
            features['zs_high'] = latest_zs.zs_high
            features['zs_low'] = latest_zs.zs_low
            features['zs_mid'] = (latest_zs.zs_high + latest_zs.zs_low) / 2
            features['zs_range'] = latest_zs.zs_high - latest_zs.zs_low
            features['zs_bi_count'] = len(latest_zs.bi_list)
            
            # 价格与中枢的关系
            features['price_vs_zs_mid'] = chan.latest_klu.close - features['zs_mid']
            features['price_vs_zs_high'] = chan.latest_klu.close - features['zs_high']
            features['price_vs_zs_low'] = chan.latest_klu.close - features['zs_low']
        else:
            features['zs_count'] = 0
            features['zs_high'] = 0
            features['zs_low'] = 0
            features['zs_mid'] = 0
            features['zs_range'] = 0
            features['zs_bi_count'] = 0
            features['price_vs_zs_mid'] = 0
            features['price_vs_zs_high'] = 0
            features['price_vs_zs_low'] = 0
        
        # 笔特征
        if hasattr(chan, 'bi_list') and chan.bi_list:
            latest_bi = chan.bi_list[-1]
            features['bi_count'] = len(chan.bi_list)
            features['bi_direction'] = 1 if latest_bi.direction == 'up' else 0
            features['bi_length'] = abs(latest_bi.end_klu.close - latest_bi.start_klu.close)
        else:
            features['bi_count'] = 0
            features['bi_direction'] = 0
            features['bi_length'] = 0
        
        # 线段特征
        if hasattr(chan, 'seg_list') and chan.seg_list:
            latest_seg = chan.seg_list[-1]
            features['seg_count'] = len(chan.seg_list)
            features['seg_direction'] = 1 if latest_seg.direction == 'up' else 0
            features['seg_length'] = abs(latest_seg.end_klu.close - latest_seg.start_klu.close)
        else:
            features['seg_count'] = 0
            features['seg_direction'] = 0
            features['seg_length'] = 0
        
        return pd.DataFrame([features])
    
    def get_buy_signal(self, chan) -> List[Dict[str, Any]]:
        """获取买入信号
        
        Args:
            chan: 缠论对象
            
        Returns:
            买入信号列表
        """
        signals = super().get_buy_signal(chan)
        
        # 额外的中枢相关买入逻辑
        if hasattr(chan, 'zs_list') and chan.zs_list:
            latest_zs = chan.zs_list[-1]
            # 价格回踩中枢下沿附近
            if abs(chan.latest_klu.close - latest_zs.zs_low) / latest_zs.zs_low < 0.02:
                signals.append({
                    'type': 'buy',
                    'price': chan.latest_klu.close,
                    'timestamp': chan.latest_klu.end_time,
                    'strategy': self.__class__.__name__,
                    'reason': '中枢下沿附近'
                })
        
        return signals
    
    def get_sell_signal(self, chan) -> List[Dict[str, Any]]:
        """获取卖出信号
        
        Args:
            chan: 缠论对象
            
        Returns:
            卖出信号列表
        """
        signals = super().get_sell_signal(chan)
        
        # 额外的中枢相关卖出逻辑
        if hasattr(chan, 'zs_list') and chan.zs_list:
            latest_zs = chan.zs_list[-1]
            # 价格触及中枢上沿附近
            if abs(chan.latest_klu.close - latest_zs.zs_high) / latest_zs.zs_high < 0.02:
                signals.append({
                    'type': 'sell',
                    'price': chan.latest_klu.close,
                    'timestamp': chan.latest_klu.end_time,
                    'strategy': self.__class__.__name__,
                    'reason': '中枢上沿附近'
                })
        
        return signals