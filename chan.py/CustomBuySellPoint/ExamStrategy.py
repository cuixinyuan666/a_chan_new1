from .Strategy import Strategy
from typing import List, Dict, Any, Optional
from Common.CEnum import KL_TYPE, BS_TYPE

class CExamStrategy(Strategy):
    """生成买卖点判断试题的策略"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """初始化策略
        
        Args:
            config: 策略配置参数
        """
        super().__init__(config)
        self.question_count = self.config.get('question_count', 10)
    
    def get_buy_signal(self, chan) -> List[Dict[str, Any]]:
        """获取买入信号（用于生成试题）
        
        Args:
            chan: 缠论对象
            
        Returns:
            买入信号列表（试题）
        """
        questions = []
        
        # 遍历所有级别
        for kl_type in chan.kl_types:
            kl = chan[kl_type]
            
            # 检查是否有笔和线段
            if not kl.bi_list or not kl.seg_list:
                continue
            
            # 检查是否有买卖点
            if not kl.bs_point_lst:
                continue
            
            # 生成试题
            questions.extend(self._generate_questions(kl, kl_type))
            
            # 达到试题数量上限
            if len(questions) >= self.question_count:
                break
        
        return questions[:self.question_count]
    
    def get_sell_signal(self, chan) -> List[Dict[str, Any]]:
        """获取卖出信号（用于生成试题）
        
        Args:
            chan: 缠论对象
            
        Returns:
            卖出信号列表（试题）
        """
        # 卖出信号也使用相同的试题生成逻辑
        return self.get_buy_signal(chan)
    
    def _generate_questions(self, kl, kl_type) -> List[Dict[str, Any]]:
        """生成试题
        
        Args:
            kl: K线对象
            kl_type: K线类型
            
        Returns:
            试题列表
        """
        questions = []
        
        # 遍历所有买卖点
        for bsp in kl.bs_point_lst:
            # 生成试题
            question = {
                'type': 'exam',
                'kl_type': kl_type,
                'bsp_type': bsp.type,
                'bsp_time': bsp.end_klu.end,
                'bsp_price': bsp.end_klu.close,
                'question': f'在{kl_type.name}级别，{bsp.end_klu.end}处是否存在{bsp.type.name}类型的买卖点？',
                'options': ['是', '否'],
                'correct_answer': '是',
                'explanation': f'根据缠论定义，此处存在{bsp.type.name}类型的买卖点'
            }
            questions.append(question)
        
        return questions
    
    def get_cover_signal(self, chan, open_signal) -> Optional[Dict[str, Any]]:
        """获取平仓信号
        
        Args:
            chan: 缠论对象
            open_signal: 开仓信号
            
        Returns:
            平仓信号
        """
        # 考试策略不需要平仓信号
        return None