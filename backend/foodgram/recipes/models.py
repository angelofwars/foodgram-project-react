from django.db import models
from django.core.validators import MinValueValidator
from backend.foodgram.foodgram.settings import QUERY_SET_LENGTH
from user.models import User


QUERY_SET_MODELS = 60

class Ingredient(models.Model):
    """Модель ингридиентов"""
    name = models.CharField(
        verbose_name="Ингридиенты",
        max_length=100,
        help_text="Ингридиенты"
    )
    # franchise = models.ForeignKey(Franchise)
    # diets = models.ManyToManyField(Diet, null=True, blank=True, verbose_name="special diets or food allergies")
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
        return self.name[:QUERY_SET_MODELS].capitalize()


class Tag(models.Model):
    """Модель тега"""
    name = models.CharField(
        verbose_name="Название",
        max_length=250,
        unique=True,
        help_text="Имя тега"
    )

    color = models.

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
        return self.name[:QUERY_SET_MODELS]

    def __unicode__(self):
        return self.name



class Recipe(models.Model):
    """Модель рецепта"""
    author = models.ForeignKey(
        User,
        verbose_name="Автор рецепта",
        default="Автор неизвестен",
        on_delete=models.SET_DEFAULT,
        related_name='author_recipe',
        help_text='Автора рецепта',
    )

    name = models.CharField(
        verbose_name="Название рецепта",
        max_length=75,

        help_text="Название рецепта"
    )

    image = models.ImageField(
        verbose_name='Изображение рецепта',
        upload_to='recipes/images',
        help_text='Изображение рецепта',
    )

    text = models.TextField(
        verbose_name="Напиши тут рецепт",
        help_text="Текст рецепта"
    )

    date = models.DateField()

    created_on = models.DateField(
        verbose_name="Дата публикации",
        auto_now_add=True,
        help_text="Дата публикации",
        )
    
    updated_on = models.DateField(
        auto_now=True
        )
    
    ingredients = models.ManyToManyField(
        Ingredient,
        verbose_name='Ингредиенты рецепта',
        through='RecipeIngredient',
        related_name='recipes',
        help_text='Ингредиенты рецепта',
    )

    tags = models.ManyToManyField(
        Tag,
        verbose_name='Тег рецепта',
        related_name='recipes',
        help_text='Тег рецепта',
    )


    cooking_time = models.IntegerField(
        verbose_name='Время приготовления',
        validators=[
            MinValueValidator(
                1,
                message='Время приготовления минимум 1 минута'
            )
        ],
        help_text='Время приготовления',
    )

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name[:QUERY_SET_MODELS]




class RecipeIngredient(models.Model):
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

    amount = models.IntegerField(
        verbose_name='Количество',
        validators=[
            MinValueValidator(
                1,
                message='Минимальное количество не меньше чем 1'
            )
        ],
        help_text='Количество',
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

class Follow(models.Model):
    pass

class Foodbasket(models.Model):
    pass
