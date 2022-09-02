from rest_framework.permissions import BasePermission, SAFE_METHODS

from parents.models import ParentProfile
from .models import CAdminUser, CounselorCAdminUser, DatabaseCAdminUser
from schools.models import SchoolProfile

class IsExecutiveUser(BasePermission):
    """
    The request is authenticated as a executive user.
    It work for counselor admin also.
    Further groups can be assign.
    """

    def has_permission(self, request, view):
        result = False
        if request.user.is_authenticated:
            try:
                cadmin_user_obj = CAdminUser.objects.get(user_ptr__id=request.user.id)
                # counselor_obj = CounselorCAdminUser.objects.get(user=cadmin_user_obj)
                if cadmin_user_obj.is_executive:
                    result = True
            except:
                result = False

        return result

class IsAdminUser(BasePermission):

    """
    The request is authenticated as a admin user.
    It work for counselor admin also.
    Further groups can be assign.
    """

    def has_permission(self, request, view):
        result = False
        if request.user.is_authenticated:
            try:
                cadmin_user_obj = CAdminUser.objects.get(user_ptr__id=request.user.id)
                # counselor_obj = CounselorCAdminUser.objects.get(user=cadmin_user_obj)
                if cadmin_user_obj.is_admin:
                    result = True
            except:
                result = False

        return result

class SchoolCounsellingDataPermission(BasePermission):

    def has_permission(self, request, view):
        result = False
        if request.user.is_authenticated:
            try:
                school = SchoolProfile.objects.get(id=request.user.current_school)
                result = True
                # counselor_obj = CounselorCAdminUser.objects.get(user=cadmin_user_obj)
                # if school.counselling_data_permission:
                #     result = True
            except:
                result = False

        return result

class IsDatabaseAdminUser(BasePermission):
    """
    The request is authenticated as a database user.
    It work for counselor admin also.
    Further groups can be assign.
    """

    def has_permission(self, request, view):
        result = False
        if request.user.is_authenticated and DatabaseCAdminUser.objects.filter(user__user_ptr__id=request.user.id).exists():
            # try:
            #     dbcadmin_user_obj = DatabaseCAdminUser.objects.get(user__user_ptr__id=request.user.id)
            #     # counselor_obj = CounselorCAdminUser.objects.get(user=cadmin_user_obj)
            #     if dbcadmin_user_obj.user.is_executive:
            result = True
        else:
            result = False

        return result
