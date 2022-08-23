from .tasks import *

arm = AccountRatioManager()
arm.update_values()

# comb2arv, new_arv_all = arm.update_values()
# # new
#
# from .models import *
#
# ar = AccountRatio.objects.get(name='CurrentRatio')
#
# panel = ar.get_panel('CFS','KOSPI')
