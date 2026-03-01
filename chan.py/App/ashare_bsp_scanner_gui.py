"""
A股缠论买点扫描器 - Powered by chan.py

功能说明:
    - 批量扫描A股市场，自动识别近期出现买点的股票
    - 支持单只股票的缠论分析和图表展示
    - 可视化显示K线、笔、线段、中枢、买卖点、MACD等

数据来源:
    - 使用 baostock 获取A股实时行情和历史K线数据

过滤规则:
    - 只保留沪深A股 (60, 00, 30开头)

依赖:
    - PyQt6: GUI框架
    - pyecharts: 图表绑定
    - baostock: A股数据接口
    - chan.py: 缠论分析核心库

使用方法:
    python App/ashare_bsp_scanner_gui.py
"""
import sys
from pathlib import Path

# 将项目根目录加入路径，以便导入 chan.py 核心模块
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from datetime import datetime, timedelta

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

from Chan import CChan
from ChanConfig import CChanConfig
from Common.CEnum import AUTYPE, DATA_SRC, KL_TYPE


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
        import traceback
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
            import traceback
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
            from Plot.PlotDriver import CPlotDriver

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
            import traceback
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
    import os
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
