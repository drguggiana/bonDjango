from rest_framework import permissions


# custom defined permission class to only allow editing of an instance if the person is the owner
class IsOwnerOrReadOnly(permissions.BasePermission):
    # override of the has_object_permission class
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        # only give permission if user is owner
        return obj.owner == request.user
