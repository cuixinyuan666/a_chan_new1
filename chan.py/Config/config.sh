#!/bin/bash

# 缠论框架配置脚本

# 加载配置文件
if [ -f "$(dirname "$0")/demo_config.yaml" ]; then
    echo "加载配置文件: $(dirname "$0")/demo_config.yaml"
else
    echo "警告: 配置文件不存在，使用默认配置"
fi

# 设置环境变量
export CHAN_DATA_API_DEFAULT="bao_stock"
export CHAN_DATABASE_DEFAULT="sqlite"
export CHAN_TRADE_ENGINE="futu"
export CHAN_MODEL_DEFAULT="xgboost"
export CHAN_PLOT_ENGINE="pyecharts"
export CHAN_LOG_LEVEL="INFO"

# 打印配置信息
echo "=== 缠论框架配置信息 ==="
echo "默认数据源: ${CHAN_DATA_API_DEFAULT}"
echo "默认数据库: ${CHAN_DATABASE_DEFAULT}"
echo "交易引擎: ${CHAN_TRADE_ENGINE}"
echo "默认模型: ${CHAN_MODEL_DEFAULT}"
echo "绘图引擎: ${CHAN_PLOT_ENGINE}"
echo "日志级别: ${CHAN_LOG_LEVEL}"
echo "======================="

# 检查必要的目录
mkdir -p ../data
mkdir -p ../models
mkdir -p ../output
mkdir -p ../logs

echo "必要目录已创建完成"