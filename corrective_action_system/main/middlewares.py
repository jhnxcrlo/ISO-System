# middlewares.py
from django.shortcuts import redirect
from django.urls import reverse


class ForcePasswordChangeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        if request.user.is_authenticated:
            # Check if the user needs to reset their password
            if hasattr(request.user, 'userprofile') and request.user.userprofile.password_needs_reset:
                # Prevent redirection loops if the user is already on the password change page
                if request.path != reverse('password_change'):
                    return redirect('password_change')

        # Proceed with the next middleware or view
        response = self.get_response(request)
        return response
