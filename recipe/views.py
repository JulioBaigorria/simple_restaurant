from django.db.models import query
from rest_framework import viewsets, mixins, status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from core import models

from recipe import serializers


class BaseRecipeAttrViewSet(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.CreateModelMixin, mixins.UpdateModelMixin):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        """Retornar objetos para el usuario autenticado"""
        assigned_only = bool(
            int(self.request.query_params.get('assigned_only', 0)))

        queryset = self.queryset

        if assigned_only:
            queryset = queryset.filter(recipe__isnull=False)

        return queryset.all().order_by('id')

    def perform_create(self, serializer):
        """ Create nuevo ingrediente o tag """
        serializer.save(user=self.request.user)


class TagViewset(BaseRecipeAttrViewSet):
    """Manejar tags en base de datos"""
    queryset = models.Tag.objects.all()
    serializer_class = serializers.TagSerializer


class IngredientViewset(BaseRecipeAttrViewSet):
    """Manejar ingredientes en base de datos"""
    queryset = models.Ingredient.objects.all()
    serializer_class = serializers.IngredientSerializer


class RecipeViewset(viewsets.ModelViewSet):
    """Manejar recipes en base de datos"""
    queryset = models.Recipe.objects.all()
    serializer_class = serializers.RecipeSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        """Retornar objetos para el usuario autenticado"""
        return self.queryset.filter(user=self.request.user)

    def get_serializer_class(self):
        print(self.action)
        """Retorna clase de serializador apropiada
            si es retrieve se usa el detalle"""
        if self.action == 'retrieve':
            return serializers.RecipeDetailSerializer
        elif self.action == 'upload_image':
            return serializers.RecipeImageSerializer
        return self.serializer_class

    def perform_create(self, serializer):
        """ Create nuevo recipe """
        serializer.save(user=self.request.user)

    @action(methods=['POST'], detail=True, url_path='upload_image')
    def upload_image(self, request, pk=None):
        recipe = self.get_object()
        serializer = self.get_serializer(
            recipe,
            data=request.data
        )
        if serializer.is_valid():
            serializer.save()
            return Response(
                serializer.data,
                status=status.HTTP_200_OK,
            )
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST,
        )

    def _params_to_ints(self, qs):
        return[int(str_id) for str_id in qs.split(',')]

    def get_queryset(self):
        tags = self.request.query_params.get('tags')
        ingredients = self.request.query_params.get('ingredients')
        queryset = self.queryset
        if tags:
            tag_ids = self._params_to_ints(tags)
            queryset = queryset.filter(tags__id__in=tag_ids)

        if ingredients:
            ing_ids = self._params_to_ints(ingredients)
            queryset = queryset.filter(ingredients__id__in=ing_ids)

        return queryset.filter(user=self.request.user)
