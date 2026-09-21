from django.db import migrations

PERMISOS = [
    ("add_libro", "catalogo", "libro"),
    ("change_libro", "catalogo", "libro"),
    ("delete_libro", "catalogo", "libro"),
    ("add_autor", "catalogo", "autor"),
    ("change_autor", "catalogo", "autor"),
]


def crear_grupo(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")
    ContentType = apps.get_model("contenttypes", "ContentType")

    grupo, _ = Group.objects.get_or_create(name="Bibliotecarios")
    for codename, app_label, modelo in PERMISOS:
        tipo, _ = ContentType.objects.get_or_create(app_label=app_label, model=modelo)
        permiso, _ = Permission.objects.get_or_create(
            codename=codename, content_type=tipo, defaults={"name": codename}
        )
        grupo.permissions.add(permiso)


def borrar_grupo(apps, schema_editor):
    apps.get_model("auth", "Group").objects.filter(name="Bibliotecarios").delete()


class Migration(migrations.Migration):
    dependencies = [
        ("catalogo", "0001_initial"),
        ("auth", "0012_alter_user_first_name_max_length"),
        ("contenttypes", "0002_remove_content_type_name"),
    ]

    operations = [migrations.RunPython(crear_grupo, borrar_grupo)]
