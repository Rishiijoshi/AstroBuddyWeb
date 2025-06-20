from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.urls import reverse
from .forms import CustomUserCreationForm, CustomAuthenticationForm

# Create your views here.

def signup_view(request):
    next_url = request.GET.get('next', '')
    login_form = CustomAuthenticationForm()
    if request.method == 'POST':
        signup_form = CustomUserCreationForm(request.POST)
        if signup_form.is_valid():
            user = signup_form.save()
            login(request, user)
            messages.success(request, f'Signup successful! Welcome aboard, {user.username}!')
            if next_url:
                return redirect(next_url)
            return redirect('astroapp:dashboard')
    else:
        signup_form = CustomUserCreationForm()
    return render(request, 'login_signup.html', {
        'signup_form': signup_form,
        'login_form': login_form,
        'view_name': 'signup',
        'next_url': next_url
    })

def login_view(request):
    next_url = request.GET.get('next', '')
    signup_form = CustomUserCreationForm()
    if request.method == 'POST':
        login_form = CustomAuthenticationForm(request, data=request.POST)
        if login_form.is_valid():
            username = login_form.cleaned_data.get('username')
            password = login_form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Login successful! Welcome aboard, {username}!')
                if next_url:
                    return redirect(next_url)
                return redirect('astroapp:dashboard')
            else:
                messages.error(request, 'Invalid username or password.')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        login_form = CustomAuthenticationForm()
    return render(request, 'login_signup.html', {
        'signup_form': signup_form,
        'login_form': login_form,
        'view_name': 'login',
        'next_url': next_url
    })

def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('astroapp:landing')
