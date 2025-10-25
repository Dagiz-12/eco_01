from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from django.contrib.auth import login
from .models import User, Profile
from .serializers import UserRegistrationSerializer, UserLoginSerializer, UserProfileSerializer


class UserRegistrationView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()

            # Create user profile
            Profile.objects.create(user=user)

            # Generate token
            token, created = Token.objects.get_or_create(user=user)

            return Response({
                'message': 'User registered successfully',
                'token': token.key,
                'user_id': user.id
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserLoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']

            # Login user (for session auth)
            login(request, user)

            # Get or create token
            token, created = Token.objects.get_or_create(user=user)

            return Response({
                'message': 'Login successful',
                'token': token.key,
                'user': UserProfileSerializer(user).data
            }, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)

    def put(self, request):
        serializer = UserProfileSerializer(
            request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserLogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        # Delete token for token authentication
        Token.objects.filter(user=request.user).delete()

        # Logout for session authentication
        from django.contrib.auth import logout
        logout(request)

        return Response({'message': 'Logged out successfully'}, status=status.HTTP_200_OK)
