# from ggdb.models import AccountRatio
# from ggdb.models import Fs
# from ggdb.models import FsAccountLite
from ggdb.models import FsDetail
from dashboard.models import FaRoot
from django.db.models.functions import Trim
from itertools import islice

import time
import datetime
import pandas as pd

class FaRootManager:
    def __init__(self):
        self.today = datetime.datetime.today()
        self.BATCH_SIZE = int(1e5)

    def batch(self, model, data, batch_size):
        while True:
            batch = list(islice(data, batch_size))
            if not batch:
                break
            model.objects.bulk_create(batch, batch_size, ignore_conflicts=True)
            data = data[batch_size:]

    def create(self, fa):
        root, created = FaRoot.objects.get_or_create(fa=fa)
        if not created:
            raise KeyError(f'root for {fa} already exists.')
        self.create_m2m(root)


    def create_m2m(self, root):
        if root.stdVal.exists() or root.nstdVal.exists():
            raise KeyError(f'm2m for {root} already exists.')

        std_id_all = root.fa.values.values_list('id', flat=True)
        nstd_id_all = (
            FsDetail.objects
            .filter(account = None, fs__type = root.fa.type)
            .annotate(lk = Trim('labelKor'))
            .filter(lk__in = root.related_lk_all)
            .values_list('id', flat = True)
        )
        m2m_std_created = [
            FaRoot.stdVal.through(
                faroot_id = root.id,
                fsdetail_id = id
            ) for id in std_id_all
        ]
        m2m_nstd_created = [
            FaRoot.nstdVal.through(
                faroot_id = root.id,
                fsdetail_id = id
            ) for id in nstd_id_all
        ]

        self.batch(
            model = FaRoot.stdVal.through,
            data = new_relation['std_added'],
            batch_size = self.BATCH_SIZE,
        )
        self.batch(
            model = FaRoot.nstdVal.through,
            data = new_relation['nstd_added'],
            batch_size = self.BATCH_SIZE,
        )

    def reset(self):
        FaRoot.objects.all().delete()
        FaRoot.stdVal.through.objects.all().delete()
        FaRoot.nstdVal.through.objects.all().delete()

    def update_daily(self):
        print('updating fa_root...')

        print('...detecting updates')
        fd_created_today = (
            FsDetail.objects
            .filter(createdAt = self.today)
            .annotate(lk = Trim('labelKor'))
        )
        lk2root = self.get_lk_to_root_map()
        m2m_std_created = []
        m2m_nstd_created = []
        for fd in fd_created_today:
            root, std = self.match_fd_to_root(fd, lk2root)
            if root:
                if std:
                    m2m = FaRoot.stdVal.through(
                        faroot_id = root.id,
                        fsdetail_id = fd.id,
                    )
                    m2m_std_created.append(m2m)
                else:
                    m2m = FaRoot.nstdVal.through(
                        faroot_id = root.id,
                        fsdetail_id = fd.id
                    )
                    m2m_nstd_created.append(m2m)

        print('...writing on db')
        self.batch(
            model = FaRoot.stdVal.through,
            data = m2m_std_created,
            batch_size = self.BATCH_SIZE
        )

        self.batch(
            model = FaRoot.nstdVal.through,
            data = m2m_nstd_created,
            batch_size = self.BATCH_SIZE
        )
        print('...complete!')


    def get_lk_to_root_map(self):
        print('...creating lk2root map')
        root_all = FaRoot.objects.all()
        root2lk = {
            root: list(root.related_lk_all)
            for root in root_all
        }
        lk2root = {}
        for root, lklist in lk2root.items():
            for lk in lklist:
                if lk not in lk2root.keys():
                    lk2root[lk] = []
                lk2root[lk].append(root)
        return lk2root

    def match_fd_to_root(self, fd, lk2root):
        if fd.account:
            std = True
            return fd.account, std
        else:
            std = False
            rootlist = lk2root.get(fd.lk)
            if rootlist:
                return list(filter(
                    lambda r: r.fa.type == fd.fs.type,
                    rootlist
                ))[0], std
            else:
                return None, std
