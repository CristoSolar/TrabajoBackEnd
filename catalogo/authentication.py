from datetime import timedelta

from django.conf import settings
from django.utils import timezone
from rest_framework import exceptions
from rest_framework.authentication import TokenAuthentication


def vencimiento(token):
    return token.created + timedelta(hours=settings.API_TOKEN_TTL_HORAS)


class TokenConExpiracion(TokenAuthentication):
    """El token de DRF no caduca nunca; aquí vence tras API_TOKEN_TTL_HORAS."""

    def authenticate_credentials(self, key):
        usuario, token = super().authenticate_credentials(key)
        if timezone.now() >= vencimiento(token):
            token.delete()
            raise exceptions.AuthenticationFailed("El token expiró. Solicite uno nuevo.")
        return usuario, token
