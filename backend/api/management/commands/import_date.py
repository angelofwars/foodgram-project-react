import json

from django.core.management import BaseCommand
from recipes.models import Ingredient


class Command(BaseCommand):
    '''
    Заполнение БД модели Ingredient.
    '''

    help = 'Импорт данных из ingredients.json в таблицу recipes_ingredient'

    def handle(self, *args, **kwargs):
        with open('data/ingredients.json', 'r', encoding='utf-8') as f:
            data = json.load(f)

        for row in data:
            account = Ingredient(
                name=row['name'],
                measurement_unit=row['measurement_unit']
            )
            account.save()