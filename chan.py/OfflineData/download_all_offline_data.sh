#!/bin/bash

# 调度下载A股，港股，美股所有数据脚本

echo "开始下载离线数据..."

# 进入脚本所在目录
cd "$(dirname "$0")"

# 下载A股数据
echo "\n=== 下载A股数据 ==="
python bao_download.py

# 下载ETF数据
echo "\n=== 下载ETF数据 ==="
python etf_download.py

# 下载港股数据
echo "\n=== 下载港股数据 ==="
python -c "from futu_download import FutuDownload; downloader = FutuDownload(); downloader.download_hk_stock('00700'); downloader.download_hk_stock('00001')"

# 下载美股数据
echo "\n=== 下载美股数据 ==="
python -c "from ak_update import AkUpdate; updater = AkUpdate(); updater.update_usshare('AAPL'); updater.update_usshare('MSFT')"

echo "\n所有数据下载完成！"

# 更新数据信息
echo "\n更新数据信息..."
python -c "from offline_data_util import OfflineDataUtil; util = OfflineDataUtil(); util.create_data_info('ashare'); util.create_data_info('hkshare'); util.create_data_info('usshare'); util.create_data_info('etf')"

echo "\n数据信息更新完成！"
