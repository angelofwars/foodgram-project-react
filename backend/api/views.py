from django.shortcuts import get_object_or_404
from rest_framework import decorators, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from user.models import User, Follow
from rest_framework.permissions import IsAuthenticated
from djoser.views import UserViewSet
from django.conf import settings
from django.db.models import Sum
from urllib.parse import unquote
from .filters import RecipeFilter, IngredientSearchFilter
from recipes.models import (Favorite, Ingredient, RecipeIngredient, Recipe,
                            Tag, Foodbasket)
from .utils import add_and_del, out_list_ingredients
from .pagination import LimitPageNumberPagination
from .permissions import IsOwnerOrReadOnly, IsAdminOrReadOnly
from .serializers import (AddFavoriteRecipeSerializer,
                          AddShoppingListRecipeSerializer,
                          IngredientSerializer, RecipeReadSerializer,
                          RecipeWriteSerializer, TagSerializer, UserSerializer,
                          FollowSerializer,
                          )


class UserViewSet(UserViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    pagination_class = LimitPageNumberPagination

    @action(detail=False,
            methods=['get'],
            permission_classes=[IsAuthenticated])
    def subscriptions(self, request):
        user = request.user
        queryset = User.objects.filter(following__user=user)
        page = self.paginate_queryset(queryset)
        serializer = FollowSerializer(page,
                                      many=True,
                                      context={'request': request})
        return self.get_paginated_response(serializer.data)

    @action(detail=True,
            methods=['post', 'delete'],
            permission_classes=[IsAuthenticated])
    def subscribe(self, request, id):
        user = request.user
        author = get_object_or_404(User, id=id)

        if request.method == 'POST':
            if user.id == author.id:
                return Response({'detail': 'Нельзя подписаться на себя'},
                                status=status.HTTP_400_BAD_REQUEST)
            if Follow.objects.filter(author=author, user=user).exists():
                return Response({'detail': 'Вы уже подписаны!'},
                                status=status.HTTP_400_BAD_REQUEST)
            Follow.objects.create(user=user, author=author)
            serializer = FollowSerializer(author,
                                          context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            if not Follow.objects.filter(user=user, author=author).exists():
                return Response({'errors': 'Вы не подписаны'},
                                status=status.HTTP_400_BAD_REQUEST)
            subscription = get_object_or_404(Follow,
                                             user=user,
                                             author=author)
            subscription.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для отображения тегов."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (IsAdminOrReadOnly,)
    pagination_class = None


class IngredientsViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для отображения ингредиентов."""
    permission_classes = (IsAdminOrReadOnly,)
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (IngredientSearchFilter,)
    search_fields = ("^name",)

    def get_queryset(self):
        """Получение ингредиентов в соответствии с запросом."""
        name = self.request.query_params.get('name')
        queryset = self.queryset
        if name:
            if name[0] == '%':
                name = unquote(name)
            else:
                name = name.translate(settings.INCORRECT_LAYOUT)
            name = name.lower()
            start_queryset = list(queryset.filter(name__istartswith=name))
            ingridients_set = set(start_queryset)
            cont_queryset = queryset.filter(name__icontains=name)
            start_queryset.extend(
                [ing for ing in cont_queryset if ing not in ingridients_set]
            )
            queryset = start_queryset
        return queryset


class RecipeViewSet(viewsets.ModelViewSet):
    """Вьюсет для отображения рецептов.
    Для запросов на чтение используется RecipeReadSerializer
    Для запросов на изменение используется RecipeWriteSerializer"""

    queryset = Recipe.objects.all()
    permission_classes = (IsOwnerOrReadOnly,)
    serializer_class = RecipeReadSerializer
    filterset_class = RecipeFilter
    pagination_class = LimitPageNumberPagination

    def get_serializer_class(self):
        if self.request.method in ("POST", "PUT", "PATCH"):
            return RecipeWriteSerializer
        return RecipeReadSerializer

    @decorators.action(
        detail=True,
        methods=["POST", "DELETE"],
        permission_classes=[permissions.IsAuthenticated]
    )
    def favorite(self, request, pk):
        return add_and_del(
            AddFavoriteRecipeSerializer, Favorite, request, pk
        )

    @decorators.action(
        detail=True,
        methods=["POST", "DELETE"],
        permission_classes=[permissions.IsAuthenticated]
    )
    def shopping_cart(self, request, pk):
        """Добавляем/удаляем рецепт в 'список покупок'"""
        return add_and_del(
            AddShoppingListRecipeSerializer, Foodbasket, request, pk
        )

    @decorators.action(
        detail=False,
        methods=["GET"],
        permission_classes=[permissions.IsAuthenticated]
    )
    def download_shopping_cart(self, request):
        ingredients = RecipeIngredient.objects.filter(
            recipe__shopping_list__user=self.request.user
        ).values(
            "ingredient__name",
            "ingredient__measurement_unit"
        ).order_by("ingredient__name").annotate(amount=Sum("amount"))
        return out_list_ingredients(self, request, ingredients)
