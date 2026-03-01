from typing import Dict, Any, Optional
from .CommSnapshot import CommSnapshot

class StockSnapshotAPI:
    """统一调用接口"""
    
    def __init__(self):
        """初始化"""
        self.snapshot_apis = {}
    
    def register_api(self, name: str, api: CommSnapshot):
        """注册快照API
        
        Args:
            name: API名称
            api: 快照API实例
        """
        self.snapshot_apis[name] = api
    
    def get_snapshot(self, code: str, api_name: str = None) -> Optional[Dict[str, Any]]:
        """获取股票快照
        
        Args:
            code: 股票代码
            api_name: API名称（可选）
            
        Returns:
            股票快照信息
        """
        if api_name and api_name in self.snapshot_apis:
            # 指定API
            return self.snapshot_apis[api_name].get_snapshot(code)
        else:
            # 尝试所有API
            for name, api in self.snapshot_apis.items():
                if api.is_supported(code):
                    result = api.get_snapshot(code)
                    if result:
                        return result
        return None
    
    def get_multi_snapshot(self, codes: list[str], api_name: str = None) -> Dict[str, Optional[Dict[str, Any]]]:
        """批量获取股票快照
        
        Args:
            codes: 股票代码列表
            api_name: API名称（可选）
            
        Returns:
            股票快照信息字典
        """
        if api_name and api_name in self.snapshot_apis:
            # 指定API
            return self.snapshot_apis[api_name].get_multi_snapshot(codes)
        else:
            # 尝试所有API
            results = {}
            remaining_codes = codes.copy()
            
            for name, api in self.snapshot_apis.items():
                if not remaining_codes:
                    break
                
                # 筛选支持的代码
                supported_codes = [code for code in remaining_codes if api.is_supported(code)]
                if supported_codes:
                    api_results = api.get_multi_snapshot(supported_codes)
                    results.update(api_results)
                    # 移除已获取的代码
                    remaining_codes = [code for code in remaining_codes if code not in api_results]
            
            # 填充未获取的代码
            for code in remaining_codes:
                results[code] = None
            
            return results
    
    def get_api(self, name: str) -> Optional[CommSnapshot]:
        """获取指定API
        
        Args:
            name: API名称
            
        Returns:
            快照API实例
        """
        return self.snapshot_apis.get(name)
    
    def list_apis(self) -> list[str]:
        """列出所有注册的API
        
        Returns:
            API名称列表
        """
        return list(self.snapshot_apis.keys())

# 导出单例实例
snapshot_api = StockSnapshotAPI()