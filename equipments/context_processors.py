from .helpers import is_admin, is_encoder, is_client, is_superadmin

def user_roles(request):
    user = request.user
    return {
        'is_admin': is_admin(user),
        'is_encoder': is_encoder(user),
        'is_client': is_client(user),
        'is_superadmin': is_superadmin(user),
    }
