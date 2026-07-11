from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as django_login, logout as django_logout
from django.contrib.auth.models import User
from django.http import HttpResponse

def login_view(request):
    if request.method == 'POST':
        u = request.POST.get('username')
        p = request.POST.get('password')
        user = authenticate(request, username=u, password=p)
        if user is not None:
            django_login(request, user)
            # Instruct HTMX to redirect the browser to the dashboard
            response = HttpResponse()
            response['HX-Redirect'] = '/'
            return response
        else:
            return render(request, 'core/auth/partials/error_message.html', {'error': 'Invalid username or password.'})
    return render(request, 'core/auth/login.html')

def signup_view(request):
    if request.method == 'POST':
        u = request.POST.get('username')
        e = request.POST.get('email')
        p = request.POST.get('password')
        q = request.POST.get('security_question')
        a = request.POST.get('security_answer')
        
        if User.objects.filter(username=u).exists():
            return render(request, 'core/auth/partials/error_message.html', {'error': 'Username is already taken.'})
            
        user = User.objects.create_user(username=u, email=e, password=p)
        user.profile.security_question = q
        user.profile.set_security_answer(a)
        
        django_login(request, user)
        response = HttpResponse()
        response['HX-Redirect'] = '/'
        return response
        
    return render(request, 'core/auth/signup.html')

def forgot_password_view(request):
    """Step 1: Check username and return security question form."""
    if request.method == 'POST':
        u = request.POST.get('username')
        try:
            user_obj = User.objects.get(username=u)
            return render(request, 'core/auth/partials/question_form.html', {'user_obj': user_obj})
        except User.DoesNotExist:
            return render(request, 'core/auth/partials/error_message.html', {'error': 'User not found. Please try again.'})
            
    return render(request, 'core/auth/forgot_password.html')
    
def reset_password_view(request):
    """Step 2: Verify answer and reset password."""
    if request.method == 'POST':
        u = request.POST.get('username')
        a = request.POST.get('security_answer')
        new_p = request.POST.get('new_password')
        
        try:
            user_obj = User.objects.get(username=u)
            if user_obj.profile.check_security_answer(a):
                user_obj.set_password(new_p)
                user_obj.save()
                return render(request, 'core/auth/partials/reset_success.html')
            else:
                return render(request, 'core/auth/partials/error_message.html', {'error': 'Incorrect security answer.'})
        except User.DoesNotExist:
            return render(request, 'core/auth/partials/error_message.html', {'error': 'Unexpected error occurred.'})
            
    return HttpResponse('Method not allowed', status=405)

def logout_view(request):
    django_logout(request)
    return redirect('core:login')
