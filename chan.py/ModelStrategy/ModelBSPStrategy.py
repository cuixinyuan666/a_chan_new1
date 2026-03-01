from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import pandas as pd
from CustomBuySellPoint.Strategy import Strategy

class ModelBSPStrategy(Strategy):
    """模型买卖点策略"""
    
    def __init__(self, model_path: str = None):
        """初始化
        
        Args:
            model_path: 模型路径
        """
        super().__init__()
        self.model_path = model_path
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """加载模型"""
        if self.model_path:
            try:
                from ChanModel.XGBModel import CXGBModel
                model = CXGBModel()
                self.model = model.load_model(self.model_path)
            except Exception as e:
                print(f"Load model error: {e}")
    
    @abstractmethod
    def extract_features(self, chan) -> pd.DataFrame:
        """提取特征
        
        Args:
            chan: 缠论对象
            
        Returns:
            特征数据
        """
        pass
    
    def get_buy_signal(self, chan) -> List[Dict[str, Any]]:
        """获取买入信号
        
        Args:
            chan: 缠论对象
            
        Returns:
            买入信号列表
        """
        if not self.model:
            return []
        
        try:
            # 提取特征
            features = self.extract_features(chan)
            
            # 预测
            from ChanModel.XGBModel import CXGBModel
            model = CXGBModel()
            prediction = model.predict(self.model, features)
            
            # 生成信号
            signals = []
            if prediction and prediction[0] == 1:
                signals.append({
                    'type': 'buy',
                    'price': chan.latest_klu.close,
                    'timestamp': chan.latest_klu.end_time,
                    'strategy': self.__class__.__name__
                })
            
            return signals
        except Exception as e:
            print(f"Get buy signal error: {e}")
            return []
    
    def get_sell_signal(self, chan) -> List[Dict[str, Any]]:
        """获取卖出信号
        
        Args:
            chan: 缠论对象
            
        Returns:
            卖出信号列表
        """
        if not self.model:
            return []
        
        try:
            # 提取特征
            features = self.extract_features(chan)
            
            # 预测
            from ChanModel.XGBModel import CXGBModel
            model = CXGBModel()
            prediction = model.predict(self.model, features)
            
            # 生成信号
            signals = []
            if prediction and prediction[0] == 0:
                signals.append({
                    'type': 'sell',
                    'price': chan.latest_klu.close,
                    'timestamp': chan.latest_klu.end_time,
                    'strategy': self.__class__.__name__
                })
            
            return signals
        except Exception as e:
            print(f"Get sell signal error: {e}")
            return []

class XGBBSPStrategy(ModelBSPStrategy):
    """XGB模型买卖点策略"""
    
    def extract_features(self, chan) -> pd.DataFrame:
        """提取特征
        
        Args:
            chan: 缠论对象
            
        Returns:
            特征数据
        """
        features = {}
        
        # 价格相关特征
        features['close'] = chan.latest_klu.close
        features['open'] = chan.latest_klu.open
        features['high'] = chan.latest_klu.high
        features['low'] = chan.latest_klu.low
        
        # 成交量特征
        features['volume'] = chan.latest_klu.volume
        
        # 指标特征
        if hasattr(chan, 'macd') and chan.macd:
            features['macd'] = chan.macd[-1]['macd']
            features['macd_diff'] = chan.macd[-1]['diff']
            features['macd_dea'] = chan.macd[-1]['dea']
        else:
            features['macd'] = 0
            features['macd_diff'] = 0
            features['macd_dea'] = 0
        
        if hasattr(chan, 'kdj') and chan.kdj:
            features['kdj_k'] = chan.kdj[-1]['k']
            features['kdj_d'] = chan.kdj[-1]['d']
            features['kdj_j'] = chan.kdj[-1]['j']
        else:
            features['kdj_k'] = 0
            features['kdj_d'] = 0
            features['kdj_j'] = 0
        
        if hasattr(chan, 'rsi') and chan.rsi:
            features['rsi'] = chan.rsi[-1]
        else:
            features['rsi'] = 50
        
        # 缠论特征
        features['bi_count'] = len(chan.bi_list) if hasattr(chan, 'bi_list') else 0
        features['seg_count'] = len(chan.seg_list) if hasattr(chan, 'seg_list') else 0
        features['zs_count'] = len(chan.zs_list) if hasattr(chan, 'zs_list') else 0
        
        # 转换为DataFrame
        return pd.DataFrame([features])