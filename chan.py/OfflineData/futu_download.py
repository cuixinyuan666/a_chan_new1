from datetime import datetime, timedelta
from typing import List
from .offline_data_util import OfflineDataUtil

class FutuDownload:
    """更新futu港股数据"""
    
    def __init__(self, data_dir: str = './data'):
        """初始化
        
        Args:
            data_dir: 数据存储目录
        """
        self.util = OfflineDataUtil(data_dir)
        self.api = None
        self._init_api()
    
    def _init_api(self):
        """初始化富途API"""
        try:
            from futu import OpenQuoteContext
            self.api = OpenQuoteContext(host='127.0.0.1', port=11111)
        except ImportError:
            print("Futu API not installed, please install futu-api")
        except Exception as e:
            print(f"Futu API init error: {e}")
    
    def download_hk_stock(self, code: str, start_date: str = '2010-01-01') -> bool:
        """下载港股数据
        
        Args:
            code: 股票代码
            start_date: 开始日期
            
        Returns:
            是否下载成功
        """
        if not self.api:
            return False
        
        try:
            # 构建富途代码
            futu_code = f"HK.{code}"
            
            # 获取数据
            ret, data = self.api.request_history_kline(
                futu_code,
                start=start_date,
                end=datetime.now().strftime('%Y-%m-%d'),
                ktype='K_DAY',
                autype='qfq'
            )
            
            if ret != 0 or data.empty:
                return False
            
            # 数据处理
            data = data[['time_key', 'open', 'high', 'low', 'close', 'volume', 'turnover']]
            data.columns = ['date', 'open', 'high', 'low', 'close', 'volume', 'amount']
            data['date'] = data['date'].apply(lambda x: datetime.strptime(x, '%Y-%m-%d'))
            
            # 计算涨跌幅
            data['change_pct'] = (data['close'] - data['close'].shift(1)) / data['close'].shift(1) * 100
            data['change_pct'].fillna(0, inplace=True)
            
            # 保存数据
            self.util.save_stock_data(code, data, 'hkshare')
            
            print(f"Download HK-share {code} successfully")
            return True
        except Exception as e:
            print(f"Download HK-share {code} error: {e}")
            return False
    
    def update_hk_stock(self, code: str) -> bool:
        """更新港股数据
        
        Args:
            code: 股票代码
            
        Returns:
            是否更新成功
        """
        if not self.api:
            return False
        
        try:
            # 获取最后更新日期
            last_date = self.util.get_last_update_date(code, 'hkshare')
            
            # 确定开始日期
            if last_date:
                start_date = (last_date + timedelta(days=1)).strftime('%Y-%m-%d')
            else:
                start_date = '2010-01-01'
            
            # 构建富途代码
            futu_code = f"HK.{code}"
            
            # 获取数据
            ret, data = self.api.request_history_kline(
                futu_code,
                start=start_date,
                end=datetime.now().strftime('%Y-%m-%d'),
                ktype='K_DAY',
                autype='qfq'
            )
            
            if ret != 0 or data.empty:
                return False
            
            # 数据处理
            data = data[['time_key', 'open', 'high', 'low', 'close', 'volume', 'turnover']]
            data.columns = ['date', 'open', 'high', 'low', 'close', 'volume', 'amount']
            data['date'] = data['date'].apply(lambda x: datetime.strptime(x, '%Y-%m-%d'))
            
            # 计算涨跌幅
            data['change_pct'] = (data['close'] - data['close'].shift(1)) / data['close'].shift(1) * 100
            data['change_pct'].fillna(0, inplace=True)
            
            # 加载旧数据
            old_df = self.util.load_stock_data(code, 'hkshare')
            
            # 合并数据
            merged_df = self.util.merge_data(old_df, data)
            
            # 保存数据
            self.util.save_stock_data(code, merged_df, 'hkshare')
            
            print(f"Update HK-share {code} successfully")
            return True
        except Exception as e:
            print(f"Update HK-share {code} error: {e}")
            return False
    
    def update_all(self, hk_codes: List[str]):
        """更新所有港股数据
        
        Args:
            hk_codes: 港股代码列表
        """
        # 更新每个港股的数据
        success_count = 0
        fail_count = 0
        
        for i, code in enumerate(hk_codes):
            print(f"Processing {i+1}/{len(hk_codes)}: {code}")
            if self.update_hk_stock(code):
                success_count += 1
            else:
                fail_count += 1
        
        print(f"Update completed: {success_count} success, {fail_count} fail")
        
        # 更新数据信息
        self.util.create_data_info('hkshare')
    
    def __del__(self):
        """析构函数，关闭API连接"""
        if self.api:
            try:
                self.api.close()
            except Exception:
                pass

if __name__ == '__main__':
    # 示例：更新港股数据
    downloader = FutuDownload()
    downloader.update_all(['00700', '00001'])