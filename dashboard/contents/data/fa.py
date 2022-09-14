from .tools import *

from dashboard.models import FaCrossSection
from dashboard.models import FaTimeSeries
from ggdb.models import Corp
from ggdb.models import FsAccount
from ggdb.models import FsDetail

import pandas as pd

class FaSeries:
    def __init__(self, acnt_nm, oc):
        self.acnt_nm = acnt_nm
        self.oc = oc

        # get ft_div
        fa = FsAccount.objects.filter(
            accountNm = self.acnt_nm,
            type__oc = self.oc,
        ).first()
        self.label_kor = fa.labelKor
        self.ft_div = fa.type.type
        self.path = ' / '.join([
            a.labelKor.replace('[abstract]', '').strip()
            for a in get_fa_path(fa, [])
        ])

        # self.corp = Corp.objects.get(stockCode=stock_code)

    def time_series(self, stock_code):
        ts = FaTimeSeries(self.acnt_nm, self.oc, stock_code)
        return ts.obs

    def cross_section(self, mkt, tp):
        cs = FaCrossSection.objects.get(
            name = self.acnt_nm,
            oc = self.oc,
            market = mkt,
            tp = tp.date(),
        )
        return cs.obs
