from django.urls import path

from . import views

app_name = "catalogo"

urlpatterns = [
    path("", views.LibroListView.as_view(), name="libro_lista"),
    path("libros/<int:pk>/", views.LibroDetailView.as_view(), name="libro_detalle"),
    path("libros/nuevo/", views.LibroCreateView.as_view(), name="libro_crear"),
    path("libros/<int:pk>/editar/", views.LibroUpdateView.as_view(), name="libro_editar"),
    path("libros/<int:pk>/eliminar/", views.LibroDeleteView.as_view(), name="libro_eliminar"),
    path("autores/", views.AutorListView.as_view(), name="autor_lista"),
    path("autores/<int:pk>/", views.AutorDetailView.as_view(), name="autor_detalle"),
]
