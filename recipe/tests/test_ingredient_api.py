from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from core.models import Ingredient
from recipe.serializers import IngredientSerializer

INGREDIENTS_URL = reverse('recipe:ingredient-list')


class PublicIngredientApiTests(TestCase):
    """Probar los API ingredientes disponibles publicamente"""

    def setUp(self) -> None:
        self.client = APIClient()

    def test_login_required(self):
        """Prueba que login sea requerido para obtener los ingredientes"""
        res = self.client.get(INGREDIENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientApiTests(TestCase):
    """Probar los API ingredientes disponibles privados"""

    def setUp(self) -> None:
        self.user = get_user_model().objects.create_user(
            'test@localhost.com',
            'password'
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_ingredients_list(self):
        """Probar obtener ingredients"""
        Ingredient.objects.create(user=self.user, name="ingrediente1")
        Ingredient.objects.create(user=self.user, name="ingrediente2")

        res = self.client.get(INGREDIENTS_URL)

        ingredients = Ingredient.objects.all().order_by('name')
        serializer = IngredientSerializer(ingredients, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_ingredient_limited_to_user(self):
        """Probar que los tags retornados sean del usuario"""
        user2 = get_user_model().objects.create_user(
            'local@localhost.com',
            'localpass'
        )

        Ingredient.objects.create(user=user2, name='salt')
        ingredient = Ingredient.objects.create(
            user=self.user, name='Comfort Food')

        res = self.client.get(INGREDIENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], ingredient.name)

    def test_create_ingredient_successful(self):
        """Prueba creando nuevo ingrediente si no esta duplicado"""
        payload = {'name': 'Manzana'}
        self.client.post(INGREDIENTS_URL, payload)

        exists = Ingredient.objects.filter(
            user=self.user,
            name=payload['name']
        ).exists()
        self.assertTrue(exists)

    def test_create_ingredient_invalid(self):
        """Prueba crear un nuevo ingrediente con un payload invalido"""
        payload = {'name': ''}
        res = self.client.post(INGREDIENTS_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
