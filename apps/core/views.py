from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta


def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    failed_attempts = request.session.get('failed_attempts', 0)
    lock_time = request.session.get('lock_time')
    context = {}
    if lock_time:
        unlock_time = timezone.datetime.fromisoformat(lock_time)
        if timezone.now() < unlock_time:
            remaining = int((unlock_time - timezone.now()).total_seconds())
            context['locked'] = True
            context['remaining'] = remaining
            messages.error(request, f"Too many failed attempts. Try again in {remaining} seconds.")
            return render(request, "auth/login.html", context)
        else:
            request.session['failed_attempts'] = 0
            request.session['lock_time'] = None
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            request.session['failed_attempts'] = 0
            request.session['lock_time'] = None
            login(request, user)
            return redirect("dashboard")
        else:
            failed_attempts += 1
            request.session['failed_attempts'] = failed_attempts
            if failed_attempts >= 5:
                lock_until = timezone.now() + timedelta(minutes=1)
                request.session['lock_time'] = lock_until.isoformat()
                context['locked'] = True
                context['remaining'] = 60
                messages.error(request, "Too many failed attempts. Locked for 1 minute.")
            else:
                remaining_attempts = 5 - failed_attempts
                messages.error(request, f"Incorrect username or password. {remaining_attempts} attempts remaining.")
    return render(request, "auth/login.html", context)


def logout_view(request):
    logout(request)
    return redirect("login")


@login_required(login_url='login')
def dashboard(request):
    return render(request, "home.html")


def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        from django.contrib.auth.models import User
        username = request.POST.get('username', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')

        errors = {}

        if not username:
            errors['username'] = 'Username is required.'
        elif User.objects.filter(username=username).exists():
            errors['username'] = 'Username already taken.'

        if not first_name:
            errors['first_name'] = 'First name is required.'

        if not last_name:
            errors['last_name'] = 'Last name is required.'

        if not email:
            errors['email'] = 'Email is required.'
        elif User.objects.filter(email=email).exists():
            errors['email'] = 'Email already registered.'

        if not password:
            errors['password'] = 'Password is required.'
        elif len(password) < 8:
            errors['password'] = 'Password must be at least 8 characters.'

        if password != confirm_password:
            errors['confirm_password'] = 'Passwords do not match.'

        if not errors:
            user = User.objects.create_user(
                username=username,
                first_name=first_name,
                last_name=last_name,
                email=email,
                password=password
            )
            login(request, user)
            return redirect('dashboard')

        return render(request, 'auth/register.html', {
            'errors': errors,
            'form_data': request.POST
        })

    return render(request, 'auth/register.html')