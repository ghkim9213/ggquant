from pandas.tseries.offsets import MonthEnd

import pandas as pd


def prev_yq(pd_tp):
    y = pd_tp.year
    m = pd_tp.month
    prev_m = m - 3
    if prev_m <= 0:
        prev_y = y - 1
        prev_m = prev_m + 12
    else:
        prev_y = y
    return pd.to_datetime(f"{prev_y}{str(prev_m).zfill(2)}", format='%Y%m') + MonthEnd(1)


def next_yq(pd_tp):
    y = pd_tp.year
    m = pd_tp.month
    next_m = m + 3
    if next_m > 12:
        next_y = y + 1
        next_m = next_m - 12
    else:
        next_y = y
    return pd.to_datetime(f"{next_y}{str(next_m).zfill(2)}", format='%Y%m') + MonthEnd(1)

def fill_tgap(ts):
    tmin = ts.fqe.min()
    tmax = ts.fqe.max()
    records = []
    ts_dict = ts.set_index('fqe').value.to_dict()
    tp = tmin
    while tp <= tmax:
        v = ts_dict.pop(tp, None)
        records.append({
            'fqe': tp,
            'value': v,
        })
        tp = next_yq(tp)
    return pd.DataFrame.from_records(records)
