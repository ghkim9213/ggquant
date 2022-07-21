from django.shortcuts import render
import json

# Create your views here.

def home(request):
    return render(request, 'layout/home.html')


def about(request):
    with open('layout/static/layout/md/about.md') as f:
        lines = ''.join(f.readlines())
    return render(request, 'layout/about.html', {'md':lines})
