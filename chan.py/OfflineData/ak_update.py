import akshare as ak
import pandas as pd
from datetime import datetime, timedelta
from .offline_data_util import OfflineDataUtil

class AkUpdate:
    """akshare更新港股美股A股离线数据"""
    
    def __init__(self, data_dir: str = './data'):
        """初始化
        
        Args:
            data_dir: 数据存储目录
        """
        self.util = OfflineDataUtil(data_dir)
    
    def update_ashare(self, code: str) -> bool:
        """更新A股数据
        
        Args:
            code: 股票代码
            
        Returns:
            是否更新成功
        """
        try:
            # 获取最后更新日期
            last_date = self.util.get_last_update_date(code, 'ashare')
            
            # 确定开始日期
            if last_date:
                start_date = (last_date + timedelta(days=1)).strftime('%Y%m%d')
            else:
                start_date = '20100101'
            
            # 获取数据
            df = ak.stock_zh_a_hist(
                symbol=code,
                period="daily",
                start_date=start_date,
                end_date=datetime.now().strftime('%Y%m%d'),
                adjust="qfq"
            )
            
            if df.empty:
                return False
            
            # 数据处理
            df = df[['日期', '开盘', '最高', '最低', '收盘', '成交量', '成交额', '涨跌幅']]
            df.columns = ['date', 'open', 'high', 'low', 'close', 'volume', 'amount', 'change_pct']
            df['date'] = pd.to_datetime(df['date'])
            
            # 加载旧数据
            old_df = self.util.load_stock_data(code, 'ashare')
            
            # 合并数据
            merged_df = self.util.merge_data(old_df, df)
            
            # 保存数据
            self.util.save_stock_data(code, merged_df, 'ashare')
            
            print(f"Update A-share {code} successfully")
            return True
        except Exception as e:
            print(f"Update A-share {code} error: {e}")
            return False
    
    def update_hkshare(self, code: str) -> bool:
        """更新港股数据
        
        Args:
            code: 股票代码
            
        Returns:
            是否更新成功
        """
        try:
            # 获取最后更新日期
            last_date = self.util.get_last_update_date(code, 'hkshare')
            
            # 确定开始日期
            if last_date:
                start_date = (last_date + timedelta(days=1)).strftime('%Y-%m-%d')
            else:
                start_date = '2010-01-01'
            
            # 获取数据
            df = ak.stock_hk_hist(
                symbol=code,
                period="daily",
                start_date=start_date,
                end_date=datetime.now().strftime('%Y-%m-%d')
            )
            
            if df.empty:
                return False
            
            # 数据处理
            df = df[['日期', '开盘', '最高', '最低', '收盘', '成交量', '成交额', '涨跌幅']]
            df.columns = ['date', 'open', 'high', 'low', 'close', 'volume', 'amount', 'change_pct']
            df['date'] = pd.to_datetime(df['date'])
            
            # 加载旧数据
            old_df = self.util.load_stock_data(code, 'hkshare')
            
            # 合并数据
            merged_df = self.util.merge_data(old_df, df)
            
            # 保存数据
            self.util.save_stock_data(code, merged_df, 'hkshare')
            
            print(f"Update HK-share {code} successfully")
            return True
        except Exception as e:
            print(f"Update HK-share {code} error: {e}")
            return False
    
    def update_usshare(self, code: str) -> bool:
        """更新美股数据
        
        Args:
            code: 股票代码
            
        Returns:
            是否更新成功
        """
        try:
            # 获取最后更新日期
            last_date = self.util.get_last_update_date(code, 'usshare')
            
            # 确定开始日期
            if last_date:
                start_date = (last_date + timedelta(days=1)).strftime('%Y-%m-%d')
            else:
                start_date = '2010-01-01'
            
            # 获取数据
            df = ak.stock_us_hist(
                symbol=code,
                period="daily",
                start_date=start_date,
                end_date=datetime.now().strftime('%Y-%m-%d')
            )
            
            if df.empty:
                return False
            
            # 数据处理
            df = df[['日期', '开盘', '最高', '最低', '收盘', '成交量', '涨跌幅']]
            df.columns = ['date', 'open', 'high', 'low', 'close', 'volume', 'change_pct']
            df['date'] = pd.to_datetime(df['date'])
            
            # 加载旧数据
            old_df = self.util.load_stock_data(code, 'usshare')
            
            # 合并数据
            merged_df = self.util.merge_data(old_df, df)
            
            # 保存数据
            self.util.save_stock_data(code, merged_df, 'usshare')
            
            print(f"Update US-share {code} successfully")
            return True
        except Exception as e:
            print(f"Update US-share {code} error: {e}")
            return False
    
    def update_all(self, ashare_codes: list[str] = None, hkshare_codes: list[str] = None, usshare_codes: list[str] = None):
        """更新所有数据
        
        Args:
            ashare_codes: A股代码列表
            hkshare_codes: 港股代码列表
            usshare_codes: 美股代码列表
        """
        # 更新A股
        if ashare_codes:
            for code in ashare_codes:
                self.update_ashare(code)
        
        # 更新港股
        if hkshare_codes:
            for code in hkshare_codes:
                self.update_hkshare(code)
        
        # 更新美股
        if usshare_codes:
            for code in usshare_codes:
                self.update_usshare(code)
        
        # 更新数据信息
        self.util.create_data_info('ashare')
        self.util.create_data_info('hkshare')
        self.util.create_data_info('usshare')

if __name__ == '__main__':
    # 示例：更新部分股票数据
    updater = AkUpdate()
    updater.update_all(
        ashare_codes=['600000', '000001'],
        hkshare_codes=['00700'],
        usshare_codes=['AAPL']
    )