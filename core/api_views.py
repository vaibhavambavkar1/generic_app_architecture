from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth.models import User
from .serializers import SignupSerializer, ForgotPasswordVerifySerializer

class SignupView(generics.CreateAPIView):
    """
    Registers a new user and sets up their security question/answer.
    """
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = SignupSerializer

class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Standard JWT Login endpoint provided by simplejwt.
    """
    permission_classes = (AllowAny,)

class ForgotPasswordQuestionView(APIView):
    """
    Returns the security question for a given username.
    """
    permission_classes = (AllowAny,)

    def get(self, request):
        username = request.query_params.get('username')
        if not username:
            return Response({"error": "username parameter is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(username=username)
            return Response({"security_question": user.profile.security_question})
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

class ResetPasswordView(APIView):
    """
    Resets the password if the security answer matches the stored hash.
    """
    permission_classes = (AllowAny,)

    def post(self, request):
        serializer = ForgotPasswordVerifySerializer(data=request.data)
        if serializer.is_valid():
            try:
                user = User.objects.get(username=serializer.validated_data['username'])
                
                # Check security answer
                if user.profile.check_security_answer(serializer.validated_data['security_answer']):
                    user.set_password(serializer.validated_data['new_password'])
                    user.save()
                    return Response({"message": "Password reset successful"}, status=status.HTTP_200_OK)
                else:
                    return Response({"error": "Incorrect security answer"}, status=status.HTTP_400_BAD_REQUEST)
                    
            except User.DoesNotExist:
                return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
                
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
