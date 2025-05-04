from django.shortcuts import redirect
from django.urls import reverse
from .models import APIKey
import openai

class CheckAPIKeyMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Paths that should be allowed without API key check
        allowed_paths = [
            reverse('login'),
            reverse('api-key'),  # Allow access to API key page
        ]

        # Allow access to login, logout, and API key pages without API key check
        if request.path in allowed_paths:
            return self.get_response(request)

        # Check if the user is authenticated
        if request.user.is_authenticated:
            # Check if an API key exists
            api_key = APIKey.objects.first()
            if api_key:
                openai.api_key = api_key.api_key
                try:
                    # Verify the API key by making a simple API call
                    openai.models.list()
                except openai.AuthenticationError:
                    # Redirect to the API key form with an error message
                    return redirect(f"{reverse('api-key')}?error=Invalid API Key")
            else:
                # If no API key exists, redirect to the API key form
                return redirect('api-key')

        # If the user is not authenticated, let the request proceed
        response = self.get_response(request)
        return response
