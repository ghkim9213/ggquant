from .contents.data.account_ratio import AccountRatioSeries

from ggdb.models import Corp, AccountRatio
from scipy.stats import skew

import numpy as np
import pandas as pd

ar_nm = 'CurrentRatio'
oc = 'CFS'
stock_code = '005930'

class Dummy:
    def __init__(self):
        pass

ar_all = AccountRatio.objects.all()

self = Dummy()
self.corp = Corp.objects.get(stockCode=stock_code)
self.ars = AccountRatioSeries(ar_nm, oc, self.corp.market)

# evaluate skewness
# remove outliers
