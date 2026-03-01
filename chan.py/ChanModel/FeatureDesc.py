from typing import Dict, Any, List, Callable

class FeatureDesc:
    """特征注册类"""
    
    def __init__(self):
        """初始化"""
        self.features = {}
    
    def register_feature(self, name: str, func: Callable, desc: str = ''):
        """注册特征
        
        Args:
            name: 特征名称
            func: 特征计算函数
            desc: 特征描述
        """
        self.features[name] = {
            'func': func,
            'desc': desc
        }
    
    def get_feature(self, name: str) -> Dict[str, Any]:
        """获取特征
        
        Args:
            name: 特征名称
            
        Returns:
            特征信息
        """
        return self.features.get(name)
    
    def list_features(self) -> List[str]:
        """列出所有特征
        
        Returns:
            特征名称列表
        """
        return list(self.features.keys())
    
    def get_feature_desc(self, name: str) -> str:
        """获取特征描述
        
        Args:
            name: 特征名称
            
        Returns:
            特征描述
        """
        feature = self.features.get(name)
        return feature['desc'] if feature else ''
    
    def calculate_feature(self, name: str, *args, **kwargs) -> Any:
        """计算特征
        
        Args:
            name: 特征名称
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            特征值
        """
        feature = self.features.get(name)
        if feature:
            return feature['func'](*args, **kwargs)
        return None

# 全局特征注册实例
feature_desc = FeatureDesc()

# 注册常用特征
def register_common_features():
    """注册常用特征"""
    # 价格相关特征
    feature_desc.register_feature(
        'close_price',
        lambda kl: kl.latest_klu.close,
        '收盘价'
    )
    
    feature_desc.register_feature(
        'open_price',
        lambda kl: kl.latest_klu.open,
        '开盘价'
    )
    
    feature_desc.register_feature(
        'high_price',
        lambda kl: kl.latest_klu.high,
        '最高价'
    )
    
    feature_desc.register_feature(
        'low_price',
        lambda kl: kl.latest_klu.low,
        '最低价'
    )
    
    # 成交量相关特征
    feature_desc.register_feature(
        'volume',
        lambda kl: kl.latest_klu.volume,
        '成交量'
    )
    
    # 指标相关特征
    feature_desc.register_feature(
        'macd',
        lambda kl: kl.macd[-1]['macd'] if hasattr(kl, 'macd') and kl.macd else 0,
        'MACD值'
    )
    
    feature_desc.register_feature(
        'kdj_k',
        lambda kl: kl.kdj[-1]['k'] if hasattr(kl, 'kdj') and kl.kdj else 0,
        'KDJ-K值'
    )
    
    feature_desc.register_feature(
        'kdj_d',
        lambda kl: kl.kdj[-1]['d'] if hasattr(kl, 'kdj') and kl.kdj else 0,
        'KDJ-D值'
    )
    
    feature_desc.register_feature(
        'kdj_j',
        lambda kl: kl.kdj[-1]['j'] if hasattr(kl, 'kdj') and kl.kdj else 0,
        'KDJ-J值'
    )
    
    feature_desc.register_feature(
        'rsi',
        lambda kl: kl.rsi[-1] if hasattr(kl, 'rsi') and kl.rsi else 0,
        'RSI值'
    )
    
    # 缠论相关特征
    feature_desc.register_feature(
        'bi_count',
        lambda kl: len(kl.bi_list) if hasattr(kl, 'bi_list') else 0,
        '笔数量'
    )
    
    feature_desc.register_feature(
        'seg_count',
        lambda kl: len(kl.seg_list) if hasattr(kl, 'seg_list') else 0,
        '线段数量'
    )
    
    feature_desc.register_feature(
        'zs_count',
        lambda kl: len(kl.zs_list) if hasattr(kl, 'zs_list') else 0,
        '中枢数量'
    )

# 自动注册常用特征
register_common_features()