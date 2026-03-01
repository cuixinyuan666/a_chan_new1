from typing import List, Dict, Any
import pandas as pd
import random
from datetime import datetime, timedelta

class ExamGenerator:
    """生成买卖点判断试题"""
    
    def __init__(self, data_dir: str = './data'):
        """初始化
        
        Args:
            data_dir: 数据存储目录
        """
        self.data_dir = data_dir
    
    def generate_exam(self, code: str, count: int = 10) -> List[Dict[str, Any]]:
        """生成试题
        
        Args:
            code: 股票代码
            count: 试题数量
            
        Returns:
            试题列表
        """
        from OfflineData.offline_data_util import OfflineDataUtil
        
        util = OfflineDataUtil(self.data_dir)
        df = util.load_stock_data(code, 'ashare')
        
        if df is None or len(df) < 30:
            return []
        
        exams = []
        
        for i in range(count):
            # 随机选择一个日期作为测试点
            test_idx = random.randint(30, len(df) - 1)
            test_date = df.iloc[test_idx]['date']
            
            # 获取测试点前后的数据
            start_idx = max(0, test_idx - 30)
            end_idx = min(len(df), test_idx + 10)
            test_data = df.iloc[start_idx:end_idx]
            
            # 生成试题
            exam = {
                'id': f"exam_{i+1}",
                'code': code,
                'test_date': test_date.strftime('%Y-%m-%d'),
                'data': test_data.to_dict('records'),
                'question': f"基于缠论分析，在{test_date.strftime('%Y-%m-%d')}这一天，该股票是否出现买入信号？",
                'options': ['是', '否'],
                'correct_answer': random.choice(['是', '否']),  # 实际应用中应该基于真实分析
                'explanation': "请基于缠论的笔、线段、中枢等概念进行分析判断"
            }
            
            exams.append(exam)
        
        return exams
    
    def generate_batch_exams(self, codes: List[str], count_per_code: int = 5) -> List[Dict[str, Any]]:
        """批量生成试题
        
        Args:
            codes: 股票代码列表
            count_per_code: 每个股票的试题数量
            
        Returns:
            试题列表
        """
        all_exams = []
        
        for code in codes:
            exams = self.generate_exam(code, count_per_code)
            all_exams.extend(exams)
        
        return all_exams
    
    def save_exams(self, exams: List[Dict[str, Any]], file_path: str):
        """保存试题
        
        Args:
            exams: 试题列表
            file_path: 保存路径
        """
        import json
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(exams, f, ensure_ascii=False, indent=2)
    
    def load_exams(self, file_path: str) -> List[Dict[str, Any]]:
        """加载试题
        
        Args:
            file_path: 试题文件路径
            
        Returns:
            试题列表
        """
        import json
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Load exams error: {e}")
            return []
    
    def grade_exam(self, exam: Dict[str, Any], user_answer: str) -> Dict[str, Any]:
        """批改试题
        
        Args:
            exam: 试题
            user_answer: 用户答案
            
        Returns:
            批改结果
        """
        is_correct = user_answer == exam['correct_answer']
        
        return {
            'exam_id': exam['id'],
            'question': exam['question'],
            'user_answer': user_answer,
            'correct_answer': exam['correct_answer'],
            'is_correct': is_correct,
            'explanation': exam['explanation']
        }

if __name__ == '__main__':
    # 示例：生成试题
    generator = ExamGenerator()
    exams = generator.generate_exam('600000', 5)
    print(f"Generated {len(exams)} exams")
    
    # 保存试题
    generator.save_exams(exams, 'exams.json')
    
    # 加载试题
    loaded_exams = generator.load_exams('exams.json')
    print(f"Loaded {len(loaded_exams)} exams")
    
    # 批改试题
    if loaded_exams:
        result = generator.grade_exam(loaded_exams[0], '是')
        print("Grading result:")
        print(result)