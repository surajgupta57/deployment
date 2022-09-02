from rest_framework.permissions import BasePermission


class IsExpert(BasePermission):
    """
    The request is authenticated as a expert user
    """

    def has_permission(self, request, view):
        if request.user and request.user.is_authenticated and request.user.is_expert:
            if request.method == "GET":
                return True
            else:
                return False
        return False
