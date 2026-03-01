from typing import List, Dict, Any, Optional
from Common.CEnum import BS_TYPE, KL_TYPE

class CCustomBSP:
    """自定义买卖点类"""
    
    def __init__(self, bsp_type: BS_TYPE, kl_type: KL_TYPE, price: float, time, reason: str = ''):
        """初始化自定义买卖点
        
        Args:
            bsp_type: 买卖点类型
            kl_type: K线类型
            price: 价格
            time: 时间
            reason: 原因
        """
        self.type = bsp_type
        self.kl_type = kl_type
        self.price = price
        self.time = time
        self.reason = reason
        self.is_cover = False
        self.cover_price = None
        self.cover_time = None
        self.profit_rate = None
    
    def set_cover(self, cover_price: float, cover_time, profit_rate: float):
        """设置平仓信息
        
        Args:
            cover_price: 平仓价格
            cover_time: 平仓时间
            profit_rate: 收益率
        """
        self.is_cover = True
        self.cover_price = cover_price
        self.cover_time = cover_time
        self.profit_rate = profit_rate
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典
        
        Returns:
            字典形式的买卖点信息
        """
        return {
            'type': self.type.name,
            'kl_type': self.kl_type.name,
            'price': self.price,
            'time': self.time,
            'reason': self.reason,
            'is_cover': self.is_cover,
            'cover_price': self.cover_price,
            'cover_time': self.cover_time,
            'profit_rate': self.profit_rate
        }
    
    def __str__(self) -> str:
        """字符串表示
        
        Returns:
            字符串表示
        """
        return f"CustomBSP(type={self.type.name}, kl_type={self.kl_type.name}, price={self.price}, time={self.time}, reason={self.reason})"

class CCustomBSPList:
    """自定义买卖点列表类"""
    
    def __init__(self):
        """初始化买卖点列表"""
        self.bsp_list = []
    
    def add_bsp(self, bsp: CCustomBSP):
        """添加买卖点
        
        Args:
            bsp: 自定义买卖点
        """
        self.bsp_list.append(bsp)
    
    def get_buy_points(self) -> List[CCustomBSP]:
        """获取买入点
        
        Returns:
            买入点列表
        """
        return [bsp for bsp in self.bsp_list if bsp.type in [BS_TYPE.BUY, BS_TYPE.BUY1, BS_TYPE.BUY2, BS_TYPE.BUY3]]
    
    def get_sell_points(self) -> List[CCustomBSP]:
        """获取卖出点
        
        Returns:
            卖出点列表
        """
        return [bsp for bsp in self.bsp_list if bsp.type in [BS_TYPE.SELL, BS_TYPE.SELL1, BS_TYPE.SELL2, BS_TYPE.SELL3]]
    
    def get_latest_bsp(self) -> Optional[CCustomBSP]:
        """获取最新的买卖点
        
        Returns:
            最新的买卖点
        """
        if not self.bsp_list:
            return None
        return self.bsp_list[-1]
    
    def to_dict(self) -> List[Dict[str, Any]]:
        """转换为字典列表
        
        Returns:
            字典列表
        """
        return [bsp.to_dict() for bsp in self.bsp_list]
    
    def __len__(self) -> int:
        """获取长度
        
        Returns:
            长度
        """
        return len(self.bsp_list)
    
    def __getitem__(self, index) -> CCustomBSP:
        """获取指定索引的买卖点
        
        Args:
            index: 索引
            
        Returns:
            买卖点
        """
        return self.bsp_list[index]