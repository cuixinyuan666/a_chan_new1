import inspect
from typing import Dict, List, Literal, Optional, Tuple, Union

from pyecharts import options as opts
from pyecharts.charts import Bar, Grid, Kline, Line, Scatter
from pyecharts.commons.utils import JsCode

from Chan import CChan
from Common.CEnum import BI_DIR, FX_TYPE, KL_TYPE, KLINE_DIR, TREND_TYPE
from Common.ChanException import CChanException, ErrCode
from Common.CTime import CTime
from Math.Demark import T_DEMARK_INDEX, CDemarkEngine

from .PlotMeta import CBi_meta, CChanPlotMeta, CZS_meta


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
