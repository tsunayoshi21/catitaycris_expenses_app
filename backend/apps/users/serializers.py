from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import get_user_model

User = get_user_model()


class UserMeSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'telegram_chat_id', 'created_at']
        read_only_fields = ['id', 'username', 'email', 'telegram_chat_id', 'created_at']


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
    imap_host = serializers.CharField(default='imap.gmail.com')
    imap_user = serializers.CharField(write_only=True)
    imap_password = serializers.CharField(write_only=True)
    last_checked = serializers.DateTimeField(required=False, allow_null=True, default=None)

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError('El nombre de usuario ya está en uso.')
        return value


class ChangeOwnPasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)


class AdminChangePasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField(write_only=True)


class UserListSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'is_staff']


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        data['is_staff'] = self.user.is_staff
        return data
