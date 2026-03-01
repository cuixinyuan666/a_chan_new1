from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import pandas as pd

class CModelGenerator(ABC):
    """训练模型通用父类"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """初始化
        
        Args:
            config: 模型配置参数
        """
        self.config = config or {}
    
    @abstractmethod
    def train(self, X: pd.DataFrame, y: pd.Series) -> Any:
        """训练模型
        
        Args:
            X: 特征数据
            y: 标签数据
            
        Returns:
            训练好的模型
        """
        pass
    
    @abstractmethod
    def predict(self, model: Any, X: pd.DataFrame) -> pd.Series:
        """预测
        
        Args:
            model: 训练好的模型
            X: 特征数据
            
        Returns:
            预测结果
        """
        pass
    
    @abstractmethod
    def save_model(self, model: Any, path: str):
        """保存模型
        
        Args:
            model: 训练好的模型
            path: 保存路径
        """
        pass
    
    @abstractmethod
    def load_model(self, path: str) -> Any:
        """加载模型
        
        Args:
            path: 模型路径
            
        Returns:
            加载的模型
        """
        pass
    
    def evaluate(self, y_true: pd.Series, y_pred: pd.Series) -> Dict[str, float]:
        """评估模型
        
        Args:
            y_true: 真实标签
            y_pred: 预测标签
            
        Returns:
            评估指标
        """
        from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
        
        return {
            'accuracy': accuracy_score(y_true, y_pred),
            'precision': precision_score(y_true, y_pred, average='weighted'),
            'recall': recall_score(y_true, y_pred, average='weighted'),
            'f1_score': f1_score(y_true, y_pred, average='weighted')
        }

class CDataSet:
    """数据集类"""
    
    def __init__(self, X: pd.DataFrame = None, y: pd.Series = None):
        """初始化
        
        Args:
            X: 特征数据
            y: 标签数据
        """
        self.X = X
        self.y = y
    
    def load_from_csv(self, X_path: str, y_path: str = None):
        """从CSV加载数据
        
        Args:
            X_path: 特征数据路径
            y_path: 标签数据路径
        """
        self.X = pd.read_csv(X_path)
        if y_path:
            self.y = pd.read_csv(y_path).squeeze()
    
    def save_to_csv(self, X_path: str, y_path: str = None):
        """保存数据到CSV
        
        Args:
            X_path: 特征数据路径
            y_path: 标签数据路径
        """
        self.X.to_csv(X_path, index=False)
        if y_path and self.y is not None:
            self.y.to_csv(y_path, index=False)
    
    def split(self, test_size: float = 0.2, random_state: int = 42) -> tuple:
        """分割数据集
        
        Args:
            test_size: 测试集比例
            random_state: 随机种子
            
        Returns:
            (X_train, X_test, y_train, y_test)
        """
        from sklearn.model_selection import train_test_split
        return train_test_split(self.X, self.y, test_size=test_size, random_state=random_state)
    
    def get_feature_names(self) -> List[str]:
        """获取特征名称
        
        Returns:
            特征名称列表
        """
        if self.X is not None:
            return list(self.X.columns)
        return []
    
    def shape(self) -> tuple:
        """获取数据集形状
        
        Returns:
            (样本数, 特征数)
        """
        if self.X is not None:
            return self.X.shape
        return (0, 0)