import xgboost as xgb
import pandas as pd
from typing import Dict, Any, List
from .CommModel import CModelGenerator

class CXGBModel(CModelGenerator):
    """XGB模型 demo"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """初始化
        
        Args:
            config: 模型配置参数
        """
        super().__init__(config)
        self.params = {
            'objective': 'binary:logistic',
            'max_depth': self.config.get('max_depth', 6),
            'learning_rate': self.config.get('learning_rate', 0.1),
            'n_estimators': self.config.get('n_estimators', 100),
            'subsample': self.config.get('subsample', 0.8),
            'colsample_bytree': self.config.get('colsample_bytree', 0.8),
            'random_state': self.config.get('random_state', 42)
        }
    
    def train(self, X: pd.DataFrame, y: pd.Series) -> Any:
        """训练模型
        
        Args:
            X: 特征数据
            y: 标签数据
            
        Returns:
            训练好的模型
        """
        model = xgb.XGBClassifier(**self.params)
        model.fit(X, y)
        return model
    
    def predict(self, model: Any, X: pd.DataFrame) -> pd.Series:
        """预测
        
        Args:
            model: 训练好的模型
            X: 特征数据
            
        Returns:
            预测结果
        """
        return model.predict(X)
    
    def predict_proba(self, model: Any, X: pd.DataFrame) -> pd.DataFrame:
        """预测概率
        
        Args:
            model: 训练好的模型
            X: 特征数据
            
        Returns:
            预测概率
        """
        return model.predict_proba(X)
    
    def save_model(self, model: Any, path: str):
        """保存模型
        
        Args:
            model: 训练好的模型
            path: 保存路径
        """
        model.save_model(path)
    
    def load_model(self, path: str) -> Any:
        """加载模型
        
        Args:
            path: 模型路径
            
        Returns:
            加载的模型
        """
        model = xgb.XGBClassifier()
        model.load_model(path)
        return model
    
    def get_feature_importance(self, model: Any) -> Dict[str, float]:
        """获取特征重要性
        
        Args:
            model: 训练好的模型
            
        Returns:
            特征重要性字典
        """
        feature_importance = model.feature_importances_
        feature_names = model.get_booster().feature_names
        return dict(zip(feature_names, feature_importance))
    
    def plot_feature_importance(self, model: Any, top_n: int = 10):
        """绘制特征重要性
        
        Args:
            model: 训练好的模型
            top_n: 显示前N个重要特征
        """
        import matplotlib.pyplot as plt
        
        feature_importance = self.get_feature_importance(model)
        sorted_importance = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)[:top_n]
        
        features = [item[0] for item in sorted_importance]
        importance = [item[1] for item in sorted_importance]
        
        plt.figure(figsize=(10, 6))
        plt.barh(features, importance)
        plt.xlabel('Importance')
        plt.ylabel('Feature')
        plt.title('Top {} Feature Importance'.format(top_n))
        plt.gca().invert_yaxis()
        plt.show()

if __name__ == '__main__':
    # 示例：使用XGB模型
    import numpy as np
    from sklearn.datasets import make_classification
    from sklearn.model_selection import train_test_split
    
    # 生成示例数据
    X, y = make_classification(n_samples=1000, n_features=20, n_classes=2, random_state=42)
    X = pd.DataFrame(X, columns=['feature_{}'.format(i) for i in range(20)])
    y = pd.Series(y)
    
    # 分割数据
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # 初始化模型
    model = CXGBModel()
    
    # 训练模型
    trained_model = model.train(X_train, y_train)
    
    # 预测
    y_pred = model.predict(trained_model, X_test)
    
    # 评估
    metrics = model.evaluate(y_test, y_pred)
    print("模型评估指标:")
    print(metrics)
    
    # 保存模型
    model.save_model(trained_model, 'xgb_model.json')
    
    # 加载模型
    loaded_model = model.load_model('xgb_model.json')
    
    # 预测
    y_pred_loaded = model.predict(loaded_model, X_test)
    
    # 评估
    metrics_loaded = model.evaluate(y_test, y_pred_loaded)
    print("\n加载模型评估指标:")
    print(metrics_loaded)
    
    # 特征重要性
    importance = model.get_feature_importance(trained_model)
    print("\n特征重要性:")
    print(importance)