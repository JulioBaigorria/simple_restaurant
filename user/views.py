from django.contrib.auth import logout
from user.serializers import UserSerializer, AuthTokenSerializer
from core.models import User
from rest_framework import status
from rest_framework.response import Response
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework import generics, authentication, permissions

from rest_framework.settings import api_settings


class CreateUserView(generics.CreateAPIView):
    """Crear nuevo usuario en el sistema"""
    serializer_class = UserSerializer


class CreateTokenView(ObtainAuthToken):
    """Crear nuevo auth token para el usuario"""
    serializer_class = AuthTokenSerializer
    renderer_classes = api_settings.DEFAULT_RENDERER_CLASSES


class ManageUserView(generics.RetrieveUpdateAPIView):
    """Manejar el usuario autenticado"""
    serializer_class = UserSerializer
    authentication_classes = (authentication.TokenAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self):
        return self.request.user


class Logout(generics.GenericAPIView):
    def post(self, request, *args, **kwargs):
        logout(request)
        return Response({'message': 'Sesión cerrada correctamente.'}, status=status.HTTP_200_OK)

class ListUsersView(generics.ListAPIView):
    serializer_class = UserSerializer
    authentication_classes = (authentication.TokenAuthentication,)
    permission_classes = (permissions.IsAuthenticated, permissions.IsAdminUser)
    queryset = User.objects.all()
