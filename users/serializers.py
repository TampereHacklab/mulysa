from rest_framework import serializers
from . import models


class UserSerializer(serializers.HyperlinkedModelSerializer):

#    url = serializers.HyperlinkedIdentityField(view_name='user-detail', read_only=True)

    class Meta:
        model = models.CustomUser
        fields = ('url', 'email', 'username', )
