from typing import Optional, Dict, Any
from .cos_config import cos_config
from .tencent_cos_api import TencentCosApi
from .minio_api import MinioApi

class CosApi:
    """通用cos上传接口，自动选择上传接口"""
    
    def __init__(self):
        """初始化"""
        self.config = cos_config
        self.api = self._get_api()
    
    def _get_api(self):
        """获取API实例
        
        Returns:
            API实例
        """
        if not self.config.is_enabled():
            return None
        
        cos_type = self.config.get_cos_type()
        
        if cos_type == 'tencent':
            return TencentCosApi()
        elif cos_type == 'minio':
            return MinioApi()
        else:
            print(f"Unsupported COS type: {cos_type}")
            return None
    
    def upload_file(self, local_file: str, cloud_path: str) -> Optional[str]:
        """上传文件
        
        Args:
            local_file: 本地文件路径
            cloud_path: 云端路径
            
        Returns:
            访问URL
        """
        if not self.api:
            return None
        
        return self.api.upload_file(local_file, cloud_path)
    
    def upload_bytes(self, data: bytes, cloud_path: str, content_type: str = 'application/octet-stream') -> Optional[str]:
        """上传字节数据
        
        Args:
            data: 字节数据
            cloud_path: 云端路径
            content_type: 内容类型
            
        Returns:
            访问URL
        """
        if not self.api:
            return None
        
        if hasattr(self.api, 'upload_bytes'):
            return self.api.upload_bytes(data, cloud_path, content_type)
        else:
            return self.api.upload_bytes(data, cloud_path)
    
    def delete_file(self, cloud_path: str) -> bool:
        """删除文件
        
        Args:
            cloud_path: 云端路径
            
        Returns:
            是否删除成功
        """
        if not self.api:
            return False
        
        return self.api.delete_file(cloud_path)
    
    def get_file_url(self, cloud_path: str, expires: int = 3600) -> Optional[str]:
        """获取文件URL
        
        Args:
            cloud_path: 云端路径
            expires: 过期时间（秒）
            
        Returns:
            文件URL
        """
        if not self.api:
            return None
        
        return self.api.get_file_url(cloud_path, expires)

# 导出单例实例
cos_api = CosApi()