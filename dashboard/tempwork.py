from ggdb.batchtools.account_ratio import *

import numpy as np

# oc, mkt = 'CFS', 'KOSPI'
# ar = AccountRatio.objects.first()
# lar_data = LatestAccountRatioManager().read_temp(oc,mkt,ar=ar)


# oc, mkt = 'CFS', 'KOSPI'
# ar = AccountRatio.objects.first()
# self = LatestAccountRatioSeries(oc, mkt, ar)
# missings = [d for d in self.cleaned_data if d['value'] == None]
# valid_rows = [d for d in self.cleaned_data if d['value'] != None]

# bounds = kwargs.pop('winsor', None)
# if winsor != None:
#     value_all = [d['value'] for d in valid_rows]
#     np.quantile(value_all)
#     s = (
#         pd.DataFrame.from_records(valid_rows)
#         .set_index(['stock_code', 'corp_name', 'by', 'bq']
#     ).value
#     lb, ub = s.quantile(bounds).tolist()
#     winsor = (s >= lb) & (s <= ub)
