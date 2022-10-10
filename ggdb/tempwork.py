from .tasks import *

import datetime

today = datetime.datetime.strptime('20221008', '%Y%m%d').date()
frm = FaRootManager()
frm.today = today
a, b = frm.update_daily()
