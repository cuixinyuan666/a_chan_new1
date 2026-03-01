import akshare as ak
import pandas as pd
from typing import Dict, Any, List

class QueryMarketValue:
    """计算股票市值分位数"""
    
    def __init__(self):
        """初始化"""
        pass
    
    def get_market_value(self) -> pd.DataFrame:
        """获取股票市值数据
        
        Returns:
            股票市值数据
        """
        try:
            # 使用akshare获取A股市值数据
            df = ak.stock_zh_a_spot_em()
            
            # 筛选需要的列
            df = df[['代码', '名称', '最新价', '总市值', '流通市值']]
            df.columns = ['code', 'name', 'price', 'market_value', 'circulating_market_value']
            
            # 数据处理
            df['market_value'] = pd.to_numeric(df['market_value'], errors='coerce')
            df['circulating_market_value'] = pd.to_numeric(df['circulating_market_value'], errors='coerce')
            df.dropna(inplace=True)
            
            return df
        except Exception as e:
            print(f"Get market value error: {e}")
            return pd.DataFrame()
    
    def calculate_quantiles(self, df: pd.DataFrame) -> Dict[str, Any]:
        """计算市值分位数
        
        Args:
            df: 股票市值数据
            
        Returns:
            分位数计算结果
        """
        if df.empty:
            return {}
        
        quantiles = {}
        
        # 计算总市值分位数
        quantiles['market_value'] = {
            'q10': df['market_value'].quantile(0.1),
            'q25': df['market_value'].quantile(0.25),
            'q50': df['market_value'].quantile(0.5),
            'q75': df['market_value'].quantile(0.75),
            'q90': df['market_value'].quantile(0.9),
            'q95': df['market_value'].quantile(0.95),
            'mean': df['market_value'].mean(),
            'median': df['market_value'].median(),
            'std': df['market_value'].std()
        }
        
        # 计算流通市值分位数
        quantiles['circulating_market_value'] = {
            'q10': df['circulating_market_value'].quantile(0.1),
            'q25': df['circulating_market_value'].quantile(0.25),
            'q50': df['circulating_market_value'].quantile(0.5),
            'q75': df['circulating_market_value'].quantile(0.75),
            'q90': df['circulating_market_value'].quantile(0.9),
            'q95': df['circulating_market_value'].quantile(0.95),
            'mean': df['circulating_market_value'].mean(),
            'median': df['circulating_market_value'].median(),
            'std': df['circulating_market_value'].std()
        }
        
        return quantiles
    
    def get_stocks_by_quantile(self, df: pd.DataFrame, market_value_type: str = 'market_value', quantile_range: tuple = (0.75, 1.0)) -> pd.DataFrame:
        """根据市值分位数筛选股票
        
        Args:
            df: 股票市值数据
            market_value_type: 市值类型 ('market_value' 或 'circulating_market_value')
            quantile_range: 分位数范围
            
        Returns:
            筛选后的股票数据
        """
        if df.empty:
            return pd.DataFrame()
        
        # 计算分位数
        q_min = df[market_value_type].quantile(quantile_range[0])
        q_max = df[market_value_type].quantile(quantile_range[1])
        
        # 筛选股票
        filtered_df = df[(df[market_value_type] >= q_min) & (df[market_value_type] <= q_max)]
        filtered_df.sort_values(market_value_type, ascending=False, inplace=True)
        
        return filtered_df
    
    def analyze_market_value_distribution(self) -> Dict[str, Any]:
        """分析市值分布
        
        Returns:
            市值分布分析结果
        """
        # 获取市值数据
        df = self.get_market_value()
        
        if df.empty:
            return {}
        
        # 计算分位数
        quantiles = self.calculate_quantiles(df)
        
        # 按市值区间分组
        market_value_ranges = {
            'small': (0, 50),      # 小市值: 0-50亿
            'mid': (50, 200),      # 中市值: 50-200亿
            'large': (200, 1000),   # 大市值: 200-1000亿
            'mega': (1000, float('inf'))  # 超大市值: 1000亿以上
        }
        
        distribution = {}
        for name, (min_val, max_val) in market_value_ranges.items():
            count = len(df[(df['market_value'] >= min_val) & (df['market_value'] < max_val)])
            percentage = count / len(df) * 100
            distribution[name] = {
                'count': count,
                'percentage': percentage
            }
        
        return {
            'quantiles': quantiles,
            'distribution': distribution,
            'total_stocks': len(df)
        }

if __name__ == '__main__':
    # 示例：分析市值分布
    analyzer = QueryMarketValue()
    result = analyzer.analyze_market_value_distribution()
    
    print("市值分布分析结果:")
    print(f"总股票数: {result.get('total_stocks', 0)}")
    print("\n市值分位数:")
    print(result.get('quantiles', {}))
    print("\n市值分布:")
    print(result.get('distribution', {}))