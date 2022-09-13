from dashboard.batchtools.fa_cs import *

import datetime
import time

facsm = FaCrossSectionManager()
# sample

facsm.today = datetime.datetime.strptime('2022-09-09', '%Y-%m-%d')
facsm.update()
