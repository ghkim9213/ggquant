from plotly.offline import plot

import plotly.graph_objects as go
import numpy as np
import pandas as pd

class DataVisualizer:
    def __init__(self, s, **kwargs):
        s = s.replace([-np.inf,np.inf],np.nan).dropna()
        bounds = kwargs.pop('bounds', None)
        if bounds != None:
            lb, ub = s.quantile(bounds).tolist()
            s = s[(s>=lb) & (s<ub)]
        self.s = s

    def get_desc(self):
        rename_map = {
            'index': '상장구분',
            'count': '종목수',
            'mean': '평균',
            'std': '표준편차',
            'min': '0.5%',
            '25%': '1분위',
            '50%': '중위',
            '75%': '3분위',
            'max': '99.5%',
        }
        ord = {
            '전체': 0,
            'KOSPI': 1,
            'KOSDAQ': 2,
        }
        desc = pd.concat([
            self.s.groupby('market').describe().T,
            self.s.describe().rename('전체'),
        ], axis=1).T.reset_index().rename(columns=rename_map).round(4)
        return {
            'header': desc.columns.tolist(),
            'rows': sorted(desc.values.tolist(), key=lambda x: ord[x[0]]),
        }

    def get_hist(self):
        fig = go.Figure()
        fig.add_trace(go.Histogram(
            x=self.s.loc[self.s.index.get_level_values('market')=='KOSPI'],
            histnorm='probability',
            name='KOSPI',
        ))
        fig.add_trace(go.Histogram(
            x=self.s.loc[self.s.index.get_level_values('market')=='KOSDAQ'],
            histnorm='probability',
            name='KOSDAQ',
        ))
        fig.update_layout(
            autosize = False,
            width = 500,
            height = 400,
            legend = dict(
                orientation="h",
                yanchor="top",
                y=-.05,
                xanchor="center",
                x=.5
            ),
            margin = dict(l=30,r=   30,b=0,t=0),
            barmode='overlay',
        )
        fig.update_traces(opacity=.75)
        return plot(fig, output_type='div')
