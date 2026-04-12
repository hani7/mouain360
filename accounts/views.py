from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
import random
from .models import UserOTP

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
            user.is_active = False 
            user.save()
            
            # Generate OTP
            otp_code = str(random.randint(100000, 999999))
            UserOTP.objects.create(user=user, otp=otp_code)
            
            # Send Email
            subject = 'Vérification de votre compte Mouain 360'
            message = f'Bonjour {user.username},\n\nVotre code de vérification est : {otp_code}\n\nL\'équipe Mouain 360.'
            try:
                send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=False)
                messages.info(request, 'Un code de vérification a été envoyé à votre adresse e-mail.')
            except Exception as e:
                messages.error(request, f"Erreur lors de l'envoi de l'e-mail : {str(e)[:100]}")
                print(e)
            
            # Save user in session to verify
            request.session['registration_user_id'] = user.id
            return redirect('verify_otp')
    return render(request, 'accounts/register.html', {})

def verify_otp_view(request):
    if 'registration_user_id' not in request.session:
        return redirect('register')
        
    user_id = request.session['registration_user_id']
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return redirect('register')
        
    if request.method == 'POST':
        otp_input = request.POST.get('otp', '').strip()
        try:
            user_otp = UserOTP.objects.get(user=user)
            if user_otp.otp == otp_input:
                user.is_active = True
                user.save()
                user_otp.delete()
                del request.session['registration_user_id']
                login(request, user)
                messages.success(request, f'Bienvenue {user.username} ! Votre compte a été vérifié avec succès.')
                return redirect('house_list')
            else:
                messages.error(request, 'Le code fourni est incorrect. Veuillez réessayer.')
        except UserOTP.DoesNotExist:
            messages.error(request, 'Aucun code OTP trouvé. Veuillez vous réinscrire.')
            
    return render(request, 'accounts/verify_otp.html', {'email': user.email})

def resend_otp_view(request):
    if 'registration_user_id' not in request.session:
        return redirect('register')
        
    user_id = request.session['registration_user_id']
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return redirect('register')
        
    # Generate new OTP
    otp_code = str(random.randint(100000, 999999))
    user_otp, created = UserOTP.objects.get_or_create(user=user, defaults={'otp': otp_code})
    if not created:
        user_otp.otp = otp_code
        user_otp.save()
        
    # Send Email
    subject = 'Nouveau code de vérification - Mouain 360'
    message = f'Bonjour {user.username},\n\nVotre nouveau code de vérification est : {otp_code}\n\nL\'équipe Mouain 360.'
    try:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=False)
        messages.success(request, 'Un nouveau code a été envoyé à votre adresse e-mail.')
    except Exception as e:
        messages.error(request, f"Erreur lors de l'envoi de l'e-mail : {str(e)[:100]}")
        print(e)
        
    return redirect('verify_otp')


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
