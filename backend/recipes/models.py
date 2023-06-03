from django.db import models
from django.core.validators import MinValueValidator
from user.models import User
from colorfield.fields import ColorField
from django.conf import settings
from django.core import validators


class Ingredient(models.Model):
    """Модель ингридиентов"""
    name = models.CharField(
        verbose_name="Ингридиенты",
        max_length=100,
        help_text="Ингридиенты"
    )
    measurement_unit = models.CharField(
        verbose_name="Единица измерения",
        max_length=200,
        help_text="Единица измерения",
    )

    class Meta:
        ordering = ('name',)
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return self.name[:settings.QUERY_SET_LENGTH].capitalize()


class Tag(models.Model):
    """Модель тега"""

    COLOR_PALETTE = [
        ("#0000FF", 'Синий'),
        ("#FFA500", 'Оранжевый'),
        ("#008000", 'Зеленый'),
        ("#800080", 'Фиолетовый'),
        ("#FFFF00", 'Желтый'),
        ("#6F4E37", 'Кофе и кофеные напитки'),
    ]

    name = models.CharField(
        verbose_name="Название",
        max_length=250,
        unique=True,
        help_text="Имя тега"
    )

    color = ColorField(
        default="##0000FF",
        verbose_name="Название",
        choices=COLOR_PALETTE,
        help_text="Имя тега"
    )

    slug = models.SlugField(
        verbose_name="Slag юрл",
        max_length=200,
        unique=True,
        help_text="Slag url"
    )

    class Meta:
        ordering = ('name',)
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name[:settings.QUERY_SET_LENGTH]

    def __unicode__(self):
        return self.name


class Recipe(models.Model):
    """Модель рецепта"""
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="recipes",
        verbose_name="Автор рецепта")

    name = models.CharField(
        max_length=200,
        verbose_name="Название рецепта"
    )

    image = models.ImageField(
        upload_to="recipes/",
        verbose_name="Картинка рецепта"
    )

    text = models.TextField(
        verbose_name="Описание рецепта"
    )

    ingredients = models.ManyToManyField(
        Ingredient,
        through="RecipeIngredient",
        verbose_name="Ингридиенты",
        related_name="recipes",
    )

    tags = models.ManyToManyField(
        Tag,
        verbose_name="Теги",
    )

    cooking_time = models.PositiveSmallIntegerField(
        validators=(
            validators.MinValueValidator(
                1, message="Минимальное время приготовления 1 минута"),),
        verbose_name="Время приготовления")

    class Meta:
        ordering = ["-id"]
        verbose_name = "Рецепт"
        verbose_name_plural = "Рецепты"


class RecipeIngredient(models.Model):
    """
    Количество ингредиентов в рецепте.
    Модель связывает Recipe и Ingredient с указанием количества ингредиентов.
    """

    recipe = models.ForeignKey(
        Recipe,
        verbose_name="Рецепт",
        on_delete=models.CASCADE,
        related_name="ingredient",
        help_text="Рецепт",
    )

    ingredient = models.ForeignKey(
        Ingredient,
        verbose_name="Ингридиенты для рецепта",
        on_delete=models.CASCADE,
        related_name="ingredient",
        help_text="Ингридиетны"
    )

    amount = models.PositiveSmallIntegerField(
        default=settings.INGREDIENT_MIN_AMOUNT,
        validators=(
            MinValueValidator(
                settings.INGREDIENT_MIN_AMOUNT,
                message=settings.INGREDIENT_MIN_AMOUNT_ERROR
            ),
        ),
        verbose_name="Количество",
        help_text="Количество",
    )

    class Meta:
        ordering = ("recipe",)
        verbose_name = "Количество ингредиентов"
        verbose_name_plural = "Количество ингредиентов"
        constraints = [
            models.UniqueConstraint(
                fields=("recipe", "ingredient",),
                name="unique_ingredient",
            ),
        ]

    def __str__(self):
        return f'{self.ingredient} в {self.ingredient.measurement_unit}'


class Favorite(models.Model):
    """Модель избранного"""
    user = models.ForeignKey(
        User,
        verbose_name="Автор добавил рецепт в избранное",
        on_delete=models.CASCADE,
        related_name="author"
    )

    recipe = models.ForeignKey(
        Recipe,
        verbose_name="Избранный рецепт",
        on_delete=models.CASCADE,
        related_name="favorite",
        help_text="Избранный рецепт",
    )

    class Meta:
        ordering = ("id",)
        verbose_name = "Избранный рецепт"
        verbose_name_plural = "Избранные рецепты"
        constraints = [
            models.UniqueConstraint(
                fields=("user", "recipe",),
                name="unique_favorite",
            ),
        ]


class Foodbasket(models.Model):
    """Рецепты в корзине покупок.
    Модель связывает Recipe и  User.
    """
    user = models.ForeignKey(
        User,
        verbose_name="Пользователь добавивший покупки",
        on_delete=models.CASCADE,
        related_name="shopping",
        help_text="Пользователь добавивший покупки",
    )
    recipe = models.ForeignKey(
        Recipe,
        verbose_name="Рецепт для покупок",
        on_delete=models.CASCADE,
        related_name="shopping",
        help_text="Рецепт для покупок",
    )

    class Meta:
        ordering = ("id",)
        verbose_name = "Рецепт для покупок"
        verbose_name_plural = "Рецепты для покупок"
        constraints = [
            models.UniqueConstraint(
                fields=("user", "recipe",),
                name="unique_shoppingcart",
            ),
        ]
