from .contents.fa_ts import *
# from ggdb.models import *

acnt_nm = 'ProfitLoss'
oc = 'CFS'
stock_code = '005930'

self = FaTs(acnt_nm, oc, stock_code)

# update_fa_info
# - fa
# - fa path


fa_info = {
    'nm': self.fa.accountNm,
    'lk': self.fa.labelKor,
    'path': ' / '.join([
        fa.labelKor.replace('[abstract]','').strip()
        for fa in get_fa_path(self.fa, [])
    ])
}

# update_graph_data
is_big_gap = self.ts.fqe - self.ts.fqe.shift(1) > '95 days'
self.ts['growth'] = (self.ts.value / self.ts.value.shift(1) - 1) * 100
self.ts.growth.loc[is_big_gap] = None

x = self.ts.fqe.to_json(orient='records')
y_line = self.ts.value.to_json(orient='records')
y_bar = self.ts.growth.to_json(orient='records')
