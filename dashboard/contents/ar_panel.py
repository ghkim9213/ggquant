from .data.account_ratio import AccountRatioSeries

from ggdb.models import Corp, AccountRatio
from plotly.subplots import make_subplots
from scipy.stats import gaussian_kde

import datetime
import numpy as np
import pandas as pd
import plotly.graph_objects as go

class ARPanel:
    def __init__(self, ar_nm, oc, stock_code):
        self.corp = Corp.objects.get(stockCode=stock_code)
        self.ar_lk = AccountRatio.objects.get(name=ar_nm).labelKor
        self.ars = AccountRatioSeries(ar_nm, oc, self.corp.market)
        self.ts = self.ars.get_time_series(self.corp.stockCode)
        self._dateformatter = lambda tp: f"{tp.year}-{str(tp.month).zfill(2)}-{str(tp.day).zfill(2)}"
        self._hex_to_rgba = lambda h, opacity: (
            f"rgba{tuple([int(h.lstrip('#')[i:i+2], 16) for i in (0, 2, 4)] + [opacity])}"
        )
        self._graph_data = None
        self._layout = None
        self._global_props = None
        self._traces = None
        self._frames = None
        self._sliders = None

        # self._table_data = None

    def update_graph_data(self, alpha):
        # reset data for figure
        self._graph_data = {}
        self._layout = None
        self._global_props = {}
        self._traces = None
        self._frames = None

        # update self._graph_data
        bound = [alpha/2, 1-alpha/2]
        gmax, gmin = None, None
        for tp in self.ts.fqe.sort_values():
            cs = self.ars.get_cross_section(tp)
            lb, ub = cs.value.quantile(bound)
            winsor = (cs.value >= lb) & (cs.value <= ub)
            desc = cs[winsor].value.describe().to_dict()
            self._graph_data[tp] = {
                'value': cs.loc[cs.stock_code==self.corp.stockCode].value.values[0],
                **desc,
                'cs': cs[winsor].value.tolist()
            }
            if not gmax:
                gmax = desc['max']
            elif gmax < desc['max']:
                gmax = desc['max']
            if not gmin:
                gmin = desc['min']
            elif gmin > desc['min']:
                gmin = desc['min']
            self._global_props['gmax'] = gmax
            self._global_props['gmin'] = gmin

    def update_layout(self):
        if not self._graph_data:
            raise ValueError('updating graph data should be precede.')
        self._layout = {}

        tp_all = self._graph_data.keys()
        self._global_props['tp_all'] = list(tp_all)
        count_all = [self._graph_data[tp]['count'] for tp in tp_all]
        count_avg = int(sum(count_all)/len(count_all))
        self._global_props['bins'] = np.linspace(
            self._global_props['gmin'],
            self._global_props['gmax'],
            count_avg
        )
        tmax = datetime.datetime.today()
        tmin = list(tp_all)[0]

        # x axis for ts plot
        self._layout['xaxis'] = {
            'anchor': 'y',
            'domain': [0, .65], # size
            'range': [
                self._dateformatter(tmin),
                self._dateformatter(tmax),
            ],
        }

        # x axis for histogram
        self._layout['xaxis2'] = {
            'anchor': 'y2',
            'domain': [.65, 1],
        }

        # y axis for ts plot
        self._layout['yaxis'] = {
            'anchor': 'x',
            'domain': [0, .95],
        }

        # y axis for histogram
        self._layout['yaxis2'] = {
            'anchor': 'x2',
            'domain': [0, .95],
            'matches': 'y', # share y
            'showticklabels': False,
        }

        # set titles for each subplot
        self._layout['annotations'] = [{
            'text': f"{self.ar_lk} 변동",
            'font': {
                'size': 15,
                'color': '#666',
            },
            'showarrow': False,
            'x': 0,
            'xref': 'paper',
            'y': 1,
            'yref': 'paper',
        }, {
            'text': f"횡단면 분포",
            'font': {
                'size': 15,
                'color': '#666',
            },
            'showarrow': False,
            'x': .77,
            'xref': 'paper',
            'y': 1,
            'yref': 'paper',
        }]

        # legends
        self._layout['showlegend'] = True
        self._layout['legend'] = {
            'x': 1,
            'xanchor': 'right',
            'y': .95,
            'yanchor': 'top',
        }


        # if null method
        self._layout['hovermode'] = 'closest'

        # animation controller
        self._layout['updatemenus'] = [{
            'type': 'buttons',
            'buttons': [{
                'label': '재생', # play button
                'method': 'animate',
                'args': [None, {
                    'mode': 'immediate',
                    'fromcurrent': True,
                    'transition': {'duration': 300, 'easing': 'quadratic-in-out'},
                    'frame': {'duration': 500, 'redraw': False},
                }],
            }, {
                'label': '일시정지', # pause button
                'method': 'animate',
                'args': [[None], {
                    'mode': 'immediate',
                    'transition': {'duration': 0},
                    'frame': {'duration': 0, 'redraw': False},
                }]
            }],
            'direction': 'left',
            'pad': {'l': 0, 'b': 100},
            'showactive': False,
            'x': .1,
            'xanchor': 'right',
            'y': 1,
            'yanchor': 'bottom',
        }]

    def update_traces(self):
        if not self._global_props:
            raise ValueError('updating layout should be precede.')
        self._traces = []

        # ts plot
        line_trace = lambda v, hex, opacity, dash: ({
            'type': 'scatter',
            'mode': 'lines',
            'x': self._global_props['tp_all'],
            'xaxis': 'x',
            'y': [self._graph_data[tp][v] for tp in self._global_props['tp_all']],
            'yaxis': 'y',
            'line': {
                'color': self._hex_to_rgba(hex, opacity),
                'dash': dash,
            },
            'showlegend': False
        })
        self._traces += [line_trace(
            'value', '#FF3C3C', 1, None
        )] * 2
        self._traces += [line_trace(
            'mean', '#457CA2', 1, None
        )] * 2
        self._traces += [line_trace(
            '75%', '#457CA2', .5, 'dash'
        )] * 2
        self._traces += [line_trace(
            '50%', '#457CA2', 1, 'dash'
        )] * 2
        self._traces += [line_trace(
            '25%', '#457CA2', .5, 'dash'
        )] * 2

        # set y range
        y_min = min([
            self._graph_data[tp][v]
            for tp in self._global_props['tp_all']
            for v in ['value', 'mean', '25%']
        ])
        y_max = max([
            self._graph_data[tp][v]
            for tp in self._global_props['tp_all']
            for v in ['value', 'mean', '75%']
        ])
        y_decile_size = (y_max - y_min) / 10
        self._layout['yaxis']['range'] = [
            y_min - y_decile_size,
            y_max + y_decile_size
        ]


        # histogram
        latest_tp = self._global_props['tp_all'][-1]
        pm = get_prob_mass(
            self._graph_data[latest_tp]['cs'],
            self._global_props['bins'],
        )
        self._traces += [{
            'type': 'bar',
            'orientation': 'h',
            'x': pm,
            'xaxis': 'x2',
            'y': self._global_props['bins'],
            'yaxis': 'y2',
            'marker': {'color': self._hex_to_rgba('#457CA2', 1)},
            'showlegend': False,
        }]

        # kde on histogram
        lnsp = np.linspace(
            self._global_props['gmin'],
            self._global_props['gmax'],
            len(self._graph_data[latest_tp]['cs'])
        )
        kernel = gaussian_kde(self._graph_data[latest_tp]['cs'])
        kde = kernel(lnsp)
        norm_kde = kde / kde.sum()
        self._traces += [{
            'type': 'scatter',
            'x': norm_kde,
            'xaxis': 'x2',
            'y': lnsp,
            'yaxis': 'y2',
            'line': {'color': self._hex_to_rgba('#457CA2', 1)},
            'fill': 'tozerox',
            'showlegend': False,
        }]

        # markers on histogram
        marker_trace = lambda name, v, hex, opacity, symbol: {
            'name': name,
            'type': 'scatter',
            'mode': 'markers+text',
            'x': [0],
            'xaxis': 'x2',
            'y': [self._graph_data[latest_tp][v]],
            'yaxis': 'y2',
            'marker': {
                'color': self._hex_to_rgba(hex, opacity),
                'size': 10,
                'symbol': symbol,
            },
            'text': [name],
            'textposition': 'middle right',
        }
        self._traces += [marker_trace(
            self.corp.corpName, 'value', '#FF3C3C', 1, None
        )]
        self._traces += [marker_trace(
            f"{self.corp.market} 평균", 'mean', '#457CA2', 1, None
        )]
        self._traces += [marker_trace(
            f"{self.corp.market} 3분위", '75%', '#457CA2', .5, 'triangle-up'
        )]
        self._traces += [marker_trace(
            f"{self.corp.market} 중위", '50%', '#457CA2', 1, 'diamond'
        )]
        self._traces += [marker_trace(
            f"{self.corp.market} 1분위", '25%', '#457CA2', .5, 'triangle-down'
        )]

    def update_frames(self):
        self._frames = []
        marker_frame = lambda tp, name, v, hex, opacity, symbol: ({
            'type': 'scatter',
            'mode': 'markers+text',
            'x': [tp],
            'y': [self._graph_data[tp][v]],
            'marker': {
                'color': self._hex_to_rgba(hex, opacity),
                'size': 10,
                'symbol': symbol,
            },
            'text': name,
            'textposition': 'middle left',
        })
        pmmax = 0
        for tp in self._global_props['tp_all']:
            pm = get_prob_mass(
                self._graph_data[tp]['cs'],
                self._global_props['bins'],
            )
            if pm.max() > pmmax:
                pmmax = pm.max()
            lnsp = np.linspace(
                self._global_props['gmin'],
                self._global_props['gmax'],
                len(self._graph_data[tp]['cs'])
            )
            kernel = gaussian_kde(self._graph_data[tp]['cs'])
            kde = kernel(lnsp)
            norm_kde = kde / kde.sum() #* .3
            self._frames += [{
                'name': self._dateformatter(tp),
                'data': [

                    # ts plot
                    {}, # no update for ts plot
                    marker_frame(
                        tp, self.corp.corpName, 'value', '#FF3C3C', 1, None
                    ),
                    {}, # no update for ts plot
                    marker_frame(
                        tp, f"{self.corp.market} 평균", 'mean', '#457CA2', 1, None
                    ),
                    {}, # no update for ts plot
                    marker_frame(
                        tp, f"{self.corp.market} 3분위", '75%', '#457CA2', .5, 'triangle-up'
                    ),
                    {}, # no update for ts plot
                    marker_frame(
                        tp, f"{self.corp.market} 중위", '50%', '#457CA2', 1, 'diamond'
                    ),
                    {}, # no update for ts plot
                    marker_frame(
                        tp, f"{self.corp.market} 1분위", '25%', '#457CA2', .5, 'triangle-down'
                    ),

                    # histogram
                    {'type': 'bar', 'x': pm},

                    # kde on histogram
                    {'type': 'scatter', 'x': norm_kde, 'y': lnsp},

                    # markers on histogram
                    {'y': [self._graph_data[tp]['value']]},
                    {'y': [self._graph_data[tp]['mean']]},
                    {'y': [self._graph_data[tp]['75%']]},
                    {'y': [self._graph_data[tp]['50%']]},
                    {'y': [self._graph_data[tp]['25%']]},
                ]
            }]
        self._layout['xaxis2']['range'] = [0, pmmax]

    def update_sliders(self):
        steps = []
        for tp in self._global_props['tp_all']:
            steps.append({
                'method': 'animate',
                'label': self._dateformatter(tp),
                'args': [
                    [self._dateformatter(tp)],
                    {
                        'frame': {
                            'duration': 300,
                            'redraw': False,
                        },
                        'mode': 'immediate',
                        'transition': {'duration': 300},
                    },
                ],
            })

        sliders = [{
            'active': len(self._global_props['tp_all'])-1,
            'yanchor': 'bottom',
            'xanchor': 'left',
            'currentvalue': {
                'font': {'size': 20, 'color': '#666'},
                'prefix': '기준일: ',
                'visible': True,
                'xanchor': 'right',
            },
            'transition': {'duration': 300, 'easing': 'cubic-in-out'},
            'pad': {'b': 50, 't': 0, 'l': 0},
            'len': 1,
            'x': 0,
            'y': 1,
            'steps': steps,
        }]
        self._layout['sliders'] = sliders

    def get_figure(self, **kwargs):
        return go.Figure({
            'data': self._traces,
            'layout': self._layout,
            'frames': self._frames,
        })

    def get_table(self):
        table_data = []
        for tp in self.ts.fqe.sort_values(ascending=False):
            val = self.ts.loc[self.ts.fqe == tp].value
            cs = self.ars.get_cross_section(tp)
            cs['rank'] = cs.value.rank(ascending=False, method='min')
            cs['pct'] = cs.value.rank(pct=True, ascending=False, method='min')
            cs['status'] = pd.cut(
                cs.pct,
                bins = [0, .05, .2, .4, .6, .8, .95, 1],
                labels = ['highest', 'higher', 'high', 'mid', 'low', 'lower', 'lowest']
                # labels = ['lowest', 'lower', 'low', 'mid', 'high', 'higher', 'highest']
            )
            d = cs.loc[cs.stock_code==self.corp.stockCode].to_dict(orient='records')[0]
            table_data.append(d)
        return pd.DataFrame.from_records(table_data)

def get_prob_mass(s, bins):
    return np.histogram(s, bins)[0] / len(s)


# def get_gaussian_kde(s, **kwargs):
#     X = np.linspace(min(s), max(s), 100)
#     sig = np.std(s)
#     h = .3
#     gaussian_kernal = lambda z, sig: np.exp(-z**2/(2*sig**2))/(((2*np.pi)**.5)*sig)
#     dist = []
#     for x in X:
#         diffs = [x-k for k in s]
#         fltrd = [gaussian_kernal(d/h, sig) for d in diffs]
#         gaussian_kernal_density = sum(fltrd) / len(s) / h
#         dist.append(gaussian_kernal_density)
#     dist /= sum(dist)
#
#     norm_coef = kwargs.pop('norm_coef', None)
#     if norm_coef:
#         dist *= norm_coef
#     return dist, X
