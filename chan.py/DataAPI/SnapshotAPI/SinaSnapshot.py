import requests
import json
from typing import Dict, Any, Optional
from .CommSnapshot import CommSnapshot

class SinaSnapshot(CommSnapshot):
    """新浪接口，支持a股，etf，港股，美股"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """初始化
        
        Args:
            config: 配置参数
        """
        super().__init__(config)
        self.timeout = self.config.get('timeout', 10)
    
    def get_snapshot(self, code: str) -> Optional[Dict[str, Any]]:
        """获取股票快照
        
        Args:
            code: 股票代码
            
        Returns:
            股票快照信息
        """
        try:
            # 转换代码格式
            sina_code = self._convert_to_sina_code(code)
            if not sina_code:
                return None
            
            # 构建URL
            url = f"http://hq.sinajs.cn/list={sina_code}"
            
            # 发送请求
            response = requests.get(url, timeout=self.timeout)
            response.encoding = 'gb2312'
            
            # 解析响应
            data = self._parse_sina_response(response.text, code)
            if data:
                return self._format_snapshot(data)
            return None
        except Exception as e:
            print(f"SinaSnapshot get_snapshot error: {e}")
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
    
    def _convert_to_sina_code(self, code: str) -> Optional[str]:
        """转换为新浪代码格式
        
        Args:
            code: 股票代码
            
        Returns:
            新浪代码格式
        """
        if code.startswith('6'):
            # 沪市A股
            return f"sh{code}"
        elif code.startswith('0') or code.startswith('3'):
            # 深市A股
            return f"sz{code}"
        elif code.startswith('HK.'):
            # 港股
            return f"hk{code[3:]}"
        elif code.endswith('.US'):
            # 美股
            return f"gb_{code[:-3]}"
        return None
    
    def _parse_sina_response(self, response_text: str, code: str) -> Optional[Dict[str, Any]]:
        """解析新浪响应
        
        Args:
            response_text: 响应文本
            code: 原始股票代码
            
        Returns:
            解析后的数据
        """
        try:
            # 提取数据部分
            if '=' in response_text:
                data_str = response_text.split('=')[1].strip().strip('"')
                data_list = data_str.split(',')
                
                if len(data_list) < 11:
                    return None
                
                # 解析数据
                if code.startswith('6') or code.startswith('0') or code.startswith('3'):
                    # A股
                    return {
                        'code': code,
                        'name': data_list[0],
                        'price': float(data_list[3]),
                        'open': float(data_list[1]),
                        'high': float(data_list[4]),
                        'low': float(data_list[5]),
                        'pre_close': float(data_list[2]),
                        'change': float(data_list[3]) - float(data_list[2]),
                        'change_pct': ((float(data_list[3]) - float(data_list[2])) / float(data_list[2])) * 100,
                        'volume': float(data_list[8]),
                        'amount': float(data_list[9]),
                        'time': data_list[30] + ' ' + data_list[31]
                    }
                elif code.startswith('HK.'):
                    # 港股
                    return {
                        'code': code,
                        'name': data_list[1],
                        'price': float(data_list[6]),
                        'open': float(data_list[2]),
                        'high': float(data_list[3]),
                        'low': float(data_list[4]),
                        'pre_close': float(data_list[5]),
                        'change': float(data_list[6]) - float(data_list[5]),
                        'change_pct': ((float(data_list[6]) - float(data_list[5])) / float(data_list[5])) * 100,
                        'volume': float(data_list[12]),
                        'amount': float(data_list[13]),
                        'time': data_list[0]
                    }
                elif code.endswith('.US'):
                    # 美股
                    return {
                        'code': code,
                        'name': data_list[0],
                        'price': float(data_list[1]),
                        'open': float(data_list[5]),
                        'high': float(data_list[3]),
                        'low': float(data_list[4]),
                        'pre_close': float(data_list[2]),
                        'change': float(data_list[1]) - float(data_list[2]),
                        'change_pct': ((float(data_list[1]) - float(data_list[2])) / float(data_list[2])) * 100,
                        'volume': float(data_list[6]),
                        'amount': float(data_list[7]),
                        'time': data_list[8]
                    }
        except Exception:
            pass
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