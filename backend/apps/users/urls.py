from django.urls import path
from .views import (
    UserMeView, RegisterView, ChangeOwnPasswordView,
    AdminChangePasswordView, UserListView,
    TelegramGenerateTokenView, TelegramUnlinkView,
)

urlpatterns = [
    path('', UserListView.as_view(), name='user-list'),
    path('me/', UserMeView.as_view(), name='user-me'),
    path('me/telegram-token/', TelegramGenerateTokenView.as_view(), name='telegram-generate-token'),
    path('me/telegram-unlink/', TelegramUnlinkView.as_view(), name='telegram-unlink'),
    path('register/', RegisterView.as_view(), name='user-register'),
    path('change-password/', ChangeOwnPasswordView.as_view(), name='change-own-password'),
    path('<int:pk>/change-password/', AdminChangePasswordView.as_view(), name='admin-change-password'),
]
