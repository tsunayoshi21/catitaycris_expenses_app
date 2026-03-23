from django.urls import path
from .views import UserMeView, RegisterView, ChangeOwnPasswordView, AdminChangePasswordView, UserListView

urlpatterns = [
    path('', UserListView.as_view(), name='user-list'),
    path('me/', UserMeView.as_view(), name='user-me'),
    path('register/', RegisterView.as_view(), name='user-register'),
    path('change-password/', ChangeOwnPasswordView.as_view(), name='change-own-password'),
    path('<int:pk>/change-password/', AdminChangePasswordView.as_view(), name='admin-change-password'),
]
