from .scrappers import *
from copy import deepcopy
from ggdb.models import Corp, CorpHistory

import datetime


class CorpToday:

    def __init__(self):
        self.kind = scrap_kind_corp_all('KOSPI') + scrap_kind_corp_all('KOSDAQ')
        self.dart = scrap_opendart_corp_all()

    def get_data(self):
        data = deepcopy(self.kind)
        dart = deepcopy(self.dart)
        sc2cc_map = {x['stock_code']: x['corp_code'] for x in dart if x['stock_code'] != None}
        for d in data:
            d['corp_code'] = sc2cc_map.pop(d['stock_code'], None)
        return data


class CorpManager:

    def __init__(self):
        self.ct = CorpToday()

    def update(self):
        # download data
        new_data = sorted(self.ct.get_data(), key=lambda x: x['listed_at'])
        new_data.reverse()
        for d in new_data:
            d['stockCode'] = d.pop('stock_code')
            d['corpCode'] = d.pop('corp_code')
            d['corpName'] = d.pop('stock_name')
            d['listedAt'] = d.pop('listed_at')

        # update
        if Corp.objects.all().exists():
            corp_all = Corp.objects.filter(delistedAt__isnull=True)
            stock_code_all = corp_all.values_list('stockCode',flat=True)
            new_corp_all = []
            new_history_all = []

            # detect changes and update
            for d in new_data:
                if d['stockCode'] in stock_code_all:
                    obj = corp_all.get(stockCode=d['stockCode'])
                    for k, v in d.items():
                        prev, curr = getattr(obj, k), v
                        if k == 'listedAt':
                            curr = datetime.datetime.strptime(curr, '%Y-%m-%d').date()
                        if prev != curr:
                            new_history_all.append(
                                CorpHistory(
                                    corp = obj,
                                    changeIn = k,
                                    prevValue = prev,
                                )
                            )
                            setattr(obj, k, curr)
                            obj.save()
                # collect new corps
                else:
                    new_corp_all.append(Corp(**d))

            # save new corps
            if len(new_corp_all) > 0:
                Corp.objects.bulk_create(new_corp_all)
            else:
                print('no new corp')

            # save history of changes in corp information
            if len(new_history_all) > 0:
                CorpHistory.objects.bulk_create(new_history_all)
            else:
                print('no new history')

            # detect delisted corps
            delisted_corp_all = []
            new_stock_code_all = [d['stockCode'] for d in new_data]
            delisted_stock_code_all = [x for x in stock_code_all if x not in new_stock_code_all]
            for sc in delisted_stock_code_all:
                obj = corp_all.get(stockCode=sc)
                obj.delistedAt = datetime.datetime.today().date()
                delisted_corp_all.append(obj)

            # save the delisted corps
            if len(delisted_corp_all) > 0:
                Corp.objects.bulk_update(delisted_corp_all,['delistedAt'])
            else:
                print('no delisted')

        # first rows for the model Corp
        else:
            corp_all = [Corp(**d) for d in new_data]
            Corp.objects.bulk_create(corp_all)
