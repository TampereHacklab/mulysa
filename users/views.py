from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from . import models
from . import serializers


class UserViewSet(viewsets.ModelViewSet):
    queryset = models.CustomUser.objects.all()
    serializer_class = serializers.UserSerializer

    @action(detail=True, methods=['post', 'get'])
    def set_activation(self, request, pk=None):
        """
        Change the users active bit
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
