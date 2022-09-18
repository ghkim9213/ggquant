from ggdb.models import Fs
from ggdb.models import FsAccountLite
from ggdb.models import FsDetail
from dashboard.models import FaCrossSection
from itertools import islice

import datetime
import pandas as pd

# FaCrossSection
class FaCrossSectionManager:
    def __init__(self):
        self.today = datetime.datetime.today()

        # OC_ALL = ['CFS', 'OFS']
        MKT_ALL = ['KOSPI', 'KOSDAQ']

        fa_all = FsAccountLite.objects.all()
        tp_all = list(set(
            Fs.objects.all()
            .values_list('fqe', flat=True)
        ))
        self.comb_all = [(
            fa, mkt, tp
            ) for fa in fa_all
            for mkt in MKT_ALL
            for tp in tp_all
        ]

    def update(self, **kwargs):
        reset = kwargs.pop('reset', None)
        if reset:
            # delete all
            print('deleting all from fa_cs...')
            FaCrossSection.objects.all().delete()
            print('...complete!')

        # settings
        print('setting up for update fa_cs...')

        facs_all = FaCrossSection.objects.all()
        comb2facs = {(facs.fa, facs.market, facs.tp): facs for facs in facs_all}

        # loop keys
        if reset:
            comb_all = sorted(self.comb_all, key=lambda comb: [comb[0].id, comb[1], comb[2]])
        else:
            print('...detecting updates in fs_detail')

            # facs_nm_all = list(set([comb[0] for comb in comb2facs.keys()]))
            fa_nm_all = list(set([comb[0].name for comb in comb2facs.keys()]))
            fd_created_all = FsDetail.objects.filter(
                createdAt = self.today,
                account__accountNm__in = fa_nm_all
            ).select_related('account', 'fs', 'fs__corp')
            if fd_created_all.count() == 0:
                print('...no update for fa_cs')
                return None
            comb_all = []
            for fd_created in fd_created_all:
                fa = FsAccountLite.objects.get(
                    name = fd_created.account.accountNm,
                    oc = fd_created.fs.type.oc,
                )
                comb = (
                    fa,
                    fd_created.fs.corp.market,
                    fd_created.fs.fqe
                )
                if comb not in comb_all:
                    comb_all.append(comb)
            comb_all = sorted(comb_all, key=lambda comb: [comb[0].id, comb[1], comb[2]])

        # loop indexes
        new_facs_id = facs_all.count() + 1
        prev_outer_idx = None

        # status
        restarted = False

        # constants
        BATCH_SIZE = int(1e5)
        FIELDS = {
            'id': 'id',
            'fs__corp_id': 'corp_id',
            'fs__fqe': 'fqe',
            'fs__type__name': 'ft',
            'value': 'value'
        }

        # containers
        m2m_created_all = []
        facs_created_all = []
        print('...complete!')


        print(f"updating fa_cs...")
        while True:
            # define loop out process
            if len(comb_all) == 0:
                if len(facs_created_all) > 0:
                    write_fa_cs(
                        data = facs_created_all,
                        batch_size = BATCH_SIZE
                    )
                if len(m2m_created_all) > 0:
                    write_fa_cs_m2m(
                        data = m2m_created_all,
                        batch_size = BATCH_SIZE
                    )
                break

            # get loop indexes
            inner_idx = comb_all.pop(0) # inner loop index: [fa, market, tp]
            outer_idx = list(inner_idx[:2]) # outer loop index: [fa, market]

            if restarted:
                restarted = False
                print(f"...restarting collection from {inner_idx}")

            ## outer loop process
            # if new outer idx, query new dataframe
            if prev_outer_idx != outer_idx:
                # query
                fltr = {
                    'account__accountNm': outer_idx[0].name,
                    'fs__type__oc': outer_idx[0].oc,
                    'fs__corp__market': outer_idx[1],
                }
                qs = (
                    FsDetail.objects.filter(**fltr)
                    .select_related('fs','fs__corp','fs__type')
                )
                if not qs.exists():
                    continue

                # qs to df
                df = (
                    pd.DataFrame
                    .from_records(qs.values(*FIELDS.keys()))
                    .rename(columns=FIELDS)
                )
                df.fqe = pd.to_datetime(df.fqe)

                # cleaning df
                prefix_ftnm_uniq = [ftnm[:-1] for ftnm in df.ft.unique()]
                if ('IS' in prefix_ftnm_uniq) and ('CIS' in prefix_ftnm_uniq):
                    df = df.loc[df.ft.str[:-1] != 'CIS']

                ft_count = df.ft.value_counts().to_dict()
                df['ft_order'] = df.ft.replace(ft_count)
                df = df.sort_values(
                    ['corp_id', 'fqe', 'ft_order'],
                    ascending = [True, False, False]
                ).drop_duplicates(['corp_id', 'fqe'])
                del df['ft_order']

            # update prev_outer_idx for next loop
            prev_outer_idx = outer_idx

            ## inner loop process

            # get facs obj
            facs = comb2facs.pop(tuple(inner_idx), None)

            # get m2m relationship for a facs
            fqe_lte = pd.Timestamp(inner_idx[2])
            fqe_gte = fqe_lte - pd.DateOffset(years=2)
            fdid_all = df.loc[(df.fqe >= fqe_gte) & (df.fqe <=fqe_lte)].id.to_list()

            # if facs already exists
            if facs:
                # detect update in m2m relationships
                old_fdid_all = facs.source.all().values_list('id', flat=True)
                fdid_added = [fdid for fdid in fdid_all if fdid not in old_fdid_all]
                fdid_removed = [fdid for fdid in old_fdid_all if fdid not in fdid_all]

                # collect new m2m relationship for a facs
                if len(fdid_added) > 0:
                    m2m_created_all += [(
                        FaCrossSection.source
                        .through(
                            facrosssection_id = facs.id,
                            fsdetail_id = fd_id
                        )
                    ) for fd_id in fdid_added]

                # removing might occurs little
                # so, use not bulk method but 'remove' method
                if len(fdid_removed) > 0:
                    fd_removed = FsDetail.objects.filter(id__in=fdid_removed)
                    facs.source.remove(*fd_removed)
            else:
                # collect new facs
                facs_created = FaCrossSection(
                    id = new_facs_id,
                    fa = inner_idx[0],
                    market = inner_idx[1],
                    tp = inner_idx[2],
                )
                facs_created_all.append(facs_created)

                # collect new m2m relationships for a facs
                m2m_created_all += [(
                    FaCrossSection.source
                    .through(
                        facrosssection_id = new_facs_id,
                        fsdetail_id = fd_id
                    )
                ) for fd_id in fdid_all]
                new_facs_id += 1

            if len(m2m_created_all) >= int(1e6):
                print(f"...large amount of updates detected: stopping collection and writing first 1M rows of new m2m on db to control memory.")
                print(f"...the collection was stopped at {inner_idx}")
                print(f"...writing on db")

                # write new facs
                write_fa_cs(
                    data = facs_created_all,
                    batch_size = BATCH_SIZE
                )

                # write new m2m
                write_fa_cs_m2m(
                    data = m2m_created_all,
                    batch_size = BATCH_SIZE
                )

                # reset containers to be restarted
                facs_created_all = []
                m2m_created_all = []
                restarted = True


def write_fa_cs(data, batch_size):
    while True:
        batch = list(islice(data, batch_size))
        if not batch:
            break
        FaCrossSection.objects.bulk_create(batch, batch_size)
        data = data[batch_size:]


def write_fa_cs_m2m(data, batch_size):
    while True:
        batch = list(islice(data, batch_size))
        if not batch:
            break
        FaCrossSection.source.through.objects.bulk_create(batch, batch_size)
        data = data[batch_size:]
