#!/bin/bash

# 调度脚本：计算股票市值分位数

echo "开始计算股票市值分位数..."

# 进入脚本所在目录
cd "$(dirname "$0")"

# 运行市值查询脚本
python query_marketvalue.py

echo "\n计算完成！"

# 运行交易信息计算脚本
echo "\n开始计算交易信息指标..."
python CalTradeInfo.py

echo "\n所有计算完成！"
