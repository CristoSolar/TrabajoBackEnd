from django.contrib import messages
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


class LibroCreateView(CreateView):
    model = Libro
    form_class = LibroForm

    def form_valid(self, form):
        messages.success(self.request, "Libro creado correctamente.")
        return super().form_valid(form)


class LibroUpdateView(UpdateView):
    model = Libro
    form_class = LibroForm

    def form_valid(self, form):
        messages.success(self.request, "Libro actualizado correctamente.")
        return super().form_valid(form)


class LibroDeleteView(DeleteView):
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
