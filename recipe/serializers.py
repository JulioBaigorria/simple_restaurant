from rest_framework import serializers
from rest_framework.settings import reload_api_settings
from core import models


class TagSerializer(serializers.ModelSerializer):
    """Serializador para el Objeto de Tag"""
    class Meta:
        model = models.Tag
        fields = ('id', 'name',)
        read_only_fields = ('id', )


class IngredientSerializer(serializers.ModelSerializer):
    """Serializador para el Objeto de Ingredient"""
    class Meta:
        model = models.Ingredient
        fields = ('id', 'name',)
        read_only_fields = ('id', )

class RecipeSerializer(serializers.ModelSerializer):
    """Serializador para el Objeto de Recipe"""
    ingredients = serializers.PrimaryKeyRelatedField(many=True, 
        queryset = models.Ingredient.objects.all())
    
    tags = serializers.PrimaryKeyRelatedField(many=True,
        queryset = models.Tag.objects.all())

    # ingredients = IngredientSerializer(many=True, read_only=True)
    # tags = TagSerializer(many=True, read_only=True)

    class Meta:
        model = models.Recipe
        fields = ('id', 'title', 'ingredients', 'tags', 'time_minutes', 'price', 'image', 'link',)
        read_only_fields = ('id', )

class RecipeDetailSerializer(RecipeSerializer):
    """Serializa Detalle de receta"""
    ingredients = IngredientSerializer(many=True, read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    

class RecipeImageSerializer(serializers.ModelSerializer):
    """Serializer imagenes"""
    class Meta:
        model = models.Recipe
        fields = ('id', 'image',)
        read_only_fields = ('id',)