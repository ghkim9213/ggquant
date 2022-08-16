from .viewmanagers.stkrpt import *

corp = Corp.objects.get(stockCode='293490')
ar = AccountRatio.objects.first()
oc = 'CFS'
ar_ts = AccountRatioTimeSeries(corp, ar, oc)
