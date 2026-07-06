from rest_framework import serializers
from django.contrib.auth.models import User
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.password_validation import validate_password
from .models import UserProfile

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email')

class SignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    security_question = serializers.CharField(write_only=True, required=True)
    security_answer = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'security_question', 'security_answer')

    def create(self, validated_data):
        security_question = validated_data.pop('security_question')
        security_answer = validated_data.pop('security_answer')

        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password']
        )
        
        # UserProfile is created via signal, now we update it
        profile = user.profile
        profile.security_question = security_question
        profile.set_security_answer(security_answer)
        
        return user

class ForgotPasswordVerifySerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    security_answer = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])
