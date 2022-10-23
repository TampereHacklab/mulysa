from decimal import Decimal

from django.db.models import Q, Sum
from django.db.models.functions import TruncDay, Coalesce

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response

from . import filters, models, permissions, serializers


class UserViewSet(viewsets.ModelViewSet):
    """
    User CRUD
    """

    model = models.CustomUser
    queryset = models.CustomUser.objects.all()
    serializer_class = serializers.UserSerializer
    permission_classes = (permissions.IsStaffOrSelf,)
    filter_class = filters.UserFilter

    # limit available methods, we don't want users to be able to create new
    # users or delete themself
    http_method_names = ["get", "patch", "head", "options", "trace"]

    def get_queryset(self):
        """
        Staff users can get all objects, normal users only themself
        """
        if self.request.user.is_staff:
            return self.model.objects.all()
        return self.model.objects.filter(id=self.request.user.id)

    @action(detail=True, methods=["patch"], permission_classes=[IsAdminUser])
    def set_activation(self, request, pk=None):
        """
        Change the user to active or inactive, only available for admin users
        """
        user = self.get_object()

        serializer = serializers.UserActivationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user.is_active = serializer.validated_data["is_active"]
        user.save()

        return Response(
            serializers.UserSerializer(user, context={"request": request}).data
        )


class BankTransactionAggregateViewSet(viewsets.ModelViewSet):
    """
    Get aggregate overview of bank transaction data

    Response contains
    aggregatedate (day for aggregation)
    withdravals summed by aggregatedate
    deposits summed by aggregatedate

    filter with `?date__gte=2022-01-01&date__lte=2022-12-31`
    """

    serializer_class = serializers.BankTransactionAggregateSerializer
    permission_classes = (IsAuthenticated,)
    http_method_names = ["get", "options", "trace"]
    pagination_class = None
    filterset_fields = {"date": ["gte", "lte"]}

    queryset = (
        models.BankTransaction.objects.values(
            aggregatedate=TruncDay("date"),
        )
        .annotate(
            withdrawals=Coalesce(Sum("amount", filter=Q(amount__lt=0)), Decimal(0)),
            deposits=Coalesce(Sum("amount", filter=Q(amount__gt=0)), Decimal(0)),
        )
        .order_by("date")
    )
