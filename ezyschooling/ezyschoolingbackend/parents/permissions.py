from rest_framework.permissions import BasePermission

from parents.models import ParentProfile


class ParentProfileModification(BasePermission):
    def has_object_permission(self, request, view, obj):
        if not request.method == "GET" and request.user.is_authenticated:
            parent_profiles = ParentProfile.objects.filter(
                user=request.user
            ).values_list("id", flat=True)
        if request.method == "GET":
            return True
        elif (
            request.method in ["PUT", "PATCH"]
            and request.user.is_authenticated
            and obj.id in parent_profiles
        ):
            return obj.id in parent_profiles
        elif (
            request.method == "DELETE"
            and request.user.is_authenticated
            and obj.id in parent_profiles
        ):
            if obj.id == int(request.user.current_parent):
                return False
            else:
                return True
        else:
            return False


class IsParentOrReadOnly(BasePermission):
    """
    The request is authenticated as a parent user, or is a read-only request.
    """

    def has_permission(self, request, view):
        if request.method == "GET":
            return True
        elif (
            request.method == "POST"
            and request.user
            and request.user.is_authenticated
            and request.user.is_parent
        ):
            return True
        else:
            return False


class IsParentOrAuthenticatedReadOnly(BasePermission):
    """
    The request is authenticated as a parent user, or is a read-only request.
    """

    def has_permission(self, request, view):
        if request.method == "GET" and request.user and request.user.is_authenticated:
            return True
        elif (
            request.method == "POST"
            and request.user
            and request.user.is_authenticated
            and request.user.is_parent
        ):
            return True
        else:
            return False


class IsParent(BasePermission):
    """
    The request is authenticated as a parent user, or is a read-only request.
    """

    def has_permission(self, request, view):
        if request.user and request.user.is_authenticated and request.user.is_parent:
            return True
        else:
            return False
