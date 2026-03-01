from Config.EnvConfig import env
from typing import Dict, Any, Optional

class CosConfig:
    """读取项目配置里面的cos配置参数"""
    
    def __init__(self):
        """初始化"""
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置
        
        Returns:
            COS配置
        """
        # 从环境变量或配置文件加载
        cos_config = {
            'enable': env.get('plot.cos.enable', False),
            'type': env.get('plot.cos.type', 'tencent'),
            'secret_id': env.get('plot.cos.secret_id', ''),
            'secret_key': env.get('plot.cos.secret_key', ''),
            'bucket': env.get('plot.cos.bucket', ''),
            'region': env.get('plot.cos.region', ''),
            'endpoint': env.get('plot.cos.endpoint', '')
        }
        return cos_config
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值
        
        Args:
            key: 配置键
            default: 默认值
            
        Returns:
            配置值
        """
        return self.config.get(key, default)
    
    def is_enabled(self) -> bool:
        """是否启用COS
        
        Returns:
            是否启用
        """
        return self.config.get('enable', False)
    
    def get_cos_type(self) -> str:
        """获取COS类型
        
        Returns:
            COS类型
        """
        return self.config.get('type', 'tencent')
    
    def get_secret_id(self) -> str:
        """获取Secret ID
        
        Returns:
            Secret ID
        """
        return self.config.get('secret_id', '')
    
    def get_secret_key(self) -> str:
        """获取Secret Key
        
        Returns:
            Secret Key
        """
        return self.config.get('secret_key', '')
    
    def get_bucket(self) -> str:
        """获取Bucket
        
        Returns:
            Bucket
        """
        return self.config.get('bucket', '')
    
    def get_region(self) -> str:
        """获取Region
        
        Returns:
            Region
        """
        return self.config.get('region', '')
    
    def get_endpoint(self) -> str:
        """获取Endpoint
        
        Returns:
            Endpoint
        """
        return self.config.get('endpoint', '')

# 导出单例实例
cos_config = CosConfig()