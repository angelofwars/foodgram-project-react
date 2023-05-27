from django.conf import settings
from django.db import models, transaction
from drf_extra_fields.fields import Base64ImageField
from rest_framework import (exceptions, fields, relations, serializers, status,
                            validators)

from recipes.models import (Favorite, Ingredient, IngredientInRecipe, Recipe,
                            ShoppingCart, Tag)
from user.models import Follow, User



class UserSerializer(serializers.ModelSerializer):
    """Сериализатор для авторизованных и 
    не аворизованных пользователей."""

    class Meta:
        model = User
        fields = (
            "username", "email", "first_name", "last_name", "bio", "role"
        )
    
    def get_is_subscribed(self, author):
        """Проверка подписки пользователей."""
        request = self.context.get("request")
        return (request and request.user.is_authenticated
                and request.user.follower.filter(author=author).exists())


class TagSerializer(serializers.ModelSerializer):
    """ Сериализатор для модели Tag."""

    class Meta:
        model = Tag
        fields = "__all__"
