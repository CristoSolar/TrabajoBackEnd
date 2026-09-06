import random

from django.core.management.base import BaseCommand
from django.db import transaction
from faker import Faker

from catalogo.models import Autor, Libro

# Semilla fija: los datos generados son siempre los mismos, lo que hace
# reproducibles las demostraciones y la revisión del proyecto.
SEMILLA = 2026

# Distribución ponderada: en una biblioteca real la mayoría de los libros
# está disponible, una parte menor prestada y muy pocos dados de baja.
ESTADOS_PONDERADOS = [
    (Libro.Estado.DISPONIBLE, 0.65),
    (Libro.Estado.PRESTADO, 0.25),
    (Libro.Estado.DADO_DE_BAJA, 0.10),
]


class Command(BaseCommand):
    help = "Genera autores y libros de prueba con Faker (locale es_ES)."

    def add_arguments(self, parser):
        parser.add_argument("--autores", type=int, default=10)
        parser.add_argument("--libros", type=int, default=40)
        parser.add_argument(
            "--limpiar",
            action="store_true",
            help="Elimina autores y libros existentes antes de generar.",
        )

    @transaction.atomic
    def handle(self, *args, **opciones):
        fake = Faker("es_ES")
        Faker.seed(SEMILLA)
        random.seed(SEMILLA)

        if opciones["limpiar"]:
            Autor.objects.all().delete()
            self.stdout.write("Datos anteriores eliminados.")

        autores = []
        for _ in range(opciones["autores"]):
            autores.append(
                Autor.objects.create(
                    nombre=fake.name(),
                    nacionalidad=fake.country(),
                    anio_nacimiento=fake.random_int(min=1920, max=1995),
                )
            )

        estados = [estado for estado, _ in ESTADOS_PONDERADOS]
        pesos = [peso for _, peso in ESTADOS_PONDERADOS]

        creados = 0
        saltados = 0
        for _ in range(opciones["libros"]):
            autor = random.choice(autores)
            titulo = fake.sentence(nb_words=4).rstrip(".")
            isbn = fake.isbn13().replace("-", "")
            # Se respetan las restricciones de unicidad saltando duplicados
            # en lugar de dejar que la inserción falle.
            if (
                Libro.objects.filter(titulo=titulo, autor=autor).exists()
                or Libro.objects.filter(isbn=isbn).exists()
            ):
                saltados += 1
                continue
            Libro.objects.create(
                titulo=titulo,
                autor=autor,
                isbn=isbn,
                anio_publicacion=fake.random_int(min=1950, max=2026),
                paginas=fake.random_int(min=60, max=900),
                estado=random.choices(estados, weights=pesos, k=1)[0],
            )
            creados += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Creados {len(autores)} autores y {creados} libros "
                f"({saltados} duplicados saltados)."
            )
        )
