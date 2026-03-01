import baostock as bs
import pandas as pd
from datetime import datetime, timedelta
from .offline_data_util import OfflineDataUtil

class BaoUpdate:
    """baostock增量更新数据"""
    
    def __init__(self, data_dir: str = './data'):
        """初始化
        
        Args:
            data_dir: 数据存储目录
        """
        self.util = OfflineDataUtil(data_dir)
    
    def update_stock(self, code: str) -> bool:
        """更新单个股票数据
        
        Args:
            code: 股票代码
            
        Returns:
            是否更新成功
        """
        # 登录baostock
        lg = bs.login()
        if lg.error_code != '0':
            print(f"Login error: {lg.error_msg}")
            return False
        
        try:
            # 获取最后更新日期
            last_date = self.util.get_last_update_date(code, 'ashare')
            
            # 确定开始日期
            if last_date:
                start_date = (last_date + timedelta(days=1)).strftime('%Y-%m-%d')
            else:
                start_date = '2010-01-01'
            
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
        finally:
            # 登出
            bs.logout()
    
    def update_all(self):
        """更新所有A股数据"""
        # 获取已有的股票列表
        stock_list = self.util.get_stock_list('ashare')
        print(f"Total stocks: {len(stock_list)}")
        
        # 更新每个股票的数据
        success_count = 0
        fail_count = 0
        
        for i, code in enumerate(stock_list):
            print(f"Processing {i+1}/{len(stock_list)}: {code}")
            if self.update_stock(code):
                success_count += 1
            else:
                fail_count += 1
        
        print(f"Update completed: {success_count} success, {fail_count} fail")
        
        # 更新数据信息
        self.util.create_data_info('ashare')

if __name__ == '__main__':
    # 示例：更新所有A股数据
    updater = BaoUpdate()
    updater.update_all()