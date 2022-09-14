from ggdb.models import *
from itertools import islice

import json

class AccountRatioManager:

    def __init__(self):
        self.ar_all = AccountRatio.objects.all()
        with open('source/account_ratios.json') as f:
            self.data = json.load(f)

    def update(self):
        print('updating account_ratio...')
        ar_created = []
        for d in self.data:
            if not AccountRatio.objects.filter(name=d['name']).exists():
                ar_created.append(AccountRatio(**d))
        if len(ar_created) > 0:
            AccountRatio.objects.bulk_create(ar_created)
            print('...following account ratios are newly defined.')
            for ar in ar_created:
                print(f"......{ar.name}")
        else:
            print('...no new account ratio')
