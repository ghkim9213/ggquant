from .tools import *

from dashboard.models import FaCrossSection
from dashboard.models import FaCsSourceNotRegisteredError
from dashboard.models import FaTimeSeries
from ggdb.batchtools.fa_cs import FaCrossSectionManager
from ggdb.models import Corp
from ggdb.models import FsAccount
from ggdb.models import FsAccountLite
from ggdb.models import FsDetail

import pandas as pd

class FaSeries:
    def __init__(self, acnt_nm, oc):
        self.acnt_nm = acnt_nm
        self.oc = oc
        self.fa, self.created = FsAccountLite.objects.get_or_create(
            name = acnt_nm,
            oc = oc
        )

    def time_series(self, stock_code):
        corp = Corp.objects.get(stockCode=stock_code)
        ts = FaTimeSeries(fa=self.fa, corp=corp)
        return ts.obs

    def cross_section(self, mkt, tp):
        if not self.fa.cs.exists():
            facsm = FaCrossSectionManager()
            facsm.update(self.fa)

        cs = FaCrossSection.objects.get(
            fa = self.fa,
            market = mkt,
            tp = tp.date(),
        )
        return cs.obs
