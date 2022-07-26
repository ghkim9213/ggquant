from django.shortcuts import render
import json

# Create your views here.

def home(request):
    with open('readme.md') as f:
        readme = f.read()

    return render(request, 'home.html', {'readme': readme})
