from typing import Dict, Any, Optional
from .CommSnapshot import CommSnapshot

class FutuSnapshot(CommSnapshot):
    """富途接口，支持a股，港股，美股"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """初始化
        
        Args:
            config: 配置参数
        """
        super().__init__(config)
        self.host = self.config.get('host', '127.0.0.1')
        self.port = self.config.get('port', 11111)
        self.user = self.config.get('user', '')
        self.password = self.config.get('password', '')
        self.api = None
        self._init_api()
    
    def _init_api(self):
        """初始化富途API"""
        try:
            from futu import OpenQuoteContext
            self.api = OpenQuoteContext(host=self.host, port=self.port)
        except ImportError:
            print("Futu API not installed, please install futu-api")
        except Exception as e:
            print(f"Futu API init error: {e}")
    
    def get_snapshot(self, code: str) -> Optional[Dict[str, Any]]:
        """获取股票快照
        
        Args:
            code: 股票代码
            
        Returns:
            股票快照信息
        """
        if not self.api:
            return None
        
        try:
            # 使用富途API获取实时数据
            ret, data = self.api.get_market_snapshot([code])
            if ret != 0 or data.empty:
                return None
            
            data = data.iloc[0].to_dict()
            return self._format_snapshot({
                'code': code,
                'name': data.get('stock_name', ''),
                'price': data.get('last_price', 0),
                'open': data.get('open_price', 0),
                'high': data.get('high_price', 0),
                'low': data.get('low_price', 0),
                'pre_close': data.get('prev_close_price', 0),
                'change': data.get('last_price', 0) - data.get('prev_close_price', 0),
                'change_pct': ((data.get('last_price', 0) - data.get('prev_close_price', 0)) / data.get('prev_close_price', 1)) * 100,
                'volume': data.get('volume', 0),
                'amount': data.get('turnover', 0),
                'time': data.get('update_time', None)
            })
        except Exception as e:
            print(f"FutuSnapshot get_snapshot error: {e}")
            return None
    
    def get_multi_snapshot(self, codes: list[str]) -> Dict[str, Optional[Dict[str, Any]]]:
        """批量获取股票快照
        
        Args:
            codes: 股票代码列表
            
        Returns:
            股票快照信息字典
        """
        if not self.api:
            return {code: None for code in codes}
        
        try:
            # 批量获取数据
            ret, data = self.api.get_market_snapshot(codes)
            if ret != 0:
                return {code: None for code in codes}
            
            results = {}
            for _, row in data.iterrows():
                code = row.get('code')
                results[code] = self._format_snapshot({
                    'code': code,
                    'name': row.get('stock_name', ''),
                    'price': row.get('last_price', 0),
                    'open': row.get('open_price', 0),
                    'high': row.get('high_price', 0),
                    'low': row.get('low_price', 0),
                    'pre_close': row.get('prev_close_price', 0),
                    'change': row.get('last_price', 0) - row.get('prev_close_price', 0),
                    'change_pct': ((row.get('last_price', 0) - row.get('prev_close_price', 0)) / row.get('prev_close_price', 1)) * 100,
                    'volume': row.get('volume', 0),
                    'amount': row.get('turnover', 0),
                    'time': row.get('update_time', None)
                })
            
            # 填充未获取的代码
            for code in codes:
                if code not in results:
                    results[code] = None
            
            return results
        except Exception as e:
            print(f"FutuSnapshot get_multi_snapshot error: {e}")
            return {code: None for code in codes}
    
    def is_supported(self, code: str) -> bool:
        """判断是否支持该股票
        
        Args:
            code: 股票代码
            
        Returns:
            是否支持
        """
        # 支持A股、港股、美股
        return (code.startswith('SH.') or code.startswith('SZ.') or 
                code.startswith('HK.') or code.endswith('.US'))
    
    def __del__(self):
        """析构函数，关闭API连接"""
        if self.api:
            try:
                self.api.close()
            except Exception:
                pass