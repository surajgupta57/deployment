from rest_framework.permissions import BasePermission, SAFE_METHODS
from admin_custom.models import DatabaseCAdminUser
from parents.models import ParentProfile
from .models import BoardingSchoolExtend

class IsSchoolOrReadOnly(BasePermission):
    """
    The request is authenticated as a parent user, or is a read-only request.
    """

    def has_object_permission(self, request, view, obj):
        if request.method not in SAFE_METHODS:
            if obj.user == request.user:
                return True
            else:
                return False
        return True

    def has_permission(self, request, view):
        if request.method == "GET":
            return True
        elif (
            request.method not in SAFE_METHODS
            and request.user
            and request.user.is_authenticated
            and request.user.is_school
        ):
            return True
        else:
            return False


class IsSchoolOrAuthenticatedReadOnly(BasePermission):
    """
    The request is authenticated as a parent user, or is a read-only request.
    """

    def has_object_permission(self, request, view, obj):
        if obj.user == request.user:
            return True
        else:
            return False

    def has_permission(self, request, view):
        if request.method == "GET" and request.user and request.user.is_authenticated:
            return True
        elif (
            request.method == "POST"
            and request.user
            and request.user.is_authenticated
            and request.user.is_school
        ):
            return True
        else:
            return False


class IsSchool(BasePermission):
    """
    The request is authenticated as a parent user, or is a read-only request.
    """

    def has_object_permission(self, request, view, obj):
        if obj.user == request.user:
            return True
        else:
            return False

    def has_permission(self, request, view):
        if request.user and request.user.is_authenticated and request.user.is_school:
            return True
        else:
            return False


class HasSchoolChildModelPermissionOrReadOnly(BasePermission):
    """
    The request is authenticated as a parent user, or is a read-only request.
    """

    def has_object_permission(self, request, view, obj):
        if request.method not in SAFE_METHODS:
            if obj.school.user == request.user:
                return True
            else:
                return False
        return True

    def has_permission(self, request, view):
        if request.method == "GET":
            return True
        elif (
            request.method not in SAFE_METHODS
            and request.user
            and request.user.is_authenticated
            and (request.user.is_school or DatabaseCAdminUser.objects.filter(user__user_ptr__id=request.user.id).exists())
        ):
            return True
        else:
            return False


class HasSchoolObjectPermission(BasePermission):

    def has_object_permission(self, request, view, obj):
        if request.method not in SAFE_METHODS:
            if obj.school.user == request.user:
                return True
            else:
                return False
        return True


class SchoolDashboardPermission(BasePermission):

    def has_object_permission(self, request, view, obj):
        if request.method not in SAFE_METHODS:
            if request.user.current_school == obj.school_id:
                return True
            else:
                return False
        return True


class SchoolViewPermission(BasePermission):
    def has_permission(self, request, view):
        if request.user.is_authenticated and request.user.is_school:
            if request.user.schoolprofile_set.first().views_permission or request.user.schoolprofile_set.first().views_check_permission:
                return True
            else:
                return False
        else:
            return False

    def has_object_permission(self, request, view, obj):
        if request.user.current_school == obj.school_id:
            return True
        else:
            return False

class SchoolViewPermission(BasePermission):
    def has_permission(self, request, view):
        if request.user.is_authenticated and request.user.is_school and request.user.schoolprofile_set.first().views_permission:
            return True
        else:
            return False

    def has_object_permission(self, request, view, obj):
        if request.user.current_school == obj.school_id:
            return True
        else:
            return False

class SchoolContactClickDataPermission(BasePermission):
    def has_permission(self, request, view):
        if request.user.is_authenticated and request.user.is_school and request.user.schoolprofile_set.first().contact_data_permission:
            return True
        else:
            return False

    def has_object_permission(self, request, view, obj):
        if request.user.current_school == obj.school_id:
            return True
        else:
            return False


class SchoolEnquiryPermission(BasePermission):

    def has_permission(self, request, view):
        if request.method == "POST" and request.user.is_authenticated and request.user.is_school:
            return False
        if (request.method == "GET"
                and request.user.is_authenticated
                and request.user.is_school
                and not request.user.schoolprofile_set.first().enquiry_permission):
            return False
        return True

class BoardingSchoolExtendProfilePermissions(BasePermission):
    def has_permission(self, request, view):
        if request.method == "GET":
            return True
        elif (
            request.method not in SAFE_METHODS
            and request.user
            and request.user.is_authenticated
            and request.user.is_school and BoardingSchoolExtend.objects.filter(extended_school__id=request.user.current_school).exists()
        ):
            return True
        else:
            return False
