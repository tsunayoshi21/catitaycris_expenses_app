from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import status
from rest_framework.generics import RetrieveAPIView, ListAPIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import (
    UserMeSerializer, RegisterSerializer,
    ChangeOwnPasswordSerializer, AdminChangePasswordSerializer,
    UserListSerializer, CustomTokenObtainPairSerializer,
)
from ..accounts.models import Account

User = get_user_model()


class UserMeView(RetrieveAPIView):
    serializer_class = UserMeSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        with transaction.atomic():
            account = Account(
                imap_host=data['imap_host'],
                last_checked=data.get('last_checked'),
            )
            account.set_imap_credentials(data['imap_user'], data['imap_password'])
            account.save()

            user = User.objects.create_user(
                username=data['username'],
                password=data['password'],
                account=account,
            )

        return Response({'id': user.id, 'username': user.username}, status=status.HTTP_201_CREATED)


class ChangeOwnPasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangeOwnPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        user = request.user
        if not user.check_password(data['current_password']):
            return Response({'detail': 'Contraseña actual incorrecta.'}, status=status.HTTP_400_BAD_REQUEST)
        user.set_password(data['new_password'])
        user.save(update_fields=['password'])
        return Response({'detail': 'Contraseña actualizada.'})


class AdminChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        if not request.user.is_staff:
            return Response({'detail': 'No tenés permisos para esto.'}, status=status.HTTP_403_FORBIDDEN)
        try:
            target_user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response({'detail': 'Usuario no encontrado.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = AdminChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        target_user.set_password(serializer.validated_data['new_password'])
        target_user.save(update_fields=['password'])
        return Response({'detail': 'Contraseña actualizada.'})


class UserListView(ListAPIView):
    serializer_class = UserListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if not self.request.user.is_staff:
            return User.objects.none()
        return User.objects.all().order_by('username')


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
