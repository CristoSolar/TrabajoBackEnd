from rest_framework import serializers

from .models import Autor, Libro, normalizar_isbn


class AutorSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="api:autor-detail")
    total_libros = serializers.SerializerMethodField()

    class Meta:
        model = Autor
        fields = ["id", "url", "nombre", "nacionalidad", "anio_nacimiento", "total_libros"]

    def get_total_libros(self, autor):
        # El listado lo trae anotado (una sola consulta); tras crear/editar no.
        if hasattr(autor, "total_libros"):
            return autor.total_libros
        return autor.libros.count()


class LibroSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="api:libro-detail")
    autor_nombre = serializers.CharField(source="autor.nombre", read_only=True)
    estado_display = serializers.CharField(source="get_estado_display", read_only=True)

    class Meta:
        model = Libro
        fields = [
            "id",
            "url",
            "titulo",
            "autor",
            "autor_nombre",
            "isbn",
            "anio_publicacion",
            "paginas",
            "estado",
            "estado_display",
            "fecha_creacion",
        ]
        read_only_fields = ["fecha_creacion"]

    def validate_isbn(self, valor):
        return normalizar_isbn(valor)
