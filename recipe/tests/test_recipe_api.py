import tempfile
import os
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from core.models import Recipe, Tag, Ingredient
from recipe import serializers
from PIL import Image


RECIPES_URL = reverse('recipe:recipe-list')


def image_upload_url(recipe_id):
    return reverse('recipe:recipe-upload-image', args=[recipe_id])


def sample_tag(user, name='meat'):
    """Crea Tag Ejemplo"""
    return Tag.objects.create(user=user, name=name)


def sample_ingredient(user, name='Coco'):
    """Crea Tag Ejemplo"""
    return Ingredient.objects.create(user=user, name=name)


def sample_recipe(user, **params):
    """Crear y retornar una receta"""
    defaults = {
        'title': 'Sample recipe',
        'time_minutes': 10,
        'price': 5.00,

    }
    defaults.update(params)
    return Recipe.objects.create(user=user, **defaults)


def detail_url(recipe_id):
    """Retorna receta detail url"""
    return reverse('recipe:recipe-detail', args=[recipe_id])


class PublicRecipeApiTests(TestCase):
    """Test acceso no autenticado al API"""

    def setUp(self) -> None:
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            'test@localhost.com',
            'testpass',
        )
        self.client.force_authenticate(self.user)

    def test_retrieve_recipes(self):
        """Probar obtener lista de recetas"""
        sample_recipe(user=self.user)
        sample_recipe(user=self.user, title="Tortilla")

        res = self.client.get(RECIPES_URL)

        recipes = Recipe.objects.all().order_by('id')
        serializer = serializers.RecipeSerializer(recipes, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_recipes_limited_to_user(self):
        """Probar obtener receta para un usuario"""
        user2 = get_user_model().objects.create_user(
            'other@localhost.com',
            'passwordd'
        )
        sample_recipe(user=user2)
        sample_recipe(user=self.user, title="ravioles con crema")

        res = self.client.get(RECIPES_URL)

        recipes = Recipe.objects.filter(user=self.user)
        serializer = serializers.RecipeSerializer(recipes, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data, serializer.data)

    def test_view_recipe_detail(self):
        recipe = sample_recipe(user=self.user)
        recipe.tags.add(sample_tag(user=self.user))
        recipe.ingredients.add(sample_ingredient(user=self.user))

        url = detail_url(recipe.id)
        res = self.client.get(url)

        serializer = serializers.RecipeDetailSerializer(recipe)
        self.assertEqual(res.data, serializer.data)

    def test_create_basic_recipe(self):
        payload = {
            'title': 'Test Recipe',
            'time_minutes': 30,
            'price': 10.00,
        }
        res = self.client.post(RECIPES_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=res.data['id'])
        for key in payload.keys():
            self.assertEqual(payload[key], getattr(recipe, key))

    def test_create_recipe_with_tags(self):
        """Prueba Crear receta con Tags"""
        tag1 = sample_tag(user=self.user, name='Tag 1')
        tag2 = sample_tag(user=self.user, name='Tag 2')
        payload = {
            'title': 'Test Recipe with two tags',
            'tags': [tag1.id, tag2.id],
            'time_minutes': 30,
            'price': 10.00
        }
        res = self.client.post(RECIPES_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=res.data['id'])
        tags = recipe.tags.all()
        self.assertEqual(tags.count(), 2)
        self.assertIn(tag1, tags)
        self.assertIn(tag2, tags)

    def test_create_recipe_with_ingredients(self):
        """Prueba Crear receta con Tags"""
        ingredient1 = sample_ingredient(user=self.user, name='Ingredient 1')
        ingredient2 = sample_ingredient(user=self.user, name='Ingredient 2')
        payload = {
            'title': 'Test Recipe with two tags',
            'ingredients': [ingredient1.id, ingredient2.id],
            'time_minutes': 30,
            'price': 10.00
        }
        res = self.client.post(RECIPES_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=res.data['id'])
        ingredients = recipe.ingredients.all()
        self.assertEqual(ingredients.count(), 2)
        self.assertIn(ingredient1, ingredients)
        self.assertIn(ingredient2, ingredients)

    def test_filter_recipes_by_tags(self):
        """Test filtrar recetas por tag"""
        recipe1 = sample_recipe(user=self.user, title='Thai')
        recipe2 = sample_recipe(user=self.user, title='comida carnaca')
        recipe3 = sample_recipe(user=self.user, title='Milanga')
        tag1 = sample_tag(user=self.user, name='vegetable')
        tag2 = sample_tag(user=self.user, name='Carnaca')
        recipe1.tags.add(tag1)
        recipe2.tags.add(tag2)
        res = self.client.get(RECIPES_URL, {'tags': f'{tag1.id},{tag2.id}'})
        serializer1 = serializers.RecipeSerializer(recipe1)
        serializer2 = serializers.RecipeSerializer(recipe2)
        serializer3 = serializers.RecipeSerializer(recipe3)
        self.assertIn(serializer1.data, res.data)
        self.assertIn(serializer2.data, res.data)
        self.assertNotIn(serializer3.data, res.data)

    def test_filter_recipes_by_ingredients(self):
        """Test filtrar recetas por tag"""
        recipe1 = sample_recipe(user=self.user, title='Coca colada')
        recipe2 = sample_recipe(user=self.user, title='comida carnaca')
        recipe3 = sample_recipe(user=self.user, title='Milanga')

        ing1 = sample_ingredient(user=self.user, name='coconut')
        ing2 = sample_ingredient(user=self.user, name='milk')

        recipe1.ingredients.add(ing1)
        recipe2.ingredients.add(ing2)

        res = self.client.get(
            RECIPES_URL, {'ingredients': f'{ing1.id},{ing2.id}'})
        # print('---------------------------', res.data)
        serializer1 = serializers.RecipeSerializer(recipe1)
        serializer2 = serializers.RecipeSerializer(recipe2)
        serializer3 = serializers.RecipeSerializer(recipe3)
        # print('---------------serializer------------', serializer1.data)

        self.assertIn(serializer1.data, res.data)
        self.assertIn(serializer2.data, res.data)
        self.assertNotIn(serializer3.data, res.data)


class PrivateRecipeApiTests(TestCase):
    pass


class RecipeImageUploadTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            'user@localhost.com', 'testest12')
        self.client.force_authenticate(self.user)
        self.recipe = sample_recipe(user=self.user)

    def tearDown(self):
        self.recipe.image.delete()

    def test_upload_image_to_recipe(self):
        """Probar subir imagen"""
        url = image_upload_url(self.recipe.id)
        with tempfile.NamedTemporaryFile(suffix='.jpg') as ntf:
            img = Image.new('RGB', (10, 10))
            img.save(ntf, format='JPEG')
            ntf.seek(0)
            res = self.client.post(url, {'image': ntf}, format='multipart')
        self.recipe.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('image', res.data)
        self.assertTrue(os.path.exists(self.recipe.image.path))

    def test_upload_image_bad_request(self):
        """Prueba subir imagen"""
        url = image_upload_url(self.recipe.id)
        res = self.client.post(url, {'image': 'notimage'}, format='multipart')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
