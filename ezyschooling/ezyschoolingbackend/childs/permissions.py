from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsChildParentOrReadOnly(BasePermission):
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
            and request.user.is_parent
        ):
            return True
        else:
            return False


