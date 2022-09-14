from .contents.data.ar import *
from .contents.data.tools import *
from ggdb.models import AccountRatio

ar = AccountRatio.objects.get(name='ChangeInAsset')
self = ArSeries(
    ar_syntax = ar.syntax,
    change_in = ar.changeIn,
    oc = 'CFS'
)
stock_code = '263750'
ts = self.time_series(stock_code)

tp = ts.fqe.to_list()[-1]

cs = self.cross_section('KOSDAQ', tp)
