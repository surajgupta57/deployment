from ownelasticsearch.models import *
from . import serializers
from parents.permissions import (IsParent)
from backend.logger import info_logger,error_logger
import pandas as pd
from rest_framework.parsers import FileUploadParser
import json
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
import customJsonData
from customJsonData.jsonDataAddress import cityUploadLocation, popAreaUploadLocation, gradeUploadLocation, boardsUploadLocation, districtUploadLocation
from ownelasticsearch.indexname import index

class CityElasticData(APIView):
    def get(self, request, format=False):
        with open(cityUploadLocation) as json_file:
            data = json.load(json_file)

        json.dumps(data, indent=4)
        return Response(data, status=status.HTTP_200_OK)

class GradeElasticData(APIView):
    def get(self, request, format=False):
        with open(gradeUploadLocation) as json_file:
            data = json.load(json_file)

        json.dumps(data, indent=4)
        return Response(data, status=status.HTTP_200_OK)

class BoardsElasticData(APIView):
    def get(self, request, format=False):
        with open(boardsUploadLocation) as json_file:
            data = json.load(json_file)

        json.dumps(data, indent=4)
        return Response(data, status=status.HTTP_200_OK)

class DistrictElasticData(APIView):
    def get(self, request, format=False):
        with open(districtUploadLocation) as json_file:
            data = json.load(json_file)

        json.dumps(data, indent=4)
        return Response(data, status=status.HTTP_200_OK)

class PopAreaElasticData(APIView):
    def get(self, request, format=False):
        city = self.request.GET.get("city", None)
        district = self.request.GET.get("district", None)

        if (city and district):
            distPopAreaUploadLocation = 'customJsonData/' + index + district + city + 'DistrictData.txt'
            with open(distPopAreaUploadLocation) as json_file:
                data = json.load(json_file)
                json.dumps(data, indent=4)
        elif (city):
            cityPopAreaUploadLocation = 'customJsonData/' + index + city + 'CitiesData.txt'
            with open(cityPopAreaUploadLocation) as json_file:
                data = json.load(json_file)
                json.dumps(data, indent=4)
        elif (district):
            data = "Provide City Name Also"
        else:
            with open(popAreaUploadLocation) as json_file:
                data = json.load(json_file)
                json.dumps(data, indent=4)

        return Response(data, status=status.HTTP_200_OK)
