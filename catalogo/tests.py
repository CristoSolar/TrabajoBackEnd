from datetime import timedelta

from django.contrib.auth.models import Group, User
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

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


class ApiTests(APITestCase):
    def setUp(self):
        cache.clear()  # el throttling guarda contadores en caché entre pruebas
        self.autor = Autor.objects.create(
            nombre="Pablo Neruda", nacionalidad="Chile", anio_nacimiento=1904
        )
        self.libro = Libro.objects.create(
            titulo="Canto general",
            autor=self.autor,
            isbn="9789560000001",
            anio_publicacion=1950,
            paginas=500,
        )
        self.bibliotecario = User.objects.create_user("biblio", password="clave-segura-123")
        self.bibliotecario.groups.add(Group.objects.get(name="Bibliotecarios"))
        self.lector = User.objects.create_user("lector", password="clave-segura-123")

    def autenticar(self, username):
        r = self.client.post(
            "/api/v1/auth/token/",
            {"username": username, "password": "clave-segura-123"},
            format="json",
        )
        self.assertEqual(r.status_code, 201)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {r.json()['token']}")
        return r.json()

    def nuevo_libro(self, **cambios):
        datos = {
            "titulo": "Veinte poemas de amor",
            "autor": self.autor.pk,
            "isbn": "978-956-00-0002-5",
            "anio_publicacion": 1924,
            "paginas": 120,
        }
        datos.update(cambios)
        return self.client.post("/api/v1/libros/", datos, format="json")

    def test_listado_publico_en_json_paginado(self):
        r = self.client.get("/api/v1/libros/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r["Content-Type"], "application/json")
        cuerpo = r.json()
        self.assertEqual(set(cuerpo), {"count", "next", "previous", "results"})
        libro = cuerpo["results"][0]
        self.assertEqual(libro["autor_nombre"], "Pablo Neruda")
        self.assertEqual(libro["estado_display"], "Disponible")

    def test_detalle_y_404(self):
        self.assertEqual(self.client.get(f"/api/v1/libros/{self.libro.pk}/").status_code, 200)
        r = self.client.get("/api/v1/libros/9999/")
        self.assertEqual(r.status_code, 404)
        self.assertIn("detail", r.json())

    def test_autores_incluyen_conteo_de_libros(self):
        r = self.client.get(f"/api/v1/autores/{self.autor.pk}/")
        self.assertEqual(r.json()["total_libros"], 1)

    def test_filtro_por_estado_y_busqueda(self):
        Libro.objects.create(
            titulo="Residencia en la tierra", autor=self.autor, isbn="9789560000003",
            anio_publicacion=1935, paginas=200, estado=Libro.Estado.PRESTADO,
        )
        r = self.client.get("/api/v1/libros/?estado=prestado")
        self.assertEqual([l["titulo"] for l in r.json()["results"]], ["Residencia en la tierra"])
        r = self.client.get("/api/v1/libros/?search=canto")
        self.assertEqual(r.json()["count"], 1)

    def test_anonimo_no_puede_escribir(self):
        self.assertEqual(self.nuevo_libro().status_code, 401)
        r = self.client.delete(f"/api/v1/libros/{self.libro.pk}/")
        self.assertEqual(r.status_code, 401)

    def test_credenciales_invalidas(self):
        r = self.client.post(
            "/api/v1/auth/token/", {"username": "biblio", "password": "mala"}, format="json"
        )
        self.assertEqual(r.status_code, 400)
        self.assertNotIn("token", r.json())

    def test_usuario_sin_rol_recibe_403(self):
        self.autenticar("lector")
        self.assertEqual(self.nuevo_libro().status_code, 403)

    def test_crud_completo_del_bibliotecario(self):
        self.autenticar("biblio")
        r = self.nuevo_libro()
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.json()["isbn"], "9789560000025")  # guiones normalizados
        url = f"/api/v1/libros/{r.json()['id']}/"
        r = self.client.patch(url, {"estado": "PRESTADO"}, format="json")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["estado"], "PRESTADO")
        datos = {**r.json(), "paginas": 130}
        self.assertEqual(self.client.put(url, datos, format="json").status_code, 200)
        self.assertEqual(self.client.delete(url).status_code, 204)
        self.assertEqual(self.client.get(url).status_code, 404)

    def test_validaciones_devuelven_400_por_campo(self):
        self.autenticar("biblio")
        r = self.nuevo_libro(isbn="abc")
        self.assertEqual(r.status_code, 400)
        self.assertIn("isbn", r.json())
        r = self.nuevo_libro(titulo="Canto general", isbn="9789560000009")
        self.assertEqual(r.status_code, 400)  # título + autor repetido

    def test_token_expirado_es_rechazado_y_borrado(self):
        self.autenticar("biblio")
        Token.objects.update(created=timezone.now() - timedelta(hours=9))
        self.assertEqual(self.nuevo_libro().status_code, 401)
        self.assertFalse(Token.objects.exists())

    def test_logout_revoca_el_token(self):
        self.autenticar("biblio")
        self.assertEqual(self.client.delete("/api/v1/auth/logout/").status_code, 204)
        self.assertEqual(self.nuevo_libro().status_code, 401)

    def test_nuevo_login_invalida_el_token_anterior(self):
        viejo = self.autenticar("biblio")["token"]
        self.autenticar("biblio")
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {viejo}")
        self.assertEqual(self.nuevo_libro().status_code, 401)

    def test_login_limitado_contra_fuerza_bruta(self):
        for _ in range(5):
            self.client.post("/api/v1/auth/token/", {"username": "biblio", "password": "x"})
        r = self.client.post("/api/v1/auth/token/", {"username": "biblio", "password": "x"})
        self.assertEqual(r.status_code, 429)
