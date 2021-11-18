from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from core import models
from recipe.serializers import TagSerializer

TAGS_URL = reverse('recipe:tag-list')


class PublicTagApiTests(TestCase):
    """Probar los API tags disponibles publicamente"""

    def setUp(self) -> None:
        self.client = APIClient()

    def test_login_required(self):
        """Prueba que login sea requerido para obtener los tags"""
        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateTagApiTests(TestCase):
    """Probar los API tags disponibles privados"""

    def setUp(self) -> None:
        self.user = get_user_model().objects.create_user(
            'test@localhost.com',
            'password'
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_tags(self):
        """Probar obtener tags"""
        models.Tag.objects.create(user=self.user, name="Meat")
        models.Tag.objects.create(user=self.user, name="Banana")

        res = self.client.get(TAGS_URL)

        tags = models.Tag.objects.all().order_by('-name')
        serializer = TagSerializer(tags, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_tags_limited_to_user(self):
        """Probar que los tags retornados sean del usuario"""
        user2 = get_user_model().objects.create_user(
            'local@localhost.com',
            'localpass'
        )

        models.Tag.objects.create(user=user2, name='Raspberry')
        tag = models.Tag.objects.create(user=self.user, name='Comfort Food')

        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], tag.name)

    def test_create_tag_successful(self):
        """Prueba creando nuevo tag si no esta duplicado"""
        payload = {'name': 'simple'}
        self.client.post(TAGS_URL, payload)

        exists = models.Tag.objects.filter(
            user=self.user, name=payload['name']).exists()
        self.assertTrue(exists)

    def test_create_tag_invalid(self):
        """Prueba crear un nuevo blog con un payload invalido"""
        payload = {'name': ''}
        res = self.client.post(TAGS_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_tags_assigned_to_recipes(self):
        """Prueba filtrando tags basado en receta"""
        tag1 = models.Tag.objects.create(user=self.user, name='Breakfast')
        tag2 = models.Tag.objects.create(user=self.user, name='Lunch')
        recipe = models.Recipe.objects.create(
            title='Coriander eggs on toast',
            time_minutes=10,
            price=5,
            user=self.user,
        )
        recipe.tags.add(tag1)

        res = self.client.get(TAGS_URL, {'assigned_only': 1})

        serializer1 = TagSerializer(tag1)
        serializer2 = TagSerializer(tag2)
        self.assertIn(serializer1.data, res.data)
        self.assertNotIn(serializer2.data, res.data)

    def test_retrieve_tags_assigned_unique(self):
        """Prueba filtro tag asignado por items unicos"""
        tag = models.Tag.objects.create(user=self.user, name='Breakfast')
        recipe1 = models.Recipe.objects.create(
            title='Pancakes',
            time_minutes=5,
            price=3.00,
            user=self.user,
        )
        recipe1.tags.add(tag)

        recipe2 = models.Recipe.objects.create(
            title='Torta',
            time_minutes=2,
            price=1154.10,
            user=self.user,
        )
        recipe2.tags.add(tag)

        res = self.client.get(TAGS_URL, {'assigned_only': 1})

        self.assertEqual(len(res.data),1)
