from typing import Dict, Any, Optional
from .CommSnapshot import CommSnapshot

class PytdxSnapshot(CommSnapshot):
    """pytdx，支持A股，ETF"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """初始化
        
        Args:
            config: 配置参数
        """
        super().__init__(config)
        self.api = None
        self._init_api()
    
    def _init_api(self):
        """初始化pytdx API"""
        try:
            from pytdx.hq import TdxHq_API
            self.api = TdxHq_API()
            # 连接服务器
            self.api.connect('119.147.212.81', 7709)
        except ImportError:
            print("Pytdx not installed, please install pytdx")
        except Exception as e:
            print(f"Pytdx init error: {e}")
    
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
            # 解析代码
            market = self._get_market(code)
            if market is None:
                return None
            
            # 使用pytdx获取实时数据
            data = self.api.get_security_quotes([(market, code)])[0]
            return self._format_snapshot({
                'code': code,
                'name': '',  # pytdx需要单独获取股票名称
                'price': data['price'],
                'open': data['open'],
                'high': data['high'],
                'low': data['low'],
                'pre_close': data['last_close'],
                'change': data['price'] - data['last_close'],
                'change_pct': ((data['price'] - data['last_close']) / data['last_close']) * 100,
                'volume': data['vol'],
                'amount': data['amount'],
                'time': None
            })
        except Exception as e:
            print(f"PytdxSnapshot get_snapshot error: {e}")
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
            # 构建请求参数
            quotes = []
            for code in codes:
                market = self._get_market(code)
                if market is not None:
                    quotes.append((market, code))
            
            if not quotes:
                return {code: None for code in codes}
            
            # 批量获取数据
            data_list = self.api.get_security_quotes(quotes)
            
            results = {}
            for i, data in enumerate(data_list):
                code = quotes[i][1]
                results[code] = self._format_snapshot({
                    'code': code,
                    'name': '',
                    'price': data['price'],
                    'open': data['open'],
                    'high': data['high'],
                    'low': data['low'],
                    'pre_close': data['last_close'],
                    'change': data['price'] - data['last_close'],
                    'change_pct': ((data['price'] - data['last_close']) / data['last_close']) * 100,
                    'volume': data['vol'],
                    'amount': data['amount'],
                    'time': None
                })
            
            # 填充未获取的代码
            for code in codes:
                if code not in results:
                    results[code] = None
            
            return results
        except Exception as e:
            print(f"PytdxSnapshot get_multi_snapshot error: {e}")
            return {code: None for code in codes}
    
    def _get_market(self, code: str) -> Optional[int]:
        """获取市场代码
        
        Args:
            code: 股票代码
            
        Returns:
            市场代码
        """
        # 上海市场
        if code.startswith('6'):
            return 1
        # 深圳市场
        elif code.startswith('0') or code.startswith('3'):
            return 0
        return None
    
    def is_supported(self, code: str) -> bool:
        """判断是否支持该股票
        
        Args:
            code: 股票代码
            
        Returns:
            是否支持
        """
        # 支持A股和ETF
        return code.startswith('6') or code.startswith('0') or code.startswith('3')
    
    def __del__(self):
        """析构函数，关闭API连接"""
        if self.api:
            try:
                self.api.disconnect()
            except Exception:
                pass