from .viewmanagers.main import *
from .viewmanagers.indicators import *
from .viewmanagers.stkrpt import *

from django.shortcuts import render

import json

def main(request):
    mvm = MainViewManager()
    context = {
        'categ': mvm.CATEG,
    }
    return render(request,'dashboard/main.html',context)


def indicators(request):
    rvm = IndicatorsViewManager()
    context = {
        'sidebar': rvm.sidebar(),
        'main': rvm.main(request),
    }
    return render(request,'dashboard/indicators.html',context)



def stkrpt(request, stock_code):
    svm = StkrptViewManager(request, stock_code)
    context = {
        'search_data': svm.search(),
        'corp': svm.corp,
        'ar_viewer': svm.ar_viewer(),
        'fa_viewer': svm.fa_viewer(),
        # 'recent_history': svm.recent_history(),
        # 'lar_viewer': svm.lar_viewer(),
        # 'ar_ts_viewer': svm.ar_ts_viewer(),
        # 'fs_viewer': svm.fs_viewer(),
    }
    return render(request,'dashboard/stkrpt.html',context)
