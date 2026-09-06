from django import forms

from .models import Libro


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
        isbn = self.cleaned_data["isbn"].replace("-", "").strip()
        if not isbn.isdigit() or len(isbn) not in (10, 13):
            raise forms.ValidationError(
                "El ISBN debe tener 10 o 13 dígitos (se permiten guiones)."
            )
        return isbn
