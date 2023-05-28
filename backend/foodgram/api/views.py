
from django.shortcuts import get_object_or_404
from rest_framework import decorators, permissions, status, viewsets
from rest_framework.decorators import action, api_view
from rest_framework.filters import SearchFilter
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from users.models import Follow, User
from django.conf import settings
from django.db.models import Sum
from urllib.parse import unquote
from reportlab.pdfgen import canvas
from recipes.models import (Favorite, Ingredient, RecipeIngredient, Recipe,
                        Tag, Foodbasket)
from .utils import add_and_del, out_list_ingredients
from .pagination import LimitPageNumberPagination
from .permissions import IsOwnerOrReadOnly, IsAdminOrReadOnly
from .serializers import (AuthSignUpSerializer, AuthTokenSerializer,
                          AddFavoriteRecipeSerializer,
                          AddShoppingListRecipeSerializer, FollowSerializer,
                          IngredientSerializer, RecipeReadSerializer,
                          RecipeWriteSerializer, TagSerializer, UserSerializer,
                          CropRecipeSerializer)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (IsAdminOrReadOnly,)
    filter_backends = (SearchFilter,)
    search_fields = ("=username",)
    lookup_field = "username"

    @action(
        detail=False,
        methods=["GET", "PATCH"],
        permission_classes=(IsOwnerOrReadOnly,)
    )
    def me(self, request):
        if request.method == "PATCH":
            serializer = UserSerializer(
                request.user, data=request.data, partial=True
            )
            serializer.is_valid(raise_exception=True)
            serializer.save(role=request.user.role)
            return Response(serializer.data, status=status.HTTP_200_OK)
        serializer = UserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def update(self, request, pk=None, **kwargs):
        if "partial" in kwargs:
            instance = self.get_object()
            serializer = UserSerializer(
                instance, data=request.data, partial=True
            )
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)


@api_view(["POST"])
def users_signup(request):
    username = request.data.get("username")
    if not User.objects.filter(username=username).exists():
        serializer = AuthSignUpSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        send_confirmation_code(username)
        return Response(serializer.data, status=status.HTTP_200_OK)
    user = get_object_or_404(User, username=username)
    serializer = AuthSignUpSerializer(
        user, data=request.data, partial=True
    )
    serializer.is_valid(raise_exception=True)
    serializer.save()
    send_confirmation_code(username)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["POST"])
def users_get_token(request):
    serializer = AuthTokenSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    username = serializer.validated_data["username"]
    confirmation_code = serializer.validated_data["confirmation_code"]
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        return Response(
            "Пользователь не найден", status=status.HTTP_404_NOT_FOUND
        )
    if user.confirmation_code == confirmation_code:
        refresh = RefreshToken.for_user(user)
        token_data = {"token": str(refresh.access_token)}
        return Response(token_data, status=status.HTTP_200_OK)
    return Response(
        "Код подтверждения неверный", status=status.HTTP_400_BAD_REQUEST
    )


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
    search_fields = ('^name',)
    
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
    