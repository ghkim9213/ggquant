from dashboard.models import *
from datalib.formdata import *

from django.shortcuts import render

import json

# Create your views here.
def main(request):
    context = {
        'form_data': {
            'univ': UNIV_CHOICES_DICT,
            'ssall': STK_SELECTALL_CHOICES_DICT,
            'stk': sorted(STK_CHOICES, key=lambda x: x['stockCode']),
            'prd': PRD_CHOICES_DICT,
            'frq': FRQ_CHOICES_DICT,
        }
    }
    return render(request,'layout/datalib/main.html',context)

def query(request):
    context = {
        'form': DataQueryForm()
    }
    return render(request,'layout/datalib/query.html',context)
