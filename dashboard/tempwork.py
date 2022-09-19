from ggdb.models import FsAccountLite

fa_unbatch = FsAccountLite.objects.filter(batch=False)

for fa in fa_unbatch:
    fa.delete()
