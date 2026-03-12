"""
A股缠论买点扫描器 - 单文件版本 (整合所有核心模块)

此文件包含chan.py的所有核心模块，无需额外导入本地自定义模块
"""

# ==================== 标准库导入 ====================
import sys
from pathlib import Path
import copy
import pickle
from collections import defaultdict
from typing import Dict, Iterable, List, Optional, Union, Tuple, Literal, Generic, TypeVar
from enum import Enum, auto
from dataclasses import dataclass
from abc import ABC, abstractmethod
import math
import traceback
import importlib

# ==================== 第三方库导入 ====================
from datetime import datetime, timedelta, date
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QComboBox, QCheckBox, QGroupBox,
    QMessageBox, QStatusBar, QSplitter, QTableWidget, QTableWidgetItem,
    QProgressBar, QHeaderView, QTextEdit
)
from PyQt6.QtCore import QDate, Qt, QThread, pyqtSignal, QUrl
from PyQt6.QtWebEngineWidgets import QWebEngineView
import baostock as bs
import pandas as pd
import numpy as np
from pyecharts.charts import Kline, Line, Bar, Grid, Scatter
from pyecharts import options as opts
from pyecharts.commons.utils import JsCode


# ==================== Common/CEnum.py ====================

from enum import Enum, auto
from typing import Literal


class DATA_SRC(Enum):
    BAO_STOCK = auto()
    CCXT = auto()
    CSV = auto()
    AKSHARE = auto()


class KL_TYPE(Enum):
    K_1M = auto()
    K_DAY = auto()
    K_WEEK = auto()
    K_MON = auto()
    K_YEAR = auto()
    K_5M = auto()
    K_15M = auto()
    K_30M = auto()
    K_60M = auto()
    K_3M = auto()
    K_QUARTER = auto()


class KLINE_DIR(Enum):
    UP = auto()
    DOWN = auto()
    COMBINE = auto()
    INCLUDED = auto()


class FX_TYPE(Enum):
    BOTTOM = auto()
    TOP = auto()
    UNKNOWN = auto()


class BI_DIR(Enum):
    UP = auto()
    DOWN = auto()


class BI_TYPE(Enum):
    UNKNOWN = auto()
    STRICT = auto()
    SUB_VALUE = auto()  # 次高低点成笔
    TIAOKONG_THRED = auto()
    DAHENG = auto()
    TUIBI = auto()
    UNSTRICT = auto()
    TIAOKONG_VALUE = auto()


BSP_MAIN_TYPE = Literal['1', '2', '3']


class BSP_TYPE(Enum):
    T1 = '1'
    T1P = '1p'
    T2 = '2'
    T2S = '2s'
    T3A = '3a'  # 中枢在1类后面
    T3B = '3b'  # 中枢在1类前面

    def main_type(self) -> BSP_MAIN_TYPE:
        return self.value[0]  # type: ignore


class AUTYPE(Enum):
    QFQ = auto()
    HFQ = auto()
    NONE = auto()


class TREND_TYPE(Enum):
    MEAN = "mean"
    MAX = "max"
    MIN = "min"


class TREND_LINE_SIDE(Enum):
    INSIDE = auto()
    OUTSIDE = auto()


class LEFT_SEG_METHOD(Enum):
    ALL = auto()
    PEAK = auto()


class FX_CHECK_METHOD(Enum):
    STRICT = auto()
    LOSS = auto()
    HALF = auto()
    TOTALLY = auto()


class SEG_TYPE(Enum):
    BI = auto()
    SEG = auto()


class MACD_ALGO(Enum):
    AREA = auto()
    PEAK = auto()
    FULL_AREA = auto()
    DIFF = auto()
    SLOPE = auto()
    AMP = auto()
    VOLUMN = auto()
    AMOUNT = auto()
    VOLUMN_AVG = auto()
    AMOUNT_AVG = auto()
    TURNRATE_AVG = auto()
    RSI = auto()


class DATA_FIELD:
    FIELD_TIME = "time_key"
    FIELD_OPEN = "open"
    FIELD_HIGH = "high"
    FIELD_LOW = "low"
    FIELD_CLOSE = "close"
    FIELD_VOLUME = "volume"  # 成交量
    FIELD_TURNOVER = "turnover"  # 成交额
    FIELD_TURNRATE = "turnover_rate"  # 换手率


TRADE_INFO_LST = [DATA_FIELD.FIELD_VOLUME, DATA_FIELD.FIELD_TURNOVER, DATA_FIELD.FIELD_TURNRATE]


# ==================== Common/ChanException.py ====================

from enum import IntEnum


class ErrCode(IntEnum):
    # chan err
    _CHAN_ERR_BEGIN = 0
    COMMON_ERROR = 1
    SRC_DATA_NOT_FOUND = 3
    SRC_DATA_TYPE_ERR = 4
    PARA_ERROR = 5
    EXTRA_KLU_ERR = 6
    SEG_END_VALUE_ERR = 7
    SEG_EIGEN_ERR = 8
    BI_ERR = 9
    COMBINER_ERR = 10
    PLOT_ERR = 11
    MODEL_ERROR = 12
    SEG_LEN_ERR = 13
    ENV_CONF_ERR = 14
    UNKNOWN_DB_TYPE = 15
    FEATURE_ERROR = 16
    CONFIG_ERROR = 17
    SRC_DATA_FORMAT_ERROR = 18
    _CHAN_ERR_END = 99

    # Trade Error
    _TRADE_ERR_BEGIN = 100
    SIGNAL_EXISTED = 101
    RECORD_NOT_EXIST = 102
    RECORD_ALREADY_OPENED = 103
    QUOTA_NOT_ENOUGH = 104
    RECORD_NOT_OPENED = 105
    TRADE_UNLOCK_FAIL = 106
    PLACE_ORDER_FAIL = 107
    LIST_ORDER_FAIL = 108
    CANDEL_ORDER_FAIL = 109
    GET_FUTU_PRICE_FAIL = 110
    GET_FUTU_LOT_SIZE_FAIL = 111
    OPEN_RECORD_NOT_WATCHING = 112
    GET_HOLDING_QTY_FAIL = 113
    RECORD_CLOSED = 114
    REQUEST_TRADING_DAYS_FAIL = 115
    COVER_ORDER_ID_NOT_UNIQUE = 116
    SIGNAL_TRADED = 117
    _TRADE_ERR_END = 199

    # KL data Error
    _KL_ERR_BEGIN = 200
    PRICE_BELOW_ZERO = 201
    KL_DATA_NOT_ALIGN = 202
    KL_DATA_INVALID = 203
    KL_TIME_INCONSISTENT = 204
    TRADEINFO_TOO_MUCH_ZERO = 205
    KL_NOT_MONOTONOUS = 206
    SNAPSHOT_ERR = 207
    SUSPENSION = 208  # 疑似停牌
    STOCK_IPO_TOO_LATE = 209
    NO_DATA = 210
    STOCK_NOT_ACTIVE = 211
    STOCK_PRICE_NOT_ACTIVE = 212
    _KL_ERR_END = 299


class CChanException(Exception):
    def __init__(self, message, code=ErrCode.COMMON_ERROR):
        self.errcode = code
        self.msg = message
        Exception.__init__(self, message)

    def is_kldata_err(self):
        return ErrCode._KL_ERR_BEGIN < self.errcode < ErrCode._KL_ERR_END

    def is_chan_err(self):
        return ErrCode._CHAN_ERR_BEGIN < self.errcode < ErrCode._CHAN_ERR_END


if __name__ == "__main__":
    def foo():
        raise CChanException("XXX", ErrCode.CONFIG_ERROR)

    try:
        foo()
    except CChanException as e:
        print(str(e.errcode))
        # python3.8 结果为： ErrCode.CONFIG_ERROR
        # python3.11 结果为：17

        print(e.errcode.name, type(e.errcode.name))


# ==================== Common/CTime.py ====================


class CTime:
    def __init__(self, year, month, day, hour, minute, second=0, auto=True):
        self.year = year
        self.month = month
        self.day = day
        self.hour = hour
        self.minute = minute
        self.second = second
        self.auto = auto  # 自适应对天的理解
        self.set_timestamp()  # set self.ts

    def __str__(self):
        if self.hour == 0 and self.minute == 0:
            return f"{self.year:04}/{self.month:02}/{self.day:02}"
        else:
            return f"{self.year:04}/{self.month:02}/{self.day:02} {self.hour:02}:{self.minute:02}"

    def to_str(self):
        if self.hour == 0 and self.minute == 0:
            return f"{self.year:04}/{self.month:02}/{self.day:02}"
        else:
            return f"{self.year:04}/{self.month:02}/{self.day:02} {self.hour:02}:{self.minute:02}"

    def toDateStr(self, splt=''):
        return f"{self.year:04}{splt}{self.month:02}{splt}{self.day:02}"

    def toDate(self):
        return CTime(self.year, self.month, self.day, 0, 0, auto=False)

    def set_timestamp(self):
        if self.hour == 0 and self.minute == 0 and self.auto:
            date = datetime(self.year, self.month, self.day, 23, 59, self.second)
        else:
            date = datetime(self.year, self.month, self.day, self.hour, self.minute, self.second)
        self.ts = date.timestamp()

    def __gt__(self, t2):
        return self.ts > t2.ts

    def __ge__(self, t2):
        return self.ts >= t2.ts


# ==================== Common/func_util.py ====================



def kltype_lt_day(_type):
    return _type in [KL_TYPE.K_1M, KL_TYPE.K_5M, KL_TYPE.K_15M, KL_TYPE.K_30M, KL_TYPE.K_60M]


def kltype_lte_day(_type):
    return _type in [KL_TYPE.K_1M, KL_TYPE.K_5M, KL_TYPE.K_15M, KL_TYPE.K_30M, KL_TYPE.K_60M, KL_TYPE.K_DAY]


def check_kltype_order(type_list: list):
    _dict = {
        KL_TYPE.K_1M: 1,
        KL_TYPE.K_3M: 2,
        KL_TYPE.K_5M: 3,
        KL_TYPE.K_15M: 4,
        KL_TYPE.K_30M: 5,
        KL_TYPE.K_60M: 6,
        KL_TYPE.K_DAY: 7,
        KL_TYPE.K_WEEK: 8,
        KL_TYPE.K_MON: 9,
        KL_TYPE.K_QUARTER: 10,
        KL_TYPE.K_YEAR: 11,
    }
    last_lv = float("inf")
    for kl_type in type_list:
        cur_lv = _dict[kl_type]
        assert cur_lv < last_lv, "lv_list的顺序必须从大级别到小级别"
        last_lv = cur_lv


def revert_bi_dir(dir):
    return BI_DIR.DOWN if dir == BI_DIR.UP else BI_DIR.UP


def has_overlap(l1, h1, l2, h2, equal=False):
    return h2 >= l1 and h1 >= l2 if equal else h2 > l1 and h1 > l2


def str2float(s):
    try:
        return float(s)
    except ValueError:
        return 0.0


def _parse_inf(v):
    if type(v) == float:
        if v == float("inf"):
            v = 'float("inf")'
        if v == float("-inf"):
            v = 'float("-inf")'
    return v


# ==================== Common/cache.py ====================

import inspect
import types


class make_cache:
    def __init__(self, func):
        self.func = func
        self.func_name = func.__name__

    def __get__(self, instance, owner):
        if instance is None:
            return self
        
        # Use a more efficient caching mechanism
        if not hasattr(instance, "_memoize_cache"):
            instance._memoize_cache = {}
        
        def wrapper(*args, **kwargs):
            if self.func_name not in instance._memoize_cache:
                instance._memoize_cache[self.func_name] = self.func(instance, *args, **kwargs)
            return instance._memoize_cache[self.func_name]
        
        return wrapper


# ==================== Math/MACD.py ====================

from typing import List


class CMACD_item:
    def __init__(self, fast_ema, slow_ema, DIF, DEA):
        self.fast_ema = fast_ema
        self.slow_ema = slow_ema
        self.DIF = DIF
        self.DEA = DEA
        self.macd = 2 * (DIF - DEA)


class CMACD:
    def __init__(self, fastperiod=12, slowperiod=26, signalperiod=9):
        self.macd_info: List[CMACD_item] = []
        self.fastperiod = fastperiod
        self.slowperiod = slowperiod
        self.signalperiod = signalperiod

    def add(self, value) -> CMACD_item:
        if not self.macd_info:
            self.macd_info.append(CMACD_item(fast_ema=value, slow_ema=value, DIF=0, DEA=0))
        else:
            _fast_ema = (2 * value + (self.fastperiod - 1) * self.macd_info[-1].fast_ema) / (self.fastperiod + 1)
            _slow_ema = (2 * value + (self.slowperiod - 1) * self.macd_info[-1].slow_ema) / (self.slowperiod + 1)
            _dif = _fast_ema - _slow_ema
            _dea = (2 * _dif + (self.signalperiod - 1) * self.macd_info[-1].DEA) / (self.signalperiod + 1)
            self.macd_info.append(CMACD_item(fast_ema=_fast_ema, slow_ema=_slow_ema, DIF=_dif, DEA=_dea))
        return self.macd_info[-1]


# ==================== Math/TrendModel.py ====================



class CTrendModel:
    def __init__(self, trend_type: TREND_TYPE, T: int):
        self.T = T
        self.arr = []
        self.type = trend_type

    def add(self, value) -> float:
        self.arr.append(value)
        if len(self.arr) > self.T:
            self.arr = self.arr[-self.T:]
        if self.type == TREND_TYPE.MEAN:
            return sum(self.arr)/len(self.arr)
        elif self.type == TREND_TYPE.MAX:
            return max(self.arr)
        elif self.type == TREND_TYPE.MIN:
            return min(self.arr)
        else:
            raise CChanException(f"Unknown trendModel Type = {self.type}", ErrCode.PARA_ERROR)


# ==================== Math/BOLL.py ====================

import math


def _truncate(x):
    return x if x != 0 else 1e-7


class BOLL_Metric:
    def __init__(self, ma, theta):
        self.theta = _truncate(theta)
        self.UP = ma + 2*theta
        self.DOWN = _truncate(ma - 2*theta)
        self.MID = ma


class BollModel:
    def __init__(self, N=20):
        assert N > 1
        self.N = N
        self.arr = []
        self.sum_x = 0.0
        self.sum_x2 = 0.0

    def add(self, value) -> BOLL_Metric:
        self.arr.append(value)
        self.sum_x += value
        self.sum_x2 += value * value
        
        if len(self.arr) > self.N:
            old_val = self.arr.pop(0)
            self.sum_x -= old_val
            self.sum_x2 -= old_val * old_val
            
        n = len(self.arr)
        ma = self.sum_x / n
        # Variance formula: E[X^2] - (E[X])^2
        var = max(0, (self.sum_x2 / n) - (ma * ma))
        theta = math.sqrt(var)
        return BOLL_Metric(ma, theta)


# ==================== Math/Demark.py ====================

import copy
from dataclasses import dataclass
from typing import List, Literal, Optional, TypedDict



@dataclass
class C_KL:
    idx: int
    close: float
    high: float
    low: float

    def v(self, is_close: bool, _dir: BI_DIR) -> float:
        if is_close:
            return self.close
        return self.high if _dir == BI_DIR.UP else self.low


T_DEMARK_TYPE = Literal['setup', 'countdown']


class T_DEMARK_INDEX(TypedDict):
    type: T_DEMARK_TYPE
    dir: BI_DIR
    idx: int
    series: 'CDemarkSetup'


class CDemarkIndex:
    def __init__(self):
        self.data: List[T_DEMARK_INDEX] = []

    def add(self, _dir: BI_DIR, _type: T_DEMARK_TYPE, idx: int, series: 'CDemarkSetup'):
        self.data.append({"dir": _dir, "idx": idx, "type": _type, "series": series})

    def get_setup(self) -> List[T_DEMARK_INDEX]:
        return [info for info in self.data if info['type'] == 'setup']

    def get_countdown(self) -> List[T_DEMARK_INDEX]:
        return [info for info in self.data if info['type'] == 'countdown']

    def update(self, demark_index: 'CDemarkIndex'):
        self.data.extend(demark_index.data)


class CDemarkCountdown:
    def __init__(self, _dir: BI_DIR, kl_list: List[C_KL], TDST_peak: float):
        self.dir = _dir
        self.kl_list: List[C_KL] = copy.deepcopy(kl_list)
        self.idx = 0
        self.TDST_peak = TDST_peak
        self.finish = False

    def update(self, kl: C_KL) -> bool:
        if self.finish:
            return False
        self.kl_list.append(kl)
        if len(self.kl_list) <= CDemarkEngine.COUNTDOWN_BIAS:
            return False
        if self.idx == CDemarkEngine.MAX_COUNTDOWN:
            self.finish = True
            return False
        if (self.dir == BI_DIR.DOWN and kl.high > self.TDST_peak) or (self.dir == BI_DIR.UP and kl.low < self.TDST_peak):
            self.finish = True
            return False
        if self.dir == BI_DIR.DOWN and self.kl_list[-1].close < self.kl_list[-1 - CDemarkEngine.COUNTDOWN_BIAS].v(CDemarkEngine.COUNTDOWN_CMP2CLOSE, self.dir):
            self.idx += 1
            return True
        if self.dir == BI_DIR.UP and self.kl_list[-1].close > self.kl_list[-1 - CDemarkEngine.COUNTDOWN_BIAS].v(CDemarkEngine.COUNTDOWN_CMP2CLOSE, self.dir):
            self.idx += 1
            return True
        return False


class CDemarkSetup:
    def __init__(self, _dir: BI_DIR, kl_list: List[C_KL], pre_kl: C_KL):
        self.dir = _dir
        self.kl_list: List[C_KL] = copy.deepcopy(kl_list)
        self.pre_kl = pre_kl  # 跳空时用
        assert len(self.kl_list) == CDemarkEngine.SETUP_BIAS
        self.countdown: Optional[CDemarkCountdown] = None
        self.setup_finished = False
        self.idx = 0
        self.TDST_peak: Optional[float] = None

        self.last_demark_index = CDemarkIndex()  # 缓存用

    def update(self, kl: C_KL) -> CDemarkIndex:
        self.last_demark_index = CDemarkIndex()
        if not self.setup_finished:
            self.kl_list.append(kl)
            if self.dir == BI_DIR.DOWN:
                if self.kl_list[-1].close < self.kl_list[-1-CDemarkEngine.SETUP_BIAS].v(CDemarkEngine.SETUP_CMP2CLOSE, self.dir):
                    self.add_setup()
                else:
                    self.setup_finished = True
            elif self.kl_list[-1].close > self.kl_list[-1-CDemarkEngine.SETUP_BIAS].v(CDemarkEngine.SETUP_CMP2CLOSE, self.dir):
                self.add_setup()
            else:
                self.setup_finished = True
        if self.idx == CDemarkEngine.DEMARK_LEN and not self.setup_finished and self.countdown is None:
            self.countdown = CDemarkCountdown(self.dir, self.kl_list[:-1], self.cal_TDST_peak())
        if self.countdown is not None and self.countdown.update(kl):
            self.last_demark_index.add(self.dir, 'countdown', self.countdown.idx, self)
        return self.last_demark_index

    def add_setup(self):
        self.idx += 1
        self.last_demark_index.add(self.dir, 'setup', self.idx, self)

    def cal_TDST_peak(self) -> float:
        assert len(self.kl_list) == CDemarkEngine.SETUP_BIAS+CDemarkEngine.DEMARK_LEN
        arr = self.kl_list[CDemarkEngine.SETUP_BIAS:CDemarkEngine.SETUP_BIAS+CDemarkEngine.DEMARK_LEN]
        assert len(arr) == CDemarkEngine.DEMARK_LEN
        if self.dir == BI_DIR.DOWN:
            res = max(kl.high for kl in arr)
            if CDemarkEngine.TIAOKONG_ST and arr[0].high < self.pre_kl.close:
                res = max(res, self.pre_kl.close)
        else:
            res = min(kl.low for kl in arr)
            if CDemarkEngine.TIAOKONG_ST and arr[0].low > self.pre_kl.close:
                res = min(res, self.pre_kl.close)
        self.TDST_peak = res
        return res


class CDemarkEngine:
    DEMARK_LEN = 9
    SETUP_BIAS = 4
    COUNTDOWN_BIAS = 2
    MAX_COUNTDOWN = 13
    TIAOKONG_ST = True  # 第一根跳空时是否跟前一根的close比
    SETUP_CMP2CLOSE = True
    COUNTDOWN_CMP2CLOSE = True

    def __init__(
        self,
        demark_len=9,
        setup_bias=4,
        countdown_bias=2,
        max_countdown=13,
        tiaokong_st=True,
        setup_cmp2close=True,
        countdown_cmp2close=True
    ):
        CDemarkEngine.DEMARK_LEN = demark_len
        CDemarkEngine.SETUP_BIAS = setup_bias
        CDemarkEngine.COUNTDOWN_BIAS = countdown_bias
        CDemarkEngine.MAX_COUNTDOWN = max_countdown
        CDemarkEngine.TIAOKONG_ST = tiaokong_st
        CDemarkEngine.SETUP_CMP2CLOSE = setup_cmp2close
        CDemarkEngine.COUNTDOWN_CMP2CLOSE = countdown_cmp2close

        self.kl_lst: List[C_KL] = []
        self.series: List[CDemarkSetup] = []

    def update(self, idx: int, close: float, high: float, low: float) -> CDemarkIndex:
        self.kl_lst.append(C_KL(idx, close, high, low))
        if len(self.kl_lst) <= CDemarkEngine.SETUP_BIAS+1:
            return CDemarkIndex()

        if self.kl_lst[-1].close < self.kl_lst[-1-self.SETUP_BIAS].close:
            if not any(series.dir == BI_DIR.DOWN and not series.setup_finished for series in self.series):
                self.series.append(CDemarkSetup(BI_DIR.DOWN, self.kl_lst[-CDemarkEngine.SETUP_BIAS-1:-1], self.kl_lst[-CDemarkEngine.SETUP_BIAS-2]))
            for series in self.series:
                if series.dir == BI_DIR.UP and series.countdown is None and not series.setup_finished:
                    series.setup_finished = True
        elif self.kl_lst[-1].close > self.kl_lst[-1-self.SETUP_BIAS].close:
            if not any(series.dir == BI_DIR.UP and not series.setup_finished for series in self.series):
                self.series.append(CDemarkSetup(BI_DIR.UP, self.kl_lst[-CDemarkEngine.SETUP_BIAS-1:-1], self.kl_lst[-CDemarkEngine.SETUP_BIAS-2]))
            for series in self.series:
                if series.dir == BI_DIR.DOWN and series.countdown is None and not series.setup_finished:
                    series.setup_finished = True

        self.clear()
        self.clean_series_from_setup_finish()

        result = self.cal_result()
        self.clear()
        return result

    def cal_result(self) -> CDemarkIndex:
        demark_index = CDemarkIndex()
        for series in self.series:
            demark_index.update(series.last_demark_index)
        return demark_index

    def clear(self):
        invalid_series = [series for series in self.series if series.setup_finished and series.countdown is None]
        for s in invalid_series:
            self.series.remove(s)
        invalid_series = [series for series in self.series if series.countdown is not None and series.countdown.finish]
        for s in invalid_series:
            self.series.remove(s)

    def clean_series_from_setup_finish(self):
        finished_setup: Optional[int] = None
        for series in self.series:
            demark_idx = series.update(self.kl_lst[-1])
            for setup_idx in demark_idx.get_setup():
                if setup_idx['idx'] == CDemarkEngine.DEMARK_LEN:
                    assert finished_setup is None
                    finished_setup = id(series)
        if finished_setup is not None:
            self.series = [series for series in self.series if id(series) == finished_setup]


# ==================== Math/RSI.py ====================

class RSI:
    def __init__(self, period: int = 14):
        super(RSI, self).__init__()
        self.close_arr = []
        self.period = period
        self.diff = []
        self.up = []
        self.down = []

    def add(self, close):
        self.close_arr.append(close)
        if len(self.close_arr) == 1:
            return 50.0

        self.diff.append(self.close_arr[-1] - self.close_arr[-2])

        if len(self.diff) < self.period:
            up_sum = sum(x for x in self.diff if x > 0)
            down_sum = sum(-x for x in self.diff if x < 0)
            self.up.append(up_sum / len(self.diff))
            self.down.append(down_sum / len(self.diff))
        else:
            if self.diff[-1] > 0:
                upval = self.diff[-1]
                downval = 0.0
            else:
                upval = 0.0
                downval = -self.diff[-1]

            self.up.append((self.up[-1] * (self.period - 1) + upval) / self.period)
            self.down.append((self.down[-1] * (self.period - 1) + downval) / self.period)

        if self.down[-1] == 0:
            return 100.0 if self.up[-1] > 0 else 0.0

        rs = self.up[-1] / self.down[-1]
        rsi = 100.0 - 100.0 / (1.0 + rs)
        return rsi


# ==================== Math/KDJ.py ====================

class KDJ_Item:
    def __init__(self, k, d, j):
        self.k = k
        self.d = d
        self.j = j


class KDJ:
    def __init__(self, period: int = 9):
        super(KDJ, self).__init__()
        self.arr = []
        self.period = period
        self.pre_kdj = KDJ_Item(50, 50, 50)

    def add(self, high, low, close) -> KDJ_Item:
        self.arr.append({
            'high': high,
            'low': low,
        })
        if len(self.arr) > self.period:
            self.arr.pop(0)

        hn = max([x['high'] for x in self.arr])
        ln = min([x['low'] for x in self.arr])
        cn = close
        rsv = 100 * (cn - ln) / (hn - ln) if hn != ln else 0.0

        cur_k = 2 / 3 * self.pre_kdj.k + 1 / 3 * rsv
        cur_d = 2 / 3 * self.pre_kdj.d + 1 / 3 * cur_k
        cur_j = 3 * cur_k - 2 * cur_d
        cur_kdj = KDJ_Item(cur_k, cur_d, cur_j)
        self.pre_kdj = cur_kdj

        return cur_kdj


# ==================== Math/TrendLine.py ====================

import copy
from dataclasses import dataclass
from math import sqrt



@dataclass
class Point:
    x: int
    y: float

    def cal_slope(self, p):
        return (self.y-p.y)/(self.x-p.x) if self.x != p.x else float("inf")


@dataclass
class MathLine:
    p: Point
    slope: float

    def cal_dis(self, p):
        return abs(self.slope*p.x - p.y + self.p.y - self.slope*self.p.x) / sqrt(self.slope**2 + 1)


class CTrendLine:
    def __init__(self, lst, side=TREND_LINE_SIDE.OUTSIDE):
        self.line = None
        self.side = side
        self.cal(lst)

    def cal(self, lst):
        bench = float('inf')
        if self.side == TREND_LINE_SIDE.INSIDE:
            all_p = [Point(bi.get_begin_klu().idx, bi.get_begin_val()) for bi in lst[-1::-2]]
        else:
            all_p = [Point(bi.get_end_klu().idx, bi.get_end_val()) for bi in lst[-1::-2]]
        c_p = copy.copy(all_p)
        while True:
            line, idx = cal_tl(c_p, lst[-1].dir, self.side)
            dis = sum(line.cal_dis(p) for p in all_p)
            if dis < bench:
                bench = dis
                self.line = line
            c_p = c_p[idx:]
            if len(c_p) == 1:
                break


def init_peak_slope(_dir, side):
    if side == TREND_LINE_SIDE.INSIDE:
        return 0
    elif _dir == BI_DIR.UP:
        return float("inf")
    else:
        return -float("inf")


def cal_tl(c_p, _dir, side):
    p = c_p[0]
    peak_slope = init_peak_slope(_dir, side)
    idx = 1
    for point_idx, p2 in enumerate(c_p[1:]):
        slope = p.cal_slope(p2)
        if (_dir == BI_DIR.UP and slope < 0) or (_dir == BI_DIR.DOWN and slope > 0):
            continue
        if side == TREND_LINE_SIDE.INSIDE:
            if (_dir == BI_DIR.UP and slope > peak_slope) or (_dir == BI_DIR.DOWN and slope < peak_slope):
                peak_slope = slope
                idx = point_idx+1
        else:
            if (_dir == BI_DIR.UP and slope < peak_slope) or (_dir == BI_DIR.DOWN and slope > peak_slope):
                peak_slope = slope
                idx = point_idx+1
    return MathLine(p, peak_slope), idx


# ==================== KLine/TradeInfo.py ====================

from typing import Dict, Optional



class CTradeInfo:
    def __init__(self, info: Dict[str, float]):
        self.metric: Dict[str, Optional[float]] = {}
        for metric_name in TRADE_INFO_LST:
            self.metric[metric_name] = info.get(metric_name)

    def __str__(self):
        return " ".join([f"{metric_name}:{value}" for metric_name, value in self.metric.items()])


# ==================== Combiner/Combine_Item.py ====================



class CCombine_Item:
    def __init__(self, item):
        if isinstance(item, CBi):
            self.time_begin = item.begin_klc.idx
            self.time_end = item.end_klc.idx
            self.high = item._high()
            self.low = item._low()
        elif isinstance(item, CKLine_Unit):
            self.time_begin = item.time
            self.time_end = item.time
            self.high = item.high
            self.low = item.low
        elif isinstance(item, CSeg):
            self.time_begin = item.start_bi.begin_klc.idx
            self.time_end = item.end_bi.end_klc.idx
            self.high = item._high()
            self.low = item._low()
        else:
            raise CChanException(f"{type(item)} is unsupport sub class of CCombine_Item", ErrCode.COMMON_ERROR)


# ==================== Combiner/KLine_Combiner.py ====================

from typing import Generic, Iterable, List, Optional, Self, TypeVar, Union, overload



T = TypeVar('T')


class CKLine_Combiner(Generic[T]):
    def __init__(self, kl_unit: T, _dir):
        item = CCombine_Item(kl_unit)
        self.__time_begin = item.time_begin
        self.__time_end = item.time_end
        self.__high = item.high
        self.__low = item.low

        self.__lst: List[T] = [kl_unit]  # 本级别每一根单位K线

        self.__dir = _dir
        self.__fx = FX_TYPE.UNKNOWN
        self.__pre: Optional[Self] = None
        self.__next: Optional[Self] = None

    def clean_cache(self):
        self._memoize_cache = {}

    @property
    def time_begin(self): return self.__time_begin

    @property
    def time_end(self): return self.__time_end

    @property
    def high(self): return self.__high

    @property
    def low(self): return self.__low

    @property
    def lst(self): return self.__lst

    @property
    def dir(self): return self.__dir

    @property
    def fx(self): return self.__fx

    @property
    def pre(self) -> Self:
        assert self.__pre is not None
        return self.__pre

    @property
    def next(self): return self.__next

    def get_next(self) -> Self:
        assert self.next is not None
        return self.next

    def test_combine(self, item: CCombine_Item, exclude_included=False, allow_top_equal=None):
        if (self.high >= item.high and self.low <= item.low):
            return KLINE_DIR.COMBINE
        if (self.high <= item.high and self.low >= item.low):
            if allow_top_equal == 1 and self.high == item.high and self.low > item.low:
                return KLINE_DIR.DOWN
            elif allow_top_equal == -1 and self.low == item.low and self.high < item.high:
                return KLINE_DIR.UP
            return KLINE_DIR.INCLUDED if exclude_included else KLINE_DIR.COMBINE
        if (self.high > item.high and self.low > item.low):
            return KLINE_DIR.DOWN
        if (self.high < item.high and self.low < item.low):
            return KLINE_DIR.UP
        else:
            raise CChanException("combine type unknown", ErrCode.COMBINER_ERR)

    def set_fx(self, fx: FX_TYPE):
        # only for deepcopy
        self.__fx = fx

    def try_add(self, unit_kl: T, exclude_included=False, allow_top_equal=None, skip_update_input=False):
        # allow_top_equal = None普通模式
        # allow_top_equal = 1 被包含，顶部相等不合并
        # allow_top_equal = -1 被包含，底部相等不合并
        combine_item = CCombine_Item(unit_kl)
        _dir = self.test_combine(combine_item, exclude_included, allow_top_equal)
        if _dir == KLINE_DIR.COMBINE:
            self.__lst.append(unit_kl)
            if isinstance(unit_kl, CKLine_Unit) and not skip_update_input:
                unit_kl.set_klc(self)
            if self.dir == KLINE_DIR.UP:
                if combine_item.high != combine_item.low or combine_item.high != self.high:  # 处理一字K线
                    self.__high = max([self.high, combine_item.high])
                    self.__low = max([self.low, combine_item.low])
            elif self.dir == KLINE_DIR.DOWN:
                if combine_item.high != combine_item.low or combine_item.low != self.low:  # 处理一字K线
                    self.__high = min([self.high, combine_item.high])
                    self.__low = min([self.low, combine_item.low])
            else:
                raise CChanException(f"KLINE_DIR = {self.dir} err!!! must be {KLINE_DIR.UP}/{KLINE_DIR.DOWN}", ErrCode.COMBINER_ERR)
            self.__time_end = combine_item.time_end
            self.clean_cache()
        # 返回UP/DOWN/COMBINE给KL_LIST，设置下一个的方向
        return _dir

    def get_peak_klu(self, is_high) -> T:
        # 获取最大值 or 最小值所在klu/bi
        return self.get_high_peak_klu() if is_high else self.get_low_peak_klu()

    @make_cache
    def get_high_peak_klu(self) -> T:
        for kl in self.lst[::-1]:
            if CCombine_Item(kl).high == self.high:
                return kl
        raise CChanException("can't find peak...", ErrCode.COMBINER_ERR)

    @make_cache
    def get_low_peak_klu(self) -> T:
        for kl in self.lst[::-1]:
            if CCombine_Item(kl).low == self.low:
                return kl
        raise CChanException("can't find peak...", ErrCode.COMBINER_ERR)

    def update_fx(self, _pre: Self, _next: Self, exclude_included=False, allow_top_equal=None):
        # allow_top_equal = None普通模式
        # allow_top_equal = 1 被包含，顶部相等不合并
        # allow_top_equal = -1 被包含，底部相等不合并
        self.set_next(_next)
        self.set_pre(_pre)
        _next.set_pre(self)
        if exclude_included:
            if _pre.high < self.high and _next.high <= self.high and _next.low < self.low:
                if allow_top_equal == 1 or _next.high < self.high:
                    self.__fx = FX_TYPE.TOP
            elif _next.high > self.high and _pre.low > self.low and _next.low >= self.low:
                if allow_top_equal == -1 or _next.low > self.low:
                    self.__fx = FX_TYPE.BOTTOM
        elif _pre.high < self.high and _next.high < self.high and _pre.low < self.low and _next.low < self.low:
            self.__fx = FX_TYPE.TOP
        elif _pre.high > self.high and _next.high > self.high and _pre.low > self.low and _next.low > self.low:
            self.__fx = FX_TYPE.BOTTOM
        self.clean_cache()

    def __str__(self):
        return f"{self.time_begin}~{self.time_end} {self.low}->{self.high}"

    @overload
    def __getitem__(self, index: int) -> T: ...

    @overload
    def __getitem__(self, index: slice) -> List[T]: ...

    def __getitem__(self, index: Union[slice, int]) -> Union[List[T], T]:
        return self.lst[index]

    def __len__(self):
        return len(self.lst)

    def __iter__(self) -> Iterable[T]:
        yield from self.lst

    def set_pre(self, _pre: Self | None):
        self.__pre = _pre
        self.clean_cache()

    def set_next(self, _next: Self | None):
        self.__next = _next
        self.clean_cache()


# ==================== KLine/KLine_Unit.py ====================

import copy
from typing import Dict, Optional




class CKLine_Unit:
    def __init__(self, kl_dict, autofix=False):
        # _time, _close, _open, _high, _low, _extra_info={}
        self.kl_type = None
        self.time: CTime = kl_dict[DATA_FIELD.FIELD_TIME]
        self.close = kl_dict[DATA_FIELD.FIELD_CLOSE]
        self.open = kl_dict[DATA_FIELD.FIELD_OPEN]
        self.high = kl_dict[DATA_FIELD.FIELD_HIGH]
        self.low = kl_dict[DATA_FIELD.FIELD_LOW]

        self.check(autofix)

        self.trade_info = CTradeInfo(kl_dict)

        self.demark: CDemarkIndex = CDemarkIndex()

        self.sub_kl_list = []  # 次级别KLU列表
        self.sup_kl: Optional[CKLine_Unit] = None  # 指向更高级别KLU

        self.__klc: Optional[CKLine] = None  # 指向KLine

        # self.macd: Optional[CMACD_item] = None
        # self.boll: Optional[BOLL_Metric] = None
        self.trend: Dict[TREND_TYPE, Dict[int, float]] = {}  # int -> float

        self.limit_flag = 0  # 0:普通 -1:跌停，1:涨停
        self.pre: Optional[CKLine_Unit] = None
        self.next: Optional[CKLine_Unit] = None

        self.set_idx(-1)

    def __deepcopy__(self, memo):
        _dict = {
            DATA_FIELD.FIELD_TIME: self.time,
            DATA_FIELD.FIELD_CLOSE: self.close,
            DATA_FIELD.FIELD_OPEN: self.open,
            DATA_FIELD.FIELD_HIGH: self.high,
            DATA_FIELD.FIELD_LOW: self.low,
        }
        for metric in TRADE_INFO_LST:
            if metric in self.trade_info.metric:
                _dict[metric] = self.trade_info.metric[metric]
        obj = CKLine_Unit(_dict)
        obj.demark = copy.deepcopy(self.demark, memo)
        obj.trend = copy.deepcopy(self.trend, memo)
        obj.limit_flag = self.limit_flag
        obj.macd = copy.deepcopy(self.macd, memo)
        obj.boll = copy.deepcopy(self.boll, memo)
        if hasattr(self, "rsi"):
            obj.rsi = copy.deepcopy(self.rsi, memo)
        if hasattr(self, "kdj"):
            obj.kdj = copy.deepcopy(self.kdj, memo)
        obj.set_idx(self.idx)
        memo[id(self)] = obj
        return obj

    @property
    def klc(self):
        assert self.__klc is not None
        return self.__klc

    def set_klc(self, klc):
        self.__klc = klc

    @property
    def idx(self):
        return self.__idx

    def set_idx(self, idx):
        self.__idx: int = idx

    def __str__(self):
        return f"{self.idx}:{self.time}/{self.kl_type} open={self.open} close={self.close} high={self.high} low={self.low} {self.trade_info}"

    def check(self, autofix=False):
        if self.low > min([self.low, self.open, self.high, self.close]):
            if autofix:
                self.low = min([self.low, self.open, self.high, self.close])
            else:
                raise CChanException(f"{self.time} low price={self.low} is not min of [low={self.low}, open={self.open}, high={self.high}, close={self.close}]", ErrCode.KL_DATA_INVALID)
        if self.high < max([self.low, self.open, self.high, self.close]):
            if autofix:
                self.high = max([self.low, self.open, self.high, self.close])
            else:
                raise CChanException(f"{self.time} high price={self.high} is not max of [low={self.low}, open={self.open}, high={self.high}, close={self.close}]", ErrCode.KL_DATA_INVALID)

    def add_children(self, child):
        self.sub_kl_list.append(child)

    def set_parent(self, parent: 'CKLine_Unit'):
        self.sup_kl = parent

    def get_children(self):
        yield from self.sub_kl_list

    def _low(self):
        return self.low

    def _high(self):
        return self.high

    def set_metric(self, metric_model_lst: list) -> None:
        for metric_model in metric_model_lst:
            if isinstance(metric_model, CMACD):
                self.macd: CMACD_item = metric_model.add(self.close)
            elif isinstance(metric_model, CTrendModel):
                if metric_model.type not in self.trend:
                    self.trend[metric_model.type] = {}
                self.trend[metric_model.type][metric_model.T] = metric_model.add(self.close)
            elif isinstance(metric_model, BollModel):
                self.boll: BOLL_Metric = metric_model.add(self.close)
            elif isinstance(metric_model, CDemarkEngine):
                self.demark = metric_model.update(idx=self.idx, close=self.close, high=self.high, low=self.low)
            elif isinstance(metric_model, RSI):
                self.rsi = metric_model.add(self.close)
            elif isinstance(metric_model, KDJ):
                self.kdj = metric_model.add(self.high, self.low, self.close)

    def get_parent_klc(self):
        assert self.sup_kl is not None
        return self.sup_kl.klc

    def include_sub_lv_time(self, sub_lv_t: str) -> bool:
        if self.time.to_str() == sub_lv_t:
            return True
        for sub_klu in self.sub_kl_list:
            if sub_klu.time.to_str() == sub_lv_t:
                return True
            if sub_klu.include_sub_lv_time(sub_lv_t):
                return True
        return False

    def set_pre_klu(self, pre_klu: Optional['CKLine_Unit']):
        if pre_klu is None:
            return
        pre_klu.next = self
        self.pre = pre_klu


# ==================== KLine/KLine.py ====================



# 合并后的K线
class CKLine(CKLine_Combiner[CKLine_Unit]):
    def __init__(self, kl_unit: CKLine_Unit, idx, _dir=KLINE_DIR.UP):
        super(CKLine, self).__init__(kl_unit, _dir)
        self.idx: int = idx
        self.kl_type = kl_unit.kl_type
        kl_unit.set_klc(self)

    def __str__(self):
        fx_token = ""
        if self.fx == FX_TYPE.TOP:
            fx_token = "^"
        elif self.fx == FX_TYPE.BOTTOM:
            fx_token = "_"
        return f"{self.idx}th{fx_token}:{self.time_begin}~{self.time_end}({self.kl_type}|{len(self.lst)}) low={self.low} high={self.high}"

    def GetSubKLC(self):
        # 可能会出现相邻的两个KLC的子KLC会有重复
        # 因为子KLU合并时正好跨过了父KLC的结束时间边界
        last_klc = None
        for klu in self.lst:
            for sub_klu in klu.get_children():
                if sub_klu.klc != last_klc:
                    last_klc = sub_klu.klc
                    yield sub_klu.klc

    def get_klu_max_high(self) -> float:
        return max(x.high for x in self.lst)

    def get_klu_min_low(self) -> float:
        return min(x.low for x in self.lst)

    def has_gap_with_next(self) -> bool:
        assert self.next is not None
        # 相同也算重叠，也就是没有gap
        return not has_overlap(self.get_klu_min_low(), self.get_klu_max_high(), self.next.get_klu_min_low(), self.next.get_klu_max_high(), equal=True)

    def check_fx_valid(self, item2: "CKLine", method, for_virtual=False):
        # for_virtual: 虚笔时使用
        assert self.next is not None and item2.pre is not None
        assert self.pre is not None
        assert item2.idx > self.idx
        if self.fx == FX_TYPE.TOP:
            assert for_virtual or item2.fx == FX_TYPE.BOTTOM
            if for_virtual and item2.dir != KLINE_DIR.DOWN:
                return False
            if method == FX_CHECK_METHOD.HALF:  # 检测前两KLC
                item2_high = max([item2.pre.high, item2.high])
                self_low = min([self.low, self.next.low])
            elif method == FX_CHECK_METHOD.LOSS:  # 只检测顶底分形KLC
                item2_high = item2.high
                self_low = self.low
            elif method in (FX_CHECK_METHOD.STRICT, FX_CHECK_METHOD.TOTALLY):
                if for_virtual:
                    item2_high = max([item2.pre.high, item2.high])
                else:
                    assert item2.next is not None
                    item2_high = max([item2.pre.high, item2.high, item2.next.high])
                self_low = min([self.pre.low, self.low, self.next.low])
            else:
                raise CChanException("bi_fx_check config error!", ErrCode.CONFIG_ERROR)
            if method == FX_CHECK_METHOD.TOTALLY:
                return self.low > item2_high
            else:
                return self.high > item2_high and item2.low < self_low
        elif self.fx == FX_TYPE.BOTTOM:
            assert for_virtual or item2.fx == FX_TYPE.TOP
            if for_virtual and item2.dir != KLINE_DIR.UP:
                return False
            if method == FX_CHECK_METHOD.HALF:
                item2_low = min([item2.pre.low, item2.low])
                cur_high = max([self.high, self.next.high])
            elif method == FX_CHECK_METHOD.LOSS:
                item2_low = item2.low
                cur_high = self.high
            elif method in (FX_CHECK_METHOD.STRICT, FX_CHECK_METHOD.TOTALLY):
                if for_virtual:
                    item2_low = min([item2.pre.low, item2.low])
                else:
                    assert item2.next is not None
                    item2_low = min([item2.pre.low, item2.low, item2.next.low])
                cur_high = max([self.pre.high, self.high, self.next.high])
            else:
                raise CChanException("bi_fx_check config error!", ErrCode.CONFIG_ERROR)
            if method == FX_CHECK_METHOD.TOTALLY:
                return self.high < item2_low
            else:
                return self.low < item2_low and item2.high > cur_high
        else:
            raise CChanException("only top/bottom fx can check_valid_top_button", ErrCode.BI_ERR)


# ==================== KLine/KLine_List.py ====================

import copy
from typing import List, Union, overload



def get_seglist_instance(seg_config: CSegConfig, lv) -> CSegListComm:
    if seg_config.seg_algo == "chan":
        return CSegListChan(seg_config, lv)
    elif seg_config.seg_algo == "1+1":
        print(f'Please avoid using seg_algo={seg_config.seg_algo} as it is deprecated and no longer maintained.')
        return CSegListDYH(seg_config, lv)
    elif seg_config.seg_algo == "break":
        print(f'Please avoid using seg_algo={seg_config.seg_algo} as it is deprecated and no longer maintained.')
        return CSegListDef(seg_config, lv)
    else:
        raise CChanException(f"unsupport seg algoright:{seg_config.seg_algo}", ErrCode.PARA_ERROR)


class CKLine_List:
    def __init__(self, kl_type, conf: CChanConfig):
        self.kl_type = kl_type
        self.config = conf
        self.lst: List[CKLine] = []  # K线列表，可递归  元素KLine类型
        self.bi_list = CBiList(bi_conf=conf.bi_conf)
        self.seg_list: CSegListComm[CBi] = get_seglist_instance(seg_config=conf.seg_conf, lv=SEG_TYPE.BI)
        self.segseg_list: CSegListComm[CSeg[CBi]] = get_seglist_instance(seg_config=conf.seg_conf, lv=SEG_TYPE.SEG)

        self.zs_list = CZSList(zs_config=conf.zs_conf)
        self.segzs_list = CZSList(zs_config=conf.zs_conf)

        self.bs_point_lst = CBSPointList[CBi, CBiList](bs_point_config=conf.bs_point_conf)
        self.seg_bs_point_lst = CBSPointList[CSeg, CSegListComm](bs_point_config=conf.seg_bs_point_conf)

        self.metric_model_lst = conf.GetMetricModel()

        self.step_calculation = self.need_cal_step_by_step()

        self.last_sure_seg_start_bi_idx = -1
        self.last_sure_segseg_start_bi_idx = -1

    def __deepcopy__(self, memo):
        new_obj = CKLine_List(self.kl_type, self.config)
        memo[id(self)] = new_obj
        for klc in self.lst:
            klus_new = []
            for klu in klc.lst:
                new_klu = copy.deepcopy(klu, memo)
                memo[id(klu)] = new_klu
                if klu.pre is not None:
                    new_klu.set_pre_klu(memo[id(klu.pre)])
                klus_new.append(new_klu)

            new_klc = CKLine(klus_new[0], idx=klc.idx, _dir=klc.dir)
            new_klc.set_fx(klc.fx)
            new_klc.kl_type = klc.kl_type
            for idx, klu in enumerate(klus_new):
                klu.set_klc(new_klc)
                if idx != 0:
                    new_klc.try_add(klu, skip_update_input=True)
            memo[id(klc)] = new_klc
            if new_obj.lst:
                new_obj.lst[-1].set_next(new_klc)
                new_klc.set_pre(new_obj.lst[-1])
            new_obj.lst.append(new_klc)
        new_obj.bi_list = copy.deepcopy(self.bi_list, memo)
        new_obj.seg_list = copy.deepcopy(self.seg_list, memo)
        new_obj.segseg_list = copy.deepcopy(self.segseg_list, memo)
        new_obj.zs_list = copy.deepcopy(self.zs_list, memo)
        new_obj.segzs_list = copy.deepcopy(self.segzs_list, memo)
        new_obj.bs_point_lst = copy.deepcopy(self.bs_point_lst, memo)
        new_obj.metric_model_lst = copy.deepcopy(self.metric_model_lst, memo)
        new_obj.step_calculation = copy.deepcopy(self.step_calculation, memo)
        new_obj.seg_bs_point_lst = copy.deepcopy(self.seg_bs_point_lst, memo)
        return new_obj

    @overload
    def __getitem__(self, index: int) -> CKLine: ...

    @overload
    def __getitem__(self, index: slice) -> List[CKLine]: ...

    def __getitem__(self, index: Union[slice, int]) -> Union[List[CKLine], CKLine]:
        return self.lst[index]

    def __len__(self):
        return len(self.lst)

    def cal_seg_and_zs(self):
        if not self.step_calculation:
            self.bi_list.try_add_virtual_bi(self.lst[-1])
        self.last_sure_seg_start_bi_idx = cal_seg(self.bi_list, self.seg_list, self.last_sure_seg_start_bi_idx)
        self.zs_list.cal_bi_zs(self.bi_list, self.seg_list)
        update_zs_in_seg(self.bi_list, self.seg_list, self.zs_list)  # 计算seg的zs_lst，以及中枢的bi_in, bi_out

        self.last_sure_segseg_start_bi_idx = cal_seg(self.seg_list, self.segseg_list, self.last_sure_segseg_start_bi_idx)
        self.segzs_list.cal_bi_zs(self.seg_list, self.segseg_list)
        update_zs_in_seg(self.seg_list, self.segseg_list, self.segzs_list)  # 计算segseg的zs_lst，以及中枢的bi_in, bi_out

        # 计算买卖点
        self.seg_bs_point_lst.cal(self.seg_list, self.segseg_list)  # 线段线段买卖点
        self.bs_point_lst.cal(self.bi_list, self.seg_list)  # 再算笔买卖点

    def need_cal_step_by_step(self):
        return self.config.trigger_step

    def add_single_klu(self, klu: CKLine_Unit):
        klu.set_metric(self.metric_model_lst)
        if len(self.lst) == 0:
            self.lst.append(CKLine(klu, idx=0))
        else:
            _dir = self.lst[-1].try_add(klu)
            if _dir != KLINE_DIR.COMBINE:  # 不需要合并K线
                self.lst.append(CKLine(klu, idx=len(self.lst), _dir=_dir))
                if len(self.lst) >= 3:
                    self.lst[-2].update_fx(self.lst[-3], self.lst[-1])
                if self.bi_list.update_bi(self.lst[-2], self.lst[-1], self.step_calculation) and self.step_calculation:
                    self.cal_seg_and_zs()
            elif self.step_calculation and self.bi_list.try_add_virtual_bi(self.lst[-1], need_del_end=True):  # 这里的必要性参见issue#175
                self.cal_seg_and_zs()

    def klu_iter(self, klc_begin_idx=0):
        for klc in self.lst[klc_begin_idx:]:
            yield from klc.lst


def cal_seg(bi_list, seg_list: CSegListComm, last_sure_seg_start_bi_idx):
    seg_list.update(bi_list)

    if len(seg_list) == 0:
        for bi in bi_list:
            bi.set_seg_idx(0)
        return -1

    cur_seg: CSeg = seg_list[-1]

    bi_idx = len(bi_list) - 1
    while bi_idx >= 0:
        bi = bi_list[bi_idx]
        if bi.seg_idx is not None and bi.idx < last_sure_seg_start_bi_idx:
            break
        if bi.idx > cur_seg.end_bi.idx:
            bi.set_seg_idx(cur_seg.idx+1)
            bi_idx -= 1
            continue
        if bi.idx < cur_seg.start_bi.idx:
            assert cur_seg.pre
            cur_seg = cur_seg.pre
        bi.set_seg_idx(cur_seg.idx)
        bi_idx -= 1

    last_sure_seg_start_bi_idx = -1
    seg = seg_list[-1]
    while seg:
        if seg.is_sure:
            last_sure_seg_start_bi_idx = seg.start_bi.idx
            break
        seg = seg.pre
    return last_sure_seg_start_bi_idx


def update_zs_in_seg(bi_list, seg_list, zs_list):
    sure_seg_cnt = 0
    seg_idx = len(seg_list) - 1
    while seg_idx >= 0:
        seg = seg_list[seg_idx]
        if seg.ele_inside_is_sure:
            break
        if seg.is_sure:
            sure_seg_cnt += 1
        seg.clear_zs_lst()
        _zs_idx = len(zs_list) - 1
        while _zs_idx >= 0:
            zs = zs_list[_zs_idx]
            if zs.end.idx < seg.start_bi.get_begin_klu().idx:
                break
            if zs.is_inside(seg):
                seg.add_zs(zs)
            assert zs.begin_bi.idx > 0
            zs.set_bi_in(bi_list[zs.begin_bi.idx-1])
            if zs.end_bi.idx+1 < len(bi_list):
                zs.set_bi_out(bi_list[zs.end_bi.idx+1])
            zs.set_bi_lst(list(bi_list[zs.begin_bi.idx:zs.end_bi.idx+1]))
            _zs_idx -= 1

        if sure_seg_cnt > 2:
            if not seg.ele_inside_is_sure:
                seg.ele_inside_is_sure = True
        seg_idx -= 1


# ==================== Bi/BiConfig.py ====================



class CBiConfig:
    def __init__(
        self,
        bi_algo="normal",
        is_strict=True,
        bi_fx_check="half",
        gap_as_kl=True,
        bi_end_is_peak=True,
        bi_allow_sub_peak=True,
    ):
        self.bi_algo = bi_algo
        self.is_strict = is_strict
        if bi_fx_check == "strict":
            self.bi_fx_check = FX_CHECK_METHOD.STRICT
        elif bi_fx_check == "loss":
            self.bi_fx_check = FX_CHECK_METHOD.LOSS
        elif bi_fx_check == "half":
            self.bi_fx_check = FX_CHECK_METHOD.HALF
        elif bi_fx_check == 'totally':
            self.bi_fx_check = FX_CHECK_METHOD.TOTALLY
        else:
            raise CChanException(f"unknown bi_fx_check={bi_fx_check}", ErrCode.PARA_ERROR)

        self.gap_as_kl = gap_as_kl
        self.bi_end_is_peak = bi_end_is_peak
        self.bi_allow_sub_peak = bi_allow_sub_peak


# ==================== Bi/Bi.py ====================

from typing import List, Optional



class CBi:
    def __init__(self, begin_klc: CKLine, end_klc: CKLine, idx: int, is_sure: bool):
        # self.__begin_klc = begin_klc
        # self.__end_klc = end_klc
        self.__dir = None
        self.__idx = idx
        self.__type = BI_TYPE.STRICT

        self.set(begin_klc, end_klc)

        self.__is_sure = is_sure
        self.__sure_end: List[CKLine] = []

        self.__seg_idx: Optional[int] = None

        self.parent_seg: Optional[CSeg[CBi]] = None  # 在哪个线段里面

        self.bsp: Optional[CBS_Point] = None  # 尾部是不是买卖点

        self.next: Optional[CBi] = None
        self.pre: Optional[CBi] = None

    def clean_cache(self):
        self._memoize_cache = {}

    @property
    def begin_klc(self): return self.__begin_klc

    @property
    def end_klc(self): return self.__end_klc

    @property
    def dir(self): return self.__dir

    @property
    def idx(self): return self.__idx

    @property
    def type(self): return self.__type

    @property
    def is_sure(self): return self.__is_sure

    @property
    def sure_end(self): return self.__sure_end

    @property
    def klc_lst(self):
        klc = self.begin_klc
        while True:
            yield klc
            klc = klc.next
            if not klc or klc.idx > self.end_klc.idx:
                break

    @property
    def klc_lst_re(self):
        klc = self.end_klc
        while True:
            yield klc
            klc = klc.pre
            if not klc or klc.idx < self.begin_klc.idx:
                break

    @property
    def seg_idx(self): return self.__seg_idx

    def set_seg_idx(self, idx):
        self.__seg_idx = idx

    def __str__(self):
        return f"{self.dir}|{self.begin_klc} ~ {self.end_klc}"

    def check(self):
        try:
            if self.is_down():
                assert self.begin_klc.high > self.end_klc.low
            else:
                assert self.begin_klc.low < self.end_klc.high
        except Exception as e:
            raise CChanException(f"{self.idx}:{self.begin_klc[0].time}~{self.end_klc[-1].time}笔的方向和收尾位置不一致!", ErrCode.BI_ERR) from e

    def set(self, begin_klc: CKLine, end_klc: CKLine):
        self.__begin_klc: CKLine = begin_klc
        self.__end_klc: CKLine = end_klc
        if begin_klc.fx == FX_TYPE.BOTTOM:
            self.__dir = BI_DIR.UP
        elif begin_klc.fx == FX_TYPE.TOP:
            self.__dir = BI_DIR.DOWN
        else:
            raise CChanException("ERROR DIRECTION when creating bi", ErrCode.BI_ERR)
        self.check()
        self.clean_cache()

    @make_cache
    def get_begin_val(self):
        return self.begin_klc.low if self.is_up() else self.begin_klc.high

    @make_cache
    def get_end_val(self):
        return self.end_klc.high if self.is_up() else self.end_klc.low

    @make_cache
    def get_begin_klu(self) -> CKLine_Unit:
        if self.is_up():
            return self.begin_klc.get_peak_klu(is_high=False)
        else:
            return self.begin_klc.get_peak_klu(is_high=True)

    @make_cache
    def get_end_klu(self) -> CKLine_Unit:
        if self.is_up():
            return self.end_klc.get_peak_klu(is_high=True)
        else:
            return self.end_klc.get_peak_klu(is_high=False)

    @make_cache
    def amp(self):
        return abs(self.get_end_val() - self.get_begin_val())

    @make_cache
    def get_klu_cnt(self):
        return self.get_end_klu().idx - self.get_begin_klu().idx + 1

    @make_cache
    def get_klc_cnt(self):
        assert self.end_klc.idx == self.get_end_klu().klc.idx
        assert self.begin_klc.idx == self.get_begin_klu().klc.idx
        return self.end_klc.idx - self.begin_klc.idx + 1

    @make_cache
    def _high(self):
        return self.end_klc.high if self.is_up() else self.begin_klc.high

    @make_cache
    def _low(self):
        return self.begin_klc.low if self.is_up() else self.end_klc.low

    @make_cache
    def _mid(self):
        return (self._high() + self._low()) / 2  # 笔的中位价

    @make_cache
    def is_down(self):
        return self.dir == BI_DIR.DOWN

    @make_cache
    def is_up(self):
        return self.dir == BI_DIR.UP

    def update_virtual_end(self, new_klc: CKLine):
        self.append_sure_end(self.end_klc)
        self.update_new_end(new_klc)
        self.__is_sure = False

    def restore_from_virtual_end(self, sure_end: CKLine):
        self.__is_sure = True
        self.update_new_end(new_klc=sure_end)
        self.__sure_end = []

    def append_sure_end(self, klc: CKLine):
        self.__sure_end.append(klc)

    def update_new_end(self, new_klc: CKLine):
        self.__end_klc = new_klc
        self.check()
        self.clean_cache()

    def cal_macd_metric(self, macd_algo, is_reverse):
        if macd_algo == MACD_ALGO.AREA:
            return self.Cal_MACD_half(is_reverse)
        elif macd_algo == MACD_ALGO.PEAK:
            return self.Cal_MACD_peak()
        elif macd_algo == MACD_ALGO.FULL_AREA:
            return self.Cal_MACD_area()
        elif macd_algo == MACD_ALGO.DIFF:
            return self.Cal_MACD_diff()
        elif macd_algo == MACD_ALGO.SLOPE:
            return self.Cal_MACD_slope()
        elif macd_algo == MACD_ALGO.AMP:
            return self.Cal_MACD_amp()
        elif macd_algo == MACD_ALGO.AMOUNT:
            return self.Cal_MACD_trade_metric(DATA_FIELD.FIELD_TURNOVER, cal_avg=False)
        elif macd_algo == MACD_ALGO.VOLUMN:
            return self.Cal_MACD_trade_metric(DATA_FIELD.FIELD_VOLUME, cal_avg=False)
        elif macd_algo == MACD_ALGO.VOLUMN_AVG:
            return self.Cal_MACD_trade_metric(DATA_FIELD.FIELD_VOLUME, cal_avg=True)
        elif macd_algo == MACD_ALGO.AMOUNT_AVG:
            return self.Cal_MACD_trade_metric(DATA_FIELD.FIELD_TURNOVER, cal_avg=True)
        elif macd_algo == MACD_ALGO.TURNRATE_AVG:
            return self.Cal_MACD_trade_metric(DATA_FIELD.FIELD_TURNRATE, cal_avg=True)
        elif macd_algo == MACD_ALGO.RSI:
            return self.Cal_Rsi()
        else:
            raise CChanException(f"unsupport macd_algo={macd_algo}, should be one of area/full_area/peak/diff/slope/amp", ErrCode.PARA_ERROR)

    @make_cache
    def Cal_Rsi(self):
        rsi_lst: List[float] = []
        for klc in self.klc_lst:
            rsi_lst.extend(klu.rsi for klu in klc.lst)
        return 10000.0/(min(rsi_lst)+1e-7) if self.is_down() else max(rsi_lst)

    @make_cache
    def Cal_MACD_area(self):
        _s = 1e-7
        begin_klu = self.get_begin_klu()
        end_klu = self.get_end_klu()
        for klc in self.klc_lst:
            for klu in klc.lst:
                if klu.idx < begin_klu.idx or klu.idx > end_klu.idx:
                    continue
                if (self.is_down() and klu.macd.macd < 0) or (self.is_up() and klu.macd.macd > 0):
                    _s += abs(klu.macd.macd)
        return _s

    @make_cache
    def Cal_MACD_peak(self):
        peak = 1e-7
        for klc in self.klc_lst:
            for klu in klc.lst:
                if abs(klu.macd.macd) > peak:
                    if self.is_down() and klu.macd.macd < 0:
                        peak = abs(klu.macd.macd)
                    elif self.is_up() and klu.macd.macd > 0:
                        peak = abs(klu.macd.macd)
        return peak

    def Cal_MACD_half(self, is_reverse):
        if is_reverse:
            return self.Cal_MACD_half_reverse()
        else:
            return self.Cal_MACD_half_obverse()

    @make_cache
    def Cal_MACD_half_obverse(self):
        _s = 1e-7
        begin_klu = self.get_begin_klu()
        peak_macd = begin_klu.macd.macd
        for klc in self.klc_lst:
            for klu in klc.lst:
                if klu.idx < begin_klu.idx:
                    continue
                if klu.macd.macd*peak_macd > 0:
                    _s += abs(klu.macd.macd)
                else:
                    break
            else:  # 没有被break，继续找写一个KLC
                continue
            break
        return _s

    @make_cache
    def Cal_MACD_half_reverse(self):
        _s = 1e-7
        begin_klu = self.get_end_klu()
        peak_macd = begin_klu.macd.macd
        for klc in self.klc_lst_re:
            for klu in klc[::-1]:
                if klu.idx > begin_klu.idx:
                    continue
                if klu.macd.macd*peak_macd > 0:
                    _s += abs(klu.macd.macd)
                else:
                    break
            else:  # 没有被break，继续找写一个KLC
                continue
            break
        return _s

    @make_cache
    def Cal_MACD_diff(self):
        """
        macd红绿柱最大值最小值之差
        """
        _max, _min = float("-inf"), float("inf")
        for klc in self.klc_lst:
            for klu in klc.lst:
                macd = klu.macd.macd
                if macd > _max:
                    _max = macd
                if macd < _min:
                    _min = macd
        return _max-_min

    @make_cache
    def Cal_MACD_slope(self):
        begin_klu = self.get_begin_klu()
        end_klu = self.get_end_klu()
        if self.is_up():
            return (end_klu.high - begin_klu.low)/end_klu.high/(end_klu.idx - begin_klu.idx + 1)
        else:
            return (begin_klu.high - end_klu.low)/begin_klu.high/(end_klu.idx - begin_klu.idx + 1)

    @make_cache
    def Cal_MACD_amp(self):
        begin_klu = self.get_begin_klu()
        end_klu = self.get_end_klu()
        if self.is_down():
            return (begin_klu.high-end_klu.low)/begin_klu.high
        else:
            return (end_klu.high-begin_klu.low)/begin_klu.low

    def Cal_MACD_trade_metric(self, metric: str, cal_avg=False) -> float:
        _s = 0
        for klc in self.klc_lst:
            for klu in klc.lst:
                metric_res = klu.trade_info.metric[metric]
                if metric_res is None:
                    return 0.0
                _s += metric_res
        return _s / self.get_klu_cnt() if cal_avg else _s

    # def set_klc_lst(self, lst):
    #     self.__klc_lst = lst


# ==================== Bi/BiList.py ====================

from typing import List, Optional, Union, overload




class CBiList:
    def __init__(self, bi_conf=CBiConfig()):
        self.bi_list: List[CBi] = []
        self.last_end = None  # 最后一笔的尾部
        self.config = bi_conf

        self.free_klc_lst = []  # 仅仅用作第一笔未画出来之前的缓存，为了获得更精准的结果而已，不加这块逻辑其实对后续计算没太大影响

    def __str__(self):
        return "\n".join([str(bi) for bi in self.bi_list])

    def __iter__(self):
        yield from self.bi_list

    @overload
    def __getitem__(self, index: int) -> CBi: ...

    @overload
    def __getitem__(self, index: slice) -> List[CBi]: ...

    def __getitem__(self, index: Union[slice, int]) -> Union[List[CBi], CBi]:
        return self.bi_list[index]

    def __len__(self):
        return len(self.bi_list)

    def try_create_first_bi(self, klc: CKLine) -> bool:
        for exist_free_klc in self.free_klc_lst:
            if exist_free_klc.fx == klc.fx:
                continue
            if self.can_make_bi(klc, exist_free_klc):
                self.add_new_bi(exist_free_klc, klc)
                self.last_end = klc
                return True
        self.free_klc_lst.append(klc)
        self.last_end = klc
        return False

    def update_bi(self, klc: CKLine, last_klc: CKLine, cal_virtual: bool) -> bool:
        # klc: 倒数第二根klc
        # last_klc: 倒数第1根klc
        flag1 = self.update_bi_sure(klc)
        if cal_virtual:
            flag2 = self.try_add_virtual_bi(last_klc)
            return flag1 or flag2
        else:
            return flag1

    def can_update_peak(self, klc: CKLine):
        if self.config.bi_allow_sub_peak or len(self.bi_list) < 2:
            return False
        if self.bi_list[-1].is_down() and klc.high < self.bi_list[-1].get_begin_val():
            return False
        if self.bi_list[-1].is_up() and klc.low > self.bi_list[-1].get_begin_val():
            return False
        if not end_is_peak(self.bi_list[-2].begin_klc, klc):
            return False
        if self[-1].is_down() and self[-1].get_end_val() < self[-2].get_begin_val():
            return False
        if self[-1].is_up() and self[-1].get_end_val() > self[-2].get_begin_val():
            return False
        return True

    def update_peak(self, klc: CKLine, for_virtual=False):
        if not self.can_update_peak(klc):
            return False
        _tmp_last_bi = self.bi_list[-1]
        self.bi_list.pop()
        if not self.try_update_end(klc, for_virtual=for_virtual):
            self.bi_list.append(_tmp_last_bi)
            return False
        else:
            if for_virtual:
                self.bi_list[-1].append_sure_end(_tmp_last_bi.end_klc)
            return True

    def update_bi_sure(self, klc: CKLine) -> bool:
        # klc: 倒数第二根klc
        _tmp_end = self.get_last_klu_of_last_bi()
        self.delete_virtual_bi()
        # 返回值：是否出现新笔
        if klc.fx == FX_TYPE.UNKNOWN:
            return _tmp_end != self.get_last_klu_of_last_bi()  # 虚笔是否有变
        if self.last_end is None or len(self.bi_list) == 0:
            return self.try_create_first_bi(klc)
        if klc.fx == self.last_end.fx:
            return self.try_update_end(klc)
        elif self.can_make_bi(klc, self.last_end):
            self.add_new_bi(self.last_end, klc)
            self.last_end = klc
            return True
        elif self.update_peak(klc):
            return True
        return _tmp_end != self.get_last_klu_of_last_bi()

    def delete_virtual_bi(self):
        if len(self) > 0 and not self.bi_list[-1].is_sure:
            sure_end_list = [klc for klc in self.bi_list[-1].sure_end]
            if len(sure_end_list):
                self.bi_list[-1].restore_from_virtual_end(sure_end_list[0])
                self.last_end = self[-1].end_klc
                for sure_end in sure_end_list[1:]:
                    self.add_new_bi(self.last_end, sure_end, is_sure=True)
                    self.last_end = self[-1].end_klc
            else:
                del self.bi_list[-1]
        self.last_end = self[-1].end_klc if len(self) > 0 else None
        if len(self) > 0:
            self[-1].next = None

    def try_add_virtual_bi(self, klc: CKLine, need_del_end=False):
        if need_del_end:
            self.delete_virtual_bi()
        if len(self) == 0:
            return False
        if klc.idx == self[-1].end_klc.idx:
            return False
        if (self[-1].is_up() and klc.high >= self[-1].end_klc.high) or (self[-1].is_down() and klc.low <= self[-1].end_klc.low):
            # 更新最后一笔
            self.bi_list[-1].update_virtual_end(klc)
            return True
        _tmp_klc = klc
        while _tmp_klc and _tmp_klc.idx > self[-1].end_klc.idx:
            assert _tmp_klc is not None
            if self.can_make_bi(_tmp_klc, self[-1].end_klc, for_virtual=True):
                # 新增一笔
                self.add_new_bi(self.last_end, _tmp_klc, is_sure=False)
                return True
            elif self.update_peak(_tmp_klc, for_virtual=True):
                return True
            _tmp_klc = _tmp_klc.pre
        return False

    def add_new_bi(self, pre_klc, cur_klc, is_sure=True):
        self.bi_list.append(CBi(pre_klc, cur_klc, idx=len(self.bi_list), is_sure=is_sure))
        if len(self.bi_list) >= 2:
            self.bi_list[-2].next = self.bi_list[-1]
            self.bi_list[-1].pre = self.bi_list[-2]

    def satisfy_bi_span(self, klc: CKLine, last_end: CKLine):
        bi_span = self.get_klc_span(klc, last_end)
        if self.config.is_strict:
            return bi_span >= 4
        uint_kl_cnt = 0
        tmp_klc = last_end.next
        while tmp_klc:
            uint_kl_cnt += len(tmp_klc.lst)
            if not tmp_klc.next:  # 最后尾部虚笔的时候，可能klc.idx == last_end.idx+1
                return False
            if tmp_klc.next.idx < klc.idx:
                tmp_klc = tmp_klc.next
            else:
                break
        return bi_span >= 3 and uint_kl_cnt >= 3

    def get_klc_span(self, klc: CKLine, last_end: CKLine) -> int:
        span = klc.idx - last_end.idx
        if not self.config.gap_as_kl:
            return span
        if span >= 4:  # 加速运算，如果span需要真正精确的值，需要去掉这一行
            return span
        tmp_klc = last_end
        while tmp_klc and tmp_klc.idx < klc.idx:
            if tmp_klc.has_gap_with_next():
                span += 1
            tmp_klc = tmp_klc.next
        return span

    def can_make_bi(self, klc: CKLine, last_end: CKLine, for_virtual: bool = False):
        satisify_span = True if self.config.bi_algo == 'fx' else self.satisfy_bi_span(klc, last_end)
        if not satisify_span:
            return False
        if not last_end.check_fx_valid(klc, self.config.bi_fx_check, for_virtual):
            return False
        if self.config.bi_end_is_peak and not end_is_peak(last_end, klc):
            return False
        return True

    def try_update_end(self, klc: CKLine, for_virtual=False) -> bool:
        def check_top(klc: CKLine, for_virtual):
            if for_virtual:
                return klc.dir == KLINE_DIR.UP
            else:
                return klc.fx == FX_TYPE.TOP

        def check_bottom(klc: CKLine, for_virtual):
            if for_virtual:
                return klc.dir == KLINE_DIR.DOWN
            else:
                return klc.fx == FX_TYPE.BOTTOM

        if len(self.bi_list) == 0:
            return False
        last_bi = self.bi_list[-1]
        if (last_bi.is_up() and check_top(klc, for_virtual) and klc.high >= last_bi.get_end_val()) or \
           (last_bi.is_down() and check_bottom(klc, for_virtual) and klc.low <= last_bi.get_end_val()):
            last_bi.update_virtual_end(klc) if for_virtual else last_bi.update_new_end(klc)
            self.last_end = klc
            return True
        else:
            return False

    def get_last_klu_of_last_bi(self) -> Optional[int]:
        return self.bi_list[-1].get_end_klu().idx if len(self) > 0 else None


def end_is_peak(last_end: CKLine, cur_end: CKLine) -> bool:
    if last_end.fx == FX_TYPE.BOTTOM:
        cmp_thred = cur_end.high  # 或者严格点选择get_klu_max_high()
        klc = last_end.get_next()
        while True:
            if klc.idx >= cur_end.idx:
                return True
            if klc.high > cmp_thred:
                return False
            klc = klc.get_next()
    elif last_end.fx == FX_TYPE.TOP:
        cmp_thred = cur_end.low  # 或者严格点选择get_klu_min_low()
        klc = last_end.get_next()
        while True:
            if klc.idx >= cur_end.idx:
                return True
            if klc.low < cmp_thred:
                return False
            klc = klc.get_next()
    return True


# ==================== Seg/SegConfig.py ====================



class CSegConfig:
    def __init__(self, seg_algo="chan", left_method="peak"):
        self.seg_algo = seg_algo
        if left_method == "all":
            self.left_method = LEFT_SEG_METHOD.ALL
        elif left_method == "peak":
            self.left_method = LEFT_SEG_METHOD.PEAK
        else:
            raise CChanException(f"unknown left_seg_method={left_method}", ErrCode.PARA_ERROR)


# ==================== Seg/Eigen.py ====================

from typing import Self



class CEigen(CKLine_Combiner[CBi]):
    def __init__(self, bi, _dir):
        super(CEigen, self).__init__(bi, _dir)
        self.gap = False

    def update_fx(self, _pre: Self, _next: Self, exclude_included=False, allow_top_equal=None):
        super(CEigen, self).update_fx(_pre, _next, exclude_included, allow_top_equal)
        if (self.fx == FX_TYPE.TOP and _pre.high < self.low) or \
           (self.fx == FX_TYPE.BOTTOM and _pre.low > self.high):
            self.gap = True

    def __str__(self):
        return f"{self.lst[0].idx}~{self.lst[-1].idx} gap={self.gap} fx={self.fx}"

    def GetPeakBiIdx(self):
        assert self.fx != FX_TYPE.UNKNOWN
        bi_dir = self.lst[0].dir
        if bi_dir == BI_DIR.UP:  # 下降线段
            return self.get_peak_klu(is_high=False).idx-1
        else:
            return self.get_peak_klu(is_high=True).idx-1


# ==================== Seg/EigenFX.py ====================

from typing import List, Optional




class CEigenFX:
    def __init__(self, _dir: BI_DIR, exclude_included=True, lv=SEG_TYPE.BI):
        self.lv = lv
        self.dir = _dir  # 线段方向
        self.ele: List[Optional[CEigen]] = [None, None, None]
        self.lst: List[CBi] = []
        self.exclude_included = exclude_included
        self.kl_dir = KLINE_DIR.UP if _dir == BI_DIR.UP else KLINE_DIR.DOWN
        self.last_evidence_bi: Optional[CBi] = None

    def treat_first_ele(self, bi: CBi) -> bool:
        self.ele[0] = CEigen(bi, self.kl_dir)
        return False

    def treat_second_ele(self, bi: CBi) -> bool:
        assert self.ele[0] is not None
        combine_dir = self.ele[0].try_add(bi, exclude_included=self.exclude_included)
        if combine_dir != KLINE_DIR.COMBINE:  # 不能合并
            self.ele[1] = CEigen(bi, self.kl_dir)
            if (self.is_up() and self.ele[1].high < self.ele[0].high) or \
               (self.is_down() and self.ele[1].low > self.ele[0].low):  # 前两元素不可能成为分形
                return self.reset()
        return False

    def treat_third_ele(self, bi: CBi) -> bool:
        assert self.ele[0] is not None
        assert self.ele[1] is not None
        self.last_evidence_bi = bi
        allow_top_equal = (1 if bi.is_down() else -1) if self.exclude_included else None
        combine_dir = self.ele[1].try_add(bi, allow_top_equal=allow_top_equal)
        if combine_dir == KLINE_DIR.COMBINE:
            return False
        self.ele[2] = CEigen(bi, combine_dir)
        if not self.actual_break():
            return self.reset()
        self.ele[1].update_fx(self.ele[0], self.ele[2], exclude_included=self.exclude_included, allow_top_equal=allow_top_equal)  # type: ignore
        fx = self.ele[1].fx
        is_fx = (self.is_up() and fx == FX_TYPE.TOP) or (self.is_down() and fx == FX_TYPE.BOTTOM)
        return True if is_fx else self.reset()

    def add(self, bi: CBi) -> bool:  # 返回是否出现分形
        assert bi.dir != self.dir
        self.lst.append(bi)
        if self.ele[0] is None:  # 第一元素
            return self.treat_first_ele(bi)
        elif self.ele[1] is None:  # 第二元素
            return self.treat_second_ele(bi)
        elif self.ele[2] is None:  # 第三元素
            return self.treat_third_ele(bi)
        else:
            raise CChanException(f"特征序列3个都找齐了还没处理!! 当前笔:{bi.idx},当前:{str(self)}", ErrCode.SEG_EIGEN_ERR)

    def reset(self):
        bi_tmp_list = list(self.lst[1:])
        if self.exclude_included:
            self.clear()
            for bi in bi_tmp_list:
                if self.add(bi):
                    return True
        else:
            assert self.ele[1] is not None
            ele2_begin_idx = self.ele[1].lst[0].idx
            self.ele[0], self.ele[1], self.ele[2] = self.ele[1], self.ele[2], None
            self.lst = [bi for bi in bi_tmp_list if bi.idx >= ele2_begin_idx]  # 从第二元素开始

        return False

    def can_be_end(self, bi_lst: CBiList):
        assert self.ele[1] is not None
        if self.ele[1].gap:
            assert self.ele[0] is not None
            end_bi_idx = self.GetPeakBiIdx()
            thred_value = bi_lst[end_bi_idx].get_end_val()
            break_thred = self.ele[0].low if self.is_up() else self.ele[0].high
            return self.find_revert_fx(bi_lst, end_bi_idx+2, thred_value, break_thred)
        else:
            return True

    def is_down(self):
        return self.dir == BI_DIR.DOWN

    def is_up(self):
        return self.dir == BI_DIR.UP

    def GetPeakBiIdx(self):
        assert self.ele[1] is not None
        return self.ele[1].GetPeakBiIdx()

    def all_bi_is_sure(self):
        assert self.last_evidence_bi is not None
        return next((False for bi in self.lst if not bi.is_sure), self.last_evidence_bi.is_sure)

    def clear(self):
        self.ele = [None, None, None]
        self.lst = []

    def __str__(self):
        _t = [f"{[] if ele is None else ','.join([str(b.idx) for b in ele.lst])}" for ele in self.ele]
        return " | ".join(_t)

    def actual_break(self):
        if not self.exclude_included:
            return True
        assert self.ele[2] and self.ele[1]
        if (self.is_up() and self.ele[2].low < self.ele[1][-1]._low()) or \
           (self.is_down() and self.ele[2].high > self.ele[1][-1]._high()):  # 防止第二元素因为合并导致后面没有实际突破
            return True
        assert len(self.ele[2]) == 1
        ele2_bi = self.ele[2][0]
        if ele2_bi.next and ele2_bi.next.next:
            if ele2_bi.is_down() and ele2_bi.next.next._low() < ele2_bi._low():
                self.last_evidence_bi = ele2_bi.next.next
                return True
            elif ele2_bi.is_up() and ele2_bi.next.next._high() > ele2_bi._high():
                self.last_evidence_bi = ele2_bi.next.next
                return True
        return False

    def find_revert_fx(self, bi_list: CBiList, begin_idx: int, thred_value: float, break_thred: float):
        COMMON_COMBINE = False  # 是否用普通分形合并规则处理
        # 如果返回None，表示找到最后了
        first_bi_dir = bi_list[begin_idx].dir  # down则是要找顶分型
        egien_fx = CEigenFX(revert_bi_dir(first_bi_dir), exclude_included=not COMMON_COMBINE, lv=self.lv)  # 顶分型的话要找上升线段
        for bi in bi_list[begin_idx::2]:
            if egien_fx.add(bi):
                if COMMON_COMBINE:
                    return True

                while True:
                    _test = egien_fx.can_be_end(bi_list)
                    if _test in [True, None]:
                        self.last_evidence_bi = bi
                        return _test
                    elif not egien_fx.reset():
                        break
            # if (bi.is_down() and bi._low() < thred_value) or (bi.is_up() and bi._high() > thred_value):
            # 这段逻辑删除的原因参看#272，如果有其他badcase，再看怎么统一修复
            #     return False
        return None


# ==================== Seg/Seg.py ====================

from typing import Generic, List, Optional, Self, TypeVar



LINE_TYPE = TypeVar('LINE_TYPE', CBi, "CSeg")


class CSeg(Generic[LINE_TYPE]):
    def __init__(self, idx: int, start_bi: LINE_TYPE, end_bi: LINE_TYPE, is_sure=True, seg_dir=None, reason="normal"):
        assert start_bi.idx == 0 or start_bi.dir == end_bi.dir or not is_sure, f"{start_bi.idx} {end_bi.idx} {start_bi.dir} {end_bi.dir}"
        self.idx = idx
        self.start_bi = start_bi
        self.end_bi = end_bi
        self.is_sure = is_sure
        self.dir = end_bi.dir if seg_dir is None else seg_dir

        self.zs_lst: List[CZS[LINE_TYPE]] = []

        self.eigen_fx: Optional[CEigenFX] = None
        self.seg_idx = None  # 线段的线段用
        self.parent_seg: Optional[CSeg] = None  # 在哪个线段里面
        self.pre: Optional[Self] = None
        self.next: Optional[Self] = None

        self.bsp: Optional[CBS_Point] = None  # 尾部是不是买卖点

        self.bi_list: List[LINE_TYPE] = []  # 仅通过self.update_bi_list来更新
        self.reason = reason
        self.support_trend_line = None
        self.resistance_trend_line = None
        if end_bi.idx - start_bi.idx < 2:
            self.is_sure = False
        self.check()

        self.ele_inside_is_sure = False

    def set_seg_idx(self, idx):
        self.seg_idx = idx

    def check(self):
        if not self.is_sure:
            return
        if self.is_down():
            if self.start_bi.get_begin_val() < self.end_bi.get_end_val():
                raise CChanException(f"下降线段起始点应该高于结束点! idx={self.idx}", ErrCode.SEG_END_VALUE_ERR)
        elif self.start_bi.get_begin_val() > self.end_bi.get_end_val():
            raise CChanException(f"上升线段起始点应该低于结束点! idx={self.idx}", ErrCode.SEG_END_VALUE_ERR)
        if self.end_bi.idx - self.start_bi.idx < 2:
            raise CChanException(f"线段({self.start_bi.idx}-{self.end_bi.idx})长度不能小于2! idx={self.idx}", ErrCode.SEG_LEN_ERR)

    def __str__(self):
        return f"{self.start_bi.idx}->{self.end_bi.idx}: {self.dir}  {self.is_sure}"

    def add_zs(self, zs):
        self.zs_lst = [zs] + self.zs_lst  # 因为中枢是反序加入的

    def cal_klu_slope(self):
        assert self.end_bi.idx >= self.start_bi.idx
        return (self.get_end_val()-self.get_begin_val())/(self.get_end_klu().idx-self.get_begin_klu().idx)/self.get_begin_val()

    def cal_amp(self):
        return (self.get_end_val()-self.get_begin_val())/self.get_begin_val()

    def cal_bi_cnt(self):
        return self.end_bi.idx-self.start_bi.idx+1

    def clear_zs_lst(self):
        self.zs_lst = []

    def _low(self):
        return self.end_bi.get_end_klu().low if self.is_down() else self.start_bi.get_begin_klu().low

    def _high(self):
        return self.end_bi.get_end_klu().high if self.is_up() else self.start_bi.get_begin_klu().high

    def is_down(self):
        return self.dir == BI_DIR.DOWN

    def is_up(self):
        return self.dir == BI_DIR.UP

    def get_end_val(self):
        return self.end_bi.get_end_val()

    def get_begin_val(self):
        return self.start_bi.get_begin_val()

    def amp(self):
        return abs(self.get_end_val() - self.get_begin_val())

    def get_end_klu(self) -> CKLine_Unit:
        return self.end_bi.get_end_klu()

    def get_begin_klu(self) -> CKLine_Unit:
        return self.start_bi.get_begin_klu()

    def get_klu_cnt(self):
        return self.get_end_klu().idx - self.get_begin_klu().idx + 1

    def cal_macd_metric(self, macd_algo, is_reverse):
        if macd_algo == MACD_ALGO.SLOPE:
            return self.Cal_MACD_slope()
        elif macd_algo == MACD_ALGO.AMP:
            return self.Cal_MACD_amp()
        else:
            raise CChanException(f"unsupport macd_algo={macd_algo} of Seg, should be one of slope/amp", ErrCode.PARA_ERROR)

    def Cal_MACD_slope(self):
        begin_klu = self.get_begin_klu()
        end_klu = self.get_end_klu()
        if self.is_up():
            return (end_klu.high - begin_klu.low)/end_klu.high/(end_klu.idx - begin_klu.idx + 1)
        else:
            return (begin_klu.high - end_klu.low)/begin_klu.high/(end_klu.idx - begin_klu.idx + 1)

    def Cal_MACD_amp(self):
        begin_klu = self.get_begin_klu()
        end_klu = self.get_end_klu()
        if self.is_down():
            return (begin_klu.high-end_klu.low)/begin_klu.high
        else:
            return (end_klu.high-begin_klu.low)/begin_klu.low

    def update_bi_list(self, bi_lst, idx1, idx2):
        for bi_idx in range(idx1, idx2+1):
            bi_lst[bi_idx].parent_seg = self
            self.bi_list.append(bi_lst[bi_idx])
        if len(self.bi_list) >= 3:
            self.support_trend_line = CTrendLine(self.bi_list, TREND_LINE_SIDE.INSIDE)
            self.resistance_trend_line = CTrendLine(self.bi_list, TREND_LINE_SIDE.OUTSIDE)

    def get_first_multi_bi_zs(self):
        return next((zs for zs in self.zs_lst if not zs.is_one_bi_zs()), None)

    def get_multi_bi_zs_lst(self):
        return [zs for zs in self.zs_lst if not zs.is_one_bi_zs()]

    def get_final_multi_bi_zs(self):
        zs_idx = len(self.zs_lst) - 1
        while zs_idx >= 0:
            zs = self.zs_lst[zs_idx]
            if not zs.is_one_bi_zs():
                return zs
            zs_idx -= 1
        return None

    def get_multi_bi_zs_cnt(self):
        return sum(not zs.is_one_bi_zs() for zs in self.zs_lst)


# ==================== Seg/SegListComm.py ====================

import abc
from typing import Generic, List, TypeVar, Union, overload



SUB_LINE_TYPE = TypeVar('SUB_LINE_TYPE', CBi, "CSeg")


class CSegListComm(Generic[SUB_LINE_TYPE]):
    def __init__(self, seg_config=CSegConfig(), lv=SEG_TYPE.BI):
        self.lst: List[CSeg[SUB_LINE_TYPE]] = []
        self.lv = lv
        self.do_init()
        self.config = seg_config

    def do_init(self):
        self.lst = []

    def __iter__(self):
        yield from self.lst

    @overload
    def __getitem__(self, index: int) -> CSeg[SUB_LINE_TYPE]: ...

    @overload
    def __getitem__(self, index: slice) -> List[CSeg[SUB_LINE_TYPE]]: ...

    def __getitem__(self, index: Union[slice, int]) -> Union[List[CSeg[SUB_LINE_TYPE]], CSeg[SUB_LINE_TYPE]]:
        return self.lst[index]

    def __len__(self):
        return len(self.lst)

    def left_bi_break(self, bi_lst: CBiList):
        # 最后一个确定线段之后的笔有突破该线段最后一笔的
        if len(self) == 0:
            return False
        last_seg_end_bi = self[-1].end_bi
        for bi in bi_lst[last_seg_end_bi.idx+1:]:
            if last_seg_end_bi.is_up() and bi._high() > last_seg_end_bi._high():
                return True
            elif last_seg_end_bi.is_down() and bi._low() < last_seg_end_bi._low():
                return True
        return False

    def collect_first_seg(self, bi_lst: CBiList):
        if len(bi_lst) < 3:
            return
        if self.config.left_method == LEFT_SEG_METHOD.PEAK:
            _high = max(bi._high() for bi in bi_lst)
            _low = min(bi._low() for bi in bi_lst)
            if abs(_high-bi_lst[0].get_begin_val()) >= abs(_low-bi_lst[0].get_begin_val()):
                peak_bi = FindPeakBi(bi_lst, is_high=True)
                assert peak_bi is not None
                self.add_new_seg(bi_lst, peak_bi.idx, is_sure=False, seg_dir=BI_DIR.UP, split_first_seg=False, reason="0seg_find_high")
            else:
                peak_bi = FindPeakBi(bi_lst, is_high=False)
                assert peak_bi is not None
                self.add_new_seg(bi_lst, peak_bi.idx, is_sure=False, seg_dir=BI_DIR.DOWN, split_first_seg=False, reason="0seg_find_low")
            self.collect_left_as_seg(bi_lst)
        elif self.config.left_method == LEFT_SEG_METHOD.ALL:
            _dir = BI_DIR.UP if bi_lst[-1].get_end_val() >= bi_lst[0].get_begin_val() else BI_DIR.DOWN
            self.add_new_seg(bi_lst, bi_lst[-1].idx, is_sure=False, seg_dir=_dir, split_first_seg=False, reason="0seg_collect_all")
        else:
            raise CChanException(f"unknown seg left_method = {self.config.left_method}", ErrCode.PARA_ERROR)

    def collect_left_seg_peak_method(self, last_seg_end_bi, bi_lst):
        find_new_seg = False
        if last_seg_end_bi.is_down():
            peak_bi = FindPeakBi(bi_lst[last_seg_end_bi.idx+3:], is_high=True)
            if peak_bi and peak_bi.idx - last_seg_end_bi.idx >= 3:
                self.add_new_seg(bi_lst, peak_bi.idx, is_sure=False, seg_dir=BI_DIR.UP, reason="collectleft_find_high")
                find_new_seg = True
        else:
            peak_bi = FindPeakBi(bi_lst[last_seg_end_bi.idx+3:], is_high=False)
            if peak_bi and peak_bi.idx - last_seg_end_bi.idx >= 3:
                self.add_new_seg(bi_lst, peak_bi.idx, is_sure=False, seg_dir=BI_DIR.DOWN, reason="collectleft_find_low")
                find_new_seg = True
        last_seg_end_bi = self[-1].end_bi
        if not find_new_seg:
            self.collect_left_as_seg(bi_lst)
        else:
            self.collect_left_seg_peak_method(last_seg_end_bi, bi_lst)

    def collect_segs(self, bi_lst):
        last_bi = bi_lst[-1]
        last_seg_end_bi = self[-1].end_bi
        if last_bi.idx-last_seg_end_bi.idx < 3:
            return
        if last_seg_end_bi.is_down() and last_bi.get_end_val() <= last_seg_end_bi.get_end_val():
            if peak_bi := FindPeakBi(bi_lst[last_seg_end_bi.idx+3:], is_high=True):
                self.add_new_seg(bi_lst, peak_bi.idx, is_sure=False, seg_dir=BI_DIR.UP, reason="collectleft_find_high_force")
                self.collect_left_seg(bi_lst)
        elif last_seg_end_bi.is_up() and last_bi.get_end_val() >= last_seg_end_bi.get_end_val():
            if peak_bi := FindPeakBi(bi_lst[last_seg_end_bi.idx+3:], is_high=False):
                self.add_new_seg(bi_lst, peak_bi.idx, is_sure=False, seg_dir=BI_DIR.DOWN, reason="collectleft_find_low_force")
                self.collect_left_seg(bi_lst)
        # 剩下线段的尾部相比于最后一个线段的尾部，高低关系和最后一个虚线段的方向一致
        elif self.config.left_method == LEFT_SEG_METHOD.ALL:  # 容易找不到二类买卖点！！
            self.collect_left_as_seg(bi_lst)
        elif self.config.left_method == LEFT_SEG_METHOD.PEAK:
            self.collect_left_seg_peak_method(last_seg_end_bi, bi_lst)
        else:
            raise CChanException(f"unknown seg left_method = {self.config.left_method}", ErrCode.PARA_ERROR)

    def collect_left_seg(self, bi_lst: CBiList):
        if len(self) == 0:
            self.collect_first_seg(bi_lst)
        else:
            self.collect_segs(bi_lst)

    def collect_left_as_seg(self, bi_lst: CBiList):
        last_bi = bi_lst[-1]
        last_seg_end_bi = self[-1].end_bi
        if last_seg_end_bi.idx+1 >= len(bi_lst):
            return
        if last_seg_end_bi.dir == last_bi.dir:
            self.add_new_seg(bi_lst, last_bi.idx-1, is_sure=False, reason="collect_left_1")
        else:
            self.add_new_seg(bi_lst, last_bi.idx, is_sure=False, reason="collect_left_0")

    def try_add_new_seg(self, bi_lst, end_bi_idx: int, is_sure=True, seg_dir=None, split_first_seg=True, reason="normal"):
        if len(self) == 0 and split_first_seg and end_bi_idx >= 3:
            if peak_bi := FindPeakBi(bi_lst[end_bi_idx-3::-1], bi_lst[end_bi_idx].is_down()):
                if (peak_bi.is_down() and (peak_bi._low() < bi_lst[0]._low() or peak_bi.idx == 0)) or \
                   (peak_bi.is_up() and (peak_bi._high() > bi_lst[0]._high() or peak_bi.idx == 0)):  # 要比第一笔开头还高/低（因为没有比较到）
                    self.add_new_seg(bi_lst, peak_bi.idx, is_sure=False, seg_dir=peak_bi.dir, reason="split_first_1st")
                    self.add_new_seg(bi_lst, end_bi_idx, is_sure=False, reason="split_first_2nd")
                    return
        bi1_idx = 0 if len(self) == 0 else self[-1].end_bi.idx+1
        bi1 = bi_lst[bi1_idx]
        bi2 = bi_lst[end_bi_idx]
        self.lst.append(CSeg(len(self.lst), bi1, bi2, is_sure=is_sure, seg_dir=seg_dir, reason=reason))

        if len(self.lst) >= 2:
            self.lst[-2].next = self.lst[-1]
            self.lst[-1].pre = self.lst[-2]
        self.lst[-1].update_bi_list(bi_lst, bi1_idx, end_bi_idx)

    def add_new_seg(self, bi_lst: CBiList, end_bi_idx: int, is_sure=True, seg_dir=None, split_first_seg=True, reason="normal"):
        try:
            self.try_add_new_seg(bi_lst, end_bi_idx, is_sure, seg_dir, split_first_seg, reason)
        except CChanException as e:
            if e.errcode == ErrCode.SEG_END_VALUE_ERR and len(self.lst) == 0:
                return False
            raise e
        except Exception as e:
            raise e
        return True

    @abc.abstractmethod
    def update(self, bi_lst: CBiList):
        ...

    def exist_sure_seg(self):
        return any(seg.is_sure for seg in self.lst)


def FindPeakBi(bi_lst: Union[CBiList, List[CBi]], is_high):
    peak_val = float("-inf") if is_high else float("inf")
    peak_bi = None
    for bi in bi_lst:
        if (is_high and bi.get_end_val() >= peak_val and bi.is_up()) or (not is_high and bi.get_end_val() <= peak_val and bi.is_down()):
            if bi.pre and bi.pre.pre and ((is_high and bi.pre.pre.get_end_val() > bi.get_end_val()) or (not is_high and bi.pre.pre.get_end_val() < bi.get_end_val())):
                continue
            peak_val = bi.get_end_val()
            peak_bi = bi
    return peak_bi


# ==================== Seg/SegListChan.py ====================




class CSegListChan(CSegListComm):
    def __init__(self, seg_config=CSegConfig(), lv=SEG_TYPE.BI):
        super(CSegListChan, self).__init__(seg_config=seg_config, lv=lv)

    def do_init(self):
        # 删除末尾不确定的线段
        while len(self) and not self.lst[-1].is_sure:
            _seg = self[-1]
            for bi in _seg.bi_list:
                bi.parent_seg = None
            if _seg.pre:
                _seg.pre.next = None
            self.lst.pop()
        if len(self):
            assert self.lst[-1].eigen_fx and self.lst[-1].eigen_fx.ele[-1]
            if not self.lst[-1].eigen_fx.ele[-1].lst[-1].is_sure:
                # 如果确定线段的分形的第三元素包含不确定笔，也需要重新算，不然线段分形元素的高低点可能不对
                self.lst.pop()

    def update(self, bi_lst: CBiList):
        self.do_init()
        if len(self) == 0:
            self.cal_seg_sure(bi_lst, begin_idx=0)
        else:
            self.cal_seg_sure(bi_lst, begin_idx=self[-1].end_bi.idx+1)
        self.collect_left_seg(bi_lst)

    def cal_seg_sure(self, bi_lst: CBiList, begin_idx: int):
        up_eigen = CEigenFX(BI_DIR.UP, lv=self.lv)  # 上升线段下降笔
        down_eigen = CEigenFX(BI_DIR.DOWN, lv=self.lv)  # 下降线段上升笔
        last_seg_dir = None if len(self) == 0 else self[-1].dir
        for bi in bi_lst[begin_idx:]:
            fx_eigen = None
            if bi.is_down() and last_seg_dir != BI_DIR.UP:
                if up_eigen.add(bi):
                    fx_eigen = up_eigen
            elif bi.is_up() and last_seg_dir != BI_DIR.DOWN:
                if down_eigen.add(bi):
                    fx_eigen = down_eigen
            if len(self) == 0:  # 尝试确定第一段方向，不要以谁先成为分形来决定，反例：US.EVRG
                if up_eigen.ele[1] is not None and bi.is_down():
                    last_seg_dir = BI_DIR.DOWN
                    down_eigen.clear()
                elif down_eigen.ele[1] is not None and bi.is_up():
                    up_eigen.clear()
                    last_seg_dir = BI_DIR.UP
                if up_eigen.ele[1] is None and last_seg_dir == BI_DIR.DOWN and bi.dir == BI_DIR.DOWN:
                    last_seg_dir = None
                elif down_eigen.ele[1] is None and last_seg_dir == BI_DIR.UP and bi.dir == BI_DIR.UP:
                    last_seg_dir = None

            if fx_eigen:
                self.treat_fx_eigen(fx_eigen, bi_lst)
                break

    def treat_fx_eigen(self, fx_eigen, bi_lst: CBiList):
        _test = fx_eigen.can_be_end(bi_lst)
        end_bi_idx = fx_eigen.GetPeakBiIdx()
        if _test in [True, None]:  # None表示反向分型找到尾部也没找到
            is_true = _test is not None  # 如果是正常结束
            if not self.add_new_seg(bi_lst, end_bi_idx, is_sure=is_true and fx_eigen.all_bi_is_sure()):  # 防止第一根线段的方向与首尾值异常
                self.cal_seg_sure(bi_lst, end_bi_idx+1)
                return
            self.lst[-1].eigen_fx = fx_eigen
            if is_true:
                self.cal_seg_sure(bi_lst, end_bi_idx + 1)
        else:
            self.cal_seg_sure(bi_lst, fx_eigen.lst[1].idx)


# ==================== Seg/SegListDYH.py ====================




def situation1(cur_bi, next_bi, pre_bi):
    if cur_bi.is_down() and cur_bi._low() > pre_bi._low():
        if next_bi._high() < cur_bi._high() and next_bi._low() < cur_bi._low():
            return True
    elif cur_bi.is_up() and cur_bi._high() < pre_bi._high():
        if next_bi._low() > cur_bi._low() and next_bi._high() > cur_bi._high():
            return True
    return False


def situation2(cur_bi, next_bi, pre_bi):
    if cur_bi.is_down() and cur_bi._low() < pre_bi._low():
        if next_bi._high() < cur_bi._high() and next_bi._low() < pre_bi._low():
            return True
    elif cur_bi.is_up() and cur_bi._high() > pre_bi._high():
        if next_bi._low() > cur_bi._low() and next_bi._high() > pre_bi._high():
            return True
    return False


class CSegListDYH(CSegListComm):
    def __init__(self, seg_config=CSegConfig(), lv=SEG_TYPE.BI):
        super(CSegListDYH, self).__init__(seg_config=seg_config, lv=lv)
        self.sure_seg_update_end = False

    def update(self, bi_lst: CBiList):
        self.do_init()
        self.cal_bi_sure(bi_lst)
        self.try_update_last_seg(bi_lst)
        if self.left_bi_break(bi_lst):
            self.cal_bi_unsure(bi_lst)
        self.collect_left_seg(bi_lst)

    def cal_bi_sure(self, bi_lst):
        BI_LEN = len(bi_lst)
        next_begin_bi = bi_lst[0]
        for idx, bi in enumerate(bi_lst):
            if idx + 2 >= BI_LEN or idx < 2:
                continue
            if len(self) > 0 and bi.dir != self[-1].end_bi.dir:
                continue
            if bi.is_down() and bi_lst[idx-1]._high() < next_begin_bi._low():
                continue
            if bi.is_up() and bi_lst[idx-1]._low() > next_begin_bi._high():
                continue
            if self.sure_seg_update_end and len(self) and ((bi.is_down() and bi._low() < self[-1].end_bi._low()) or (bi.is_up() and bi._high() > self[-1].end_bi._high())):
                self[-1].end_bi = bi
                if idx != BI_LEN-1:
                    next_begin_bi = bi_lst[idx+1]
                    continue
            if (len(self) == 0 or bi.idx - self[-1].end_bi.idx >= 4) and (situation1(bi, bi_lst[idx + 2], bi_lst[idx - 2]) or situation2(bi, bi_lst[idx + 2], bi_lst[idx - 2])):
                self.add_new_seg(bi_lst, idx-1)
                next_begin_bi = bi

    def cal_bi_unsure(self, bi_lst: CBiList):
        if len(self) == 0:
            return
        last_seg_dir = self[-1].end_bi.dir
        end_bi = None
        peak_value = float("inf") if last_seg_dir == BI_DIR.UP else float("-inf")
        for bi in bi_lst[self[-1].end_bi.idx+3:]:
            if bi.dir == last_seg_dir:
                continue
            cur_value = bi._low() if last_seg_dir == BI_DIR.UP else bi._high()
            if (last_seg_dir == BI_DIR.UP and cur_value < peak_value) or \
               (last_seg_dir == BI_DIR.DOWN and cur_value > peak_value):
                end_bi = bi
                peak_value = cur_value
        if end_bi:
            self.add_new_seg(bi_lst, end_bi.idx, is_sure=False)

    def try_update_last_seg(self, bi_lst: CBiList):
        if len(self) == 0:
            return
        last_bi = self[-1].end_bi
        peak_value = last_bi.get_end_val()
        new_peak_bi = None
        for bi in bi_lst[self[-1].end_bi.idx+1:]:
            if bi.dir != last_bi.dir:
                continue
            if bi.is_down() and bi._low() < peak_value:
                peak_value = bi._low()
                new_peak_bi = bi
            elif bi.is_up() and bi._high() > peak_value:
                peak_value = bi._high()
                new_peak_bi = bi
        if new_peak_bi:
            self[-1].end_bi = new_peak_bi
            self[-1].is_sure = False


# ==================== Seg/SegListDef.py ====================




def is_up_seg(bi, pre_bi):
    return bi._high() > pre_bi._high()


def is_down_seg(bi, pre_bi):
    return bi._low() < pre_bi._low()


class CSegListDef(CSegListComm):
    def __init__(self, seg_config=CSegConfig(), lv=SEG_TYPE.BI):
        super(CSegListDef, self).__init__(seg_config=seg_config, lv=lv)
        self.sure_seg_update_end = False

    def update(self, bi_lst: CBiList):
        self.do_init()
        self.cal_bi_sure(bi_lst)
        self.collect_left_seg(bi_lst)

    def update_last_end(self, bi_lst, new_endbi_idx: int):
        last_endbi_idx = self[-1].end_bi.idx
        assert new_endbi_idx >= last_endbi_idx + 2
        self[-1].end_bi = bi_lst[new_endbi_idx]
        self.lst[-1].update_bi_list(bi_lst, last_endbi_idx, new_endbi_idx)

    def cal_bi_sure(self, bi_lst):
        peak_bi = None
        if len(bi_lst) == 0:
            return
        for idx, bi in enumerate(bi_lst):
            if idx < 2:
                continue
            if peak_bi and ((bi.is_up() and peak_bi.is_up() and bi._high() >= peak_bi._high()) or (bi.is_down() and peak_bi.is_down() and bi._low() <= peak_bi._low())):
                peak_bi = bi
                continue
            if self.sure_seg_update_end and len(self) and bi.dir == self[-1].dir and ((bi.is_up() and bi._high() >= self[-1].end_bi._high()) or (bi.is_down() and bi._low() <= self[-1].end_bi._low())):
                self.update_last_end(bi_lst, bi.idx)
                peak_bi = None
                continue
            pre_bi = bi_lst[idx-2]
            if (bi.is_up() and is_up_seg(bi, pre_bi)) or \
               (bi.is_down() and is_down_seg(bi, pre_bi)):
                if peak_bi is None:
                    if len(self) == 0 or bi.dir != self[-1].dir:
                        peak_bi = bi
                        continue
                elif peak_bi.dir != bi.dir:
                    if bi.idx - peak_bi.idx <= 2:
                        continue
                    self.add_new_seg(bi_lst, peak_bi.idx)
                    peak_bi = bi
                    continue
        if peak_bi is not None:
            self.add_new_seg(bi_lst, peak_bi.idx, is_sure=False)


# ==================== ZS/ZSConfig.py ====================

class CZSConfig:
    def __init__(self, need_combine=True, zs_combine_mode="zs", one_bi_zs=False, zs_algo="normal"):
        self.need_combine = need_combine
        self.zs_combine_mode = zs_combine_mode
        self.one_bi_zs = one_bi_zs
        self.zs_algo = zs_algo


# ==================== ZS/ZS.py ====================

from typing import Generic, List, Optional, TypeVar


LINE_TYPE = TypeVar('LINE_TYPE', CBi, "CSeg")


class CZS(Generic[LINE_TYPE]):
    def __init__(self, lst: Optional[List[LINE_TYPE]], is_sure=True):
        # begin/end：永远指向 klu
        # low/high: 中枢的范围
        # peak_low/peak_high: 中枢所涉及到的笔的最大值，最小值
        self.__is_sure = is_sure
        self.__sub_zs_lst: List[CZS] = []

        if lst is None:
            return

        self.__begin: CKLine_Unit = lst[0].get_begin_klu()
        self.__begin_bi: LINE_TYPE = lst[0]  # 中枢内部的笔

        # self.__low = None
        # self.__high = None
        # self.__mid = None
        self.update_zs_range(lst)

        # self.__end: CKLine_Unit = None
        # self.__end_bi: CBi = None  # 中枢内部的笔
        self.__peak_high = float("-inf")
        self.__peak_low = float("inf")
        for item in lst:
            self.update_zs_end(item)

        self.__bi_in: Optional[LINE_TYPE] = None  # 进中枢那一笔
        self.__bi_out: Optional[LINE_TYPE] = None  # 出中枢那一笔

        self.__bi_lst: List[LINE_TYPE] = []  # begin_bi~end_bi之间的笔，在update_zs_in_seg函数中更新

    def clean_cache(self):
        self._memoize_cache = {}

    @property
    def is_sure(self): return self.__is_sure

    @property
    def sub_zs_lst(self): return self.__sub_zs_lst

    @property
    def begin(self): return self.__begin

    @property
    def begin_bi(self): return self.__begin_bi

    @property
    def low(self): return self.__low

    @property
    def high(self): return self.__high

    @property
    def mid(self): return self.__mid

    @property
    def end(self): return self.__end

    @property
    def end_bi(self): return self.__end_bi

    @property
    def peak_high(self): return self.__peak_high

    @property
    def peak_low(self): return self.__peak_low

    @property
    def bi_in(self): return self.__bi_in

    @property
    def bi_out(self): return self.__bi_out

    @property
    def bi_lst(self): return self.__bi_lst

    def update_zs_range(self, lst):
        self.__low: float = max(bi._low() for bi in lst)
        self.__high: float = min(bi._high() for bi in lst)
        self.__mid: float = (self.__low + self.__high) / 2  # 中枢的中点
        self.clean_cache()

    def is_one_bi_zs(self):
        assert self.end_bi is not None
        return self.begin_bi.idx == self.end_bi.idx

    def update_zs_end(self, item):
        self.__end: CKLine_Unit = item.get_end_klu()
        self.__end_bi: CBi = item
        if item._low() < self.peak_low:
            self.__peak_low = item._low()
        if item._high() > self.peak_high:
            self.__peak_high = item._high()
        self.clean_cache()

    def __str__(self):
        _str = f"{self.begin_bi.idx}->{self.end_bi.idx}"
        if _str2 := ",".join([str(sub_zs) for sub_zs in self.sub_zs_lst]):
            return f"{_str}({_str2})"
        else:
            return _str

    def combine(self, zs2: 'CZS', combine_mode) -> bool:
        if zs2.is_one_bi_zs():
            return False
        if self.begin_bi.seg_idx != zs2.begin_bi.seg_idx:
            return False
        if combine_mode == 'zs':
            if not has_overlap(self.low, self.high, zs2.low, zs2.high, equal=True):
                return False
            self.do_combine(zs2)
            return True
        elif combine_mode == 'peak':
            if has_overlap(self.peak_low, self.peak_high, zs2.peak_low, zs2.peak_high):
                self.do_combine(zs2)
                return True
            else:
                return False
        else:
            raise CChanException(f"{combine_mode} is unsupport zs conbine mode", ErrCode.PARA_ERROR)

    def do_combine(self, zs2: 'CZS'):
        if len(self.sub_zs_lst) == 0:
            self.__sub_zs_lst.append(self.make_copy())
        self.__sub_zs_lst.append(zs2)

        self.__low = min([self.low, zs2.low])
        self.__high = max([self.high, zs2.high])
        self.__peak_low = min([self.peak_low, zs2.peak_low])
        self.__peak_high = max([self.peak_high, zs2.peak_high])
        self.__end = zs2.end
        self.__bi_out = zs2.bi_out
        self.__end_bi = zs2.end_bi
        self.clean_cache()

    def try_add_to_end(self, item):
        if not self.in_range(item):
            return False
        if self.is_one_bi_zs():
            self.update_zs_range([self.begin_bi, item])
        self.update_zs_end(item)
        return True

    def in_range(self, item):
        return has_overlap(self.low, self.high, item._low(), item._high())

    def is_inside(self, seg: CSeg):
        return seg.start_bi.idx <= self.begin_bi.idx <= seg.end_bi.idx

    def is_divergence(self, config: CPointConfig, out_bi=None):
        if not self.end_bi_break(out_bi):  # 最后一笔必须突破中枢
            return False, None
        in_metric = self.get_bi_in().cal_macd_metric(config.macd_algo, is_reverse=False)
        if out_bi is None:
            out_metric = self.get_bi_out().cal_macd_metric(config.macd_algo, is_reverse=True)
        else:
            out_metric = out_bi.cal_macd_metric(config.macd_algo, is_reverse=True)

        if config.divergence_rate > 100:  # 保送
            return True, out_metric/in_metric
        else:
            return out_metric <= config.divergence_rate*in_metric, out_metric/in_metric

    def init_from_zs(self, zs: 'CZS'):
        self.__begin = zs.begin
        self.__end = zs.end
        self.__low = zs.low
        self.__high = zs.high
        self.__peak_high = zs.peak_high
        self.__peak_low = zs.peak_low
        self.__begin_bi = zs.begin_bi
        self.__end_bi = zs.end_bi
        self.__bi_in = zs.bi_in
        self.__bi_out = zs.bi_out

    def make_copy(self) -> 'CZS':
        copy = CZS(lst=None, is_sure=self.is_sure)
        copy.init_from_zs(zs=self)
        return copy

    def end_bi_break(self, end_bi=None) -> bool:
        if end_bi is None:
            end_bi = self.get_bi_out()
        assert end_bi is not None
        return (end_bi.is_down() and end_bi._low() < self.low) or \
            (end_bi.is_up() and end_bi._high() > self.high)

    def out_bi_is_peak(self, end_bi_idx: int):
        # 返回 (是否最低点，bi_out与中枢里面尾部最接近它的差距比例)
        assert len(self.bi_lst) > 0
        if self.bi_out is None:
            return False, None
        peak_rate = float("inf")
        for bi in self.bi_lst:
            if bi.idx > end_bi_idx:
                break
            if (self.bi_out.is_down() and bi._low() < self.bi_out._low()) or (self.bi_out.is_up() and bi._high() > self.bi_out._high()):
                return False, None
            r = abs(bi.get_end_val()-self.bi_out.get_end_val())/self.bi_out.get_end_val()
            if r < peak_rate:
                peak_rate = r
        return True, peak_rate

    def get_bi_in(self) -> LINE_TYPE:
        assert self.bi_in is not None
        return self.bi_in

    def get_bi_out(self) -> LINE_TYPE:
        assert self.__bi_out is not None
        return self.__bi_out

    def set_bi_in(self, bi):
        self.__bi_in = bi
        self.clean_cache()

    def set_bi_out(self, bi):
        self.__bi_out = bi
        self.clean_cache()

    def set_bi_lst(self, bi_lst):
        self.__bi_lst = bi_lst
        self.clean_cache()


# ==================== ZS/ZSList.py ====================

from typing import List, Union, overload




class CZSList:
    def __init__(self, zs_config=CZSConfig()):
        self.zs_lst: List[CZS] = []

        self.config = zs_config
        self.free_item_lst = []

        self.last_sure_pos = -1
        self.last_seg_idx = 0

    def update_last_pos(self, seg_list: CSegListComm):
        self.last_sure_pos = -1
        self.last_seg_idx = 0
        _seg_idx = len(seg_list) - 1
        while _seg_idx >= 0:
            seg = seg_list[_seg_idx]
            if seg.is_sure:
                self.last_sure_pos = seg.start_bi.idx
                self.last_seg_idx = seg.idx
                return
            _seg_idx -= 1

    def seg_need_cal(self, seg: CSeg):
        return seg.start_bi.idx >= self.last_sure_pos

    def add_to_free_lst(self, item, is_sure, zs_algo):
        if len(self.free_item_lst) != 0 and item.idx == self.free_item_lst[-1].idx:
            # 防止笔新高或新低的更新带来bug
            self.free_item_lst = self.free_item_lst[:-1]
        self.free_item_lst.append(item)
        res = self.try_construct_zs(self.free_item_lst, is_sure, zs_algo)  # 可能是一笔中枢
        if res is not None and res.begin_bi.idx > 0:  # 禁止第一笔就是中枢的起点
            self.zs_lst.append(res)
            self.clear_free_lst()
            self.try_combine()

    def clear_free_lst(self):
        self.free_item_lst = []

    def update(self, bi: CBi, is_sure=True):
        if len(self.free_item_lst) == 0 and self.try_add_to_end(bi):
            # zs_combine_mode=peak合并模式下会触发生效，=zs合并一定无效返回
            self.try_combine()  # 新形成的中枢尝试和之前的中枢合并
            return
        self.add_to_free_lst(bi, is_sure, "normal")

    def try_add_to_end(self, bi):
        return False if len(self.zs_lst) == 0 else self[-1].try_add_to_end(bi)

    def add_zs_from_bi_range(self, seg_bi_lst: list, seg_dir, seg_is_sure):
        deal_bi_cnt = 0
        for bi in seg_bi_lst:
            if bi.dir == seg_dir:
                continue
            if deal_bi_cnt < 1:  # 防止try_add_to_end执行到上一个线段的中枢里面去
                self.add_to_free_lst(bi, seg_is_sure, "normal")
                deal_bi_cnt += 1
            else:
                self.update(bi, seg_is_sure)

    def try_construct_zs(self, lst, is_sure, zs_algo):
        if zs_algo == "normal":
            if not self.config.one_bi_zs:
                if len(lst) == 1:
                    return None
                else:
                    lst = lst[-2:]
        elif zs_algo == "over_seg":
            if len(lst) < 3:
                return None
            lst = lst[-3:]
            if lst[0].dir == lst[0].parent_seg.dir:
                lst = lst[1:]
                return None
        min_high = min(item._high() for item in lst)
        max_low = max(item._low() for item in lst)
        return CZS(lst, is_sure=is_sure) if min_high > max_low else None

    def cal_bi_zs(self, bi_lst: Union[CBiList, CSegListComm], seg_lst: CSegListComm):
        while self.zs_lst and self.zs_lst[-1].begin_bi.idx >= self.last_sure_pos:
            self.zs_lst.pop()
        if self.config.zs_algo == "normal":
            for seg in seg_lst[self.last_seg_idx:]:
                if not self.seg_need_cal(seg):
                    continue
                self.clear_free_lst()
                seg_bi_lst = bi_lst[seg.start_bi.idx:seg.end_bi.idx+1]
                self.add_zs_from_bi_range(seg_bi_lst, seg.dir, seg.is_sure)

            # 处理未生成新线段的部分
            if len(seg_lst):
                self.clear_free_lst()
                self.add_zs_from_bi_range(bi_lst[seg_lst[-1].end_bi.idx+1:], revert_bi_dir(seg_lst[-1].dir), False)
        elif self.config.zs_algo == "over_seg":
            assert self.config.one_bi_zs is False
            self.clear_free_lst()
            begin_bi_idx = self.zs_lst[-1].end_bi.idx+1 if self.zs_lst else 0
            for bi in bi_lst[begin_bi_idx:]:
                self.update_overseg_zs(bi)
        elif self.config.zs_algo == "auto":
            sure_seg_appear = False
            exist_sure_seg = seg_lst.exist_sure_seg()
            for seg in seg_lst[self.last_seg_idx:]:
                if seg.is_sure:
                    sure_seg_appear = True
                if not self.seg_need_cal(seg):
                    continue
                if seg.is_sure or (not sure_seg_appear and exist_sure_seg):
                    self.clear_free_lst()
                    self.add_zs_from_bi_range(bi_lst[seg.start_bi.idx:seg.end_bi.idx+1], seg.dir, seg.is_sure)
                else:
                    self.clear_free_lst()
                    for bi in bi_lst[seg.start_bi.idx:]:
                        self.update_overseg_zs(bi)
                    break
        else:
            raise Exception(f"unknown zs_algo {self.config.zs_algo}")
        self.update_last_pos(seg_lst)

    def update_overseg_zs(self, bi: CBi | CSeg):
        if len(self.zs_lst) and len(self.free_item_lst) == 0:
            if bi.next is None:
                return
            if bi.idx - self.zs_lst[-1].end_bi.idx <= 1 and self.zs_lst[-1].in_range(bi.next) and self.zs_lst[-1].try_add_to_end(bi):
                return
        if len(self.zs_lst) and len(self.free_item_lst) == 0 and self.zs_lst[-1].in_range(bi) and bi.idx - self.zs_lst[-1].end_bi.idx <= 1:
            return
        self.add_to_free_lst(bi, bi.is_sure, zs_algo="over_seg")

    def __iter__(self):
        yield from self.zs_lst

    def __len__(self):
        return len(self.zs_lst)

    @overload
    def __getitem__(self, index: int) -> CZS: ...

    @overload
    def __getitem__(self, index: slice) -> List[CZS]: ...

    def __getitem__(self, index: Union[slice, int]) -> Union[List[CZS], CZS]:
        return self.zs_lst[index]

    def try_combine(self):
        if not self.config.need_combine:
            return
        while len(self.zs_lst) >= 2 and self.zs_lst[-2].combine(self.zs_lst[-1], combine_mode=self.config.zs_combine_mode):
            self.zs_lst = self.zs_lst[:-1]  # 合并后删除最后一个


# ==================== BuySellPoint/BSPointConfig.py ====================

from typing import Dict, List, Optional



class CBSPointConfig:
    def __init__(self, **args):
        self.b_conf = CPointConfig(**args)
        self.s_conf = CPointConfig(**args)

    def GetBSConfig(self, is_buy):
        return self.b_conf if is_buy else self.s_conf


class CPointConfig:
    def __init__(self,
                 divergence_rate,
                 min_zs_cnt,
                 bsp1_only_multibi_zs,
                 max_bs2_rate,
                 macd_algo,
                 bs1_peak,
                 bs_type,
                 bsp2_follow_1,
                 bsp3_follow_1,
                 bsp3_peak,
                 bsp2s_follow_2,
                 max_bsp2s_lv,
                 strict_bsp3,
                 bsp3a_max_zs_cnt,
                 ):
        self.divergence_rate = divergence_rate
        self.min_zs_cnt = min_zs_cnt
        self.bsp1_only_multibi_zs = bsp1_only_multibi_zs
        self.max_bs2_rate = max_bs2_rate
        assert self.max_bs2_rate <= 1
        self.SetMacdAlgo(macd_algo)
        self.bs1_peak = bs1_peak
        self.tmp_target_types = bs_type
        self.target_types: List[BSP_TYPE] = []
        self.bsp2_follow_1 = bsp2_follow_1
        self.bsp3_follow_1 = bsp3_follow_1
        self.bsp3_peak = bsp3_peak
        self.bsp2s_follow_2 = bsp2s_follow_2
        self.max_bsp2s_lv: Optional[int] = max_bsp2s_lv
        self.strict_bsp3 = strict_bsp3
        self.bsp3a_max_zs_cnt = bsp3a_max_zs_cnt
        assert self.bsp3a_max_zs_cnt >= 1

    def parse_target_type(self):
        _d: Dict[str, BSP_TYPE] = {x.value: x for x in BSP_TYPE}
        if isinstance(self.tmp_target_types, str):
            self.tmp_target_types = [t.strip() for t in self.tmp_target_types.split(",")]
        for target_t in self.tmp_target_types:
            assert target_t in ['1', '2', '3a', '2s', '1p', '3b']
        self.target_types = [_d[_type] for _type in self.tmp_target_types]

    def SetMacdAlgo(self, macd_algo):
        _d = {
            "area": MACD_ALGO.AREA,
            "peak": MACD_ALGO.PEAK,
            "full_area": MACD_ALGO.FULL_AREA,
            "diff": MACD_ALGO.DIFF,
            "slope": MACD_ALGO.SLOPE,
            "amp": MACD_ALGO.AMP,
            "amount": MACD_ALGO.AMOUNT,
            "volumn": MACD_ALGO.VOLUMN,
            "amount_avg": MACD_ALGO.AMOUNT_AVG,
            "volumn_avg": MACD_ALGO.VOLUMN_AVG,
            "turnrate_avg": MACD_ALGO.AMOUNT_AVG,
            "rsi": MACD_ALGO.RSI,
        }
        self.macd_algo = _d[macd_algo]

    def set(self, k, v):
        v = _parse_inf(v)
        if k == "macd_algo":
            self.SetMacdAlgo(v)
        else:
            exec(f"self.{k} = {v}")


# ==================== BuySellPoint/BS_Point.py ====================

from typing import Dict, Generic, List, Optional, TypeVar, Union


LINE_TYPE = TypeVar('LINE_TYPE', CBi, CSeg)


class CBS_Point(Generic[LINE_TYPE]):
    def __init__(self, bi: LINE_TYPE, is_buy, bs_type: BSP_TYPE, relate_bsp1: Optional['CBS_Point'], feature_dict=None):
        self.bi: LINE_TYPE = bi
        self.klu = bi.get_end_klu()
        self.is_buy = is_buy
        self.type: List[BSP_TYPE] = [bs_type]
        self.relate_bsp1 = relate_bsp1

        self.bi.bsp = self  # type: ignore
        self.features = CFeatures(feature_dict)

        self.is_segbsp = False

    def add_type(self, bs_type: BSP_TYPE):
        self.type.append(bs_type)

    def type2str(self):
        return ",".join([x.value for x in self.type])

    def add_another_bsp_prop(self, bs_type: BSP_TYPE, relate_bsp1):
        self.add_type(bs_type)
        if self.relate_bsp1 is None:
            self.relate_bsp1 = relate_bsp1
        elif relate_bsp1 is not None:
            assert self.relate_bsp1.klu.idx == relate_bsp1.klu.idx

    def add_feat(self, inp1: Union[str, Dict[str, float], Dict[str, Optional[float]], 'CFeatures'], inp2: Optional[float] = None):
        self.features.add_feat(inp1, inp2)


# ==================== BuySellPoint/BSPointList.py ====================

from typing import Dict, Generic, Iterable, List, Optional, Tuple, TypeVar



LINE_TYPE = TypeVar('LINE_TYPE', CBi, CSeg[CBi])
LINE_LIST_TYPE = TypeVar('LINE_LIST_TYPE', CBiList, CSegListComm[CBi])


class CBSPointList(Generic[LINE_TYPE, LINE_LIST_TYPE]):
    def __init__(self, bs_point_config: CBSPointConfig):
        self.bsp_store_dict: Dict[BSP_TYPE, Tuple[List[CBS_Point[LINE_TYPE]], List[CBS_Point[LINE_TYPE]]]] = {}
        self.bsp_store_flat_dict: Dict[int, CBS_Point[LINE_TYPE]] = {}

        self.bsp1_list: List[CBS_Point[LINE_TYPE]] = []
        self.bsp1_dict: Dict[int, CBS_Point[LINE_TYPE]] = {}

        self.config = bs_point_config
        self.last_sure_pos = -1
        self.last_sure_seg_idx = 0

    def store_add_bsp(self, bsp_type: BSP_TYPE, bsp: CBS_Point[LINE_TYPE]):
        if bsp_type not in self.bsp_store_dict:
            self.bsp_store_dict[bsp_type] = ([], [])
        if len(self.bsp_store_dict[bsp_type][bsp.is_buy]) > 0:
            assert self.bsp_store_dict[bsp_type][bsp.is_buy][-1].bi.idx < bsp.bi.idx, f"{bsp_type}, {bsp.is_buy} {self.bsp_store_dict[bsp_type][bsp.is_buy][-1].bi.idx} {bsp.bi.idx}"
        self.bsp_store_dict[bsp_type][bsp.is_buy].append(bsp)
        self.bsp_store_flat_dict[bsp.bi.idx] = bsp

    def add_bsp1(self, bsp: CBS_Point[LINE_TYPE]):
        if len(self.bsp1_list) > 0:
            assert self.bsp1_list[-1].bi.idx < bsp.bi.idx
        self.bsp1_list.append(bsp)
        self.bsp1_dict[bsp.bi.idx] = bsp

    def clear_store_end(self):
        for bsp_list in self.bsp_store_dict.values():
            for is_buy in [True, False]:
                while len(bsp_list[is_buy]) > 0:
                    if bsp_list[is_buy][-1].bi.get_end_klu().idx <= self.last_sure_pos:
                        break
                    del self.bsp_store_flat_dict[bsp_list[is_buy][-1].bi.idx]
                    # 同时把失效买卖点从Bi删除
                    bsp_list[is_buy][-1].bi.bsp = None
                    bsp_list[is_buy].pop()

    def clear_bsp1_end(self):
        while len(self.bsp1_list) > 0:
            if self.bsp1_list[-1].bi.get_end_klu().idx <= self.last_sure_pos:
                break
            del self.bsp1_dict[self.bsp1_list[-1].bi.idx]
            self.bsp1_list.pop()

    def bsp_iter(self) -> Iterable[CBS_Point[LINE_TYPE]]:
        for bsp_list in self.bsp_store_dict.values():
            yield from bsp_list[True]
            yield from bsp_list[False]

    def bsp_iter_v2(self) -> Iterable[CBS_Point[LINE_TYPE]]:
        list_indices = []
        for bsp_type, bsp_list in self.bsp_store_dict.items():
            if bsp_list[True]:
                list_indices.append([bsp_type, True, len(bsp_list[True]) - 1])
            if bsp_list[False]:
                list_indices.append([bsp_type, False, len(bsp_list[False]) - 1])

        while list_indices:
            max_idx = -1
            max_bi_idx = -1
            max_bsp = None

            for i, (bsp_type, is_buy, idx) in enumerate(list_indices):
                if idx >= 0:
                    bsp = self.bsp_store_dict[bsp_type][is_buy][idx]
                    if bsp.bi.idx > max_bi_idx:
                        max_bi_idx = bsp.bi.idx
                        max_idx = i
                        max_bsp = bsp

            if max_bsp is None:
                break

            yield max_bsp

            list_indices[max_idx][2] -= 1
            if list_indices[max_idx][2] < 0:
                list_indices.pop(max_idx)

    def __len__(self):
        return len(self.bsp_store_flat_dict)

    def cal(self, bi_list: LINE_LIST_TYPE, seg_list: CSegListComm[LINE_TYPE]):
        self.clear_store_end()
        self.clear_bsp1_end()
        self.cal_seg_bs1point(seg_list, bi_list)
        self.cal_seg_bs2point(seg_list, bi_list)
        self.cal_seg_bs3point(seg_list, bi_list)

        self.update_last_pos(seg_list)

    def update_last_pos(self, seg_list: CSegListComm):
        self.last_sure_pos = -1
        self.last_sure_seg_idx = 0
        seg_idx = len(seg_list)-1
        while seg_idx >= 0:
            seg = seg_list[seg_idx]
            if seg.is_sure:
                self.last_sure_pos = seg.end_bi.get_begin_klu().idx
                self.last_sure_seg_idx = seg.idx
                return
            seg_idx -= 1

    def seg_need_cal(self, seg: CSeg):
        return seg.end_bi.get_end_klu().idx > self.last_sure_pos

    def add_bs(
        self,
        bs_type: BSP_TYPE,
        bi: LINE_TYPE,
        relate_bsp1: Optional[CBS_Point],
        is_target_bsp: bool = True,
        feature_dict=None,
    ):
        is_buy = bi.is_down()
        if exist_bsp := self.bsp_store_flat_dict.get(bi.idx):
            assert exist_bsp.is_buy == is_buy
            exist_bsp.add_another_bsp_prop(bs_type, relate_bsp1)
            return
        if bs_type not in self.config.GetBSConfig(is_buy).target_types:
            is_target_bsp = False

        if is_target_bsp or bs_type in [BSP_TYPE.T1, BSP_TYPE.T1P]:
            bsp = CBS_Point[LINE_TYPE](
                bi=bi,
                is_buy=is_buy,
                bs_type=bs_type,
                relate_bsp1=relate_bsp1,
                feature_dict=feature_dict,
            )
        else:
            return
        if is_target_bsp:
            self.store_add_bsp(bs_type, bsp)
        else:
            bsp.bi.bsp = None
        if bs_type in [BSP_TYPE.T1, BSP_TYPE.T1P]:
            self.add_bsp1(bsp)

    def cal_seg_bs1point(self, seg_list: CSegListComm[LINE_TYPE], bi_list: LINE_LIST_TYPE):
        for seg in seg_list[self.last_sure_seg_idx:]:
            if not self.seg_need_cal(seg):
                continue
            self.cal_single_bs1point(seg, bi_list)

    def cal_single_bs1point(self, seg: CSeg[LINE_TYPE], bi_list: LINE_LIST_TYPE):
        BSP_CONF = self.config.GetBSConfig(seg.is_down())
        zs_cnt = seg.get_multi_bi_zs_cnt() if BSP_CONF.bsp1_only_multibi_zs else len(seg.zs_lst)
        is_target_bsp = (BSP_CONF.min_zs_cnt <= 0 or zs_cnt >= BSP_CONF.min_zs_cnt)
        if len(seg.zs_lst) > 0 and \
           not seg.zs_lst[-1].is_one_bi_zs() and \
           ((seg.zs_lst[-1].bi_out and seg.zs_lst[-1].bi_out.idx >= seg.end_bi.idx) or seg.zs_lst[-1].bi_lst[-1].idx >= seg.end_bi.idx) \
           and seg.end_bi.idx - seg.zs_lst[-1].get_bi_in().idx > 2:
            self.treat_bsp1(seg, BSP_CONF, is_target_bsp)
        else:
            self.treat_pz_bsp1(seg, BSP_CONF, bi_list, is_target_bsp)

    def treat_bsp1(self, seg: CSeg[LINE_TYPE], BSP_CONF: CPointConfig, is_target_bsp: bool):
        last_zs = seg.zs_lst[-1]
        break_peak, _ = last_zs.out_bi_is_peak(seg.end_bi.idx)
        if BSP_CONF.bs1_peak and not break_peak:
            is_target_bsp = False
        is_diver, divergence_rate = last_zs.is_divergence(BSP_CONF, out_bi=seg.end_bi)
        if not is_diver:
            is_target_bsp = False
        feature_dict = {'divergence_rate': divergence_rate}
        self.add_bs(bs_type=BSP_TYPE.T1, bi=seg.end_bi, relate_bsp1=None, is_target_bsp=is_target_bsp, feature_dict=feature_dict)

    def treat_pz_bsp1(self, seg: CSeg[LINE_TYPE], BSP_CONF: CPointConfig, bi_list: LINE_LIST_TYPE, is_target_bsp):
        last_bi = seg.end_bi
        pre_bi = bi_list[last_bi.idx-2]
        if last_bi.seg_idx != pre_bi.seg_idx:
            return
        if last_bi.dir != seg.dir:
            return
        if last_bi.is_down() and last_bi._low() > pre_bi._low():  # 创新低
            return
        if last_bi.is_up() and last_bi._high() < pre_bi._high():  # 创新高
            return
        in_metric = pre_bi.cal_macd_metric(BSP_CONF.macd_algo, is_reverse=False)
        out_metric = last_bi.cal_macd_metric(BSP_CONF.macd_algo, is_reverse=True)
        is_diver, divergence_rate = out_metric <= BSP_CONF.divergence_rate*in_metric, out_metric/(in_metric+1e-7)
        if not is_diver:
            is_target_bsp = False
        if isinstance(bi_list, CBiList):
            assert isinstance(last_bi, CBi) and isinstance(pre_bi, CBi)
        feature_dict = {'divergence_rate': divergence_rate}
        self.add_bs(bs_type=BSP_TYPE.T1P, bi=last_bi, relate_bsp1=None, is_target_bsp=is_target_bsp, feature_dict=feature_dict)

    def cal_seg_bs2point(self, seg_list: CSegListComm[LINE_TYPE], bi_list: LINE_LIST_TYPE):
        for seg in seg_list[self.last_sure_seg_idx:]:
            config = self.config.GetBSConfig(seg.is_down())
            if BSP_TYPE.T2 not in config.target_types and BSP_TYPE.T2S not in config.target_types:
                continue
            if not self.seg_need_cal(seg):
                continue
            self.treat_bsp2(seg, seg_list, bi_list)

    def treat_bsp2(self, seg: CSeg, seg_list: CSegListComm[LINE_TYPE], bi_list: LINE_LIST_TYPE):
        if len(seg_list) > 1:
            BSP_CONF = self.config.GetBSConfig(seg.is_down())
            bsp1_bi = seg.end_bi
            real_bsp1 = self.bsp1_dict.get(bsp1_bi.idx)
            if bsp1_bi.idx + 2 >= len(bi_list):
                return
            break_bi = bi_list[bsp1_bi.idx + 1]
            bsp2_bi = bi_list[bsp1_bi.idx + 2]
        else:
            BSP_CONF = self.config.GetBSConfig(seg.is_up())
            bsp1_bi, real_bsp1 = None, None
            if len(bi_list) == 1:
                return
            bsp2_bi = bi_list[1]
            break_bi = bi_list[0]
        if BSP_CONF.bsp2_follow_1 and (not bsp1_bi or bsp1_bi.idx not in self.bsp_store_flat_dict):
            return
        retrace_rate = bsp2_bi.amp()/break_bi.amp()
        bsp2_flag = retrace_rate <= BSP_CONF.max_bs2_rate
        if bsp2_flag:
            self.add_bs(bs_type=BSP_TYPE.T2, bi=bsp2_bi, relate_bsp1=real_bsp1)  # type: ignore
        elif BSP_CONF.bsp2s_follow_2:
            return
        if BSP_TYPE.T2S not in self.config.GetBSConfig(seg.is_down()).target_types:
            return
        self.treat_bsp2s(seg_list, bi_list, bsp2_bi, break_bi, real_bsp1, BSP_CONF)  # type: ignore

    def treat_bsp2s(
        self,
        seg_list: CSegListComm,
        bi_list: LINE_LIST_TYPE,
        bsp2_bi: LINE_TYPE,
        break_bi: LINE_TYPE,
        real_bsp1: Optional[CBS_Point],
        BSP_CONF: CPointConfig,
    ):
        bias = 2
        _low, _high = None, None
        while bsp2_bi.idx + bias < len(bi_list):  # 计算类二
            bsp2s_bi = bi_list[bsp2_bi.idx + bias]
            assert bsp2s_bi.seg_idx is not None and bsp2_bi.seg_idx is not None
            if BSP_CONF.max_bsp2s_lv is not None and bias/2 > BSP_CONF.max_bsp2s_lv:
                break
            if bsp2s_bi.seg_idx != bsp2_bi.seg_idx and (bsp2s_bi.seg_idx < len(seg_list)-1 or bsp2s_bi.seg_idx - bsp2_bi.seg_idx >= 2 or seg_list[bsp2_bi.seg_idx].is_sure):
                break
            if bias == 2:
                if not has_overlap(bsp2_bi._low(), bsp2_bi._high(), bsp2s_bi._low(), bsp2s_bi._high()):
                    break
                _low = max([bsp2_bi._low(), bsp2s_bi._low()])
                _high = min([bsp2_bi._high(), bsp2s_bi._high()])
            elif not has_overlap(_low, _high, bsp2s_bi._low(), bsp2s_bi._high()):
                break

            if bsp2s_break_bsp1(bsp2s_bi, break_bi):
                break
            retrace_rate = abs(bsp2s_bi.get_end_val()-break_bi.get_end_val())/break_bi.amp()
            if retrace_rate > BSP_CONF.max_bs2_rate:
                break

            self.add_bs(bs_type=BSP_TYPE.T2S, bi=bsp2s_bi, relate_bsp1=real_bsp1)  # type: ignore
            bias += 2

    def cal_seg_bs3point(self, seg_list: CSegListComm[LINE_TYPE], bi_list: LINE_LIST_TYPE):
        for seg in seg_list[self.last_sure_seg_idx:]:
            if not self.seg_need_cal(seg):
                continue
            config = self.config.GetBSConfig(seg.is_down())
            if BSP_TYPE.T3A not in config.target_types and BSP_TYPE.T3B not in config.target_types:
                continue
            if len(seg_list) > 1:
                bsp1_bi = seg.end_bi
                bsp1_bi_idx = bsp1_bi.idx
                BSP_CONF = self.config.GetBSConfig(seg.is_down())
                real_bsp1 = self.bsp1_dict.get(bsp1_bi.idx)
                next_seg_idx = seg.idx+1
                next_seg = seg.next  # 可能为None, 所以并不一定可以保证next_seg_idx == next_seg.idx
            else:
                next_seg = seg
                next_seg_idx = seg.idx
                bsp1_bi, real_bsp1 = None, None
                bsp1_bi_idx = -1
                BSP_CONF = self.config.GetBSConfig(seg.is_up())
            if BSP_CONF.bsp3_follow_1 and (not bsp1_bi or bsp1_bi.idx not in self.bsp_store_flat_dict):
                continue
            if next_seg:
                self.treat_bsp3_after(seg_list, next_seg, BSP_CONF, bi_list, real_bsp1, bsp1_bi_idx, next_seg_idx)
            self.treat_bsp3_before(seg_list, seg, next_seg, bsp1_bi, BSP_CONF, bi_list, real_bsp1, next_seg_idx)

    def treat_bsp3_after(
        self,
        seg_list: CSegListComm[LINE_TYPE],
        next_seg: CSeg[LINE_TYPE],
        BSP_CONF: CPointConfig,
        bi_list: LINE_LIST_TYPE,
        real_bsp1,
        bsp1_bi_idx,
        next_seg_idx
    ):
        first_zs = next_seg.get_first_multi_bi_zs()
        if first_zs is None:
            return
        if BSP_CONF.strict_bsp3 and first_zs.get_bi_in().idx != bsp1_bi_idx+1:
            return

        config = self.config.GetBSConfig(next_seg.is_down())
        bsp3a_max_zs_cnt = config.bsp3a_max_zs_cnt
        for zs_idx, zs in enumerate(next_seg.get_multi_bi_zs_lst()):
            if zs_idx >= bsp3a_max_zs_cnt:
                break
            if zs.bi_out is None or zs.bi_out.idx+1 >= len(bi_list):
                break
            bsp3_bi = bi_list[zs.bi_out.idx+1]
            if bsp3_bi.parent_seg is None:
                if next_seg.idx != len(seg_list)-1:
                    break
            elif bsp3_bi.parent_seg.idx != next_seg.idx:
                if len(bsp3_bi.parent_seg.bi_list) >= 3:
                    break
            if bsp3_bi.dir == next_seg.dir:
                break
            if bsp3_bi.seg_idx != next_seg_idx and next_seg_idx < len(seg_list)-2:
                break
            if bsp3_back2zs(bsp3_bi, zs):
                continue
            bsp3_peak_zs = bsp3_break_zspeak(bsp3_bi, zs)
            if BSP_CONF.bsp3_peak and not bsp3_peak_zs:
                continue
            self.add_bs(bs_type=BSP_TYPE.T3A, bi=bsp3_bi, relate_bsp1=real_bsp1)  # type: ignore

    def treat_bsp3_before(
        self,
        seg_list: CSegListComm[LINE_TYPE],
        seg: CSeg[LINE_TYPE],
        next_seg: Optional[CSeg[LINE_TYPE]],
        bsp1_bi: Optional[LINE_TYPE],
        BSP_CONF: CPointConfig,
        bi_list: LINE_LIST_TYPE,
        real_bsp1,
        next_seg_idx
    ):
        cmp_zs = seg.get_final_multi_bi_zs()
        if cmp_zs is None:
            return
        if not bsp1_bi:
            return
        if BSP_CONF.strict_bsp3 and (cmp_zs.bi_out is None or cmp_zs.bi_out.idx != bsp1_bi.idx):
            return
        end_bi_idx = cal_bsp3_bi_end_idx(next_seg)
        for bsp3_bi in bi_list[bsp1_bi.idx+2::2]:
            if bsp3_bi.idx > end_bi_idx:
                break
            assert bsp3_bi.seg_idx is not None
            if bsp3_bi.seg_idx != next_seg_idx and bsp3_bi.seg_idx < len(seg_list)-1:
                break
            if bsp3_back2zs(bsp3_bi, cmp_zs):  # type: ignore
                continue
            self.add_bs(bs_type=BSP_TYPE.T3B, bi=bsp3_bi, relate_bsp1=real_bsp1)  # type: ignore
            break

    def getSortedBspList(self) -> List[CBS_Point[LINE_TYPE]]:
        return sorted(self.bsp_iter(), key=lambda bsp: bsp.bi.idx)

    def get_latest_bsp(self, number: int) -> List[CBS_Point[LINE_TYPE]]:
        res = []
        for bsp in self.bsp_iter_v2():
            res.append(bsp)
            if number != 0 and len(res) >= number:
                break
        return res


def bsp2s_break_bsp1(bsp2s_bi: LINE_TYPE, bsp2_break_bi: LINE_TYPE) -> bool:
    return (bsp2s_bi.is_down() and bsp2s_bi._low() < bsp2_break_bi._low()) or \
           (bsp2s_bi.is_up() and bsp2s_bi._high() > bsp2_break_bi._high())


def bsp3_back2zs(bsp3_bi: LINE_TYPE, zs: CZS) -> bool:
    return (bsp3_bi.is_down() and bsp3_bi._low() < zs.high) or (bsp3_bi.is_up() and bsp3_bi._high() > zs.low)


def bsp3_break_zspeak(bsp3_bi: LINE_TYPE, zs: CZS) -> bool:
    return (bsp3_bi.is_down() and bsp3_bi._high() >= zs.peak_high) or (bsp3_bi.is_up() and bsp3_bi._low() <= zs.peak_low)


def cal_bsp3_bi_end_idx(seg: Optional[CSeg[LINE_TYPE]]):
    if not seg:
        return float("inf")
    if seg.get_multi_bi_zs_cnt() == 0 and seg.next is None:
        return float("inf")
    end_bi_idx = seg.end_bi.idx-1
    for zs in seg.zs_lst:
        if zs.is_one_bi_zs():
            continue
        if zs.bi_out is not None:
            end_bi_idx = zs.bi_out.idx
            break
    return end_bi_idx


# ==================== DataAPI/CommonStockAPI.py ====================

import abc
from typing import Iterable



class CCommonStockApi:
    def __init__(self, code, k_type, begin_date, end_date, autype):
        self.code = code
        self.name = None
        self.is_stock = None
        self.k_type = k_type
        self.begin_date = begin_date
        self.end_date = end_date
        self.autype = autype
        self.SetBasciInfo()

    @abc.abstractmethod
    def get_kl_data(self) -> Iterable[CKLine_Unit]:
        pass

    @abc.abstractmethod
    def SetBasciInfo(self):
        pass

    @classmethod
    @abc.abstractmethod
    def do_init(cls):
        pass

    @classmethod
    @abc.abstractmethod
    def do_close(cls):
        pass


# ==================== DataAPI/BaoStockAPI.py ====================

import baostock as bs




def create_item_dict(data, column_name):
    for i in range(len(data)):
        data[i] = parse_time_column(data[i]) if i == 0 else str2float(data[i])
    return dict(zip(column_name, data))


def parse_time_column(inp):
    # 20210902113000000
    # 2021-09-13
    if len(inp) == 10:
        year = int(inp[:4])
        month = int(inp[5:7])
        day = int(inp[8:10])
        hour = minute = 0
    elif len(inp) == 17:
        year = int(inp[:4])
        month = int(inp[4:6])
        day = int(inp[6:8])
        hour = int(inp[8:10])
        minute = int(inp[10:12])
    elif len(inp) == 19:
        year = int(inp[:4])
        month = int(inp[5:7])
        day = int(inp[8:10])
        hour = int(inp[11:13])
        minute = int(inp[14:16])
    else:
        raise Exception(f"unknown time column from baostock:{inp}")
    return CTime(year, month, day, hour, minute)


def GetColumnNameFromFieldList(fileds: str):
    _dict = {
        "time": DATA_FIELD.FIELD_TIME,
        "date": DATA_FIELD.FIELD_TIME,
        "open": DATA_FIELD.FIELD_OPEN,
        "high": DATA_FIELD.FIELD_HIGH,
        "low": DATA_FIELD.FIELD_LOW,
        "close": DATA_FIELD.FIELD_CLOSE,
        "volume": DATA_FIELD.FIELD_VOLUME,
        "amount": DATA_FIELD.FIELD_TURNOVER,
        "turn": DATA_FIELD.FIELD_TURNRATE,
    }
    return [_dict[x] for x in fileds.split(",")]


class CBaoStock(CCommonStockApi):
    is_connect = None

    def __init__(self, code, k_type=KL_TYPE.K_DAY, begin_date=None, end_date=None, autype=AUTYPE.QFQ):
        super(CBaoStock, self).__init__(code, k_type, begin_date, end_date, autype)

    def get_kl_data(self):
        # 天级别以上才有详细交易信息
        if kltype_lt_day(self.k_type):
            if not self.is_stock:
                raise Exception("没有获取到数据，注意指数是没有分钟级别数据的！")
            fields = "time,open,high,low,close"
        else:
            fields = "date,open,high,low,close,volume,amount,turn"
        autype_dict = {AUTYPE.QFQ: "2", AUTYPE.HFQ: "1", AUTYPE.NONE: "3"}
        rs = bs.query_history_k_data_plus(
            code=self.code,
            fields=fields,
            start_date=self.begin_date,
            end_date=self.end_date,
            frequency=self.__convert_type(),
            adjustflag=autype_dict[self.autype],
        )
        if rs.error_code != '0':
            raise Exception(rs.error_msg)
        while rs.error_code == '0' and rs.next():
            yield CKLine_Unit(create_item_dict(rs.get_row_data(), GetColumnNameFromFieldList(fields)))

    def SetBasciInfo(self):
        rs = bs.query_stock_basic(code=self.code)
        if rs.error_code != '0':
            raise Exception(rs.error_msg)
        code, code_name, ipoDate, outDate, stock_type, status = rs.get_row_data()
        self.name = code_name
        self.is_stock = (stock_type == '1')

    @classmethod
    def do_init(cls):
        if not cls.is_connect:
            cls.is_connect = bs.login()

    @classmethod
    def do_close(cls):
        if cls.is_connect:
            bs.logout()
            cls.is_connect = None

    def __convert_type(self):
        _dict = {
            KL_TYPE.K_DAY: 'd',
            KL_TYPE.K_WEEK: 'w',
            KL_TYPE.K_MON: 'm',
            KL_TYPE.K_5M: '5',
            KL_TYPE.K_15M: '15',
            KL_TYPE.K_30M: '30',
            KL_TYPE.K_60M: '60',
        }
        return _dict[self.k_type]


# ==================== DataAPI/csvAPI.py ====================

import os




def create_item_dict(data, column_name):
    for i in range(len(data)):
        data[i] = parse_time_column(data[i]) if column_name[i] == DATA_FIELD.FIELD_TIME else str2float(data[i])
    return dict(zip(column_name, data))


def parse_time_column(inp):
    # 20210902113000000
    # 2021-09-13
    if len(inp) == 10:
        year = int(inp[:4])
        month = int(inp[5:7])
        day = int(inp[8:10])
        hour = minute = 0
    elif len(inp) == 17:
        year = int(inp[:4])
        month = int(inp[4:6])
        day = int(inp[6:8])
        hour = int(inp[8:10])
        minute = int(inp[10:12])
    elif len(inp) == 19:
        year = int(inp[:4])
        month = int(inp[5:7])
        day = int(inp[8:10])
        hour = int(inp[11:13])
        minute = int(inp[14:16])
    else:
        raise Exception(f"unknown time column from csv:{inp}")
    return CTime(year, month, day, hour, minute)


class CSV_API(CCommonStockApi):
    def __init__(self, code, k_type=KL_TYPE.K_DAY, begin_date=None, end_date=None, autype=None):
        self.headers_exist = True  # 第一行是否是标题，如果是数据，设置为False
        self.columns = [
            DATA_FIELD.FIELD_TIME,
            DATA_FIELD.FIELD_OPEN,
            DATA_FIELD.FIELD_HIGH,
            DATA_FIELD.FIELD_LOW,
            DATA_FIELD.FIELD_CLOSE,
            # DATA_FIELD.FIELD_VOLUME,
            # DATA_FIELD.FIELD_TURNOVER,
            # DATA_FIELD.FIELD_TURNRATE,
        ]  # 每一列字段
        self.time_column_idx = self.columns.index(DATA_FIELD.FIELD_TIME)
        super(CSV_API, self).__init__(code, k_type, begin_date, end_date, autype)

    def get_kl_data(self):
        cur_path = os.path.dirname(os.path.realpath(__file__))
        k_type = self.k_type.name[2:].lower()
        file_path = f"{cur_path}/../{self.code}_{k_type}.csv"
        if not os.path.exists(file_path):
            raise CChanException(f"file not exist: {file_path}", ErrCode.SRC_DATA_NOT_FOUND)

        for line_number, line in enumerate(open(file_path, 'r')):
            if self.headers_exist and line_number == 0:
                continue
            data = line.strip("\n").split(",")
            if len(data) != len(self.columns):
                raise CChanException(f"file format error: {file_path}", ErrCode.SRC_DATA_FORMAT_ERROR)
            if self.begin_date is not None and data[self.time_column_idx] < self.begin_date:
                continue
            if self.end_date is not None and data[self.time_column_idx] > self.end_date:
                continue
            yield CKLine_Unit(create_item_dict(data, self.columns))

    def SetBasciInfo(self):
        pass

    @classmethod
    def do_init(cls):
        pass

    @classmethod
    def do_close(cls):
        pass


# ==================== Plot/PlotMeta.py ====================

from typing import List



class Cklc_meta:
    def __init__(self, klc: CKLine):
        self.high = klc.high
        self.low = klc.low
        self.begin_idx = klc.lst[0].idx
        self.end_idx = klc.lst[-1].idx
        self.type = klc.fx if klc.fx != FX_TYPE.UNKNOWN else klc.dir

        self.klu_list = list(klc.lst)


class CBi_meta:
    def __init__(self, bi: CBi):
        self.idx = bi.idx
        self.dir = bi.dir
        self.type = bi.type
        self.begin_x = bi.get_begin_klu().idx
        self.end_x = bi.get_end_klu().idx
        self.begin_y = bi.get_begin_val()
        self.end_y = bi.get_end_val()
        self.is_sure = bi.is_sure


class CSeg_meta:
    def __init__(self, seg: CSeg):
        if isinstance(seg.start_bi, CBi):
            self.begin_x = seg.start_bi.get_begin_klu().idx
            self.begin_y = seg.start_bi.get_begin_val()
            self.end_x = seg.end_bi.get_end_klu().idx
            self.end_y = seg.end_bi.get_end_val()
        else:
            assert isinstance(seg.start_bi, CSeg)
            self.begin_x = seg.start_bi.start_bi.get_begin_klu().idx
            self.begin_y = seg.start_bi.start_bi.get_begin_val()
            self.end_x = seg.end_bi.end_bi.get_end_klu().idx
            self.end_y = seg.end_bi.end_bi.get_end_val()
        self.dir = seg.dir
        self.is_sure = seg.is_sure
        self.idx = seg.idx

        self.tl = {}
        if seg.support_trend_line and seg.support_trend_line.line:
            self.tl["support"] = seg.support_trend_line
        if seg.resistance_trend_line and seg.resistance_trend_line.line:
            self.tl["resistance"] = seg.resistance_trend_line

    def format_tl(self, tl):
        assert tl.line
        tl_slope = tl.line.slope + 1e-7
        tl_x = tl.line.p.x
        tl_y = tl.line.p.y
        tl_y0 = self.begin_y
        tl_y1 = self.end_y
        tl_x0 = (tl_y0-tl_y)/tl_slope + tl_x
        tl_x1 = (tl_y1-tl_y)/tl_slope + tl_x
        return tl_x0, tl_y0, tl_x1, tl_y1


class CEigen_meta:
    def __init__(self, eigen: CEigen):
        self.begin_x = eigen.lst[0].get_begin_klu().idx
        self.end_x = eigen.lst[-1].get_end_klu().idx
        self.begin_y = eigen.low
        self.end_y = eigen.high
        self.w = self.end_x - self.begin_x
        self.h = self.end_y - self.begin_y


class CEigenFX_meta:
    def __init__(self, eigenFX: CEigenFX):
        self.ele = [CEigen_meta(ele) for ele in eigenFX.ele if ele is not None]
        assert len(self.ele) == 3
        assert eigenFX.ele[1] is not None
        self.gap = eigenFX.ele[1].gap
        self.fx = eigenFX.ele[1].fx


class CZS_meta:
    def __init__(self, zs: CZS):
        self.low = zs.low
        self.high = zs.high
        self.begin = zs.begin.idx
        self.end = zs.end.idx
        self.w = self.end - self.begin
        self.h = self.high - self.low
        self.is_sure = zs.is_sure
        self.sub_zs_lst = [CZS_meta(t) for t in zs.sub_zs_lst]
        self.is_onebi_zs = zs.is_one_bi_zs()


class CBS_Point_meta:
    def __init__(self, bsp: CBS_Point, is_seg):
        self.is_buy = bsp.is_buy
        self.type = bsp.type2str()
        self.is_seg = is_seg

        self.x = bsp.klu.idx
        self.y = bsp.klu.low if self.is_buy else bsp.klu.high

    def desc(self):
        is_seg_flag = "※" if self.is_seg else ""
        return f'{is_seg_flag}b{self.type}' if self.is_buy else f'{is_seg_flag}s{self.type}'


class CChanPlotMeta:
    def __init__(self, kl_list: CKLine_List):
        self.data = kl_list

        self.klc_list: List[Cklc_meta] = [Cklc_meta(klc) for klc in kl_list.lst]
        self.datetick = [klu.time.to_str() for klu in self.klu_iter()]
        self.klu_len = sum(len(klc.klu_list) for klc in self.klc_list)

        self.bi_list = [CBi_meta(bi) for bi in kl_list.bi_list]

        self.seg_list: List[CSeg_meta] = []
        self.eigenfx_lst: List[CEigenFX_meta] = []
        for seg in kl_list.seg_list:
            self.seg_list.append(CSeg_meta(seg))
            if seg.eigen_fx:
                self.eigenfx_lst.append(CEigenFX_meta(seg.eigen_fx))

        self.seg_eigenfx_lst: List[CEigenFX_meta] = []
        self.segseg_list: List[CSeg_meta] = []
        for segseg in kl_list.segseg_list:
            self.segseg_list.append(CSeg_meta(segseg))
            if segseg.eigen_fx:
                self.seg_eigenfx_lst.append(CEigenFX_meta(segseg.eigen_fx))

        self.zs_lst: List[CZS_meta] = [CZS_meta(zs) for zs in kl_list.zs_list]
        self.segzs_lst: List[CZS_meta] = [CZS_meta(segzs) for segzs in kl_list.segzs_list]

        self.bs_point_lst: List[CBS_Point_meta] = [CBS_Point_meta(bs_point, is_seg=False) for bs_point in kl_list.bs_point_lst.bsp_iter()]
        self.seg_bsp_lst: List[CBS_Point_meta] = [CBS_Point_meta(seg_bsp, is_seg=True) for seg_bsp in kl_list.seg_bs_point_lst.bsp_iter()]

    def klu_iter(self):
        for klc in self.klc_list:
            yield from klc.klu_list

    def sub_last_kseg_start_idx(self, seg_cnt):
        if seg_cnt is None or len(self.data.seg_list) <= seg_cnt:
            return 0
        else:
            return self.data.seg_list[-seg_cnt].get_begin_klu().sub_kl_list[0].idx

    def sub_last_kbi_start_idx(self, bi_cnt):
        if bi_cnt is None or len(self.data.bi_list) <= bi_cnt:
            return 0
        else:
            return self.data.bi_list[-bi_cnt].begin_klc.lst[0].sub_kl_list[0].idx

    def sub_range_start_idx(self, x_range):
        for klc in self.data[::-1]:
            for klu in klc[::-1]:
                x_range -= 1
                if x_range == 0:
                    return klu.sub_kl_list[0].idx
        return 0


# ==================== Plot/PlotDriver.py ====================

import inspect
from typing import Dict, List, Literal, Optional, Tuple, Union

from pyecharts import options as opts
from pyecharts.charts import Bar, Grid, Kline, Line, Scatter
from pyecharts.commons.utils import JsCode



def reformat_plot_config(plot_config: Dict[str, bool]):
    """
    兼容不填写`plot_`前缀的情况
    """
    def _format(s):
        return s if s.startswith("plot_") else f"plot_{s}"

    return {_format(k): v for k, v in plot_config.items()}


def parse_single_lv_plot_config(plot_config: Union[str, dict, list]) -> Dict[str, bool]:
    """
    返回单一级别的plot_config配置
    """
    if isinstance(plot_config, dict):
        return reformat_plot_config(plot_config)
    elif isinstance(plot_config, str):
        return reformat_plot_config(dict([(k.strip().lower(), True) for k in plot_config.split(",")]))
    elif isinstance(plot_config, list):
        return reformat_plot_config(dict([(k.strip().lower(), True) for k in plot_config]))
    else:
        raise CChanException("plot_config only support list/str/dict", ErrCode.PLOT_ERR)


def parse_plot_config(plot_config: Union[str, dict, list], lv_list: List[KL_TYPE]) -> Dict[KL_TYPE, Dict[str, bool]]:
    """
    支持：
        - 传入字典
        - 传入字符串，逗号分割
        - 传入数组，元素为各个需要画的笔的元素
        - 传入key为各个级别的字典
        - 传入key为各个级别的字符串
        - 传入key为各个级别的数组
    """
    if isinstance(plot_config, dict):
        if all(isinstance(_key, str) for _key in plot_config.keys()):  # 单层字典
            return {lv: parse_single_lv_plot_config(plot_config) for lv in lv_list}
        elif all(isinstance(_key, KL_TYPE) for _key in plot_config.keys()):  # key为KL_TYPE
            for lv in lv_list:
                assert lv in plot_config
            return {lv: parse_single_lv_plot_config(plot_config[lv]) for lv in lv_list}
        else:
            raise CChanException("plot_config if is dict, key must be str/KL_TYPE", ErrCode.PLOT_ERR)
    return {lv: parse_single_lv_plot_config(plot_config) for lv in lv_list}


def cal_x_limit(meta: CChanPlotMeta, x_range):
    X_LEN = meta.klu_len
    return [X_LEN - x_range, X_LEN - 1] if x_range and X_LEN > x_range else [0, X_LEN - 1]


def GetPlotMeta(chan: CChan, figure_config) -> List[CChanPlotMeta]:
    plot_metas = [CChanPlotMeta(chan[kl_type]) for kl_type in chan.lv_list]
    if figure_config.get("only_top_lv", False):
        plot_metas = [plot_metas[0]]
    return plot_metas


class CPlotDriver:
    def __init__(self, chan: CChan, plot_config: Union[str, dict, list] = '', plot_para=None):
        if plot_para is None:
            plot_para = {}
        figure_config: dict = plot_para.get('figure', {})

        plot_config = parse_plot_config(plot_config, chan.lv_list)
        plot_metas = GetPlotMeta(chan, figure_config)
        self.lv_lst = chan.lv_list[:len(plot_metas)]

        x_range = self.GetRealXrange(figure_config, plot_metas[0])
        plot_macd: Dict[KL_TYPE, bool] = {kl_type: conf.get("plot_macd", False) for kl_type, conf in plot_config.items()}
        
        self.grid = Grid(init_opts=opts.InitOpts(width=f"{figure_config.get('w', 1200)}px", height=f"{figure_config.get('h', 800)}px"))
        
        total_lv = len(self.lv_lst)
        for i, (meta, lv) in enumerate(zip(plot_metas, self.lv_lst)):
            x_limits = cal_x_limit(meta, x_range)
            
            top = f"{10 + i * (90 / total_lv)}%"
            height = f"{90 / total_lv - 5}%"
            
            chart = self.create_single_chart(meta, lv, plot_config[lv], plot_para, x_limits, plot_macd[lv])
            
            if plot_macd[lv]:
                kline_chart, macd_chart = chart
                self.grid.add(kline_chart, grid_opts=opts.GridOpts(pos_top=top, height=f"{float(height[:-1])*0.7}%", pos_left="5%", pos_right="5%"))
                self.grid.add(macd_chart, grid_opts=opts.GridOpts(pos_top=f"{float(top[:-1]) + float(height[:-1])*0.75}%", height=f"{float(height[:-1])*0.2}%", pos_left="5%", pos_right="5%"))
            else:
                self.grid.add(chart, grid_opts=opts.GridOpts(pos_top=top, height=height, pos_left="5%", pos_right="5%"))

        self.figure = self.grid

    def create_single_chart(self, meta: CChanPlotMeta, lv: KL_TYPE, plot_config: Dict[str, bool], plot_para: dict, x_limits: List[int], has_macd: bool):
        x_data = meta.datetick[x_limits[0]:x_limits[1]+1]
        
        # Base Kline Chart
        kline = Kline().add_xaxis(xaxis_data=x_data)
        
        if plot_config.get("plot_kline", False):
            k_data = [[kl.open, kl.close, kl.low, kl.high] for kl in list(meta.klu_iter())[x_limits[0]:x_limits[1]+1]]
            kline.add_yaxis(
                series_name="K-Line",
                y_axis=k_data,
                itemstyle_opts=opts.ItemStyleOpts(color="#ec0000", color0="#00da3c", border_color="#8A0000", border_color0="#008F28"),
            )

        if plot_config.get("plot_kline_combine", False):
            self.draw_klc(kline, meta, x_limits, **plot_para.get('klc', {}))

        title = plot_para.get('title', f"{lv.name}")
        kline.set_global_opts(
            xaxis_opts=opts.AxisOpts(is_scale=True),
            yaxis_opts=opts.AxisOpts(is_scale=True, splitarea_opts=opts.SplitAreaOpts(is_show=True, areastyle_opts=opts.AreaStyleOpts(opacity=1))),
            datazoom_opts=[opts.DataZoomOpts(type_="inside")],
            title_opts=opts.TitleOpts(title=title, pos_left="center"),
            tooltip_opts=opts.TooltipOpts(is_show=False, trigger="axis", axis_pointer_type="cross"),
            legend_opts=opts.LegendOpts(is_show=False)
        )

        # Overlap other elements
        if plot_config.get("plot_bi", False):
            kline.overlap(self.draw_bi(meta, x_limits, **plot_para.get('bi', {})))
            
        if plot_config.get("plot_seg", False):
            kline.overlap(self.draw_seg(meta, x_limits, **plot_para.get('seg', {})))

        if plot_config.get("plot_zs", False):
            self.draw_zs(kline, meta, x_limits, **plot_para.get('zs', {}))

        if plot_config.get("plot_mean", False):
            kline.overlap(self.draw_mean(meta, x_limits, **plot_para.get('mean', {})))

        if plot_config.get("plot_boll", False):
            kline.overlap(self.draw_boll(meta, x_limits, **plot_para.get('boll', {})))

        if plot_config.get("plot_bsp", False):
            kline.overlap(self.draw_bs_point(meta, x_limits, **plot_para.get('bsp', {})))

        if plot_config.get("plot_rsi", False):
            # RSI can be added as another grid or overlapping Line with secondary Y-axis
            pass

        if not has_macd:
            return kline

        # MACD Chart
        macd_chart = self.draw_macd(meta, x_limits, **plot_para.get('macd', {}))
        return kline, macd_chart

    def draw_klc(self, kline: Kline, meta: CChanPlotMeta, x_limits, width=0.4, **kwargs):
        color_type = {FX_TYPE.TOP: 'red', FX_TYPE.BOTTOM: 'blue', KLINE_DIR.UP: 'green', KLINE_DIR.DOWN: 'green'}
        mark_area_data = []
        for klc in meta.klc_list:
            if klc.klu_list[-1].idx < x_limits[0] or klc.klu_list[0].idx > x_limits[1]:
                continue
            
            start_x = max(0, klc.begin_idx - x_limits[0])
            end_x = min(x_limits[1] - x_limits[0], klc.end_idx - x_limits[0])
            
            mark_area_data.append([
                {"xAxis": start_x, "yAxis": klc.low, "itemStyle": {"color": color_type[klc.type], "opacity": 0.1, "borderWidth": 1, "borderColor": color_type[klc.type]}},
                {"xAxis": end_x, "yAxis": klc.high}
            ])
        kline.set_series_opts(markarea_opts=opts.MarkAreaOpts(data=mark_area_data))

    def draw_bi(self, meta: CChanPlotMeta, x_limits, color='black', **kwargs):
        bi_data = []
        # bi_list is a list of CBi objects
        for bi in meta.bi_list:
            if bi.end_x < x_limits[0] or bi.begin_x > x_limits[1]:
                continue
            bi_data.append({"xAxis": max(0, bi.begin_x - x_limits[0]), "yAxis": bi.begin_y})
            bi_data.append({"xAxis": min(x_limits[1] - x_limits[0], bi.end_x - x_limits[0]), "yAxis": bi.end_y})
            
        line = Line().add_xaxis(xaxis_data=list(range(x_limits[1] - x_limits[0] + 1)))
        
        # We need to draw segments. In pyecharts, we can use a single line with None for breaks, 
        # or multiple series. For Bi, they are continuous.
        y_data = [None] * (x_limits[1] - x_limits[0] + 1)
        for bi in meta.bi_list:
            if bi.end_x < x_limits[0] or bi.begin_x > x_limits[1]:
                continue
            for idx in range(max(x_limits[0], bi.begin_x), min(x_limits[1], bi.end_x) + 1):
                # Linear interpolation for Bi line
                ratio = (idx - bi.begin_x) / (bi.end_x - bi.begin_x)
                val = bi.begin_y + (bi.end_y - bi.begin_y) * ratio
                y_data[idx - x_limits[0]] = val
                
        line.add_yaxis(
            series_name="Bi",
            y_axis=y_data,
            is_symbol_show=False,
            label_opts=opts.LabelOpts(is_show=False),
            linestyle_opts=opts.LineStyleOpts(color=color, width=2),
            is_connect_nones=True,
        )
        return line

    def draw_seg(self, meta: CChanPlotMeta, x_limits, color='green', width=3, **kwargs):
        y_data = [None] * (x_limits[1] - x_limits[0] + 1)
        for seg in meta.seg_list:
            if seg.end_x < x_limits[0] or seg.begin_x > x_limits[1]:
                continue
            for idx in range(max(x_limits[0], seg.begin_x), min(x_limits[1], seg.end_x) + 1):
                ratio = (idx - seg.begin_x) / (seg.end_x - seg.begin_x)
                val = seg.begin_y + (seg.end_y - seg.begin_y) * ratio
                y_data[idx - x_limits[0]] = val
                
        return Line().add_xaxis(xaxis_data=list(range(x_limits[1] - x_limits[0] + 1))).add_yaxis(
            series_name="Segment",
            y_axis=y_data,
            is_symbol_show=False,
            label_opts=opts.LabelOpts(is_show=False),
            linestyle_opts=opts.LineStyleOpts(color=color, width=width, type_="solid" if getattr(seg, 'is_sure', True) else "dashed"),
            is_connect_nones=True,
        )

    def draw_zs(self, kline: Kline, meta: CChanPlotMeta, x_limits, color='orange', **kwargs):
        mark_area_data = []
        for zs in meta.zs_lst:
            if zs.begin + zs.w < x_limits[0] or zs.begin > x_limits[1]:
                continue
            
            start_x = max(0, zs.begin - x_limits[0])
            end_x = min(x_limits[1] - x_limits[0], zs.begin + zs.w - x_limits[0])
            
            mark_area_data.append([
                {"xAxis": start_x, "yAxis": zs.low, "itemStyle": {"color": color, "opacity": 0.2, "borderWidth": 2, "borderColor": color}},
                {"xAxis": end_x, "yAxis": zs.low + zs.h}
            ])
        
        # Note: If we already have markarea from klc, we need to append
        series = kline.options.get('series', [{}])
        existing = []
        if series and isinstance(series, list):
            first_series = series[0]
            mark_area = first_series.get('markArea')
            if mark_area:
                if isinstance(mark_area, dict):
                    existing = mark_area.get('data', [])
                elif hasattr(mark_area, "opts"):
                    existing = mark_area.opts.get("data", [])
        
        mark_area_data.extend(existing)
        kline.set_series_opts(markarea_opts=opts.MarkAreaOpts(data=mark_area_data))

    def draw_macd(self, meta: CChanPlotMeta, x_limits, **kwargs):
        macd_lst = [klu.macd for klu in list(meta.klu_iter())[x_limits[0]:x_limits[1]+1]]
        x_data = meta.datetick[x_limits[0]:x_limits[1]+1]
        
        dif = [m.DIF for m in macd_lst]
        dea = [m.DEA for m in macd_lst]
        macd_bar = [m.macd for m in macd_lst]
        
        bar = Bar().add_xaxis(xaxis_data=x_data).add_yaxis(
            series_name="MACD",
            y_axis=macd_bar,
            label_opts=opts.LabelOpts(is_show=False),
        )
        
        line = Line().add_xaxis(xaxis_data=x_data).add_yaxis(
            series_name="DIF", y_axis=dif, label_opts=opts.LabelOpts(is_show=False), is_symbol_show=False
        ).add_yaxis(
            series_name="DEA", y_axis=dea, label_opts=opts.LabelOpts(is_show=False), is_symbol_show=False
        )
        
        return bar.overlap(line)

    def draw_mean(self, meta: CChanPlotMeta, x_limits, **kwargs):
        mean_lst = [klu.trend[TREND_TYPE.MEAN] for klu in list(meta.klu_iter())[x_limits[0]:x_limits[1]+1]]
        if not mean_lst:
            return Line()
            
        Ts = list(mean_lst[0].keys())
        line = Line().add_xaxis(xaxis_data=meta.datetick[x_limits[0]:x_limits[1]+1])
        
        for T in Ts:
            mean_arr = [m[T] for m in mean_lst]
            line.add_yaxis(series_name=f"{T} Mean", y_axis=mean_arr, is_symbol_show=False, label_opts=opts.LabelOpts(is_show=False))
            
        return line

    def draw_boll(self, meta: CChanPlotMeta, x_limits, mid_color="black", up_color="blue", down_color="purple", **kwargs):
        try:
            ma = [klu.boll.MID for klu in list(meta.klu_iter())[x_limits[0]:x_limits[1]+1]]
            up = [klu.boll.UP for klu in list(meta.klu_iter())[x_limits[0]:x_limits[1]+1]]
            down = [klu.boll.DOWN for klu in list(meta.klu_iter())[x_limits[0]:x_limits[1]+1]]
        except AttributeError:
            return Line()
            
        line = Line().add_xaxis(xaxis_data=meta.datetick[x_limits[0]:x_limits[1]+1])
        line.add_yaxis(series_name="BOLL MID", y_axis=ma, is_symbol_show=False, label_opts=opts.LabelOpts(is_show=False), linestyle_opts=opts.LineStyleOpts(color=mid_color))
        line.add_yaxis(series_name="BOLL UP", y_axis=up, is_symbol_show=False, label_opts=opts.LabelOpts(is_show=False), linestyle_opts=opts.LineStyleOpts(color=up_color))
        line.add_yaxis(series_name="BOLL DOWN", y_axis=down, is_symbol_show=False, label_opts=opts.LabelOpts(is_show=False), linestyle_opts=opts.LineStyleOpts(color=down_color))
        
        return line

    def draw_bs_point(self, meta: CChanPlotMeta, x_limits, buy_color='red', sell_color='green', **kwargs):
        buy_data = []
        sell_data = []
        for bsp in meta.bs_point_lst:
            if bsp.x < x_limits[0] or bsp.x > x_limits[1]:
                continue
            item = {
                "value": [bsp.x - x_limits[0], bsp.y],
                "name": bsp.desc(),
            }
            if bsp.is_buy:
                buy_data.append(item)
            else:
                sell_data.append(item)
            
        scatter = Scatter().add_xaxis(xaxis_data=list(range(x_limits[1] - x_limits[0] + 1)))
        
        if buy_data:
            scatter.add_yaxis(
                series_name="Buy Points",
                y_axis=buy_data,
                symbol="arrow",
                symbol_size=20,
                itemstyle_opts=opts.ItemStyleOpts(color=buy_color),
                label_opts=opts.LabelOpts(is_show=True, position="bottom", formatter="{b}")
            )
        
        if sell_data:
            scatter.add_yaxis(
                series_name="Sell Points",
                y_axis=sell_data,
                symbol="arrow",
                symbol_size=20,
                symbol_rotate=180,
                itemstyle_opts=opts.ItemStyleOpts(color=sell_color),
                label_opts=opts.LabelOpts(is_show=True, position="top", formatter="{b}")
            )
            
        return scatter

    def GetRealXrange(self, figure_config, meta: CChanPlotMeta):
        x_range = figure_config.get("x_range", 0)
        bi_cnt = figure_config.get("x_bi_cnt", 0)
        seg_cnt = figure_config.get("x_seg_cnt", 0)
        x_begin_date = figure_config.get("x_begin_date", 0)
        if x_range != 0:
            return x_range
        if bi_cnt != 0:
            if len(meta.bi_list) < bi_cnt:
                return 0
            return meta.klu_len - meta.bi_list[-bi_cnt].begin_x
        if seg_cnt != 0:
            if len(meta.seg_list) < seg_cnt:
                return 0
            return meta.klu_len - meta.seg_list[-seg_cnt].begin_x
        if x_begin_date != 0:
            x_range = 0
            for date_tick in meta.datetick[::-1]:
                if date_tick >= x_begin_date:
                    x_range += 1
                else:
                    break
            return x_range
        return x_range

    def save2img(self, path):
        self.figure.render(path.replace(".png", ".html"))

    def render_notebook(self):
        return self.figure.render_notebook()


# ==================== ChanConfig.py ====================

from typing import List



class CChanConfig:
    def __init__(self, conf=None):
        if conf is None:
            conf = {}
        conf = ConfigWithCheck(conf)
        self.bi_conf = CBiConfig(
            bi_algo=conf.get("bi_algo", "normal"),
            is_strict=conf.get("bi_strict", True),
            bi_fx_check=conf.get("bi_fx_check", "strict"),
            gap_as_kl=conf.get("gap_as_kl", False),
            bi_end_is_peak=conf.get('bi_end_is_peak', True),
            bi_allow_sub_peak=conf.get("bi_allow_sub_peak", True),
        )
        self.seg_conf = CSegConfig(
            seg_algo=conf.get("seg_algo", "chan"),
            left_method=conf.get("left_seg_method", "peak"),
        )
        self.zs_conf = CZSConfig(
            need_combine=conf.get("zs_combine", True),
            zs_combine_mode=conf.get("zs_combine_mode", "zs"),
            one_bi_zs=conf.get("one_bi_zs", False),
            zs_algo=conf.get("zs_algo", "normal"),
        )

        self.trigger_step = conf.get("trigger_step", False)
        self.skip_step = conf.get("skip_step", 0)

        self.kl_data_check = conf.get("kl_data_check", True)
        self.max_kl_misalgin_cnt = conf.get("max_kl_misalgin_cnt", 2)
        self.max_kl_inconsistent_cnt = conf.get("max_kl_inconsistent_cnt", 5)
        self.auto_skip_illegal_sub_lv = conf.get("auto_skip_illegal_sub_lv", False)
        self.print_warning = conf.get("print_warning", True)
        self.print_err_time = conf.get("print_err_time", True)

        self.mean_metrics: List[int] = conf.get("mean_metrics", [])
        self.trend_metrics: List[int] = conf.get("trend_metrics", [])
        self.macd_config = conf.get("macd", {"fast": 12, "slow": 26, "signal": 9})
        self.cal_demark = conf.get("cal_demark", False)
        self.cal_rsi = conf.get("cal_rsi", False)
        self.cal_kdj = conf.get("cal_kdj", False)
        self.rsi_cycle = conf.get("rsi_cycle", 14)
        self.kdj_cycle = conf.get("kdj_cycle", 9)
        self.demark_config = conf.get("demark", {
            'demark_len': 9,
            'setup_bias': 4,
            'countdown_bias': 2,
            'max_countdown': 13,
            'tiaokong_st': True,
            'setup_cmp2close': True,
            'countdown_cmp2close': True,
        })
        self.boll_n = conf.get("boll_n", 20)

        self.set_bsp_config(conf)

        conf.check()

    def GetMetricModel(self):
        res: List[CMACD | CTrendModel | BollModel | CDemarkEngine | RSI | KDJ] = [
            CMACD(
                fastperiod=self.macd_config['fast'],
                slowperiod=self.macd_config['slow'],
                signalperiod=self.macd_config['signal'],
            )
        ]
        res.extend(CTrendModel(TREND_TYPE.MEAN, mean_T) for mean_T in self.mean_metrics)

        for trend_T in self.trend_metrics:
            res.append(CTrendModel(TREND_TYPE.MAX, trend_T))
            res.append(CTrendModel(TREND_TYPE.MIN, trend_T))
        res.append(BollModel(self.boll_n))
        if self.cal_demark:
            res.append(CDemarkEngine(
                demark_len=self.demark_config['demark_len'],
                setup_bias=self.demark_config['setup_bias'],
                countdown_bias=self.demark_config['countdown_bias'],
                max_countdown=self.demark_config['max_countdown'],
                tiaokong_st=self.demark_config['tiaokong_st'],
                setup_cmp2close=self.demark_config['setup_cmp2close'],
                countdown_cmp2close=self.demark_config['countdown_cmp2close'],
            ))
        if self.cal_rsi:
            res.append(RSI(self.rsi_cycle))
        if self.cal_kdj:
            res.append(KDJ(self.kdj_cycle))
        return res

    def set_bsp_config(self, conf):
        para_dict = {
            "divergence_rate": float("inf"),
            "min_zs_cnt": 1,
            "bsp1_only_multibi_zs": True,
            "max_bs2_rate": 0.9999,
            "macd_algo": "peak",
            "bs1_peak": True,
            "bs_type": "1,1p,2,2s,3a,3b",
            "bsp2_follow_1": True,
            "bsp3_follow_1": True,
            "bsp3_peak": False,
            "bsp2s_follow_2": False,
            "max_bsp2s_lv": None,
            "strict_bsp3": False,
            "bsp3a_max_zs_cnt": 1,
        }
        args = {para: conf.get(para, default_value) for para, default_value in para_dict.items()}
        self.bs_point_conf = CBSPointConfig(**args)

        self.seg_bs_point_conf = CBSPointConfig(**args)
        self.seg_bs_point_conf.b_conf.set("macd_algo", "slope")
        self.seg_bs_point_conf.s_conf.set("macd_algo", "slope")
        self.seg_bs_point_conf.b_conf.set("bsp1_only_multibi_zs", False)
        self.seg_bs_point_conf.s_conf.set("bsp1_only_multibi_zs", False)

        for k, v in conf.items():
            if isinstance(v, str):
                v = f'"{v}"'
            v = _parse_inf(v)
            if k.endswith("-buy"):
                prop = k.replace("-buy", "")
                exec(f"self.bs_point_conf.b_conf.set('{prop}', {v})")
            elif k.endswith("-sell"):
                prop = k.replace("-sell", "")
                exec(f"self.bs_point_conf.s_conf.set('{prop}', {v})")
            elif k.endswith("-segbuy"):
                prop = k.replace("-segbuy", "")
                exec(f"self.seg_bs_point_conf.b_conf.set('{prop}', {v})")
            elif k.endswith("-segsell"):
                prop = k.replace("-segsell", "")
                exec(f"self.seg_bs_point_conf.s_conf.set('{prop}', {v})")
            elif k.endswith("-seg"):
                prop = k.replace("-seg", "")
                exec(f"self.seg_bs_point_conf.b_conf.set('{prop}', {v})")
                exec(f"self.seg_bs_point_conf.s_conf.set('{prop}', {v})")
            elif k in args:
                exec(f"self.bs_point_conf.b_conf.set({k}, {v})")
                exec(f"self.bs_point_conf.s_conf.set({k}, {v})")
            else:
                raise CChanException(f"unknown para = {k}", ErrCode.PARA_ERROR)
        self.bs_point_conf.b_conf.parse_target_type()
        self.bs_point_conf.s_conf.parse_target_type()
        self.seg_bs_point_conf.b_conf.parse_target_type()
        self.seg_bs_point_conf.s_conf.parse_target_type()


class ConfigWithCheck:
    def __init__(self, conf):
        self.conf = conf

    def get(self, k, default_value=None):
        res = self.conf.get(k, default_value)
        if k in self.conf:
            del self.conf[k]
        return res

    def items(self):
        visit_keys = set()
        for k, v in self.conf.items():
            yield k, v
            visit_keys.add(k)
        for k in visit_keys:
            del self.conf[k]

    def check(self):
        if len(self.conf) > 0:
            invalid_key_lst = ",".join(list(self.conf.keys()))
            raise CChanException(f"invalid CChanConfig: {invalid_key_lst}", ErrCode.PARA_ERROR)


# ==================== ChanModel/Features.py ====================

class CFeatures:
    def __init__(self, initFeat=None):
        self.__features = {} if initFeat is None else dict(initFeat)

    def items(self):
        yield from self.__features.items()

    def __getitem__(self, k):
        return self.__features[k]

    def add_feat(self, inp1, inp2=None):
        if inp2 is None:
            self.__features.update(inp1)
        else:
            self.__features.update({inp1: inp2})


# ==================== Chan.py ====================

import copy
import pickle
import sys
from collections import defaultdict
from typing import Dict, Iterable, List, Optional, Union


class CChan:
    def __init__(
        self,
        code,
        begin_time=None,
        end_time=None,
        data_src: Union[DATA_SRC, str] = DATA_SRC.BAO_STOCK,
        lv_list=None,
        config=None,
        autype: AUTYPE = AUTYPE.QFQ,
    ):
        if lv_list is None:
            lv_list = [KL_TYPE.K_DAY, KL_TYPE.K_60M]
        check_kltype_order(lv_list)  # lv_list顺序从高到低
        self.code = code
        self.begin_time = str(begin_time) if isinstance(begin_time, date) else begin_time
        self.end_time = str(end_time) if isinstance(end_time, date) else end_time
        self.autype = autype
        self.data_src = data_src
        self.lv_list: List[KL_TYPE] = lv_list

        if config is None:
            config = CChanConfig()
        self.conf = config

        self.kl_misalign_cnt = 0
        self.kl_inconsistent_detail = defaultdict(list)

        self.g_kl_iter = defaultdict(list)

        self.do_init()

        if not config.trigger_step:
            for _ in self.load():
                ...

    def __deepcopy__(self, memo):
        cls = self.__class__
        obj: CChan = cls.__new__(cls)
        memo[id(self)] = obj
        obj.code = self.code
        obj.begin_time = self.begin_time
        obj.end_time = self.end_time
        obj.autype = self.autype
        obj.data_src = self.data_src
        obj.lv_list = copy.deepcopy(self.lv_list, memo)
        obj.conf = copy.deepcopy(self.conf, memo)
        obj.kl_misalign_cnt = self.kl_misalign_cnt
        obj.kl_inconsistent_detail = copy.deepcopy(self.kl_inconsistent_detail, memo)
        obj.g_kl_iter = copy.deepcopy(self.g_kl_iter, memo)
        if hasattr(self, 'klu_cache'):
            obj.klu_cache = copy.deepcopy(self.klu_cache, memo)
        if hasattr(self, 'klu_last_t'):
            obj.klu_last_t = copy.deepcopy(self.klu_last_t, memo)
        obj.kl_datas = {}
        for kl_type, ckline in self.kl_datas.items():
            obj.kl_datas[kl_type] = copy.deepcopy(ckline, memo)
        for kl_type, ckline in self.kl_datas.items():
            for klc in ckline:
                for klu in klc.lst:
                    assert id(klu) in memo
                    if klu.sup_kl:
                        memo[id(klu)].sup_kl = memo[id(klu.sup_kl)]
                    memo[id(klu)].sub_kl_list = [memo[id(sub_kl)] for sub_kl in klu.sub_kl_list]
        return obj

    def do_init(self):
        self.kl_datas: Dict[KL_TYPE, CKLine_List] = {}
        for idx in range(len(self.lv_list)):
            self.kl_datas[self.lv_list[idx]] = CKLine_List(self.lv_list[idx], conf=self.conf)

    def load_stock_data(self, stockapi_instance: CCommonStockApi, lv) -> Iterable[CKLine_Unit]:
        for KLU_IDX, klu in enumerate(stockapi_instance.get_kl_data()):
            klu.set_idx(KLU_IDX)
            klu.kl_type = lv
            yield klu

    def get_load_stock_iter(self, stockapi_cls, lv):
        stockapi_instance = stockapi_cls(code=self.code, k_type=lv, begin_date=self.begin_time, end_date=self.end_time, autype=self.autype)
        return self.load_stock_data(stockapi_instance, lv)

    def add_lv_iter(self, lv_idx, iter):
        if isinstance(lv_idx, int):
            self.g_kl_iter[self.lv_list[lv_idx]].append(iter)
        else:
            self.g_kl_iter[lv_idx].append(iter)

    def get_next_lv_klu(self, lv_idx):
        if isinstance(lv_idx, int):
            lv_idx = self.lv_list[lv_idx]
        if len(self.g_kl_iter[lv_idx]) == 0:
            raise StopIteration
        try:
            return self.g_kl_iter[lv_idx][0].__next__()
        except StopIteration:
            self.g_kl_iter[lv_idx] = self.g_kl_iter[lv_idx][1:]
            if len(self.g_kl_iter[lv_idx]) != 0:
                return self.get_next_lv_klu(lv_idx)
            else:
                raise

    def step_load(self):
        assert self.conf.trigger_step
        self.do_init()  # 清空数据，防止再次重跑没有数据
        yielded = False  # 是否曾经返回过结果
        for idx, snapshot in enumerate(self.load(self.conf.trigger_step)):
            if idx < self.conf.skip_step:
                continue
            yield snapshot
            yielded = True
        if not yielded:
            yield self

    def trigger_load(self, inp):
        # {type: [klu, ...]}
        if not hasattr(self, 'klu_cache'):
            self.klu_cache: List[Optional[CKLine_Unit]] = [None for _ in self.lv_list]
        if not hasattr(self, 'klu_last_t'):
            self.klu_last_t = [CTime(1980, 1, 1, 0, 0) for _ in self.lv_list]
        for lv_idx, lv in enumerate(self.lv_list):
            if lv not in inp:
                if lv_idx == 0:
                    raise CChanException(f"最高级别{lv}没有传入数据", ErrCode.NO_DATA)
                continue
            for klu in inp[lv]:
                klu.kl_type = lv
            assert isinstance(inp[lv], list)
            self.add_lv_iter(lv, iter(inp[lv]))
        for _ in self.load_iterator(lv_idx=0, parent_klu=None, step=False):
            ...
        if not self.conf.trigger_step:  # 非回放模式全部算完之后才算一次中枢和线段
            for lv in self.lv_list:
                self.kl_datas[lv].cal_seg_and_zs()

    def init_lv_klu_iter(self, stockapi_cls):
        # 为了跳过一些获取数据失败的级别
        lv_klu_iter = []
        valid_lv_list = []
        for lv in self.lv_list:
            try:
                lv_klu_iter.append(self.get_load_stock_iter(stockapi_cls, lv))
                valid_lv_list.append(lv)
            except CChanException as e:
                if e.errcode == ErrCode.SRC_DATA_NOT_FOUND and self.conf.auto_skip_illegal_sub_lv:
                    if self.conf.print_warning:
                        print(f"[WARNING-{self.code}]{lv}级别获取数据失败，跳过")
                    del self.kl_datas[lv]
                    continue
                raise e
        self.lv_list = valid_lv_list
        return lv_klu_iter

    def GetStockAPI(self):
        _dict = {}
        if self.data_src == DATA_SRC.BAO_STOCK:
            _dict[DATA_SRC.BAO_STOCK] = CBaoStock
        elif self.data_src == DATA_SRC.CCXT:
            _dict[DATA_SRC.CCXT] = CCXT
        elif self.data_src == DATA_SRC.CSV:
            _dict[DATA_SRC.CSV] = CSV_API
        elif self.data_src == DATA_SRC.AKSHARE:
            _dict[DATA_SRC.AKSHARE] = CAkshare
        if self.data_src in _dict:
            return _dict[self.data_src]
        assert isinstance(self.data_src, str)
        if self.data_src.find("custom:") < 0:
            raise CChanException("load src type error", ErrCode.SRC_DATA_TYPE_ERR)
        package_info = self.data_src.split(":")[1]
        package_name, cls_name = package_info.split(".")
        import importlib
        module = importlib.import_module(f"DataAPI.{package_name}")
        return getattr(module, cls_name)

    def load(self, step=False):
        stockapi_cls = self.GetStockAPI()
        try:
            stockapi_cls.do_init()
            for lv_idx, klu_iter in enumerate(self.init_lv_klu_iter(stockapi_cls)):
                self.add_lv_iter(lv_idx, klu_iter)
            self.klu_cache: List[Optional[CKLine_Unit]] = [None for _ in self.lv_list]
            self.klu_last_t = [CTime(1980, 1, 1, 0, 0) for _ in self.lv_list]

            yield from self.load_iterator(lv_idx=0, parent_klu=None, step=step)  # 计算入口
            if not step:  # 非回放模式全部算完之后才算一次中枢和线段
                for lv in self.lv_list:
                    self.kl_datas[lv].cal_seg_and_zs()
        except Exception:
            raise
        finally:
            stockapi_cls.do_close()
        if len(self[0]) == 0:
            raise CChanException("最高级别没有获得任何数据", ErrCode.NO_DATA)

    def set_klu_parent_relation(self, parent_klu, kline_unit, cur_lv, lv_idx):
        if self.conf.kl_data_check and kltype_lte_day(cur_lv) and kltype_lte_day(self.lv_list[lv_idx-1]):
            self.check_kl_consitent(parent_klu, kline_unit)
        parent_klu.add_children(kline_unit)
        kline_unit.set_parent(parent_klu)

    def add_new_kl(self, cur_lv: KL_TYPE, kline_unit):
        try:
            self.kl_datas[cur_lv].add_single_klu(kline_unit)
        except Exception:
            if self.conf.print_err_time:
                print(f"[ERROR-{self.code}]在计算{kline_unit.time}K线时发生错误!")
            raise

    def try_set_klu_idx(self, lv_idx: int, kline_unit: CKLine_Unit):
        if kline_unit.idx >= 0:
            return
        if len(self[lv_idx]) == 0:
            kline_unit.set_idx(0)
        else:
            kline_unit.set_idx(self[lv_idx][-1][-1].idx + 1)

    def load_iterator(self, lv_idx, parent_klu, step):
        # K线时间天级别以下描述的是结束时间，如60M线，每天第一根是10点30的
        # 天以上是当天日期
        cur_lv = self.lv_list[lv_idx]
        pre_klu = self[lv_idx][-1][-1] if len(self[lv_idx]) > 0 and len(self[lv_idx][-1]) > 0 else None
        while True:
            if self.klu_cache[lv_idx]:
                kline_unit = self.klu_cache[lv_idx]
                assert kline_unit is not None
                self.klu_cache[lv_idx] = None
            else:
                try:
                    kline_unit = self.get_next_lv_klu(lv_idx)
                    self.try_set_klu_idx(lv_idx, kline_unit)
                    if not kline_unit.time > self.klu_last_t[lv_idx]:
                        raise CChanException(f"kline time err, cur={kline_unit.time}, last={self.klu_last_t[lv_idx]}, or refer to quick_guide.md, try set auto=False in the CTime returned by your data source class", ErrCode.KL_NOT_MONOTONOUS)
                    self.klu_last_t[lv_idx] = kline_unit.time
                except StopIteration:
                    break

            if parent_klu and kline_unit.time > parent_klu.time:
                self.klu_cache[lv_idx] = kline_unit
                break
            kline_unit.set_pre_klu(pre_klu)
            pre_klu = kline_unit
            self.add_new_kl(cur_lv, kline_unit)
            if parent_klu:
                self.set_klu_parent_relation(parent_klu, kline_unit, cur_lv, lv_idx)
            if lv_idx != len(self.lv_list)-1:
                for _ in self.load_iterator(lv_idx+1, kline_unit, step):
                    ...
                self.check_kl_align(kline_unit, lv_idx)
            if lv_idx == 0 and step:
                yield self

    def check_kl_consitent(self, parent_klu, sub_klu):
        if parent_klu.time.year != sub_klu.time.year or \
           parent_klu.time.month != sub_klu.time.month or \
           parent_klu.time.day != sub_klu.time.day:
            self.kl_inconsistent_detail[str(parent_klu.time)].append(sub_klu.time)
            if self.conf.print_warning:
                print(f"[WARNING-{self.code}]父级别时间是{parent_klu.time}，次级别时间却是{sub_klu.time}")
            if len(self.kl_inconsistent_detail) >= self.conf.max_kl_inconsistent_cnt:
                raise CChanException(f"父&子级别K线时间不一致条数超过{self.conf.max_kl_inconsistent_cnt}！！", ErrCode.KL_TIME_INCONSISTENT)

    def check_kl_align(self, kline_unit, lv_idx):
        if self.conf.kl_data_check and len(kline_unit.sub_kl_list) == 0:
            self.kl_misalign_cnt += 1
            if self.conf.print_warning:
                print(f"[WARNING-{self.code}]当前{kline_unit.time}没在次级别{self.lv_list[lv_idx+1]}找到K线！！")
            if self.kl_misalign_cnt >= self.conf.max_kl_misalgin_cnt:
                raise CChanException(f"在次级别找不到K线条数超过{self.conf.max_kl_misalgin_cnt}！！", ErrCode.KL_DATA_NOT_ALIGN)

    def __getitem__(self, n) -> CKLine_List:
        if isinstance(n, KL_TYPE):
            return self.kl_datas[n]
        elif isinstance(n, int):
            return self.kl_datas[self.lv_list[n]]
        else:
            raise CChanException("unspoourt query type", ErrCode.COMMON_ERROR)

    def get_bsp(self, idx=None) -> List[CBS_Point]:
        print('[deprecated] use get_latest_bsp instead')
        if idx is not None:
            return self[idx].bs_point_lst.getSortedBspList()
        assert len(self.lv_list) == 1
        return self[0].bs_point_lst.getSortedBspList()

    def get_latest_bsp(self, idx=None, number=1) -> List[CBS_Point]:
        # number=0则取全部bsp，从最新到最旧排序
        if idx is not None:
            return self[idx].bs_point_lst.get_latest_bsp(number)
        assert len(self.lv_list) == 1
        return self[0].bs_point_lst.get_latest_bsp(number)

    def chan_dump_pickle(self, file_path):
        _pre_limit = sys.getrecursionlimit()
        sys.setrecursionlimit(0x100000)
        for kl_list in self.kl_datas.values():
            for klc in kl_list.lst:
                for klu in klc.lst:
                    klu.pre = None
                    klu.next = None
                klc.set_pre(None)
                klc.set_next(None)
            for bi in kl_list.bi_list:
                bi.pre = None
                bi.next = None
            for seg in kl_list.seg_list:
                seg.pre = None
                seg.next = None

            for segseg in kl_list.segseg_list:
                segseg.pre = None
                segseg.next = None

        with open(file_path, "wb") as f:
            pickle.dump(self, f)

        sys.setrecursionlimit(_pre_limit)
        self.chan_pickle_restore()

    @staticmethod
    def chan_load_pickle(file_path) -> 'CChan':
        with open(file_path, "rb") as f:
            chan = pickle.load(f)
        chan.chan_pickle_restore()

        return chan

    def chan_pickle_restore(self):
        for kl_list in self.kl_datas.values():
            last_klu = None
            last_klc = None
            last_bi = None
            last_seg = None
            last_segseg = None
            for klc in kl_list.lst:
                for klu in klc.lst:
                    klu.pre = last_klu
                    if last_klu:
                        last_klu.next = klu
                    last_klu = klu
                klc.set_pre(last_klc)
                if last_klc:
                    last_klc.set_next(klc)
                last_klc = klc
            for bi in kl_list.bi_list:
                bi.pre = last_bi
                if last_bi:
                    last_bi.next = bi
                last_bi = bi
            for seg in kl_list.seg_list:
                seg.pre = last_seg
                if last_seg:
                    last_seg.next = seg
                last_seg = seg
            for segseg in kl_list.segseg_list:
                segseg.pre = last_segseg
                if last_segseg:
                    last_segseg.next = segseg
                last_segseg = segseg


# ==================== GUI代码 ====================



def format_stock_code(code):
    """
    将股票代码格式化为 baostock 要求的格式 (sh.xxxxxx 或 sz.xxxxxx)
    """
    if code.startswith(('sh.', 'sz.')):
        return code
    if code.startswith('6'):
        return f"sh.{code}"
    else:
        return f"sz.{code}"


def get_tradable_stocks():
    """
    获取所有可交易的A股股票列表（使用 baostock）
    """
    try:
        lg = bs.login()
        if lg.error_code != '0':
            print(f"baostock login failed: {lg.error_msg}")
            return pd.DataFrame()

        # 如果今天是周末，尝试获取最近一个交易日的股票列表
        now = datetime.now()
        stock_list = []
        rs = None
        
        # 尝试最近 7 天，直到找到有数据的日期
        for i in range(7):
            target_date = (now - timedelta(days=i)).strftime("%Y-%m-%d")
            rs = bs.query_all_stock(day=target_date)
            if rs.error_code == '0' and rs.next():
                # 找到了有数据的日期
                stock_list.append(rs.get_row_data())
                while rs.next():
                    stock_list.append(rs.get_row_data())
                print(f"成功获取 {target_date} 的股票列表，共 {len(stock_list)} 只")
                break
        
        bs.logout()

        if not stock_list:
            print("无法获取任何日期的股票列表")
            return pd.DataFrame()

        df = pd.DataFrame(stock_list, columns=rs.fields)
        
        # 过滤条件
        # 1. 只保留沪深A股
        df = df[df['code'].str.startswith(('sh.60', 'sz.00', 'sz.30'))]
        
        # 为了保持界面一致性，我们给它加上 '名称', '最新价', '涨跌幅' 等列
        # baostock query_all_stock 返回 ['code', 'tradeStatus', 'code_name']
        df.rename(columns={'code': '代码', 'code_name': '名称'}, inplace=True)
        df['最新价'] = 0.0
        df['涨跌幅'] = 0.0
        
        return df[['代码', '名称', '最新价', '涨跌幅']].reset_index(drop=True)
    except Exception as e:
        print(f"获取股票列表过程中发生异常: {e}")
        traceback.print_exc()
        return pd.DataFrame()


class ScanThread(QThread):
    """
    批量扫描股票的后台线程

    在独立线程中遍历股票列表，对每只股票进行缠论分析，
    检测最近3天内是否出现买点。

    Signals:
        progress: (int, int, str) 当前进度、总数、当前股票信息
        found_signal: (dict) 发现买点时发出，包含股票详情和 CChan 对象
        finished: (int, int) 扫描完成，返回成功数和失败数
        log_signal: (str) 日志消息
    """
    progress = pyqtSignal(int, int, str)
    found_signal = pyqtSignal(dict)
    finished = pyqtSignal(int, int)
    log_signal = pyqtSignal(str)

    def __init__(self, stock_list, config, days=365):
        """
        初始化扫描线程

        Args:
            stock_list: pd.DataFrame, 待扫描的股票列表
            config: CChanConfig, 缠论配置
            days: int, 获取多少天的历史数据，默认365天
        """
        super().__init__()
        self.stock_list = stock_list
        self.config = config
        self.days = days
        self.is_running = True

    def stop(self):
        """停止扫描，设置标志位让 run() 循环退出"""
        self.is_running = False

    def run(self):
        """
        线程主函数，遍历股票列表进行缠论分析

        扫描逻辑:
            1. 跳过无K线数据的股票
            2. 跳过停牌超过15天的股票
            3. 检测最近3天内是否出现买点
            4. 发现买点时通过 found_signal 发出通知
        """
        begin_time = (datetime.now() - timedelta(days=self.days)).strftime("%Y-%m-%d")
        end_time = datetime.now().strftime("%Y-%m-%d")
        total = len(self.stock_list)
        success_count = 0
        fail_count = 0

        for idx, row in self.stock_list.iterrows():
            if not self.is_running:
                break

            code = row['代码']
            name = row['名称']
            self.progress.emit(idx + 1, total, f"{code} {name}")
            self.log_signal.emit(f"🔍 扫描 {code} {name}...")

            try:
                chan = CChan(
                    code=code,
                    begin_time=begin_time,
                    end_time=end_time,
                    data_src=DATA_SRC.BAO_STOCK,
                    lv_list=[KL_TYPE.K_DAY],
                    config=self.config,
                    autype=AUTYPE.QFQ,
                )

                # 检查最近15天是否有数据
                if len(chan[0]) == 0:
                    fail_count += 1
                    self.log_signal.emit(f"⏭️ {code} {name}: 无K线数据")
                    continue
                last_klu = chan[0][-1][-1]
                last_time = last_klu.time
                last_date = datetime(last_time.year, last_time.month, last_time.day)
                if (datetime.now() - last_date).days > 15:
                    fail_count += 1
                    self.log_signal.emit(f"⏸️ {code} {name}: 停牌超过15天")
                    continue

                success_count += 1

                # 检查是否有买点（只找最近3天内出现的买点）
                bsp_list = chan.get_latest_bsp(number=0)
                cutoff_date = datetime.now() - timedelta(days=3)
                buy_points = [
                    bsp for bsp in bsp_list
                    if bsp.is_buy and datetime(bsp.klu.time.year, bsp.klu.time.month, bsp.klu.time.day) >= cutoff_date
                ]

                if buy_points:
                    # 获取最近的买点
                    latest_buy = buy_points[0]
                    self.log_signal.emit(f"✅ {code} {name}: 发现买点 {latest_buy.type2str()}")
                    self.found_signal.emit({
                        'code': code,
                        'name': name,
                        'price': row['最新价'],
                        'change': row['涨跌幅'],
                        'bsp_type': latest_buy.type2str(),
                        'bsp_time': str(latest_buy.klu.time),
                        'chan': chan,
                    })
                else:
                    self.log_signal.emit(f"➖ {code} {name}: 无近期买点")
            except Exception as e:
                fail_count += 1
                self.log_signal.emit(f"❌ {code} {name}: {str(e)[:50]}")
                continue

        self.finished.emit(success_count, fail_count)


class SingleAnalysisThread(QThread):
    """
    单只股票分析的后台线程

    用于分析用户手动输入的股票代码，避免阻塞 UI。

    Signals:
        finished: (CChan) 分析完成，返回 CChan 对象
        error: (str) 分析出错时返回错误信息
    """
    finished = pyqtSignal(object, str)
    error = pyqtSignal(str)

    def __init__(self, code, config, days=365):
        """
        初始化分析线程

        Args:
            code: str, 股票代码（如 '000001'）
            config: CChanConfig, 缠论配置
            days: int, 获取多少天的历史数据
        """
        super().__init__()
        self.code = code
        self.config = config
        self.days = days

    def run(self):
        """执行缠论分析，完成后通过信号返回结果"""
        try:
            begin_time = (datetime.now() - timedelta(days=self.days)).strftime("%Y-%m-%d")
            end_time = datetime.now().strftime("%Y-%m-%d")
            formatted_code = format_stock_code(self.code)
            
            print(f"开始分析股票: {formatted_code}, 周期: {begin_time} 到 {end_time}")

            # 获取股票名称
            stock_name = ""
            bs.login()
            rs = bs.query_stock_basic(code=formatted_code)
            if rs.error_code == '0' and rs.next():
                # query_stock_basic 返回: code, code_name, ipoDate, outDate, type, status
                stock_name = rs.get_row_data()[1]
            bs.logout()

            chan = CChan(
                code=formatted_code,
                begin_time=begin_time,
                end_time=end_time,
                data_src=DATA_SRC.BAO_STOCK,
                lv_list=[KL_TYPE.K_DAY],
                config=self.config,
                autype=AUTYPE.QFQ,
            )
            
            if not chan[0]:
                print(f"分析完成但未获取到 K 线数据: {formatted_code}")
                self.error.emit(f"未获取到 {formatted_code} 的 K 线数据，请检查代码或时间范围")
            else:
                print(f"分析完成, 获取到 {len(chan[0])} 根 K 线: {formatted_code}")
                self.finished.emit(chan, stock_name)
        except Exception as e:
            print(f"分析过程中发生异常: {e}")
            traceback.print_exc()
            self.error.emit(str(e))


class ChanPlotCanvas(QWebEngineView):
    """
    嵌入 PyQt 的 QWebEngineView

    用于在 GUI 中显示 pyecharts 分析图表。

    Args:
        parent: 父控件
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(400)

    def clear(self):
        """清空画布内容"""
        self.setHtml("")


class BaoStockGUI(QMainWindow):
    """
    A股缠论买点扫描器主窗口

    主要功能:
        - 批量扫描: 自动获取所有可交易股票，逐一分析寻找买点
        - 单股分析: 手动输入股票代码进行缠论分析
        - 图表显示: 可视化展示K线、笔、线段、中枢、买卖点、MACD

    界面布局:
        - 左侧面板: 扫描控制、单股输入、买点列表、扫描日志
        - 右侧面板: 图表显示区域，支持缩放和导航
    """

    def __init__(self):
        """初始化主窗口"""
        super().__init__()
        self.chan = None  # 当前分析的 CChan 对象
        self.stock_name = "" # 当前分析的股票名称
        self.scan_thread = None  # 批量扫描线程
        self.analysis_thread = None  # 单股分析线程
        self.stock_cache = {}  # 缓存已分析的股票 {code: CChan}
        self.name_cache = {}  # 缓存股票名称 {code: name}
        self.init_ui()

    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle('A股缠论买点扫描器 - Powered by chan.py')
        self.setGeometry(100, 100, 1600, 900)

        # 创建中央 widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 主布局
        main_layout = QHBoxLayout(central_widget)

        # 左侧控制面板和股票列表
        left_panel = self.create_left_panel()

        # 右侧图表区域
        right_panel = self.create_chart_panel()

        # 使用分割器
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([450, 1150])

        main_layout.addWidget(splitter)

        # 状态栏
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage('就绪 - 点击"开始扫描"分析所有股票')

    def create_left_panel(self):
        """创建左侧面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)

        # 扫描控制
        scan_group = QGroupBox("扫描设置")
        scan_layout = QVBoxLayout(scan_group)

        # 笔严格模式
        self.bi_strict_cb = QCheckBox("笔严格模式")
        self.bi_strict_cb.setChecked(True)
        self.bi_strict_cb.stateChanged.connect(self.on_bi_strict_changed)
        scan_layout.addWidget(self.bi_strict_cb)

        # 扫描按钮
        btn_layout = QHBoxLayout()
        self.scan_btn = QPushButton("开始扫描")
        self.scan_btn.clicked.connect(self.start_scan)
        self.scan_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-size: 14px;
                padding: 10px;
                border-radius: 5px;
            }
            QPushButton:hover { background-color: #45a049; }
            QPushButton:disabled { background-color: #cccccc; }
        """)
        btn_layout.addWidget(self.scan_btn)

        self.stop_btn = QPushButton("停止")
        self.stop_btn.clicked.connect(self.stop_scan)
        self.stop_btn.setEnabled(False)
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                font-size: 14px;
                padding: 10px;
                border-radius: 5px;
            }
            QPushButton:hover { background-color: #da190b; }
            QPushButton:disabled { background-color: #cccccc; }
        """)
        btn_layout.addWidget(self.stop_btn)
        scan_layout.addLayout(btn_layout)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        scan_layout.addWidget(self.progress_bar)

        self.progress_label = QLabel("")
        scan_layout.addWidget(self.progress_label)

        layout.addWidget(scan_group)

        # 单只股票分析
        single_group = QGroupBox("单只股票分析")
        single_layout = QVBoxLayout(single_group)

        code_row = QHBoxLayout()
        code_row.addWidget(QLabel("股票代码:"))
        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("如: 000001")
        self.code_input.returnPressed.connect(self.analyze_single)
        code_row.addWidget(self.code_input)

        self.analyze_btn = QPushButton("分析")
        self.analyze_btn.clicked.connect(self.analyze_single)
        code_row.addWidget(self.analyze_btn)
        single_layout.addLayout(code_row)

        layout.addWidget(single_group)

        # 买点股票列表
        list_group = QGroupBox("买点股票列表")
        list_layout = QVBoxLayout(list_group)

        self.stock_table = QTableWidget()
        self.stock_table.setColumnCount(5)
        self.stock_table.setHorizontalHeaderLabels(['代码', '名称', '现价', '涨跌%', '买点'])
        self.stock_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.stock_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.stock_table.cellClicked.connect(self.on_stock_clicked)
        list_layout.addWidget(self.stock_table)

        # 清空按钮
        self.clear_list_btn = QPushButton("清空列表")
        self.clear_list_btn.clicked.connect(self.clear_stock_list)
        list_layout.addWidget(self.clear_list_btn)

        layout.addWidget(list_group)

        # 日志区域
        log_group = QGroupBox("扫描日志")
        log_layout = QVBoxLayout(log_group)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        log_layout.addWidget(self.log_text)

        clear_log_btn = QPushButton("清空日志")
        clear_log_btn.clicked.connect(lambda: self.log_text.clear())
        log_layout.addWidget(clear_log_btn)

        layout.addWidget(log_group)

        return panel

    def create_chart_panel(self):
        """创建右侧图表面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)

        # 绘图配置
        config_layout = QHBoxLayout()

        self.plot_kline_cb = QCheckBox("K线")
        self.plot_kline_cb.setChecked(True)
        self.plot_kline_cb.stateChanged.connect(self.refresh_chart)
        config_layout.addWidget(self.plot_kline_cb)

        self.plot_bi_cb = QCheckBox("笔")
        self.plot_bi_cb.setChecked(True)
        self.plot_bi_cb.stateChanged.connect(self.refresh_chart)
        config_layout.addWidget(self.plot_bi_cb)

        self.plot_seg_cb = QCheckBox("线段")
        self.plot_seg_cb.setChecked(True)
        self.plot_seg_cb.stateChanged.connect(self.refresh_chart)
        config_layout.addWidget(self.plot_seg_cb)

        self.plot_zs_cb = QCheckBox("中枢")
        self.plot_zs_cb.setChecked(True)
        self.plot_zs_cb.stateChanged.connect(self.refresh_chart)
        config_layout.addWidget(self.plot_zs_cb)

        self.plot_bsp_cb = QCheckBox("买卖点")
        self.plot_bsp_cb.setChecked(True)
        self.plot_bsp_cb.stateChanged.connect(self.refresh_chart)
        config_layout.addWidget(self.plot_bsp_cb)

        self.plot_macd_cb = QCheckBox("MACD")
        self.plot_macd_cb.setChecked(True)
        self.plot_macd_cb.stateChanged.connect(self.refresh_chart)
        config_layout.addWidget(self.plot_macd_cb)

        config_layout.addStretch()

        # 刷新按钮
        self.refresh_btn = QPushButton("刷新图表")
        self.refresh_btn.clicked.connect(self.refresh_chart)
        config_layout.addWidget(self.refresh_btn)

        layout.addLayout(config_layout)

        # pyecharts 画布
        self.canvas = ChanPlotCanvas(panel)

        layout.addWidget(self.canvas)

        return panel

    def on_bi_strict_changed(self, state):
        """笔严格模式切换"""
        if self.chan:
            self.analyze_stock(self.chan.code)

    def get_chan_config(self):
        """
        获取缠论分析配置

        Returns:
            CChanConfig: 包含笔严格模式、买卖点类型等配置的对象
        """
        return CChanConfig({
            "bi_strict": self.bi_strict_cb.isChecked(),  # 笔严格模式
            "trigger_step": False,  # 不启用逐步触发模式
            "skip_step": 0,
            "divergence_rate": float("inf"),  # 背驰比率
            "bsp2_follow_1": False,  # 二类买卖点不跟随一类
            "bsp3_follow_1": False,  # 三类买卖点不跟随一类
            "min_zs_cnt": 0,  # 最小中枢数量
            "bs1_peak": False,
            "macd_algo": "peak",  # MACD 算法
            "bs_type": "1,1p,2,2s,3a,3b",  # 启用的买卖点类型
            "print_warning": False,
            "zs_algo": "normal",  # 中枢算法
        })

    def get_plot_config(self):
        """
        获取图表绑定配置

        Returns:
            dict: 包含各图层显示开关的配置字典
        """
        return {
            "plot_kline": self.plot_kline_cb.isChecked(),  # 显示K线
            "plot_kline_combine": True,  # 显示合并K线
            "plot_bi": self.plot_bi_cb.isChecked(),  # 显示笔
            "plot_seg": self.plot_seg_cb.isChecked(),  # 显示线段
            "plot_zs": self.plot_zs_cb.isChecked(),  # 显示中枢
            "plot_macd": self.plot_macd_cb.isChecked(),  # 显示MACD
            "plot_bsp": self.plot_bsp_cb.isChecked(),  # 显示买卖点
        }

    def start_scan(self):
        """开始批量扫描所有可交易股票"""
        self.scan_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.stock_cache.clear()

        self.statusBar.showMessage('正在获取股票列表...')
        QApplication.processEvents()

        # 获取股票列表
        stock_list = get_tradable_stocks()
        if stock_list.empty:
            QMessageBox.warning(self, "警告", "获取股票列表失败")
            self.scan_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
            self.progress_bar.setVisible(False)
            return

        self.statusBar.showMessage(f'获取到 {len(stock_list)} 只可交易股票，开始扫描...')
        self.progress_bar.setMaximum(len(stock_list))

        # 启动扫描线程
        config = self.get_chan_config()
        self.scan_thread = ScanThread(stock_list, config, days=365)
        self.scan_thread.progress.connect(self.on_scan_progress)
        self.scan_thread.found_signal.connect(self.on_buy_point_found)
        self.scan_thread.finished.connect(self.on_scan_finished)
        self.scan_thread.log_signal.connect(self.on_log_message)
        self.scan_thread.start()

    def stop_scan(self):
        """停止扫描"""
        if self.scan_thread:
            self.scan_thread.stop()
        self.statusBar.showMessage('正在停止扫描...')

    def on_scan_progress(self, current, total, stock_info):
        """扫描进度更新"""
        self.progress_bar.setValue(current)
        self.progress_label.setText(f"进度: {current}/{total} - {stock_info}")

    def on_log_message(self, msg):
        """显示日志消息"""
        self.log_text.append(msg)

    def on_buy_point_found(self, data):
        """
        发现买点的回调函数

        Args:
            data: dict, 包含股票代码、名称、价格、买点类型、CChan对象等信息
        """
        row = self.stock_table.rowCount()
        self.stock_table.insertRow(row)
        self.stock_table.setItem(row, 0, QTableWidgetItem(data['code']))
        self.stock_table.setItem(row, 1, QTableWidgetItem(data['name']))
        self.stock_table.setItem(row, 2, QTableWidgetItem(f"{data['price']:.2f}"))
        self.stock_table.setItem(row, 3, QTableWidgetItem(f"{data['change']:.2f}%"))
        self.stock_table.setItem(row, 4, QTableWidgetItem(f"{data['bsp_type']} ({data['bsp_time']})"))

        # 缓存 chan 对象和名称
        self.stock_cache[data['code']] = data['chan']
        self.name_cache[data['code']] = data['name']

    def on_scan_finished(self, success_count, fail_count):
        """扫描完成"""
        self.scan_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.progress_bar.setVisible(False)
        found_count = self.stock_table.rowCount()
        self.statusBar.showMessage(f'扫描完成: 成功{success_count}只, 跳过{fail_count}只, 发现{found_count}只买点股票')
        self.progress_label.setText(f"完成: 成功{success_count}, 跳过{fail_count}, 买点{found_count}")

    def on_stock_clicked(self, row, col):
        """点击股票列表"""
        code = self.stock_table.item(row, 0).text()
        name = self.stock_table.item(row, 1).text()

        if code in self.stock_cache:
            self.chan = self.stock_cache[code]
            self.stock_name = name
            self.plot_chart()
            self.statusBar.showMessage(f'显示: {code} {name}')
        else:
            # 重新分析
            self.analyze_stock(code)

    def analyze_single(self):
        """分析单只股票"""
        code = self.code_input.text().strip()
        if not code:
            QMessageBox.warning(self, "警告", "请输入股票代码")
            return
        self.analyze_stock(code)

    def analyze_stock(self, code):
        """分析指定股票"""
        self.analyze_btn.setEnabled(False)
        self.statusBar.showMessage(f'正在分析 {code}...')

        config = self.get_chan_config()
        self.analysis_thread = SingleAnalysisThread(code, config, days=365)
        self.analysis_thread.finished.connect(self.on_analysis_finished)
        self.analysis_thread.error.connect(self.on_analysis_error)
        self.analysis_thread.start()

    def on_analysis_finished(self, chan, stock_name):
        """单只股票分析完成"""
        self.chan = chan
        self.stock_name = stock_name
        self.analyze_btn.setEnabled(True)
        self.plot_chart()
        self.statusBar.showMessage(f'分析完成: {chan.code} {stock_name}')

    def on_analysis_error(self, error_msg):
        """分析出错"""
        self.analyze_btn.setEnabled(True)
        QMessageBox.critical(self, "分析错误", error_msg)
        self.statusBar.showMessage('分析失败')

    def plot_chart(self):
        """
        绑定当前股票的缠论分析图表

        使用 CPlotDriver 生成图表，显示K线、笔、线段、中枢等元素。
        """
        if not self.chan:
            return

        try:

            plot_config = self.get_plot_config()

            # 获取控件宽度，计算合适的图表尺寸
            canvas_width = self.canvas.width()
            canvas_height = self.canvas.height()

            # 尝试获取股票名称
            stock_name = self.stock_name
            # 如果当前没有名称，从缓存或表格中查找
            if not stock_name:
                for r in range(self.stock_table.rowCount()):
                    if self.stock_table.item(r, 0).text() == self.chan.code or \
                    format_stock_code(self.stock_table.item(r, 0).text()) == self.chan.code:
                        stock_name = self.stock_table.item(r, 1).text()
                        break
            
            if not stock_name and self.chan.code in self.name_cache:
                stock_name = self.name_cache[self.chan.code]

            # 标题: 股票名称-周期名称
            period_name = "日线"  # 默认为日线，如果是多周期可以根据 lv_list 判断
            if self.chan.lv_list[0] == KL_TYPE.K_DAY:
                period_name = "日线"
            elif self.chan.lv_list[0] == KL_TYPE.K_60M:
                period_name = "60分钟"
            # ... 其他周期可以在此添加

            title = f"{stock_name}-{period_name}" if stock_name else f"{self.chan.code}-{period_name}"

            plot_para = {
                "figure": {
                    "x_range": 200,
                    "w": canvas_width,
                    "h": canvas_height,
                },
                "title": title
            }

            plot_driver = CPlotDriver(self.chan, plot_config=plot_config, plot_para=plot_para)

            # 获取 pyecharts 生成的 HTML 并加载到 QWebEngineView
            html_content = plot_driver.figure.render_embed()
            
            # 注入 JS 实现双击显示 tooltip
            js_patch = """
            <script>
            setTimeout(function() {
                var chartDoms = document.getElementsByClassName('chart-container');
                for (var i = 0; i < chartDoms.length; i++) {
                    var chart = echarts.getInstanceByDom(chartDoms[i]);
                    if (chart) {
                        chartDoms[i].ondblclick = function() {
                            var chartInstance = echarts.getInstanceByDom(this);
                            var options = chartInstance.getOption();
                            var isShow = options.tooltip[0].show;
                            chartInstance.setOption({
                                tooltip: { show: !isShow }
                            });
                        };
                    }
                }
            }, 500);
            </script>
            """
            if html_content:
                html_content += js_patch
                print(f"成功生成图表 HTML，长度: {len(html_content)}")
                self.canvas.setHtml(html_content)
            else:
                print("生成图表 HTML 为空")
                QMessageBox.warning(self, "图表错误", "生成图表内容为空")
        except Exception as e:
            print(f"图表渲染失败: {e}")
            traceback.print_exc()
            QMessageBox.critical(self, "绑定错误", str(e))

    def refresh_chart(self):
        """刷新图表"""
        self.plot_chart()

    def clear_stock_list(self):
        """清空股票列表"""
        self.stock_table.setRowCount(0)
        self.stock_cache.clear()
        self.statusBar.showMessage('列表已清空')


def main():
    """程序入口函数，创建并运行 GUI 应用"""
    # 彻底禁用硬件加速，强制使用软件渲染
    os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--disable-gpu --disable-software-rasterizer --disable-gpu-compositing"
    os.environ["QT_OPENGL"] = "software"
    
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # 使用 Fusion 风格，跨平台一致性好

    window = BaoStockGUI()
    window.show()

    sys.exit(app.exec())


if __name__ == '__main__':
    main()
