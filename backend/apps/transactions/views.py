import re

from django.db.models import Q, Sum, Case, When, DecimalField, Value
from django.db.models.functions import TruncMonth
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import Transaction, Category, Person, ExpenseSplit
from .serializers import (
    TransactionListSerializer, TransactionDetailSerializer,
    CategorySerializer, PersonSerializer, ExpenseSplitSerializer,
)
from .filters import TransactionFilter


class TransactionViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet
):
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = TransactionFilter
    search_fields = ['merchant', 'description']
    ordering_fields = ['date', 'amount']
    ordering = ['-date']
    http_method_names = ['get', 'patch', 'head', 'options']

    def get_queryset(self):
        return Transaction.objects.filter(user=self.request.user).select_related('category')

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return TransactionDetailSerializer
        return TransactionListSerializer

    def partial_update(self, request, *args, **kwargs):
        # Only allow editing description and category fields
        allowed = {'description', 'category_name', 'category'}
        data = {k: v for k, v in request.data.items() if k in allowed}
        serializer = self.get_serializer(self.get_object(), data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class ExpenseSplitViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = ExpenseSplitSerializer
    pagination_class = None
    http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']

    def _get_transaction(self):
        return get_object_or_404(
            Transaction,
            pk=self.kwargs['transaction_pk'],
            user=self.request.user
        )

    def get_queryset(self):
        tx = self._get_transaction()
        return tx.splits.all()

    def perform_create(self, serializer):
        tx = self._get_transaction()
        # Create Person inline if provided by name
        person_name = self.request.data.get('person_name')
        person = None
        if person_name:
            person, _ = Person.objects.get_or_create(
                user=self.request.user,
                name=person_name
            )
        serializer.save(
            transaction=tx,
            person=person,
            person_name_snapshot=person_name or (person.name if person else ''),
        )


class CategoryViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet
):
    permission_classes = [IsAuthenticated]
    serializer_class = CategorySerializer
    pagination_class = None

    def get_queryset(self):
        return Category.get_valid_for_user(self.request.user.id)

    def perform_create(self, serializer):
        name = re.sub(r'[^a-z0-9_-]', '_', serializer.validated_data.get('label', '').lower())
        serializer.save(owner=self.request.user, name=name)

    def destroy(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.is_default or obj.owner != request.user:
            return Response({'detail': 'No autorizado.'}, status=status.HTTP_403_FORBIDDEN)
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class PersonViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet
):
    permission_classes = [IsAuthenticated]
    serializer_class = PersonSerializer
    pagination_class = None
    http_method_names = ['get', 'post', 'patch', 'head', 'options']

    def get_queryset(self):
        show_archived = self.request.query_params.get('archived') == 'true'
        qs = Person.objects.filter(user=self.request.user)
        if not show_archived:
            qs = qs.filter(archived=False)
        return qs

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class DashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        start_str = request.query_params.get('start')
        end_str = request.query_params.get('end')
        year_str = request.query_params.get('year')
        month_str = request.query_params.get('month')

        type_str = request.query_params.get('type')
        search_str = request.query_params.get('search')
        category_str = request.query_params.get('category')

        qs = Transaction.objects.filter(user=request.user)
        if year_str and month_str:
            qs = qs.filter(date__year=int(year_str), date__month=int(month_str))
        elif year_str:
            qs = qs.filter(date__year=int(year_str))
        else:
            if start_str:
                qs = qs.filter(date__gte=start_str)
            if end_str:
                qs = qs.filter(date__lt=end_str)
        if type_str:
            qs = qs.filter(type=type_str)
        if search_str:
            qs = qs.filter(
                Q(merchant__icontains=search_str) | Q(description__icontains=search_str)
            )
        if category_str:
            qs = qs.filter(category_name=category_str)

        # Monthly totals with net_total via conditional aggregate
        paid_back_sum = Sum(
            Case(
                When(splits__paid_back=True, then='splits__amount'),
                default=Value(0),
                output_field=DecimalField(max_digits=14, decimal_places=2),
            )
        )

        monthly = (
            qs.annotate(month=TruncMonth('date'))
            .values('month')
            .annotate(total=Sum('amount'), paid_back=paid_back_sum)
            .order_by('month')
        )

        monthly_totals = [
            {
                'year': m['month'].year,
                'month': m['month'].month,
                'total': str(m['total'] or 0),
                'net_total': str((m['total'] or 0) - (m['paid_back'] or 0)),
            }
            for m in monthly
        ]

        # By category
        by_cat_paid_back = Sum(
            Case(
                When(splits__paid_back=True, then='splits__amount'),
                default=Value(0),
                output_field=DecimalField(max_digits=14, decimal_places=2),
            )
        )

        by_category = (
            qs.values('category_name')
            .annotate(total=Sum('amount'), paid_back=by_cat_paid_back)
            .order_by('-total')
        )

        by_cat_list = [
            {
                'category_name': c['category_name'] or 'sin categoria',
                'total': str(c['total'] or 0),
                'net_total': str((c['total'] or 0) - (c['paid_back'] or 0)),
            }
            for c in by_category
        ]

        return Response({
            'period': {'start': start_str, 'end': end_str},
            'monthly_totals': monthly_totals,
            'by_category': by_cat_list,
        })
