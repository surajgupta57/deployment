from django.db.models import BooleanField, Case, Value, When
from rest_framework import generics, permissions

from parents.permissions import IsParentOrReadOnly

from childs.permissions import IsChildParentOrReadOnly
from .serializers import *


class ChildView(generics.ListCreateAPIView):
    serializer_class = ChildSerialzer
    permission_classes = [
        IsChildParentOrReadOnly,
        permissions.IsAuthenticated
    ]
    filterset_fields = ["no_school"]

    def get_queryset(self):
        user_id = self.kwargs.get("user_id", None)
        if user_id is not None:
            childs = Child.objects.filter(user_id=user_id)
        else:
            childs = Child.objects.filter(user=self.request.user)
        childs = childs.annotate(
            current_child=Case(
                When(id=self.request.user.current_child, then=Value(True)),
                default=Value(False),
                output_field=BooleanField(),
            )
        )
        return childs.order_by("id")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ChildDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ChildSerialzer
    permission_classes = [
        IsChildParentOrReadOnly,
    ]

    def get_object(self, queryset=None):
        if queryset is None:
            queryset = self.get_queryset()

        pk = self.kwargs.get("pk", None)
        slug = self.kwargs.get("slug", None)
        if pk is not None:
            return generics.get_object_or_404(queryset, pk=pk)
        elif slug is not None:
            return generics.get_object_or_404(queryset, slug=slug)

    def get_queryset(self):
        childs = Child.objects.filter(user=self.request.user)
        childs = childs.annotate(
            current_child=Case(
                When(id=self.request.user.current_child, then=Value(True)),
                default=Value(False),
                output_field=BooleanField(),
            )
        )
        return childs

    def perform_update(self, serializer):
        serializer.save(user=self.request.user)
