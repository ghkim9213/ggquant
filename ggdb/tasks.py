from .batchtools.account_ratio import *
from .batchtools.corp import *
from .batchtools.fa_cs import *
from .batchtools.fs import *
# from .batchtools.temp import *

from celery import shared_task

import datetime


@shared_task
def batchs():
    cm = CorpManager()
    cm.update()

    ftm = FsTypeManager()
    ftm.update()

    fam = FsAccountManager()
    fam.update()

    odfm = OpendartFileManager()
    odfm.update()

    if len(odfm._updated_file_all) > 0:
        for odf in odfm._updated_file_all:
            fsm = FsManager(odf)
            fsm.update()
            fsm.update_details()

        arm = AccountRatioManager()
        arm.update()

        facsm = FaCrossSectionManager()
        facsm.update()
