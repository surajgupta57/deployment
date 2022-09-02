from notification.api.v1.serializers import *
from webpush.models import *
from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
import requests
import json
from notification.models import *
from parents.models import *
from schools.models import City
class WebPushSubscribe(generics.CreateAPIView):
    queryset = PushInformation.objects.all()
    serializer_class = WebPushSerializer


class WebPushUnsubcribe(APIView):
    def post(self, request):
        data = request.data
        s = SubscriptionInfo.objects.get(
            browser=data['subscription']['browser'],
            endpoint=data['subscription']['endpoint'],
            auth=data['subscription']['auth'],
            p256dh=data['subscription']['p256dh']
        )
        w = PushInformation.objects.get(
            subscription__pk=s.id, group__name=data['group'])
        w.delete()
        # s.delete()  # Dont delete the subscription object as it might be used by other group based notification

        return Response({"status": "success"})


# class DeviceRegistration(APIView):
#     def get(self, request):
#         qs = DeviceRegistrationToken.objects.all()
#         serializer = DeviceRegistrationTokenSerializer(qs, many=True)
#         return Response({'result': serializer.data})
#
#     def post(self, request):
#         reg_id = request.data.get('device_token')
#         if DeviceRegistrationToken.objects.filter(registration_id=reg_id).exists():
#             return Response({'result': "Device Registration key added"})
#             # if request.user.is_authenticated :
#             #     obj = DeviceRegistrationToken.objects.get(registration_id=reg_id)
#             #     obj.user=self.request.user
#             #     obj.save()
#             #     return Response({'result':"Device Registration key added"})
#             # else:
#             #     return Response({'result':"Device Registration key added"})
#         else:
#             # if request.user.is_authenticated :
#             #     obj = DeviceRegistrationToken.objects.create(registration_id=reg_id,user=self.request.user)
#             #     return Response({'result':"Device Registration key added"})
#             obj = DeviceRegistrationToken.objects.create(registration_id=reg_id)
#             return Response({'result': "Device Registration key added"})


class WhatsappSubscriptionView(APIView):
    def post(self, request):
        data = request.data
        is_Subscriber = data.get('is_subscriber')
        phone_number = data.get('phone_number')
        enquiry = data.get('enquiry')
        result = {}
        if not request.user.is_authenticated and WhatsappSubscribers.objects.filter(phone_number=phone_number).exists():
            obj = WhatsappSubscribers.objects.get(phone_number=phone_number)
            obj.is_Subscriber = is_Subscriber
            obj.save()

        else:
            if self.request.user.is_authenticated:
                obj = WhatsappSubscribers.objects.create(user=self.request.user, is_Subscriber=is_Subscriber)
                if phone_number:
                    obj.phone_number = phone_number
                else:
                    phone_number = ''
                    for i in ParentProfile.objects.filter(user=self.request.user.id):
                        p_profile = ParentProfile.objects.filter(user=i.user).first()
                        if p_profile and p_profile.phone:
                            number = p_profile.phone
                        else:
                            p_address = ParentAddress.objects.filter(parent=i).first()
                            number = p_address.phone_no if p_address and p_address.phone_no else ''

                    obj.phone_number = number
            else:
                if enquiry:
                    WhatsappSubscribers.objects.create(is_Subscriber=is_Subscriber, phone_number=phone_number, enquiry__id=enquiry)
                else:
                    WhatsappSubscribers.objects.create(is_Subscriber=is_Subscriber, phone_number=phone_number)

        user_id = settings.WHATSAPP_HSM_USER_ID
        password = settings.WHATSAPP_HSM_USER_PASSWORD

        if is_Subscriber == 'True':
            response = requests.get(
                f"https://media.smsgupshup.com/GatewayAPI/rest?method=OPT_IN&format=json&userid={user_id}&password={password}&phone_number={phone_number}&v=1.1&auth_scheme=plain&channel=WHATSAPP")
            result = response.json()
        elif is_Subscriber == 'False':
            response = requests.get(
                f"https://media.smsgupshup.com/GatewayAPI/rest?method=OPT_OUT&format=json&userid={user_id}&password={password}&phone_number={phone_number}&v=1.1&auth_scheme=plain&channel=WHATSAPP")
            result = response.json()
        else:
            pass

        return Response("SUCCESS", status=status.HTTP_200_OK)
        # return Response("Need phone number to do action")

class DeviceRegistration(APIView):
    def get(self, request):
        qs = DeviceRegistrationToken.objects.all()
        serializer = DeviceRegistrationTokenSerializer(qs, many=True)
        return Response({'result': serializer.data})

    def post(self,request):
        device =""
        city =None
        is_boarding_school =None
        is_online_school =None

        if request.user_agent.is_pc:
            device = "Pc"
        elif request.user_agent.is_mobile:
            device = "Mobile"
        else:
            pass

        reg_id = request.data.get('device_token')
        city_slug = request.data.get('city_slug')
        if city_slug:
            city_obj = City.objects.get(slug=city_slug)
            is_boarding_school = True if city_obj.slug == "boarding-schools" else False
            if is_boarding_school:
                city = None
            else:
                city = city_obj

            is_online_school = True if city_obj.slug == "online-schools" else False
            if is_online_school:
                city = None
            else:
                city = city_obj


        if request.user.is_authenticated and DeviceRegistrationToken.objects.filter(user=self.request.user).exists():
            obj = DeviceRegistrationToken.objects.get(user =self.request.user)
            if device == "Pc":
                obj.pc_registration_id=reg_id
            elif device =="Mobile":
                obj.mobile_registration_id=reg_id
            obj.city = obj.city if is_boarding_school or is_online_school == "True" else city
            obj.is_boarding_school = is_boarding_school
            obj.is_online_school = is_online_school
            obj.save()
            return Response({'result':"Device Registration key added"})
        elif DeviceRegistrationToken.objects.filter(pc_registration_id=reg_id).exists() or DeviceRegistrationToken.objects.filter(mobile_registration_id=reg_id).exists():
            if DeviceRegistrationToken.objects.filter(pc_registration_id=reg_id).exists():
                obj = DeviceRegistrationToken.objects.get(pc_registration_id=reg_id)
                obj.user = self.request.user if request.user.is_authenticated else obj.user
                obj.city = obj.city if is_boarding_school or is_online_school == "True" else city
                obj.is_boarding_school = is_boarding_school
                obj.is_online_school = is_online_school
                obj.save()
                return Response({'result':"Device Registration key added"})

            elif DeviceRegistrationToken.objects.filter(mobile_registration_id=reg_id).exists():
                obj = DeviceRegistrationToken.objects.get(mobile_registration_id=reg_id)
                obj.user = self.request.user if request.user.is_authenticated else obj.user
                obj.city = obj.city if is_boarding_school or is_online_school == "True" else city
                obj.is_boarding_school = is_boarding_school
                obj.is_online_school = is_online_school
                obj.save()
                return Response({'result':"Device Registration key added"})

        else:
            if request.user.is_authenticated :
                if device =="Pc":
                    obj = DeviceRegistrationToken.objects.create(user=self.request.user,pc_registration_id=reg_id,is_boarding_school=is_boarding_school,is_online_school=is_online_school,city=city)
                    return Response({'result':"Device Registration key added"})
                elif device =="Mobile":
                    obj = DeviceRegistrationToken.objects.create(user=self.request.user,mobile_registration_id=reg_id,is_boarding_school=is_boarding_school,is_online_school=is_online_school,city=city)
                    return Response({'result':"Device Registration key added"})

            else:
                if device =="Pc":
                    obj = DeviceRegistrationToken.objects.create(pc_registration_id=reg_id,is_boarding_school=is_boarding_school,is_online_school=is_online_school,city=city)
                    return Response({'result':"Device Registration key added"})
                elif device =="Mobile":
                    obj = DeviceRegistrationToken.objects.create(mobile_registration_id=reg_id,is_boarding_school=is_boarding_school,is_online_school=is_online_school,city=city)
                    return Response({'result':"Device Registration key added"})
            return Response({})

class UserSelectedCityView(APIView):
    def post(self,request,*args, **kwargs):
        data =request.data
        city = data.get('city_slug')
        if city:
            if request.user.is_authenticated:
                city = City.objects.get(slug=city)
                if UserSelectedCity.objects.filter(user=self.request.user).exists():
                    obj = UserSelectedCity.objects.get(user=self.request.user)
                    if city.slug =="boarding-schools":
                        obj.is_boarding_school = True
                    elif city.slug =="online-schools":
                        obj.is_online_school = True
                    else:
                        obj.city = city
                    obj.save()
                    return Response("City Updated", status=status.HTTP_200_OK)

                else:
                    obj = UserSelectedCity.objects.create(user=self.request.user,city=city)
                    if city.slug =="boarding-schools":
                        obj.is_boarding_school = True
                    elif city.slug =="online-schools":
                        obj.is_online_school = True
                    else:
                        obj.city = city
                    obj.save()
                    return Response("City Stored", status=status.HTTP_200_OK)
            else:
                return Response("User is not authenticated", status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response("City is not provided", status=status.HTTP_400_BAD_REQUEST)
