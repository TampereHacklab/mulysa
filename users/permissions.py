from rest_framework import permissions


class IsStaffOrSelf(permissions.BasePermission):
    """
    Permissions that we are the user
    """
    def has_object_permission(self, request, view, obj):
        """
        Staff users can change any user, normal users only themself
        """
        if(request.user.is_staff):
            return True
        return obj.id == request.user.id
