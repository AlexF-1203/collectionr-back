import requests
import logging
from django.conf import settings
from django.http import HttpResponseRedirect
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
import uuid

logger = logging.getLogger(__name__)
User = get_user_model()

class GoogleLoginView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        code = request.GET.get('code')

        if not code:
            logger.error("Code d'autorisation Google manquant")
            return Response({'error': 'Code manquant'}, status=status.HTTP_400_BAD_REQUEST)

        token_url = 'https://oauth2.googleapis.com/token'
        redirect_uri = f"{settings.BASE_API_URL}/auth/api/login/google/"

        logger.info(f"Redirect URI utilisé: {redirect_uri}")

        token_payload = {
            'code': code,
            'client_id': settings.GOOGLE_OAUTH2_CLIENT_ID,
            'client_secret': settings.GOOGLE_OAUTH2_CLIENT_SECRET,
            'redirect_uri': redirect_uri,
            'grant_type': 'authorization_code'
        }

        token_response = requests.post(token_url, data=token_payload)
        token_data = token_response.json()

        if 'error' in token_data:
            logger.error(f"Erreur lors de l'obtention du token Google: {token_data['error']}")
            return Response({'error': token_data['error']}, status=status.HTTP_400_BAD_REQUEST)

        user_info_url = 'https://www.googleapis.com/oauth2/v2/userinfo'
        headers = {'Authorization': f"Bearer {token_data['access_token']}"}
        user_info_response = requests.get(user_info_url, headers=headers)
        user_info = user_info_response.json()

        email = user_info.get('email')
        if not email:
            logger.error("Email non fourni par Google")
            return Response({'error': 'Email non fourni'}, status=status.HTTP_400_BAD_REQUEST)

        base_username = email.split('@')[0]
        try:
            user = User.objects.get(email=email)
            logger.info(f"Utilisateur existant trouvé: {user.username}")
        except User.DoesNotExist:
            username = base_username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1

            user = User(
                username=username,
                email=email,
            )
            user.set_unusable_password()
            user.is_google_account = True
            user.save()

            logger.info(f"Nouvel utilisateur créé: {user.username}")

        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)

        response = HttpResponseRedirect(settings.BASE_APP_URL)

        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=False,
            samesite='Lax',
            path='/'
        )
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=False,
            samesite='Lax',
            path='/'
        )

        logger.info(f"Connexion OAuth2 réussie. Redirection vers {settings.BASE_APP_URL}")
        return response
