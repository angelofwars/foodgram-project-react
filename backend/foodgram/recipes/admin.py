from django.contrib import admin
from .models import (Ingredient, Tag, Recipe, RecipeIngredient,
                     Foodbasket)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ("name", "measurement_unit",)
    list_filter = ("name",)
    search_fields = ("name",)
    ordering = ("measurement_unit",)
    empty_value_display = "-пусто-"


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "color", "slug",)
    search_fields = ("name", "slug",)
    ordering = ("color",)


class IngredientInRecipeInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 2
    min_num = 1

@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'author', 'count_favorites')
    list_filter = ('author', 'name', 'tags')

    def count_favorites(self, obj):
        return obj.favorites.count()


@admin.register(Foodbasket)
class FoodbasketAdmin(admin.ModelAdmin):
    list_display = ("user", "recipe", )
    empty_value_display = "-пусто-"

