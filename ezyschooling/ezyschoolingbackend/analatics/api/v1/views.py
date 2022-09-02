from rest_framework import generics
from rest_framework.response import Response

from analatics.models import PageVisited
from analatics.utils import save_user_actions, save_click_actions

from .serializers import PageVisitedSerializer, ClickLogEntrySerializer


class PageVisitedView(generics.CreateAPIView):
    serializer_class = PageVisitedSerializer

    def post(self, request, *args, **kwargs):
        serializer = PageVisitedSerializer(data=request.data)
        if serializer.is_valid():
            save_user_actions(request)
        return Response({})


class ClickLogEntryView(generics.CreateAPIView):
    serializer_class = ClickLogEntrySerializer

    def post(self, request, *args, **kwargs):
        serializer = ClickLogEntrySerializer(data=request.data)
        if serializer.is_valid():
            save_click_actions(request)
            return Response(serializer.data)
        return Response(serializer.errors)
