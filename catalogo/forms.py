from django import forms

from .models import Libro, normalizar_isbn


class LibroForm(forms.ModelForm):
    class Meta:
        model = Libro
        fields = [
            "titulo",
            "autor",
            "isbn",
            "anio_publicacion",
            "paginas",
            "estado",
        ]

    def clean_isbn(self):
        return normalizar_isbn(self.cleaned_data["isbn"])
