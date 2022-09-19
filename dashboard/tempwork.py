from .contents.data.ar import *
from ggdb.models import AccountRatio

ar_all = AccountRatio.objects.filter(name='ReturnOnEquity')
ar_all_d = {ar.oc: ar for ar in ar_all}
oc = 'CFS'
ar = ar_all_d[oc]
r = ar.to_request()
ars = ArSeries(
    operation = r['operation'],
    change_in = r['changeIn'],
    items = r['items']
)
