from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db.models import Count
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from .forms import LibroForm
from .models import Autor, Libro


class SoloBibliotecario(LoginRequiredMixin, PermissionRequiredMixin):
    """Exige sesión iniciada y el permiso concreto del modelo.

    La consulta al catálogo es pública; crear, editar y eliminar quedan
    restringidos al grupo "Bibliotecarios" (ver migración 0002).
    """

    raise_exception = False  # usuario anónimo -> redirige a LOGIN_URL


class LibroListView(ListView):
    model = Libro
    paginate_by = 10

    def get_queryset(self):
        qs = Libro.objects.select_related("autor")
        busqueda = self.request.GET.get("q", "").strip()
        estado = self.request.GET.get("estado", "").strip()
        if busqueda:
            qs = qs.filter(titulo__icontains=busqueda)
        if estado:
            qs = qs.filter(estado=estado)
        return qs

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto["estados"] = Libro.Estado.choices
        contexto["q"] = self.request.GET.get("q", "")
        contexto["estado_actual"] = self.request.GET.get("estado", "")
        return contexto


class LibroDetailView(DetailView):
    model = Libro


class LibroCreateView(SoloBibliotecario, CreateView):
    permission_required = "catalogo.add_libro"
    model = Libro
    form_class = LibroForm

    def form_valid(self, form):
        messages.success(self.request, "Libro creado correctamente.")
        return super().form_valid(form)


class LibroUpdateView(SoloBibliotecario, UpdateView):
    permission_required = "catalogo.change_libro"
    model = Libro
    form_class = LibroForm

    def form_valid(self, form):
        messages.success(self.request, "Libro actualizado correctamente.")
        return super().form_valid(form)


class LibroDeleteView(SoloBibliotecario, DeleteView):
    permission_required = "catalogo.delete_libro"
    model = Libro
    success_url = reverse_lazy("catalogo:libro_lista")

    def form_valid(self, form):
        messages.success(self.request, "Libro eliminado correctamente.")
        return super().form_valid(form)


class AutorListView(ListView):
    model = Autor

    def get_queryset(self):
        return Autor.objects.annotate(total_libros=Count("libros"))


class AutorDetailView(DetailView):
    model = Autor

    def get_queryset(self):
        return Autor.objects.annotate(total_libros=Count("libros"))
