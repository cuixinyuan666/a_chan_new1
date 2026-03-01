import akshare as ak
import pandas as pd
from datetime import datetime
from .offline_data_util import OfflineDataUtil

class EtfDownload:
    """下载A股ETF数据脚本"""
    
    def __init__(self, data_dir: str = './data'):
        """初始化
        
        Args:
            data_dir: 数据存储目录
        """
        self.util = OfflineDataUtil(data_dir)
    
    def get_etf_list(self) -> list[str]:
        """获取ETF列表
        
        Returns:
            ETF代码列表
        """
        try:
            # 使用akshare获取ETF列表
            df = ak.fund_etf_category_sina()
            etf_list = df['代码'].tolist()
            return etf_list
        except Exception as e:
            print(f"Get ETF list error: {e}")
            return []
    
    def download_etf(self, code: str, start_date: str = '2010-01-01') -> bool:
        """下载单个ETF数据
        
        Args:
            code: ETF代码
            start_date: 开始日期
            
        Returns:
            是否下载成功
        """
        try:
            # 获取数据
            df = ak.fund_etf_hist_em(
                symbol=code,
                period="daily",
                start_date=start_date,
                end_date=datetime.now().strftime('%Y-%m-%d'),
                adjust="qfq"
            )
            
            if df.empty:
                return False
            
            # 数据处理
            df = df[['日期', '开盘', '最高', '最低', '收盘', '成交量', '成交额', '涨跌幅']]
            df.columns = ['date', 'open', 'high', 'low', 'close', 'volume', 'amount', 'change_pct']
            df['date'] = pd.to_datetime(df['date'])
            
            # 保存数据
            self.util.save_stock_data(code, df, 'etf')
            
            print(f"Download ETF {code} successfully")
            return True
        except Exception as e:
            print(f"Download ETF {code} error: {e}")
            return False
    
    def download_all(self, start_date: str = '2010-01-01'):
        """下载所有ETF数据
        
        Args:
            start_date: 开始日期
        """
        # 获取ETF列表
        etf_list = self.get_etf_list()
        print(f"Total ETFs: {len(etf_list)}")
        
        # 下载每个ETF的数据
        success_count = 0
        fail_count = 0
        
        for i, code in enumerate(etf_list):
            print(f"Processing {i+1}/{len(etf_list)}: {code}")
            if self.download_etf(code, start_date):
                success_count += 1
            else:
                fail_count += 1
        
        print(f"Download completed: {success_count} success, {fail_count} fail")
        
        # 更新数据信息
        self.util.create_data_info('etf')

if __name__ == '__main__':
    # 示例：下载所有ETF数据
    downloader = EtfDownload()
    downloader.download_all()