from ggdb.models import *

import datetime


class DBHistoryViewManager:

    def __init__(self):
        self.today = datetime.datetime.today().date()

    def corp_today(self):
        return {
            'listed': Corp.objects.filter(listedAt=self.today),
            'delisted': Corp.objects.filter(delistedAt=self.today),
            'updated': CorpHistory.objects.filter(updatedAt=self.today),
        }

    def fs_today(self):
        pass
        # return {
        #     'created': Fs.objects.filter(createdAt=self.today),
        # }

    def arv_today(self):
        pass
