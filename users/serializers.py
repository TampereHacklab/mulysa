from rest_framework import serializers

from . import models


class UserSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = models.CustomUser
        fields = ('url',
                  'email',
                  'first_name',
                  'last_name',
                  'phone',
                  'is_active',
                  'is_staff',
                  'created',
                  'last_modified',
                  'marked_for_deletion_on',
                  'birthday',
                  'nick',
                  'municipality',
                  )
        read_only_fields = ('is_active', 'is_staff', 'created',
                            'last_modified', 'marked_for_deletion_on')


class UserActivationSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = models.CustomUser
        fields = ('is_active',)
        extra_kwargs = {'is_active': {'required': True}}
