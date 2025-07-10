from django.contrib import messages
from django.shortcuts import redirect
from functools import wraps

def is_admin(user):
    return user.groups.filter(name='admin').exists()

def is_encoder(user):
    return user.groups.filter(name='encoder').exists()

def is_client(user):
    return user.groups.filter(name='client').exists()

def is_superadmin(user):
    return user.is_superuser

def is_admin_or_superadmin(user):
    return user.is_superuser or user.groups.filter(name='admin').exists()

def is_admin_superadmin_encoder(user):
    return user.is_superuser or user.groups.filter(name__in=['admin', 'encoder']).exists()

def encoder_readonly_or_denied(user):
    return user.is_superuser or user.groups.filter(name='admin').exists() or user.groups.filter(name='encoder').exists()

def is_viewer_or_above(user):
    return user.is_superuser or user.groups.filter(name__in=['admin', 'encoder', 'client']).exists()

def role_required_with_feedback(test_func):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not test_func(request.user):
                messages.error(request, "You do not have permission to access this page.")
                return redirect('equipments:dashboard')
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator
