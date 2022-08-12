from .viewmanagers.main import *
from .viewmanagers.indicators import *
from .viewmanagers.stkrpt import *

from django.shortcuts import render

import json

def main(request):
    mvm = MainViewManager()
    context = {
        'categ': mvm.categ,
    }
    return render(request,'dashboard/main.html',context)


def indicators(request):
    rvm = IndicatorsViewManager()
    context = {
        'sidebar': rvm.sidebar(),
        'main': rvm.main(request),
    }
    return render(request,'dashboard/indicators.html',context)



def stkrpt(request):
    svm = StkrptViewManager(request)
    context = {
        'search_data': svm.search(),
        'corp': svm.corp,
        'recent_history': svm.recent_history(),
        'ar_viewer': svm.ar_viewer(),
        'fs_viewer': svm.fs_viewer(),
    }
    return render(request,'dashboard/stkrpt.html',context)
