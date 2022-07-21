from dashboard.models import AccountRatio

import json

class AccountRatioManager:

    def __init__(self):
        self.ar_all = AccountRatio.objects.all()
        with open('source/rankings_ar.json') as f:
            self.data = json.load(f)

    def update(self):
        print('updating account ratios...')
        if self.ar_all.exists():
            print('...no new account ratios.')
            # raise ValueError()
        else:
            AccountRatio.objects.bulk_create(
                [AccountRatio(**d) for d in self.data]
            )
        print('...update complete!')

    def bulk_inspect(self):
        print('inspecting account ratios...')
        for ar in self.ar_all:
            print(f"...inspecting {ar.name}")
            ar.inspect()
        print('...inspect complete!')
