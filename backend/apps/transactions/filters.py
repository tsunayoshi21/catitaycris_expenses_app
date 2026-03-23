import django_filters
from .models import Transaction


class TransactionFilter(django_filters.FilterSet):
    start = django_filters.DateTimeFilter(field_name='date', lookup_expr='gte')
    end = django_filters.DateTimeFilter(field_name='date', lookup_expr='lt')
    year = django_filters.NumberFilter(field_name='date', lookup_expr='year')
    month = django_filters.NumberFilter(field_name='date', lookup_expr='month')
    type = django_filters.MultipleChoiceFilter(
        choices=[
            ('debito', 'Débito'),
            ('credito', 'Crédito'),
            ('transferencia', 'Transferencia'),
            ('ingreso', 'Ingreso'),
            ('desconocido', 'Desconocido'),
        ]
    )
    category = django_filters.CharFilter(field_name='category_name', lookup_expr='icontains')

    class Meta:
        model = Transaction
        fields = ['start', 'end', 'year', 'month', 'type', 'category']
