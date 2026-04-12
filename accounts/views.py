from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.contrib import messages


def register_view(request):
    if request.user.is_authenticated:
        return redirect('house_list')
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password1 = request.POST.get('password1', '')
        password2 = request.POST.get('password2', '')

        if not username or not email or not password1 or not password2:
            messages.error(request, 'Veuillez remplir tous les champs.')
        elif password1 != password2:
            messages.error(request, 'Les mots de passe ne correspondent pas.')
        elif len(password1) < 8:
            messages.error(request, 'Le mot de passe doit contenir au moins 8 caractères.')
        elif User.objects.filter(username=username).exists():
            messages.error(request, "Ce nom d'utilisateur est déjà pris.")
        elif User.objects.filter(email=email).exists():
            messages.error(request, 'Cette adresse e-mail est déjà utilisée.')
        else:
            user = User.objects.create_user(username=username, email=email, password=password1)
            login(request, user)
            messages.success(request, f'Bienvenue {user.username} ! Votre compte a été créé.')
            return redirect('house_list')
    return render(request, 'accounts/register.html', {})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('house_list')
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Bon retour, {user.username} !')
            next_url = request.GET.get('next', 'house_list')
            return redirect(next_url)
        else:
            messages.error(request, 'Nom d\'utilisateur ou mot de passe invalide.')
    else:
        form = AuthenticationForm()
    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, 'Vous avez été déconnecté.')
    return redirect('login')
