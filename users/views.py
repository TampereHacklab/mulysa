from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser

from . import models
from . import serializers
from . import permissions


class UserViewSet(viewsets.ModelViewSet):
    """
    User CRUD
    """
    model = models.CustomUser
    queryset = models.CustomUser.objects.all()
    serializer_class = serializers.UserSerializer
    permission_classes = (
        permissions.IsStaffOrSelf,
    )

    # limit available methods, we don't want users to be able to create new
    # users or delete themself
    http_method_names = ['get', 'patch', 'head', 'options', 'trace']

    def get_queryset(self):
        """
        Staff users can get all objects, normal users only themself
        """
        if(self.request.user.is_staff):
            return self.model.objects.all()
        return self.model.objects.filter(id=self.request.user.id)

    @action(detail=True, methods=['patch'], permission_classes=[IsAdminUser])
    def add_transaction(self, request, pk=None):
        """
        Add a payment transaction for the user (TODO!)
        Or maybe this should be in its own "transactions"??
        """
        # TODO: implement me, allow staff users to push
        # transaction information under the user
        #
        pass

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def set_activation(self, request, pk=None):
        """
        Change the user to active or inactive, only available for admin users
        """
        user = self.get_object()

        if request.data:
            serializer = serializers.UserActivationSerializer(
                data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors,
                                status=status.HTTP_400_BAD_REQUEST)
            user.is_active = data['is_active']
            user.save()

        return Response(serializers.UserSerializer(user, context={'request': request}).data)
