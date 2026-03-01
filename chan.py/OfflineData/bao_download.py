import baostock as bs
import pandas as pd
from datetime import datetime
from .offline_data_util import OfflineDataUtil

class BaoDownload:
    """baostock下载全量A股数据"""
    
    def __init__(self, data_dir: str = './data'):
        """初始化
        
        Args:
            data_dir: 数据存储目录
        """
        self.util = OfflineDataUtil(data_dir)
    
    def get_stock_list(self) -> list[str]:
        """获取A股股票列表
        
        Returns:
            股票代码列表
        """
        # 登录baostock
        lg = bs.login()
        if lg.error_code != '0':
            print(f"Login error: {lg.error_msg}")
            return []
        
        # 获取股票列表
        rs = bs.query_all_stock(day=datetime.now().strftime('%Y-%m-%d'))
        stock_list = []
        while (rs.error_code == '0') & rs.next():
            stock_info = rs.get_row_data()
            # 只获取A股
            if stock_info[1].startswith('sh.') or stock_info[1].startswith('sz.'):
                stock_list.append(stock_info[1].split('.')[1])
        
        # 登出
        bs.logout()
        return stock_list
    
    def download_stock(self, code: str, start_date: str = '2010-01-01') -> bool:
        """下载单个股票数据
        
        Args:
            code: 股票代码
            start_date: 开始日期
            
        Returns:
            是否下载成功
        """
        # 登录baostock
        lg = bs.login()
        if lg.error_code != '0':
            print(f"Login error: {lg.error_msg}")
            return False
        
        try:
            # 构建股票代码
            if code.startswith('6'):
                bs_code = f'sh.{code}'
            else:
                bs_code = f'sz.{code}'
            
            # 获取数据
            rs = bs.query_history_k_data_plus(
                bs_code,
                "date,open,high,low,close,volume,amount,percent",
                start_date=start_date,
                end_date=datetime.now().strftime('%Y-%m-%d'),
                frequency="d",
                adjustflag="3"  # 前复权
            )
            
            if rs.error_code != '0':
                print(f"Query error: {rs.error_msg}")
                return False
            
            # 转换为DataFrame
            data_list = []
            while (rs.error_code == '0') & rs.next():
                data_list.append(rs.get_row_data())
            
            if not data_list:
                return False
            
            df = pd.DataFrame(data_list, columns=rs.fields)
            
            # 数据处理
            df['date'] = pd.to_datetime(df['date'])
            df[['open', 'high', 'low', 'close', 'volume', 'amount', 'percent']] = \
                df[['open', 'high', 'low', 'close', 'volume', 'amount', 'percent']].astype(float)
            
            # 重命名列
            df.rename(columns={'percent': 'change_pct'}, inplace=True)
            
            # 保存数据
            self.util.save_stock_data(code, df, 'ashare')
            
            print(f"Download A-share {code} successfully")
            return True
        except Exception as e:
            print(f"Download A-share {code} error: {e}")
            return False
        finally:
            # 登出
            bs.logout()
    
    def download_all(self, start_date: str = '2010-01-01'):
        """下载全量A股数据
        
        Args:
            start_date: 开始日期
        """
        # 获取股票列表
        stock_list = self.get_stock_list()
        print(f"Total stocks: {len(stock_list)}")
        
        # 下载每个股票的数据
        success_count = 0
        fail_count = 0
        
        for i, code in enumerate(stock_list):
            print(f"Processing {i+1}/{len(stock_list)}: {code}")
            if self.download_stock(code, start_date):
                success_count += 1
            else:
                fail_count += 1
        
        print(f"Download completed: {success_count} success, {fail_count} fail")
        
        # 更新数据信息
        self.util.create_data_info('ashare')

if __name__ == '__main__':
    # 示例：下载全量A股数据
    downloader = BaoDownload()
    downloader.download_all()