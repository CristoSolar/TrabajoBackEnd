from django.db import models
from django.urls import reverse


class Autor(models.Model):
    nombre = models.CharField("nombre", max_length=200)
    nacionalidad = models.CharField("nacionalidad", max_length=100)
    anio_nacimiento = models.PositiveIntegerField("año de nacimiento")

    class Meta:
        verbose_name = "autor"
        verbose_name_plural = "autores"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre

    def get_absolute_url(self):
        return reverse("catalogo:autor_detalle", kwargs={"pk": self.pk})


class Libro(models.Model):
    class Estado(models.TextChoices):
        DISPONIBLE = "DISPONIBLE", "Disponible"
        PRESTADO = "PRESTADO", "Prestado"
        DADO_DE_BAJA = "BAJA", "Dado de baja"

    titulo = models.CharField("título", max_length=300)
    autor = models.ForeignKey(
        Autor,
        on_delete=models.CASCADE,
        related_name="libros",
        verbose_name="autor",
    )
    isbn = models.CharField("ISBN", max_length=17, unique=True)
    anio_publicacion = models.PositiveIntegerField("año de publicación")
    paginas = models.PositiveIntegerField("páginas")
    estado = models.CharField(
        "estado",
        max_length=10,
        choices=Estado.choices,
        default=Estado.DISPONIBLE,
    )
    fecha_creacion = models.DateTimeField("fecha de creación", auto_now_add=True)

    class Meta:
        verbose_name = "libro"
        verbose_name_plural = "libros"
        ordering = ["titulo"]
        constraints = [
            models.UniqueConstraint(
                fields=["titulo", "autor"], name="libro_unico_por_autor"
            )
        ]

    def __str__(self):
        return f"{self.titulo} ({self.autor})"

    def get_absolute_url(self):
        return reverse("catalogo:libro_detalle", kwargs={"pk": self.pk})
