from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.conf import settings
from django.contrib.auth import get_user_model

User = get_user_model()


class UserMeSerializer(serializers.ModelSerializer):
    telegram_bot_username = serializers.SerializerMethodField()
    telegram_linked = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'telegram_chat_id',
            'telegram_link_token', 'telegram_linked',
            'telegram_bot_username', 'created_at',
        ]
        read_only_fields = fields

    def get_telegram_bot_username(self, obj) -> str:
        return settings.TELEGRAM_BOT_USERNAME

    def get_telegram_linked(self, obj) -> bool:
        return bool(obj.telegram_chat_id)


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
    imap_host = serializers.CharField(default='imap.gmail.com')
    imap_user = serializers.CharField(write_only=True)
    imap_password = serializers.CharField(write_only=True)

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
        data['username'] = self.user.username
        data['is_staff'] = self.user.is_staff
        return data
