from rest_framework.permissions import BasePermission

class IsReceptionist(BasePermission):
    """
    Allows access only to users with the 'receptionist' role.
    """

    def has_permission(self, request, view):
        # Check if the user is authenticated and has a user_type of 'receptionist'
        return request.user.is_authenticated and request.user.user_type == 'receptionist'
