from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
# from django.urls.base import reverse_lazy

from rest_framework.test import APIClient
from rest_framework import status

CREATE_USER_URL = reverse('user:create')
TOKEN_URL = reverse('user:token')
ME_URL = reverse('user:me')


def create_user(**params):
    return get_user_model().objects.create_user(**params)


class PublicUserApiTests(TestCase):
    """Testear la API PUBLICA DEL USUARIO"""

    def setUp(self):
        self.client = APIClient()

    def test_create_valid_user_success(self):
        """Probar crear usuario con un payload exitoso"""
        payload = {
            'email': 'prueba@localhost.com',
            'password': 'acavaelpasword',
        }
        res = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        user = get_user_model().objects.get(**res.data)
        self.assertTrue(user.check_password(payload['password']))
        self.assertNotIn('password', res.data)

    def test_user_exists(self):
        """Probar que un usuario ya existe"""
        payload = {
            'email': 'test@localhost.com',
            'password': 'testpassword',
            'name': 'Test Name',
        }
        create_user(**payload)
        res = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_too_short(self):
        """La contraseña debe ser mayor a 5 caracteres"""
        payload = {
            'email': 'testttt@localhost.com',
            'password': 'pass',
            'name': 'Test Name',
        }
        res = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

        user_exists = get_user_model().objects.filter(
            email=payload['email']).exists()
        self.assertFalse(user_exists)

    def test_create_token_for_user(self):
        """El token sea creado para el usuario"""
        payload = {
            'email': 'test@localhost.com',
            'password': 'testpassword',
            'name': 'Test Name',
        }
        create_user(**payload)
        res = self.client.post(TOKEN_URL, payload)

        self.assertIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
    
    def test_create_token_invalid_credentials(self):
        """Probar que el token no es creado con credenciales invalidas"""
        create_user(email='test@localhost.com', password='testpass')
        payload = {'email':'test@localhost.com', 'password':'wrongPassword', 'name':'Test Name'}
        res = self.client.post(TOKEN_URL, payload)

        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_no_user(self):
        """Prueba que no se crea un token si no existe el usuario"""
        payload = {
            'email':'test@localhost.com',
            'password':'testpass',
            'name':'Test Name',
        }
        res = self.client.post(TOKEN_URL, payload)
        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_missing_field(self):
        """Probar que el mail y contraseña sean requeridos"""
        res = self.client.post(TOKEN_URL, {'email':'one','password':''})
        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_user_unauthorized(self):
        """Prueba que la autencitacion sea requerida para los usuarios"""
        res = self.client.get(ME_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

class PrivateUserApiTests(TestCase):
    """Testear la API PRIVADA DEL USUARIO"""

    def setUp(self) -> None:
        self.user = create_user(
            email='test@localhost.com',
            password='testpassword',
            name='Test Name',
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_retrieve_profile_sucess(self):
        """Probar obtener perfil para usuario con Login"""
        res = self.client.get(ME_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, {'email': self.user.email,})

    def test_post_me_not_allowed(self):
        """Prueba que el POST no sea permitido"""
        res = self.client.post(ME_URL, {})
        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_update_user_profile(self):
        """Probar que el usuario esta siendo actualizado si esta auta autenticado"""
        payload = {
            'email':'test@localhost.com',
            'password':'testpass',
            'name':'Test Name',
        }

        res = self.client.patch(ME_URL, payload)
        self.user.refresh_from_db()
        self.assertEqual(self.user.name, payload['name'])
        self.assertTrue(self.user.check_password(payload['password']))
        self.assertEqual(res.status_code, status.HTTP_200_OK)