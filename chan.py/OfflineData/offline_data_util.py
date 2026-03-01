import os
import json
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

class OfflineDataUtil:
    """离线数据更新通用工具类"""
    
    def __init__(self, data_dir: str = './data'):
        """初始化
        
        Args:
            data_dir: 数据存储目录
        """
        self.data_dir = data_dir
        os.makedirs(self.data_dir, exist_ok=True)
    
    def get_stock_file_path(self, code: str, market: str = 'ashare') -> str:
        """获取股票数据文件路径
        
        Args:
            code: 股票代码
            market: 市场类型
            
        Returns:
            文件路径
        """
        market_dir = os.path.join(self.data_dir, market)
        os.makedirs(market_dir, exist_ok=True)
        return os.path.join(market_dir, f'{code}.csv')
    
    def load_stock_data(self, code: str, market: str = 'ashare') -> Optional[pd.DataFrame]:
        """加载股票数据
        
        Args:
            code: 股票代码
            market: 市场类型
            
        Returns:
            股票数据
        """
        file_path = self.get_stock_file_path(code, market)
        if not os.path.exists(file_path):
            return None
        
        try:
            df = pd.read_csv(file_path)
            df['date'] = pd.to_datetime(df['date'])
            df.sort_values('date', inplace=True)
            df.reset_index(drop=True, inplace=True)
            return df
        except Exception as e:
            print(f"Load stock data error: {e}")
            return None
    
    def save_stock_data(self, code: str, df: pd.DataFrame, market: str = 'ashare'):
        """保存股票数据
        
        Args:
            code: 股票代码
            df: 股票数据
            market: 市场类型
        """
        file_path = self.get_stock_file_path(code, market)
        try:
            df.to_csv(file_path, index=False)
        except Exception as e:
            print(f"Save stock data error: {e}")
    
    def get_last_update_date(self, code: str, market: str = 'ashare') -> Optional[datetime]:
        """获取最后更新日期
        
        Args:
            code: 股票代码
            market: 市场类型
            
        Returns:
            最后更新日期
        """
        df = self.load_stock_data(code, market)
        if df is None or df.empty:
            return None
        return df['date'].max()
    
    def need_update(self, code: str, market: str = 'ashare', days: int = 1) -> bool:
        """判断是否需要更新
        
        Args:
            code: 股票代码
            market: 市场类型
            days: 天数阈值
            
        Returns:
            是否需要更新
        """
        last_date = self.get_last_update_date(code, market)
        if last_date is None:
            return True
        
        today = datetime.now().date()
        days_diff = (today - last_date.date()).days
        return days_diff >= days
    
    def merge_data(self, old_df: pd.DataFrame, new_df: pd.DataFrame) -> pd.DataFrame:
        """合并数据
        
        Args:
            old_df: 旧数据
            new_df: 新数据
            
        Returns:
            合并后的数据
        """
        if old_df is None or old_df.empty:
            return new_df
        
        # 合并数据，去重
        merged_df = pd.concat([old_df, new_df])
        merged_df.drop_duplicates(subset=['date'], keep='last', inplace=True)
        merged_df.sort_values('date', inplace=True)
        merged_df.reset_index(drop=True, inplace=True)
        return merged_df
    
    def get_stock_list(self, market: str = 'ashare') -> list[str]:
        """获取股票列表
        
        Args:
            market: 市场类型
            
        Returns:
            股票代码列表
        """
        market_dir = os.path.join(self.data_dir, market)
        if not os.path.exists(market_dir):
            return []
        
        stock_list = []
        for file_name in os.listdir(market_dir):
            if file_name.endswith('.csv'):
                code = file_name[:-4]
                stock_list.append(code)
        return stock_list
    
    def create_data_info(self, market: str = 'ashare') -> Dict[str, Any]:
        """创建数据信息
        
        Args:
            market: 市场类型
            
        Returns:
            数据信息
        """
        stock_list = self.get_stock_list(market)
        data_info = {
            'market': market,
            'stock_count': len(stock_list),
            'last_update': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'stocks': {}
        }
        
        for code in stock_list:
            last_date = self.get_last_update_date(code, market)
            data_info['stocks'][code] = {
                'last_update': last_date.strftime('%Y-%m-%d') if last_date else None
            }
        
        # 保存数据信息
        info_file = os.path.join(self.data_dir, f'{market}_info.json')
        with open(info_file, 'w', encoding='utf-8') as f:
            json.dump(data_info, f, ensure_ascii=False, indent=2)
        
        return data_info
    
    def get_data_info(self, market: str = 'ashare') -> Optional[Dict[str, Any]]:
        """获取数据信息
        
        Args:
            market: 市场类型
            
        Returns:
            数据信息
        """
        info_file = os.path.join(self.data_dir, f'{market}_info.json')
        if not os.path.exists(info_file):
            return None
        
        try:
            with open(info_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Get data info error: {e}")
            return None