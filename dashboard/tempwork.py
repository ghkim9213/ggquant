from .contents.data.ar import *
from ggdb.models import AccountRatio

ar = AccountRatio.objects.first()
r = ar.to_request()
operation = r['operation']
change_in = r['changeIn']
items = r['items']

ars = ArSeries(operation, change_in, items)
ts = ars.time_series('005930')
tp = ts.fqe.to_list()[-1]
ars.cross_section('KOSPI', tp)
