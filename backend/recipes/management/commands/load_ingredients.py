import json

from django.conf import settings
from django.core.management.base import BaseCommand

from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'Загрузка данных из ingredients.json в базу данных.'
    INGREDIENT_LOAD_SUCCESS = 'Ингредиент "{name}" успешно добавлен.'
    INGREDIENT_LOAD_ERROR = 'Ошибка загрузки Ингредиента "{name}": {error}.'
    INGREDIENT_ALREADY_EXISTS = 'Ингредиент "{name}" уже существует.'

    def handle(self, *args, **kwargs):
        file_path = settings.BASE_DIR / 'static/data/ingredients.json'
        with open(file_path, 'r', encoding='utf-8') as file:
            ingredients = json.load(file)
            for ingredient_data in ingredients:
                try:
                    ingredient, created = Ingredient.objects.get_or_create(
                        name=ingredient_data['name'],
                        measurement_unit=ingredient_data['measurement_unit']
                    )
                    if created:
                        self.stdout.write(
                            self.style.SUCCESS(
                                self.INGREDIENT_LOAD_SUCCESS.format(
                                    name=ingredient_data['name']
                                )
                            )
                        )
                    else:
                        self.stdout.write(
                            self.style.WARNING(
                                self.INGREDIENT_ALREADY_EXISTS.format(
                                    name=ingredient_data['name']
                                )
                            )
                        )
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(
                            self.INGREDIENT_LOAD_ERROR.format(
                                name=ingredient_data['name'],
                                error=str(e)
                            )
                        )
                    )
