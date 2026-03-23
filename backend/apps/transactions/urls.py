from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import TransactionViewSet, CategoryViewSet, PersonViewSet, DashboardView, ExpenseSplitViewSet

router = DefaultRouter()
router.register(r'transactions', TransactionViewSet, basename='transaction')
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'persons', PersonViewSet, basename='person')

urlpatterns = [
    path('', include(router.urls)),
    # Nested routes for splits under transactions (manual, no extra dependency)
    path(
        'transactions/<int:transaction_pk>/splits/',
        ExpenseSplitViewSet.as_view({'get': 'list', 'post': 'create'}),
        name='transaction-splits-list',
    ),
    path(
        'transactions/<int:transaction_pk>/splits/<int:pk>/',
        ExpenseSplitViewSet.as_view({'get': 'retrieve', 'patch': 'partial_update', 'delete': 'destroy'}),
        name='transaction-splits-detail',
    ),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
]
