from ggdb.models import Fs
from ggdb.models import FsAccountLite
from ggdb.models import FsDetail
from dashboard.models import FaCrossSection
from django.db.models import Max
from itertools import islice

import datetime
import pandas as pd

class FaCrossSectionManager:
    def __init__(self):
        self.today = datetime.datetime.today()
        self.tp_all = sorted(list(set(
            Fs.objects.all()
            .values_list('fqe', flat=True)
        )))
        self.BATCH_SIZE = int(1e5)

    def batch(self, model, data, batch_size):
        while True:
            batch = list(islice(data, batch_size))
            if not batch:
                break
            model.objects.bulk_create(batch, batch_size)
            data = data[batch_size:]

    def update(self, fa):
        if not fa.batch:
            return None

        print(f"updating cross section for {fa.name} {fa.oc}...")
        facs_all = fa.cs.all()
        comb2facs = {(
                facs.market,
                facs.tp
            ):facs for facs in facs_all
        }
        df = fa.query_panel()
        if len(df) == 0:
            fa.delete()
            return None

        new_facs_id = FaCrossSection.objects.aggregate(Max('id'))['id__max'] + 1
        facs_created_all = []
        m2m_created_all = []
        for mkt in ['KOSPI', 'KOSDAQ']:
            for tp in self.tp_all:
                comb = (mkt, tp)
                facs = comb2facs.pop(comb, None)

                fqe_lte = pd.Timestamp(tp)
                fqe_gte = fqe_lte - pd.DateOffset(years=2)
                fdid_all = (
                    df.loc[
                        (df.market == mkt)
                        & (df.fqe >= fqe_gte)
                        & (df.fqe <= fqe_lte)
                    ].id.to_list()
                )

                if facs:
                    old_fdid_all = (
                        facs.source.all()
                        .values_list('id', flat=True)
                    )
                    fdid_added = [id for id in fdid_all if id not in old_fdid_all]
                    fdid_removed = [id for id in old_fdid_all if id not in fdid_all]
                    if len(fdid_added) > 0:
                        m2m_created_all += [(
                            FaCrossSection.source
                            .through(
                                facrosssection_id = facs.id,
                                fsdetail_id = fdid
                            )
                        ) for fdid in fdid_added]
                    if len(fdid_removed) > 0:
                        fd_removed = FsDetail.objects.filter(id__in=fdid_removed)
                        facs.source.remove(*fd_removed)
                else:
                    facs_created_all.append(FaCrossSection(
                        id = new_facs_id,
                        fa = fa,
                        market = mkt,
                        tp = tp,
                    ))

                    m2m_created_all += [(
                        FaCrossSection.source
                        .through(
                            facrosssection_id = new_facs_id,
                            fsdetail_id = fdid
                        )
                    ) for fdid in fdid_all]
                    new_facs_id += 1
        self.batch(
            model = FaCrossSection,
            data = facs_created_all,
            batch_size = self.BATCH_SIZE,
        )
        self.batch(
            model = FaCrossSection.source.through,
            data = m2m_created_all,
            batch_size = self.BATCH_SIZE,
        )

    def reset(self):
        FaCrossSection.objects.all().delete()
        FaCrossSection.source.through.objects.all().delete()
        fa_all = FsAccountLite.objects.all()
        for fa in fa_all:
            self.update(fa)

    def update_by_new_fd(self):
        fd_created_all = FsDetails.objects.filter(
            createdAt = self.today,
        ).select_related('account', 'fs__type')
        fa_updated = []
        for fd in fd_created_all:
            acnt_nm = fd.account.accountNm
            oc = fd.fs.type.oc
            try:
                fa = FsAccountLite.objects.get(
                    name = acnt_nm,
                    oc = oc
                )
                if fa not in fa_updated:
                    fa_updated.append(fa)
            except: # what kind of error in this cas?
                continue
        for fa in fa_updated:
            self.update(fa)
