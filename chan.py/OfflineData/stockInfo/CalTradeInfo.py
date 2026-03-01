import pandas as pd
import numpy as np
from typing import Dict, Any

class CalTradeInfo:
    """计算股票指标数据分布，分位数"""
    
    def __init__(self, data_dir: str = './data'):
        """初始化
        
        Args:
            data_dir: 数据存储目录
        """
        self.data_dir = data_dir
    
    def calculate_metrics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """计算股票指标
        
        Args:
            df: 股票数据
            
        Returns:
            指标计算结果
        """
        metrics = {}
        
        # 计算成交量指标
        metrics['volume_mean'] = df['volume'].mean()
        metrics['volume_median'] = df['volume'].median()
        metrics['volume_std'] = df['volume'].std()
        metrics['volume_max'] = df['volume'].max()
        metrics['volume_min'] = df['volume'].min()
        
        # 计算成交额指标
        if 'amount' in df.columns:
            metrics['amount_mean'] = df['amount'].mean()
            metrics['amount_median'] = df['amount'].median()
            metrics['amount_std'] = df['amount'].std()
            metrics['amount_max'] = df['amount'].max()
            metrics['amount_min'] = df['amount'].min()
        
        # 计算涨跌幅指标
        metrics['change_pct_mean'] = df['change_pct'].mean()
        metrics['change_pct_median'] = df['change_pct'].median()
        metrics['change_pct_std'] = df['change_pct'].std()
        metrics['change_pct_max'] = df['change_pct'].max()
        metrics['change_pct_min'] = df['change_pct'].min()
        
        # 计算收益率指标
        df['return'] = df['close'].pct_change()
        metrics['return_mean'] = df['return'].mean()
        metrics['return_median'] = df['return'].median()
        metrics['return_std'] = df['return'].std()
        metrics['return_max'] = df['return'].max()
        metrics['return_min'] = df['return'].min()
        
        # 计算分位数
        metrics['volume_quantiles'] = {
            'q25': df['volume'].quantile(0.25),
            'q50': df['volume'].quantile(0.5),
            'q75': df['volume'].quantile(0.75),
            'q90': df['volume'].quantile(0.9),
            'q95': df['volume'].quantile(0.95)
        }
        
        if 'amount' in df.columns:
            metrics['amount_quantiles'] = {
                'q25': df['amount'].quantile(0.25),
                'q50': df['amount'].quantile(0.5),
                'q75': df['amount'].quantile(0.75),
                'q90': df['amount'].quantile(0.9),
                'q95': df['amount'].quantile(0.95)
            }
        
        metrics['change_pct_quantiles'] = {
            'q25': df['change_pct'].quantile(0.25),
            'q50': df['change_pct'].quantile(0.5),
            'q75': df['change_pct'].quantile(0.75),
            'q90': df['change_pct'].quantile(0.9),
            'q95': df['change_pct'].quantile(0.95)
        }
        
        return metrics
    
    def calculate_market_value(self, code: str, price: float, shares: int) -> Dict[str, Any]:
        """计算市值
        
        Args:
            code: 股票代码
            price: 价格
            shares: 总股本
            
        Returns:
            市值计算结果
        """
        market_value = price * shares
        circulating_market_value = market_value * 0.8  # 假设流通比例为80%
        
        return {
            'code': code,
            'price': price,
            'shares': shares,
            'market_value': market_value,
            'circulating_market_value': circulating_market_value,
            'market_value_billion': market_value / 100000000,
            'circulating_market_value_billion': circulating_market_value / 100000000
        }
    
    def analyze_volatility(self, df: pd.DataFrame) -> Dict[str, Any]:
        """分析波动率
        
        Args:
            df: 股票数据
            
        Returns:
            波动率分析结果
        """
        # 计算日收益率
        df['return'] = df['close'].pct_change()
        
        # 计算波动率指标
        volatility = {
            'daily_volatility': df['return'].std(),
            'annualized_volatility': df['return'].std() * np.sqrt(252),
            'max_drawdown': self._calculate_max_drawdown(df['close']),
            'sharpe_ratio': self._calculate_sharpe_ratio(df['return'])
        }
        
        return volatility
    
    def _calculate_max_drawdown(self, prices: pd.Series) -> float:
        """计算最大回撤
        
        Args:
            prices: 价格序列
            
        Returns:
            最大回撤
        """
        cumulative_returns = (1 + prices.pct_change()).cumprod()
        peak = cumulative_returns.cummax()
        drawdown = (cumulative_returns - peak) / peak
        return drawdown.min()
    
    def _calculate_sharpe_ratio(self, returns: pd.Series, risk_free_rate: float = 0.03) -> float:
        """计算夏普比率
        
        Args:
            returns: 收益率序列
            risk_free_rate: 无风险利率
            
        Returns:
            夏普比率
        """
        excess_returns = returns - risk_free_rate / 252
        return excess_returns.mean() / excess_returns.std() * np.sqrt(252)

if __name__ == '__main__':
    # 示例：计算股票指标
    import pandas as pd
    from OfflineData.offline_data_util import OfflineDataUtil
    
    util = OfflineDataUtil()
    df = util.load_stock_data('600000', 'ashare')
    
    if df is not None:
        calculator = CalTradeInfo()
        metrics = calculator.calculate_metrics(df)
        volatility = calculator.analyze_volatility(df)
        
        print("指标计算结果:")
        print(metrics)
        print("\n波动率分析结果:")
        print(volatility)