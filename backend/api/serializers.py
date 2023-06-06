from django.conf import settings
from django.contrib.auth.hashers import check_password
from django.db import models, transaction
from drf_extra_fields.fields import Base64ImageField
from rest_framework import (exceptions, fields, relations, serializers, status,
                            validators)
from django.shortcuts import get_object_or_404
from recipes.models import (Favorite, Ingredient, RecipeIngredient, Recipe,
                            Tag, Foodbasket)
from user.models import User, Subscribe
from rest_framework.exceptions import ValidationError
from djoser.serializers import (PasswordSerializer, UserCreateSerializer,
                                UserSerializer)


class CropRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Recipe.
    Определён укороченный набор полей для некоторых эндпоинтов."""

    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ("id", "name", "image", "cooking_time")
        read_only_fields = ("id", "name", "image", "cooking_time")


class UserListSerializer(UserSerializer):
    """Серелайзер списка пользователей"""
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('email', 'id',
                  'role',
                  'username',
                  'first_name',
                  'last_name',
                  'is_subscribed')

    def get_is_subscribed(self, obj):
        return obj.id in self.context['subscriptions']


class UserCreateSerializer(UserCreateSerializer):
    """Серелайзер создания пользователя"""
    class Meta:
        model = User
        fields = '__all__'
        required_fields = '__all__'


class TagSerializer(serializers.ModelSerializer):
    """ Сериализатор для модели Tag."""

    class Meta:
        model = Tag
        fields = "__all__"


class IngredientSerializer(serializers.ModelSerializer):
    """ Сериализатор для модели Ingredient."""

    class Meta:
        model = Ingredient
        fields = '__all__'


class RecipeIngredient(serializers.ModelSerializer):
    """ Сериализатор для вывода количество ингредиентов в рецепте."""

    id = serializers.PrimaryKeyRelatedField(
        read_only=True,
        source='ingredient'
    )

    name = serializers.SlugRelatedField(
        source='ingredient',
        read_only=True,
        slug_field='name'
    )

    measurement_unit = serializers.SlugRelatedField(
        source='ingredient',
        read_only=True,
        slug_field='measurement_unit'
    )

    class Meta:
        model = RecipeIngredient
        fields = '__all__'


class RecipeReadSerializer(serializers.ModelSerializer):
    """ Сериализатор для возврата списка рецептов."""

    tags = TagSerializer(many=True, read_only=True)
    author = UserSerializer(read_only=True)
    ingredients = RecipeIngredient(many=True,
                                   required=True,
                                   source="ingredient_list")
    image = Base64ImageField()
    is_favorited = fields.SerializerMethodField(read_only=True)
    is_in_shopping_cart = fields.SerializerMethodField(read_only=True)

    class Meta:
        model = Recipe
        fields = (
            "id", "tags", "author", "ingredients", 'is_favorited',
            "is_in_shopping_cart", 'name', 'image', 'text', 'cooking_time',
        )

    def get_ingredients(self, recipe):
        """Получает список ингредиентов для рецепта."""
        return recipe.ingredients.values(
            "id",
            "name",
            "measurement_unit",
            amount=models.F("recipes__ingredient_list")
        )

    def get_is_favorited(self, obj):
        """Проверка - находится ли рецепт в избранном."""
        request = self.context.get("request")
        return (request and request.user.is_authenticated
                and request.user.favorites.filter(recipe=obj).exists())

    def get_is_in_shopping_cart(self, obj):
        """Проверка - находится ли рецепт в списке покупок."""
        request = self.context.get("request")
        return (request and request.user.is_authenticated
                and request.user.shopping_list.filter(recipe=obj).exists())


class RecipeIngredientPuthSerializer(serializers.ModelSerializer):
    """ Сериализатор для ингредиента в рецепте."""

    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())

    class Meta:
        model = RecipeIngredient
        fields = ("id", "amount")


class RecipeWriteSerializer(serializers.ModelSerializer):
    """ Сериализатор для создание рецептов."""

    tags = relations.PrimaryKeyRelatedField(queryset=Tag.objects.all(),
                                            many=True)
    author = UserSerializer(read_only=True)
    ingredients = RecipeIngredientPuthSerializer(many=True)
    image = Base64ImageField(max_length=None, use_url=True)

    class Meta:
        model = Recipe
        fields = ("id", "image", "tags", "author", "ingredients",
                  "name", "text", "cooking_time")
        read_only_fields = ("author",)

    @transaction.atomic
    def create_bulk_ingredients(self, ingredients, recipe):
        for ingredient in ingredients:
            RecipeIngredient.objects.get_or_create(
                recipe=recipe,
                ingredient=ingredient["id"],
                amount=ingredient["amount"]
            )

    @transaction.atomic
    def create(self, validated_data):
        ingredients_list = validated_data.pop('ingredients')
        tags = validated_data.pop("tags")
        author = self.context.get("request").user
        recipe = Recipe.objects.create(author=author, **validated_data)
        recipe.save()
        recipe.tags.set(tags)
        self.create_bulk_ingredients(ingredients_list, recipe)
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        tags = validated_data.pop("tags")
        ingredients = validated_data.pop("ingredients")
        instance.tags.clear()
        instance.tags.set(tags)
        instance.ingredients.clear()
        self.create_bulk_ingredients(recipe=instance,
                                     ingredients=ingredients)
        return super().update(instance, validated_data)

    def validate_ingredients(self, value):
        """Проверяем ингредиенты в рецепте."""
        ingredients = self.initial_data.get("ingredients")
        if len(ingredients) <= 0:
            raise exceptions.ValidationError(
                {"ingredients": settings.INGREDIENT_MIN_AMOUNT_ERROR}
            )
        ingredients_list = []
        for item in ingredients:
            if item["id"] in ingredients_list:
                raise exceptions.ValidationError(
                    {"ingredients": settings.INGREDIENT_DUBLICATE_ERROR}
                )
            ingredients_list.append(item['id'])
            if int(item["amount"]) <= 0:
                raise exceptions.ValidationError(
                    {"amount": settings.INGREDIENT_MIN_AMOUNT_ERROR}
                )
        return value

    def validate_cooking_time(self, data):
        """Проверяем время приготовления рецепта."""
        cooking_time = self.initial_data.get("cooking_time")
        if int(cooking_time) <= 0:
            raise serializers.ValidationError(
                settings.COOKING_TIME_MIN_ERROR
            )
        return data

    def validate_tags(self, value):
        """Проверяем на наличие уникального тега."""
        tags = value
        if not tags:
            raise exceptions.ValidationError(
                {"tags": settings.TAG_ERROR}
            )
        tags_list = []
        for tag in tags:
            if tag in tags_list:
                raise exceptions.ValidationError(
                    {"tags": settings.TAG_UNIQUE_ERROR}
                )
            tags_list.append(tag)
        return value

    def to_representation(self, instance):
        request = self.context.get('request')
        context = {"request": request}
        return RecipeReadSerializer(instance,
                                    context=context).data


class SetPasswordSerializer(PasswordSerializer):
    current_password = serializers.CharField(
        required=True,
        label='Текущий пароль')

    def validate(self, data):
        user = self.context.get('request').user
        if data['new_password'] == data['current_password']:
            raise serializers.ValidationError({
                "new_password": settings.ERROR_EQUAL_PASSWORD})
        check_current = check_password(data['current_password'], user.password)
        if check_current is False:
            raise serializers.ValidationError({
                "current_password": settings.ERROR_WRONG_PASSWORD})
        return data


class SubscribeRecipeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class SubscribeSerializer(serializers.ModelSerializer):
    email = serializers.CharField(
        source='author.email',
        read_only=True)
    id = serializers.IntegerField(
        source='author.id',
        read_only=True)
    username = serializers.CharField(
        source='author.username',
        read_only=True)
    first_name = serializers.CharField(
        source='author.first_name',
        read_only=True)
    last_name = serializers.CharField(
        source='author.last_name',
        read_only=True)
    recipes = serializers.SerializerMethodField()
    is_subscribed = serializers.SerializerMethodField()
    recipes_count = serializers.ReadOnlyField(
        source='author.recipe.count')

    class Meta:
        model = Subscribe
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'is_subscribed', 'recipes', 'recipes_count',)

    def validate(self, data):
        user = self.context.get('request').user
        author = self.context.get('author_id')
        if user.id == int(author):
            raise serializers.ValidationError({
                'errors': 'Нельзя подписаться на самого себя'})
        if Subscribe.objects.filter(user=user, author=author).exists():
            raise serializers.ValidationError({
                'errors': settings.ERROR_ALREADY_FOLLOW})
        return data

    def get_recipes(self, obj):
        recipes = obj.author.recipe.all()
        return SubscribeRecipeSerializer(
            recipes,
            many=True).data

    def get_is_subscribed(self, obj):
        subscribe = obj.id in self.context['subscriptions']
        if subscribe:
            return True
        return False


class AddFavoriteRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор добавления рецептов в избранное."""

    class Meta:
        model = Favorite
        fields = ("user", "recipe")
        validators = [
            validators.UniqueTogetherValidator(
                queryset=Favorite.objects.all(),
                fields=["user", "recipe"],
                message=settings.RECIPE_IN_FAVORITE
            )
        ]

    def to_representation(self, instance):
        request = self.context.get("request")
        return CropRecipeSerializer(
            instance.recipe,
            context={"request": request}
        ).data


class AddShoppingListRecipeSerializer(AddFavoriteRecipeSerializer):
    """Сериализатор добавления рецептов в список покупок."""

    class Meta(AddFavoriteRecipeSerializer.Meta):
        model = Foodbasket
        validators = [
            validators.UniqueTogetherValidator(
                queryset=Foodbasket.objects.all(),
                fields=["user", "recipe"],
                message=settings.ALREADY_BUY
            )
        ]

    def to_representation(self, instance):
        request = self.context.get("request")
        return CropRecipeSerializer(
            instance.recipe,
            context={"request": request}
        ).data


class AuthSignUpSerializer(serializers.ModelSerializer):

    def validate(self, data):
        username = data.get('username')
        if not User.objects.filter(username=username).exists():
            if username == 'me':
                raise ValidationError('Username указан неверно!')
            return data
        user = get_object_or_404(User, username=username)
        if data.get('email') != user.email:
            raise ValidationError('Почта указана неверно!')
        return data

    class Meta:
        model = User
        fields = ('email', 'username')


class AuthTokenSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    confirmation_code = serializers.CharField(max_length=50)
