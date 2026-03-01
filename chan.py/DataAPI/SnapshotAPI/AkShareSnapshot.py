import akshare as ak
from typing import Dict, Any, Optional
from .CommSnapshot import CommSnapshot

class AkShareSnapshot(CommSnapshot):
    """akshare接口，支持a股，etf，港股，美股"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """初始化
        
        Args:
            config: 配置参数
        """
        super().__init__(config)
        self.timeout = self.config.get('timeout', 30)
    
    def get_snapshot(self, code: str) -> Optional[Dict[str, Any]]:
        """获取股票快照
        
        Args:
            code: 股票代码
            
        Returns:
            股票快照信息
        """
        try:
            # 根据代码类型选择不同的接口
            if code.startswith('6') or code.startswith('0') or code.startswith('3'):
                # A股
                return self._get_ashare_snapshot(code)
            elif code.startswith('HK.'):
                # 港股
                return self._get_hkshare_snapshot(code)
            elif code.endswith('.US'):
                # 美股
                return self._get_usshare_snapshot(code)
            else:
                return None
        except Exception as e:
            print(f"AkShareSnapshot get_snapshot error: {e}")
            return None
    
    def get_multi_snapshot(self, codes: list[str]) -> Dict[str, Optional[Dict[str, Any]]]:
        """批量获取股票快照
        
        Args:
            codes: 股票代码列表
            
        Returns:
            股票快照信息字典
        """
        results = {}
        for code in codes:
            results[code] = self.get_snapshot(code)
        return results
    
    def _get_ashare_snapshot(self, code: str) -> Optional[Dict[str, Any]]:
        """获取A股快照
        
        Args:
            code: 股票代码
            
        Returns:
            股票快照信息
        """
        try:
            # 使用akshare获取A股实时数据
            df = ak.stock_zh_a_spot_em()
            stock_data = df[df['代码'] == code]
            if stock_data.empty:
                return None
            
            data = stock_data.iloc[0].to_dict()
            return self._format_snapshot({
                'code': code,
                'name': data.get('名称', ''),
                'price': data.get('最新价', 0),
                'open': data.get('开盘价', 0),
                'high': data.get('最高价', 0),
                'low': data.get('最低价', 0),
                'pre_close': data.get('昨收价', 0),
                'change': data.get('涨跌额', 0),
                'change_pct': data.get('涨跌幅', 0),
                'volume': data.get('成交量', 0),
                'amount': data.get('成交额', 0),
                'time': None
            })
        except Exception:
            return None
    
    def _get_hkshare_snapshot(self, code: str) -> Optional[Dict[str, Any]]:
        """获取港股快照
        
        Args:
            code: 股票代码
            
        Returns:
            股票快照信息
        """
        try:
            # 使用akshare获取港股实时数据
            df = ak.stock_hk_spot_em()
            stock_data = df[df['代码'] == code.replace('HK.', '')]
            if stock_data.empty:
                return None
            
            data = stock_data.iloc[0].to_dict()
            return self._format_snapshot({
                'code': code,
                'name': data.get('名称', ''),
                'price': data.get('最新价', 0),
                'open': data.get('开盘价', 0),
                'high': data.get('最高价', 0),
                'low': data.get('最低价', 0),
                'pre_close': data.get('昨收价', 0),
                'change': data.get('涨跌额', 0),
                'change_pct': data.get('涨跌幅', 0),
                'volume': data.get('成交量', 0),
                'amount': data.get('成交额', 0),
                'time': None
            })
        except Exception:
            return None
    
    def _get_usshare_snapshot(self, code: str) -> Optional[Dict[str, Any]]:
        """获取美股快照
        
        Args:
            code: 股票代码
            
        Returns:
            股票快照信息
        """
        try:
            # 使用akshare获取美股实时数据
            df = ak.stock_us_spot_em()
            stock_data = df[df['代码'] == code.replace('.US', '')]
            if stock_data.empty:
                return None
            
            data = stock_data.iloc[0].to_dict()
            return self._format_snapshot({
                'code': code,
                'name': data.get('名称', ''),
                'price': data.get('最新价', 0),
                'open': data.get('开盘价', 0),
                'high': data.get('最高价', 0),
                'low': data.get('最低价', 0),
                'pre_close': data.get('昨收价', 0),
                'change': data.get('涨跌额', 0),
                'change_pct': data.get('涨跌幅', 0),
                'volume': data.get('成交量', 0),
                'amount': data.get('成交额', 0),
                'time': None
            })
        except Exception:
            return None
    
    def is_supported(self, code: str) -> bool:
        """判断是否支持该股票
        
        Args:
            code: 股票代码
            
        Returns:
            是否支持
        """
        # 支持A股、港股、美股
        return (code.startswith('6') or code.startswith('0') or code.startswith('3') or 
                code.startswith('HK.') or code.endswith('.US'))