from .batchtools.account_ratio import *
from .batchtools.corp import *
from .batchtools.fs import *
from .batchtools.temp import *

import time

def update_corp():
    cm = CorpManager()
    cm.update()

def update_fs():
    ftm = FsTypeManager()
    ftm.update()

    fam = FsAccountManager()
    fam.update()
    t2 = time.time()

    odfm = OpendartFileManager()
    odfm.update()
    t3 = time.time()

    if len(odfm._updated_file_all) > 0:
        for odf in odfm._updated_file_all:
            fsm = FsManager(odf)
            fsm.update()
            fsm.update_details()

        arm = AccountRatioManager()
        arm.update()
        arm.update_values()

        arcsm = AccountRatioCrossSectionManager()
        arcsm.update()
