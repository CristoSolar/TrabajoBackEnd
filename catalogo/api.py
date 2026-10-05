"""API REST del catálogo: autenticación por token y recursos /autores y /libros."""

from django.db.models import Count
from django.urls import path
from django.utils import timezone
from rest_framework import filters, permissions, status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.response import Response
from rest_framework.routers import DefaultRouter
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from .authentication import vencimiento
from .models import Autor, Libro
from .serializers import AutorSerializer, LibroSerializer


class Login(ObtainAuthToken):
    """POST usuario y contraseña → token nuevo. Cada login invalida el anterior."""

    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "login"

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        usuario = serializer.validated_data["user"]
        Token.objects.filter(user=usuario).delete()
        token = Token.objects.create(user=usuario)
        return Response(
            {
                "token": token.key,
                "expira": timezone.localtime(vencimiento(token)),
                "usuario": usuario.username,
            },
            status=status.HTTP_201_CREATED,
        )


class Logout(APIView):
    """DELETE revoca el token del usuario autenticado."""

    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request):
        Token.objects.filter(user=request.user).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AutorViewSet(viewsets.ModelViewSet):
    queryset = Autor.objects.annotate(total_libros=Count("libros"))
    serializer_class = AutorSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["nombre", "nacionalidad"]
    ordering_fields = ["nombre", "anio_nacimiento"]


class LibroViewSet(viewsets.ModelViewSet):
    serializer_class = LibroSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["titulo", "isbn", "autor__nombre"]
    ordering_fields = ["titulo", "anio_publicacion", "fecha_creacion"]

    def get_queryset(self):
        libros = Libro.objects.select_related("autor")
        estado = self.request.query_params.get("estado")
        if estado:
            libros = libros.filter(estado=estado.upper())
        autor = self.request.query_params.get("autor")
        if autor and autor.isdigit():
            libros = libros.filter(autor_id=autor)
        return libros


app_name = "api"

router = DefaultRouter()
router.register("autores", AutorViewSet, basename="autor")
router.register("libros", LibroViewSet, basename="libro")

urlpatterns = [
    path("auth/token/", Login.as_view(), name="token"),
    path("auth/logout/", Logout.as_view(), name="logout"),
] + router.urls
