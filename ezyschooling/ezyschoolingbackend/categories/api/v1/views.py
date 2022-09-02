from rest_framework import generics

from categories.models import Board, ExpertUserVideoCategory, SubCategory

from .serializers import (BoardSerializer, ExpertUserVideoCategorySerializer,
                          SubCategorySerializer)


class BoardView(generics.ListAPIView):
    serializer_class = BoardSerializer
    queryset = Board.objects.filter(active=True)
    pagination_class = None

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.only(
            "name", "min_age", "max_age", "slug", "thumbnail"
        ).order_by("min_age")
        return queryset


class SubCategoryView(generics.ListAPIView):
    serializer_class = SubCategorySerializer
    queryset = (
        SubCategory.objects.only("name", "slug", "thumbnail")
        .filter(active=True)
        .order_by("id")
    )
    pagination_class = None


class ExpertUserVideoCategoryView(generics.ListAPIView):
    serializer_class = ExpertUserVideoCategorySerializer
    queryset = (
        ExpertUserVideoCategory.objects.only("name", "slug")
        .filter(active=True)
        .order_by("id")
    )
    pagination_class = None
