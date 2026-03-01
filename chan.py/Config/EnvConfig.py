import os
import yaml

class Env:
    """配置管理类"""
    _instance = None
    _config = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Env, cls).__new__(cls)
            cls._instance._load_config()
        return cls._instance
    
    def _load_config(self):
        """加载配置"""
        # 尝试从YAML文件加载配置
        config_file = os.path.join(os.path.dirname(__file__), 'demo_config.yaml')
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                self._config.update(yaml.safe_load(f))
        
        # 从环境变量加载配置，覆盖文件配置
        for key, value in os.environ.items():
            if key.startswith('CHAN_'):
                config_key = key[5:].lower()
                self._config[config_key] = value
    
    def get(self, key, default=None):
        """获取配置值"""
        return self._config.get(key, default)
    
    def set(self, key, value):
        """设置配置值"""
        self._config[key] = value
    
    def __getitem__(self, key):
        """支持通过[]访问配置"""
        return self._config[key]
    
    def __contains__(self, key):
        """支持in操作符"""
        return key in self._config

# 导出单例实例
env = Env()