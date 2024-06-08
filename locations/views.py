import json

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
from django.urls import reverse
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from .forms import LocationCreateForm
from .models import Location


class HtmxMixin:
    """Switches template depending on request.htmx"""

    def get_template_names(self) -> list[str]:
        if not self.request.htmx:
            return [self.template_name.replace("htmx/", "")]
        return [self.template_name]


class BaseListView(HtmxMixin, ListView):
    model = Location
    context_object_name = "markers"
    template_name = "locations/htmx/base_list.html"

    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        if request.htmx:
            dict = {"refreshData": True}
            response["HX-Trigger-After-Swap"] = json.dumps(dict)
        return response


class LocationCreateView(LoginRequiredMixin, HtmxMixin, CreateView):
    model = Location
    template_name = "locations/htmx/location_create.html"
    form_class = LocationCreateForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["markers"] = Location.objects.none()
        return context

    def get_success_url(self):
        return reverse("locations:location_detail", kwargs={"pk": self.object.id})

    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        if request.htmx:
            dict = {"refreshData": True}
            response["HX-Trigger-After-Swap"] = json.dumps(dict)
        return response


class LocationDetailView(HtmxMixin, DetailView):
    model = Location
    template_name = "locations/htmx/location_detail.html"

    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        if request.htmx:
            dict = {"refreshData": True}
            response["HX-Trigger-After-Swap"] = json.dumps(dict)
            response["HX-Push-Url"] = self.object.get_absolute_url()
        return response


class LocationUpdateView(LoginRequiredMixin, HtmxMixin, UpdateView):
    model = Location
    template_name = "locations/htmx/location_update.html"
    form_class = LocationCreateForm

    def get_initial(self):
        # if lat or long are not given
        initial = super().get_initial()
        initial["lat"] = self.object.geom["coordinates"][1]
        initial["long"] = self.object.geom["coordinates"][0]
        return initial

    def get_success_url(self):
        return reverse("locations:location_detail", kwargs={"pk": self.object.id})

    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        if request.htmx:
            dict = {"refreshData": True}
            response["HX-Trigger-After-Swap"] = json.dumps(dict)
        return response


@login_required
def location_delete_view(request, pk):
    if not request.htmx:
        raise Http404("Request without HTMX headers")
    location = get_object_or_404(Location, id=pk)
    location.delete()
    return TemplateResponse(
        request,
        "locations/htmx/location_delete.html",
        {},
    )
