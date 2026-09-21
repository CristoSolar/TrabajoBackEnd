from django.contrib.auth.models import Group, User
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

    def test_rutas_publicas_responden_200(self):
        libro = Libro.objects.get(titulo="Rayuela")
        rutas = [
            reverse("catalogo:libro_lista"),
            reverse("catalogo:libro_detalle", args=[libro.pk]),
            reverse("catalogo:autor_lista"),
            reverse("catalogo:autor_detalle", args=[self.autor.pk]),
        ]
        for ruta in rutas:
            respuesta = self.client.get(ruta)
            self.assertEqual(respuesta.status_code, 200, f"Falló {ruta}")


class SesionYPermisosTests(TestCase):
    def setUp(self):
        self.autor = Autor.objects.create(
            nombre="Nicanor Parra", nacionalidad="Chile", anio_nacimiento=1914
        )
        self.libro = Libro.objects.create(
            titulo="Poemas y antipoemas",
            autor=self.autor,
            isbn="9789561111114",
            anio_publicacion=1954,
            paginas=180,
        )
        self.bibliotecario = User.objects.create_user("biblio", password="clave-de-prueba-1")
        self.bibliotecario.groups.add(Group.objects.get(name="Bibliotecarios"))
        self.lector = User.objects.create_user("lector", password="clave-de-prueba-2")

    def rutas_protegidas(self):
        return [
            reverse("catalogo:libro_crear"),
            reverse("catalogo:libro_editar", args=[self.libro.pk]),
            reverse("catalogo:libro_eliminar", args=[self.libro.pk]),
        ]

    def test_anonimo_es_redirigido_al_login(self):
        for ruta in self.rutas_protegidas():
            respuesta = self.client.get(ruta)
            self.assertRedirects(respuesta, f"{reverse('login')}?next={ruta}")

    def test_usuario_sin_permisos_recibe_403(self):
        self.client.force_login(self.lector)
        for ruta in self.rutas_protegidas():
            respuesta = self.client.get(ruta)
            self.assertEqual(respuesta.status_code, 403, f"Falló {ruta}")

    def test_bibliotecario_accede_a_las_rutas_protegidas(self):
        self.client.force_login(self.bibliotecario)
        for ruta in self.rutas_protegidas():
            respuesta = self.client.get(ruta)
            self.assertEqual(respuesta.status_code, 200, f"Falló {ruta}")

    def test_anonimo_no_puede_eliminar_por_post(self):
        respuesta = self.client.post(
            reverse("catalogo:libro_eliminar", args=[self.libro.pk])
        )
        self.assertEqual(respuesta.status_code, 302)
        self.assertTrue(Libro.objects.filter(pk=self.libro.pk).exists())

    def test_login_y_logout_gestionan_la_sesion(self):
        ok = self.client.login(username="biblio", password="clave-de-prueba-1")
        self.assertTrue(ok)
        self.assertIn("_auth_user_id", self.client.session)
        self.client.post(reverse("logout"))
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_grupo_bibliotecarios_tiene_los_permisos_crud(self):
        permisos = set(
            Group.objects.get(name="Bibliotecarios")
            .permissions.values_list("codename", flat=True)
        )
        self.assertTrue({"add_libro", "change_libro", "delete_libro"} <= permisos)
