from django.utils.deprecation import MiddlewareMixin
from django.conf import settings

class JWTCookieMiddleware(MiddlewareMixin):
    """Middleware qui extrait les tokens JWT des cookies et les place dans l'entête d'autorisation"""

    def __call__(self, request):
        PUBLIC_PATHS = [
            '/auth/api/login/google/',
            '/api/token/',
            '/api/token/refresh/',
            '/auth-callback',
            '/login',
            '/register',
        ]
        if any(request.path.startswith(path) for path in PUBLIC_PATHS):
            return self.get_response(request)
            
        access_token = request.COOKIES.get('access_token')

        if access_token:
            request.META['HTTP_AUTHORIZATION'] = f"Bearer {access_token}"

        return self.get_response(request)
