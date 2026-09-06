from django.contrib import admin

from .models import Autor, Libro


@admin.register(Autor)
class AutorAdmin(admin.ModelAdmin):
    list_display = ("nombre", "nacionalidad", "anio_nacimiento")
    search_fields = ("nombre",)


@admin.register(Libro)
class LibroAdmin(admin.ModelAdmin):
    list_display = ("titulo", "autor", "isbn", "estado", "anio_publicacion")
    list_filter = ("estado",)
    search_fields = ("titulo", "isbn")
