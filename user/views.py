from django.shortcuts import render, redirect

from django.contrib import auth
from django.contrib.auth import login, authenticate, get_user_model

from random import randint

# Create your views here.

def signup(request):
    if request.method == 'POST':
        if request.POST['password1'] == request.POST['password2']:
            User = get_user_model()
            if request.POST['username'] == '':
                is_random_username = True
                username = get_random_username(User)
            else:
                is_random_username = False
                username = request.POST['username']

            user = User.objects.create_user(
                email = request.POST['email'],
                password = request.POST['password1'],
                username = username,
                is_random_username = is_random_username,
            )
            auth.login(request, user)
            return redirect('/')
        else:
            error = 'failed to password verification.'
            return render(request, 'layout/user/signup.html', {'error':error})
    return render(request,'layout/user/signup.html')

def signin(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']
        user = authenticate(request, username=email, password=password)
        print(user)
        if user is not None:
            auth.login(request,user)
            return redirect('/')
        else:
            context = {
                'error': 'email or password is incorrect.'
            }
            return render(request,'layout/user/signin.html',context)
    else:
        return render(request,'layout/user/signin.html')

def signout(request):
    auth.logout(request)
    return redirect('/')


def get_random_username(usermodel):
    random_username = f'user{str(randint(0,99999999)).zfill(8)}'
    if [user.username for user in usermodel.objects.filter(is_random_username=True)]:
        return get_random_username()
    else:
        return random_username
