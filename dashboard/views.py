from django.shortcuts import render
# from dashboard.contents.stock import *
from dashboard.viewmanagers.rankings import *
from dashboard.viewmanagers.stkrpt import *
# from dashboard.contents.accountRatios import *

import json

def main(request):
    return render(request,'layout/dashboard/main.html',{'data':data})


def rankings(request):
    rvm = RankingsViewManager()
    context = {
        'sidebar': rvm.sidebar(),
        'main': rvm.main(request),
    }
    return render(request,'layout/dashboard/rankings.html',context)



def stkrpt(request):
    svm = StkrptViewManager(request)
    context = {
        'search_data': svm.search(),
        'corp': svm.corp,
        'fs_viewer': svm.fs_viewer(),
    }
    return render(request,'layout/dashboard/stkrpt.html',context)


def vdataControl(request):
    return render(request,'layout/dashboard/vdataControl.html')
