from .viewmanagers.main import *
from .viewmanagers.rankings import *
from .viewmanagers.stkrpt import *

from django.shortcuts import render

import json

def main(request):
    mvm = MainViewManager()
    context = {
        'categ': mvm.categ,
    }
    return render(request,'layout/dashboard/main.html',context)


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
