from typing import Optional, Dict, Any
from .cos_config import cos_config

class MinioApi:
    """minio上传接口"""
    
    def __init__(self):
        """初始化"""
        self.config = cos_config
        self.client = None
        self._init_client()
    
    def _init_client(self):
        """初始化客户端"""
        try:
            from minio import Minio
            
            # 初始化客户端
            self.client = Minio(
                self.config.get_endpoint() or 'localhost:9000',
                access_key=self.config.get_secret_id(),
                secret_key=self.config.get_secret_key(),
                secure=False  # 根据实际情况设置
            )
            
            # 检查bucket是否存在
            if not self.client.bucket_exists(self.config.get_bucket()):
                self.client.make_bucket(self.config.get_bucket())
        except ImportError:
            print("Minio SDK not installed, please install minio")
        except Exception as e:
            print(f"Init Minio client error: {e}")
    
    def upload_file(self, local_file: str, cloud_path: str) -> Optional[str]:
        """上传文件
        
        Args:
            local_file: 本地文件路径
            cloud_path: 云端路径
            
        Returns:
            访问URL
        """
        if not self.client:
            return None
        
        try:
            # 上传文件
            self.client.fput_object(
                self.config.get_bucket(),
                cloud_path,
                local_file
            )
            
            # 生成访问URL
            url = f"http://{self.config.get_endpoint() or 'localhost:9000'}/{self.config.get_bucket()}/{cloud_path}"
            return url
        except Exception as e:
            print(f"Upload file error: {e}")
            return None
    
    def upload_bytes(self, data: bytes, cloud_path: str, content_type: str = 'application/octet-stream') -> Optional[str]:
        """上传字节数据
        
        Args:
            data: 字节数据
            cloud_path: 云端路径
            content_type: 内容类型
            
        Returns:
            访问URL
        """
        if not self.client:
            return None
        
        try:
            # 上传数据
            self.client.put_object(
                self.config.get_bucket(),
                cloud_path,
                data,
                len(data),
                content_type=content_type
            )
            
            # 生成访问URL
            url = f"http://{self.config.get_endpoint() or 'localhost:9000'}/{self.config.get_bucket()}/{cloud_path}"
            return url
        except Exception as e:
            print(f"Upload bytes error: {e}")
            return None
    
    def delete_file(self, cloud_path: str) -> bool:
        """删除文件
        
        Args:
            cloud_path: 云端路径
            
        Returns:
            是否删除成功
        """
        if not self.client:
            return False
        
        try:
            # 删除文件
            self.client.remove_object(
                self.config.get_bucket(),
                cloud_path
            )
            return True
        except Exception as e:
            print(f"Delete file error: {e}")
            return False
    
    def get_file_url(self, cloud_path: str, expires: int = 3600) -> Optional[str]:
        """获取文件URL
        
        Args:
            cloud_path: 云端路径
            expires: 过期时间（秒）
            
        Returns:
            文件URL
        """
        if not self.client:
            return None
        
        try:
            # 生成预签名URL
            url = self.client.presigned_get_object(
                self.config.get_bucket(),
                cloud_path,
                expires=expires
            )
            return url
        except Exception as e:
            print(f"Get file URL error: {e}")
            return None

if __name__ == '__main__':
    # 示例：上传文件
    minio_api = MinioApi()
    # url = minio_api.upload_file('test.txt', 'test/test.txt')
    # print(f"Upload URL: {url}")