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
