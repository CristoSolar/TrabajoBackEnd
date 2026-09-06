from django.test import TestCase
from django.urls import reverse

from .forms import LibroForm
from .models import Autor, Libro


class ModeloTests(TestCase):
    def setUp(self):
        self.autor = Autor.objects.create(
            nombre="Gabriela Mistral",
            nacionalidad="Chile",
            anio_nacimiento=1889,
        )
        self.libro = Libro.objects.create(
            titulo="Desolación",
            autor=self.autor,
            isbn="9789561111111",
            anio_publicacion=1922,
            paginas=250,
        )

    def test_str_de_los_modelos(self):
        self.assertEqual(str(self.autor), "Gabriela Mistral")
        self.assertEqual(str(self.libro), "Desolación (Gabriela Mistral)")

    def test_estado_inicial_es_disponible(self):
        self.assertEqual(self.libro.estado, Libro.Estado.DISPONIBLE)


class LibroFormTests(TestCase):
    def setUp(self):
        self.autor = Autor.objects.create(
            nombre="Isabel Allende",
            nacionalidad="Chile",
            anio_nacimiento=1942,
        )

    def datos(self, isbn):
        return {
            "titulo": "La casa de los espíritus",
            "autor": self.autor.pk,
            "isbn": isbn,
            "anio_publicacion": 1982,
            "paginas": 450,
            "estado": Libro.Estado.DISPONIBLE,
        }

    def test_isbn_invalido_es_rechazado(self):
        for isbn in ("123", "abcdefghij", "12345678901234"):
            form = LibroForm(data=self.datos(isbn))
            self.assertFalse(form.is_valid(), f"ISBN {isbn!r} debió ser rechazado")
            self.assertIn("isbn", form.errors)

    def test_isbn_valido_con_guiones_es_aceptado(self):
        form = LibroForm(data=self.datos("978-956-111-111-1"))
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["isbn"], "9789561111111")


class VistasTests(TestCase):
    def setUp(self):
        self.autor = Autor.objects.create(
            nombre="Julio Cortázar",
            nacionalidad="Argentina",
            anio_nacimiento=1914,
        )
        Libro.objects.create(
            titulo="Rayuela",
            autor=self.autor,
            isbn="9789561111112",
            anio_publicacion=1963,
            paginas=600,
        )
        Libro.objects.create(
            titulo="Bestiario",
            autor=self.autor,
            isbn="9789561111113",
            anio_publicacion=1951,
            paginas=160,
        )

    def test_listado_responde_200(self):
        respuesta = self.client.get(reverse("catalogo:libro_lista"))
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "Rayuela")

    def test_busqueda_filtra_por_titulo(self):
        respuesta = self.client.get(
            reverse("catalogo:libro_lista"), {"q": "rayuela"}
        )
        self.assertContains(respuesta, "Rayuela")
        self.assertNotContains(respuesta, "Bestiario")

    def test_todas_las_rutas_responden_200(self):
        libro = Libro.objects.get(titulo="Rayuela")
        rutas = [
            reverse("catalogo:libro_lista"),
            reverse("catalogo:libro_detalle", args=[libro.pk]),
            reverse("catalogo:libro_crear"),
            reverse("catalogo:libro_editar", args=[libro.pk]),
            reverse("catalogo:libro_eliminar", args=[libro.pk]),
            reverse("catalogo:autor_lista"),
            reverse("catalogo:autor_detalle", args=[self.autor.pk]),
        ]
        for ruta in rutas:
            respuesta = self.client.get(ruta)
            self.assertEqual(respuesta.status_code, 200, f"Falló {ruta}")
