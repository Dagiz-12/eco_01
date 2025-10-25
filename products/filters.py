import django_filters
from .models import Product


class ProductFilter(django_filters.FilterSet):
    min_price = django_filters.NumberFilter(
        field_name='price', lookup_expr='gte')
    max_price = django_filters.NumberFilter(
        field_name='price', lookup_expr='lte')
    category = django_filters.CharFilter(field_name='category__slug')
    brand = django_filters.CharFilter(field_name='brand__slug')
    in_stock = django_filters.BooleanFilter(method='filter_in_stock')
    featured = django_filters.BooleanFilter(field_name='is_featured')

    class Meta:
        model = Product
        fields = ['category', 'brand', 'min_price',
                  'max_price', 'in_stock', 'featured']

    def filter_in_stock(self, queryset, name, value):
        if value:
            return queryset.filter(quantity__gt=0)
        return queryset
