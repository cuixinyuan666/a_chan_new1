from typing import Optional, Dict, Any
from .cos_config import cos_config

class TencentCosApi:
    """腾讯云cos上传接口"""
    
    def __init__(self):
        """初始化"""
        self.config = cos_config
        self.client = None
        self._init_client()
    
    def _init_client(self):
        """初始化客户端"""
        try:
            from qcloud_cos import CosConfig
            from qcloud_cos import CosS3Client
            
            # 初始化配置
            config = CosConfig(
                Region=self.config.get_region(),
                SecretId=self.config.get_secret_id(),
                SecretKey=self.config.get_secret_key()
            )
            
            # 初始化客户端
            self.client = CosS3Client(config)
        except ImportError:
            print("QCloud COS SDK not installed, please install cos-python-sdk-v5")
        except Exception as e:
            print(f"Init Tencent COS client error: {e}")
    
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
            response = self.client.upload_file(
                Bucket=self.config.get_bucket(),
                LocalFilePath=local_file,
                Key=cloud_path,
                PartSize=10,
                MAXThread=10
            )
            
            # 生成访问URL
            url = f"https://{self.config.get_bucket()}.cos.{self.config.get_region()}.myqcloud.com/{cloud_path}"
            return url
        except Exception as e:
            print(f"Upload file error: {e}")
            return None
    
    def upload_bytes(self, data: bytes, cloud_path: str) -> Optional[str]:
        """上传字节数据
        
        Args:
            data: 字节数据
            cloud_path: 云端路径
            
        Returns:
            访问URL
        """
        if not self.client:
            return None
        
        try:
            # 上传数据
            response = self.client.put_object(
                Bucket=self.config.get_bucket(),
                Body=data,
                Key=cloud_path
            )
            
            # 生成访问URL
            url = f"https://{self.config.get_bucket()}.cos.{self.config.get_region()}.myqcloud.com/{cloud_path}"
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
            response = self.client.delete_object(
                Bucket=self.config.get_bucket(),
                Key=cloud_path
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
            url = self.client.get_presigned_url(
                Bucket=self.config.get_bucket(),
                Key=cloud_path,
                HttpMethod='GET',
                Expires=expires
            )
            return url
        except Exception as e:
            print(f"Get file URL error: {e}")
            return None

if __name__ == '__main__':
    # 示例：上传文件
    cos_api = TencentCosApi()
    # url = cos_api.upload_file('test.txt', 'test/test.txt')
    # print(f"Upload URL: {url}")